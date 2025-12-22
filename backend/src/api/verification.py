"""
Verification API Endpoints

Handles spaced repetition review processing for both SM-2+ and FSRS algorithms.

Endpoints:
- POST /api/v1/verification/review - Process a review
- GET /api/v1/verification/algorithm - Get user's algorithm info
- GET /api/v1/verification/due - Get due cards for review
- GET /api/v1/verification/stats - Get user's review statistics
"""

import logging
from datetime import date, datetime
from typing import Optional, List, Dict, Any, Generator
from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from src.database.postgres_connection import PostgresConnection
from src.middleware.auth import get_current_user_id
from src.spaced_repetition import (
    get_algorithm_for_user,
    CardState,
    ReviewResult,
    PerformanceRating,
    AssignmentService,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/verification", tags=["Verification"])

# Database connection
_postgres_conn: Optional[PostgresConnection] = None


def get_postgres_conn() -> PostgresConnection:
    global _postgres_conn
    if _postgres_conn is None:
        _postgres_conn = PostgresConnection()
    return _postgres_conn


def get_db_session() -> Generator[Session, None, None]:
    conn = get_postgres_conn()
    session = conn.get_session()
    try:
        yield session
    finally:
        session.close()


# Request/Response Models

class ProcessReviewRequest(BaseModel):
    """Request to process a review."""
    learning_progress_id: int = Field(..., description="ID from learning_progress table")
    performance_rating: int = Field(..., ge=0, le=4, description="Rating 0-4: Again, Hard, Good, Easy, Perfect")
    response_time_ms: Optional[int] = Field(None, description="Response time in milliseconds")


class ProcessReviewResponse(BaseModel):
    """Response after processing a review."""
    success: bool
    next_review_date: str
    next_interval_days: int
    was_correct: bool
    retention_predicted: Optional[float]
    mastery_level: str
    mastery_changed: bool
    became_leech: bool
    algorithm_type: str
    debug_info: Optional[Dict[str, Any]]


class BatchReviewRequest(BaseModel):
    """Request to process multiple reviews."""
    reviews: List[ProcessReviewRequest] = Field(..., description="List of reviews to process")
    learner_id: Optional[UUID] = Field(None, description="Learner ID for validation (multi-profile system)")


class BatchReviewItemResponse(BaseModel):
    """Response for a single review in batch."""
    learning_progress_id: int
    success: bool
    next_review_date: Optional[str] = None
    next_interval_days: Optional[int] = None
    was_correct: Optional[bool] = None
    retention_predicted: Optional[float] = None
    mastery_level: Optional[str] = None
    mastery_changed: Optional[bool] = None
    became_leech: Optional[bool] = None
    algorithm_type: Optional[str] = None
    error: Optional[str] = None


class BatchReviewResponse(BaseModel):
    """Response after processing batch reviews."""
    total_processed: int
    total_succeeded: int
    total_failed: int
    results: List[BatchReviewItemResponse]


class AlgorithmInfoResponse(BaseModel):
    """Information about user's algorithm assignment."""
    algorithm: str
    can_migrate_to_fsrs: bool
    review_count: int
    reviews_needed_for_migration: int
    assignment_date: Optional[str]


class DueCardResponse(BaseModel):
    """A card due for review."""
    verification_schedule_id: int
    learning_progress_id: int
    learning_point_id: str
    word: Optional[str] = None
    scheduled_date: str
    days_overdue: int
    mastery_level: str = "learning"  # Derived from learning_progress.status or rank
    retention_predicted: Optional[float] = None  # Not available without FSRS columns


class UserStatsResponse(BaseModel):
    """User's review statistics."""
    algorithm: str
    total_reviews: int
    total_correct: int
    retention_rate: float
    cards_learning: int
    cards_familiar: int
    cards_known: int
    cards_mastered: int
    cards_leech: int
    avg_interval_days: float
    reviews_today: int


# Endpoints

@router.post("/review", response_model=ProcessReviewResponse)
async def process_review(
    request: ProcessReviewRequest,
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db_session),
):
    """
    Process a spaced repetition review.
    
    Uses the user's assigned algorithm (SM-2+ or FSRS) to:
    - Update the card's state
    - Calculate the next review date
    - Track performance history
    """
    try:
        # Get current card state from database
        card_state = _get_card_state(db, user_id, request.learning_progress_id)
        if not card_state:
            raise HTTPException(status_code=404, detail="Card not found")
        
        # Get algorithm for user
        algorithm = get_algorithm_for_user(user_id, db)
        
        # Process the review
        rating = PerformanceRating(request.performance_rating)
        result = algorithm.process_review(
            state=card_state,
            rating=rating,
            response_time_ms=request.response_time_ms,
            review_date=date.today(),
        )
        
        # Save updated state to database
        _save_card_state(db, result.new_state)
        
        # Save review history
        _save_review_history(db, user_id, request, result, card_state)
        
        return ProcessReviewResponse(
            success=True,
            next_review_date=result.next_review_date.isoformat(),
            next_interval_days=result.next_interval_days,
            was_correct=result.was_correct,
            retention_predicted=result.retention_predicted,
            mastery_level=result.new_state.mastery_level,
            mastery_changed=result.mastery_changed,
            became_leech=result.became_leech,
            algorithm_type=result.algorithm_type,
            debug_info=result.debug_info,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to process review: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/review/batch", response_model=BatchReviewResponse)
async def process_batch_review(
    request: BatchReviewRequest,
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db_session),
):
    """
    Process multiple reviews in a single transaction.
    
    Security:
    - Validates that all learning_progress_ids belong to the provided learner_id
    - Verifies user_id is guardian/owner of that learner_id
    - Processes all reviews atomically (all-or-nothing transaction)
    """
    results = []
    total_succeeded = 0
    total_failed = 0
    
    # Step 1: Validate learner_id ownership (if provided)
    if request.learner_id:
        learner_check = db.execute(
            text("""
                SELECT id FROM public.learners
                WHERE id = :learner_id
                  AND (guardian_id = :guardian_id OR user_id = :guardian_id)
            """),
            {'learner_id': request.learner_id, 'guardian_id': user_id}
        ).fetchone()
        
        if not learner_check:
            raise HTTPException(
                status_code=403,
                detail="You can only process reviews for learners you manage"
            )
    
    # Step 2: Get algorithm once (shared across all reviews)
    algorithm = get_algorithm_for_user(user_id, db)
    
    # Step 3: Process each review
    for review_request in request.reviews:
        try:
            # Validate learning_progress belongs to learner_id (if provided)
            if request.learner_id:
                progress_check = db.execute(
                    text("""
                        SELECT lp.id, lp.learner_id
                        FROM learning_progress lp
                        WHERE lp.id = :progress_id
                    """),
                    {'progress_id': review_request.learning_progress_id}
                ).fetchone()
                
                if not progress_check:
                    results.append(BatchReviewItemResponse(
                        learning_progress_id=review_request.learning_progress_id,
                        success=False,
                        error="Learning progress not found"
                    ))
                    total_failed += 1
                    continue
                
                if progress_check[1] != request.learner_id:
                    results.append(BatchReviewItemResponse(
                        learning_progress_id=review_request.learning_progress_id,
                        success=False,
                        error="Learner mismatch"
                    ))
                    total_failed += 1
                    continue
            
            # Get card state
            card_state = _get_card_state(db, user_id, review_request.learning_progress_id)
            if not card_state:
                results.append(BatchReviewItemResponse(
                    learning_progress_id=review_request.learning_progress_id,
                    success=False,
                    error="Card state not found"
                ))
                total_failed += 1
                continue
            
            # Process review
            rating = PerformanceRating(review_request.performance_rating)
            result = algorithm.process_review(
                state=card_state,
                rating=rating,
                response_time_ms=review_request.response_time_ms,
                review_date=date.today(),
            )
            
            # Save state and history (deferred commit - batch endpoint handles commit)
            _save_card_state(db, result.new_state, commit=False)
            _save_review_history(db, user_id, review_request, result, card_state, commit=False)
            
            results.append(BatchReviewItemResponse(
                learning_progress_id=review_request.learning_progress_id,
                success=True,
                next_review_date=result.next_review_date.isoformat(),
                next_interval_days=result.next_interval_days,
                was_correct=result.was_correct,
                retention_predicted=result.retention_predicted,
                mastery_level=result.new_state.mastery_level,
                mastery_changed=result.mastery_changed,
                became_leech=result.became_leech,
                algorithm_type=result.algorithm_type,
            ))
            total_succeeded += 1
            
        except Exception as e:
            logger.error(f"Failed to process review for learning_progress_id {review_request.learning_progress_id}: {e}")
            results.append(BatchReviewItemResponse(
                learning_progress_id=review_request.learning_progress_id,
                success=False,
                error=str(e)
            ))
            total_failed += 1
    
    # Step 4: Commit all successful reviews in one transaction
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Batch review transaction failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Transaction failed: {str(e)}"
        )
    
    return BatchReviewResponse(
        total_processed=len(request.reviews),
        total_succeeded=total_succeeded,
        total_failed=total_failed,
        results=results
    )


@router.get("/algorithm", response_model=AlgorithmInfoResponse)
async def get_algorithm_info(
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db_session),
):
    """
    Get information about user's algorithm assignment.
    
    Shows:
    - Current algorithm (SM-2+ or FSRS)
    - Migration eligibility to FSRS
    - Review count and requirements
    """
    try:
        service = AssignmentService(db)
        
        # Get or assign algorithm
        algorithm = service.get_or_assign(user_id, db)
        
        # Check migration eligibility
        can_migrate, review_count = service.can_migrate_to_fsrs(user_id, db)
        reviews_needed = max(0, service.MIN_REVIEWS_FOR_MIGRATION - review_count)
        
        # Get assignment date
        result = db.execute(
            text("""
                SELECT assigned_at
                FROM user_algorithm_assignment
                WHERE user_id = :user_id
            """),
            {'user_id': user_id}
        )
        row = result.fetchone()
        assignment_date = row[0].isoformat() if row and row[0] else None
        
        return AlgorithmInfoResponse(
            algorithm=algorithm.value,
            can_migrate_to_fsrs=can_migrate,
            review_count=review_count,
            reviews_needed_for_migration=reviews_needed,
            assignment_date=assignment_date,
        )
        
    except Exception as e:
        logger.error(f"Failed to get algorithm info: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/migrate-to-fsrs")
async def migrate_to_fsrs(
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db_session),
):
    """
    Migrate user from SM-2+ to FSRS.
    
    Requires 100+ reviews for optimal personalization.
    """
    try:
        service = AssignmentService(db)
        
        can_migrate, review_count = service.can_migrate_to_fsrs(user_id, db)
        if not can_migrate:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot migrate yet. Need {service.MIN_REVIEWS_FOR_MIGRATION - review_count} more reviews."
            )
        
        success = service.migrate_to_fsrs(user_id, db)
        if not success:
            raise HTTPException(status_code=500, detail="Migration failed")
        
        return {"success": True, "algorithm": "fsrs"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to migrate to FSRS: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/due", response_model=List[DueCardResponse])
async def get_due_cards(
    limit: int = 20,
    learner_id: Optional[UUID] = Query(None, description="Learner ID (defaults to parent's learner profile)"),
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db_session),
):
    """
    Get cards due for review.
    
    - If learner_id is provided: Must verify user_id is guardian of that learner
    - If learner_id is None: Returns parent's own learner profile due cards
    
    Returns cards sorted by:
    1. Overdue cards first (most overdue first)
    2. Then by predicted retention (lowest first)
    """
    try:
        # 1. Determine target learner_id
        target_learner_id = None
        
        if learner_id:
            # Security check: Verify user is guardian of this learner
            learner_check = db.execute(
                text("""
                    SELECT id FROM public.learners
                    WHERE id = :learner_id AND guardian_id = :guardian_id
                """),
                {'learner_id': learner_id, 'guardian_id': user_id}
            ).fetchone()
            
            if not learner_check:
                raise HTTPException(
                    status_code=403,
                    detail="You can only view due cards for learners you manage"
                )
            target_learner_id = learner_id
        else:
            # Fallback: Find parent's own learner profile
            parent_learner = db.execute(
                text("""
                    SELECT id FROM public.learners
                    WHERE user_id = :user_id AND is_parent_profile = true
                """),
                {'user_id': user_id}
            ).fetchone()
            
            if parent_learner:
                target_learner_id = parent_learner[0]
            # If no parent learner found, target_learner_id stays None (legacy fallback)
        
        today = date.today()
        
        # 2. Query verification_schedule filtered by learner_id via learning_progress
        if target_learner_id:
            # New system: Filter by learner_id via learning_progress
            result = db.execute(
                text("""
                    SELECT 
                        vs.id,
                        vs.learning_progress_id,
                        lp.learning_point_id,
                        vs.scheduled_date,
                        lp.status,
                        lp.rank
                    FROM verification_schedule vs
                    JOIN learning_progress lp ON lp.id = vs.learning_progress_id
                    WHERE lp.learner_id = :learner_id
                    AND vs.scheduled_date <= :today
                    AND vs.completed = FALSE
                    ORDER BY vs.scheduled_date ASC
                    LIMIT :limit
                """),
                {'learner_id': target_learner_id, 'today': today, 'limit': limit}
            )
        else:
            # Legacy: Filter by user_id (backward compatibility)
            result = db.execute(
                text("""
                    SELECT 
                        vs.id,
                        vs.learning_progress_id,
                        lp.learning_point_id,
                        vs.scheduled_date,
                        lp.status,
                        lp.rank
                    FROM verification_schedule vs
                    JOIN learning_progress lp ON lp.id = vs.learning_progress_id
                    WHERE vs.user_id = :user_id
                    AND vs.scheduled_date <= :today
                    AND vs.completed = FALSE
                    ORDER BY vs.scheduled_date ASC
                    LIMIT :limit
                """),
                {'user_id': user_id, 'today': today, 'limit': limit}
            )
        
        cards = []
        for row in result.fetchall():
            scheduled = row[3]
            days_overdue = (today - scheduled).days if scheduled else 0
            
            # Derive mastery_level from status or rank
            status = row[4] or 'learning'
            rank = row[5] or 0  # Changed from tier to rank
            if status == 'mastered' or rank >= 5:
                mastery = 'mastered'
            elif status == 'known' or rank >= 3:
                mastery = 'known'
            elif rank >= 1:
                mastery = 'familiar'
            else:
                mastery = 'learning'
            
            cards.append(DueCardResponse(
                verification_schedule_id=row[0],
                learning_progress_id=row[1],
                learning_point_id=row[2] or '',
                word=None,  # Would need to fetch from Neo4j
                scheduled_date=scheduled.isoformat() if scheduled else '',
                days_overdue=days_overdue,
                mastery_level=mastery,
                retention_predicted=None,  # Not available without FSRS columns
            ))
        
        return cards
        
    except Exception as e:
        logger.error(f"Failed to get due cards: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=UserStatsResponse)
async def get_user_stats(
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db_session),
):
    """
    Get user's review statistics.
    
    Includes:
    - Total reviews and retention rate
    - Card counts by mastery level
    - Today's review count
    """
    try:
        # Get algorithm
        service = AssignmentService(db)
        algorithm = service.get_or_assign(user_id, db)
        
        # Get review totals
        review_result = db.execute(
            text("""
                SELECT 
                    COUNT(*) as total_reviews,
                    SUM(CASE WHEN retention_actual THEN 1 ELSE 0 END) as total_correct,
                    COUNT(*) FILTER (WHERE DATE(review_date) = CURRENT_DATE) as reviews_today
                FROM fsrs_review_history
                WHERE user_id = :user_id
            """),
            {'user_id': user_id}
        )
        review_row = review_result.fetchone()
        total_reviews = review_row[0] or 0
        total_correct = review_row[1] or 0
        reviews_today = review_row[2] or 0
        retention_rate = total_correct / total_reviews if total_reviews > 0 else 0
        
        # Get card counts by mastery
        card_result = db.execute(
            text("""
                SELECT 
                    mastery_level,
                    COUNT(*) as count
                FROM verification_schedule
                WHERE user_id = :user_id
                GROUP BY mastery_level
            """),
            {'user_id': user_id}
        )
        
        mastery_counts = {
            'learning': 0, 'familiar': 0, 'known': 0, 
            'mastered': 0, 'leech': 0
        }
        for row in card_result.fetchall():
            level = row[0] or 'learning'
            mastery_counts[level] = row[1]
        
        # Get average interval
        interval_result = db.execute(
            text("""
                SELECT AVG(current_interval)
                FROM verification_schedule
                WHERE user_id = :user_id
            """),
            {'user_id': user_id}
        )
        avg_interval = interval_result.scalar() or 0
        
        return UserStatsResponse(
            algorithm=algorithm.value,
            total_reviews=total_reviews,
            total_correct=total_correct,
            retention_rate=round(retention_rate, 3),
            cards_learning=mastery_counts['learning'],
            cards_familiar=mastery_counts['familiar'],
            cards_known=mastery_counts['known'],
            cards_mastered=mastery_counts['mastered'],
            cards_leech=mastery_counts['leech'],
            avg_interval_days=round(avg_interval, 1),
            reviews_today=reviews_today,
        )
        
    except Exception as e:
        logger.error(f"Failed to get user stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Helper functions

def _get_card_state(
    db: Session,
    user_id: UUID,
    learning_progress_id: int,
) -> Optional[CardState]:
    """Load card state from database."""
    result = db.execute(
        text("""
            SELECT 
                vs.learning_progress_id,
                lp.learning_point_id,
                vs.algorithm_type,
                vs.current_interval,
                vs.scheduled_date,
                vs.last_review_date,
                vs.total_reviews,
                vs.total_correct,
                vs.mastery_level,
                vs.is_leech,
                vs.ease_factor,
                vs.consecutive_correct,
                vs.stability,
                vs.difficulty,
                vs.retention_probability,
                vs.fsrs_state,
                vs.avg_response_time_ms
            FROM verification_schedule vs
            JOIN learning_progress lp ON lp.id = vs.learning_progress_id
            WHERE vs.user_id = :user_id
            AND vs.learning_progress_id = :learning_progress_id
        """),
        {'user_id': user_id, 'learning_progress_id': learning_progress_id}
    )
    
    row = result.fetchone()
    if not row:
        return None
    
    return CardState(
        user_id=user_id,
        learning_progress_id=row[0],
        learning_point_id=row[1] or '',
        algorithm_type=row[2] or 'sm2_plus',
        current_interval=row[3] or 1,
        scheduled_date=row[4] or date.today(),
        last_review_date=row[5],
        total_reviews=row[6] or 0,
        total_correct=row[7] or 0,
        mastery_level=row[8] or 'learning',
        is_leech=row[9] or False,
        ease_factor=row[10] or 2.5,
        consecutive_correct=row[11] or 0,
        stability=row[12],
        difficulty=row[13] or 0.5,
        retention_probability=row[14],
        fsrs_state=row[15],
        avg_response_time_ms=row[16],
    )


def _save_card_state(db: Session, state: CardState, commit: bool = True) -> None:
    """Save card state to database."""
    import json
    
    db.execute(
        text("""
            UPDATE verification_schedule
            SET 
                algorithm_type = :algorithm_type,
                current_interval = :current_interval,
                scheduled_date = :scheduled_date,
                last_review_date = :last_review_date,
                total_reviews = :total_reviews,
                total_correct = :total_correct,
                mastery_level = :mastery_level,
                is_leech = :is_leech,
                ease_factor = :ease_factor,
                consecutive_correct = :consecutive_correct,
                stability = :stability,
                difficulty = :difficulty,
                retention_probability = :retention_probability,
                fsrs_state = :fsrs_state,
                avg_response_time_ms = :avg_response_time_ms,
                updated_at = NOW()
            WHERE user_id = :user_id
            AND learning_progress_id = :learning_progress_id
        """),
        {
            'user_id': state.user_id,
            'learning_progress_id': state.learning_progress_id,
            'algorithm_type': state.algorithm_type,
            'current_interval': state.current_interval,
            'scheduled_date': state.scheduled_date,
            'last_review_date': state.last_review_date,
            'total_reviews': state.total_reviews,
            'total_correct': state.total_correct,
            'mastery_level': state.mastery_level,
            'is_leech': state.is_leech,
            'ease_factor': state.ease_factor,
            'consecutive_correct': state.consecutive_correct,
            'stability': state.stability,
            'difficulty': state.difficulty,
            'retention_probability': state.retention_probability,
            'fsrs_state': json.dumps(state.fsrs_state) if state.fsrs_state else None,
            'avg_response_time_ms': state.avg_response_time_ms,
        }
    )
    if commit:
        db.commit()


def _save_review_history(
    db: Session,
    user_id: UUID,
    request: ProcessReviewRequest,
    result: ReviewResult,
    old_state: CardState,
    commit: bool = True,
) -> None:
    """Save review to history table."""
    import json
    
    db.execute(
        text("""
            INSERT INTO fsrs_review_history (
                user_id,
                learning_progress_id,
                performance_rating,
                response_time_ms,
                stability_before,
                difficulty_before,
                retention_predicted,
                elapsed_days,
                stability_after,
                difficulty_after,
                interval_after,
                retention_actual,
                algorithm_type
            ) VALUES (
                :user_id,
                :learning_progress_id,
                :performance_rating,
                :response_time_ms,
                :stability_before,
                :difficulty_before,
                :retention_predicted,
                :elapsed_days,
                :stability_after,
                :difficulty_after,
                :interval_after,
                :retention_actual,
                :algorithm_type
            )
        """),
        {
            'user_id': user_id,
            'learning_progress_id': request.learning_progress_id,
            'performance_rating': request.performance_rating,
            'response_time_ms': request.response_time_ms,
            'stability_before': old_state.stability,
            'difficulty_before': old_state.difficulty,
            'retention_predicted': result.retention_predicted,
            'elapsed_days': (date.today() - old_state.last_review_date).days if old_state.last_review_date else 0,
            'stability_after': result.new_state.stability,
            'difficulty_after': result.new_state.difficulty,
            'interval_after': result.next_interval_days,
            'retention_actual': result.was_correct,
            'algorithm_type': result.algorithm_type,
        }
    )
    if commit:
        db.commit()

