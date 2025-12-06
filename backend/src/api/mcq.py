"""
MCQ API Endpoints

Handles MCQ generation, adaptive selection, and verification testing.

Endpoints:
- POST /api/v1/mcq/generate - Generate MCQs for a sense
- GET /api/v1/mcq/get - Get adaptive MCQ for verification
- POST /api/v1/mcq/submit - Submit MCQ answer
- GET /api/v1/mcq/quality - Get MCQ quality report
- POST /api/v1/mcq/recalculate - Trigger quality recalculation
"""

import logging
from typing import Optional, List, Dict, Any, Generator
from uuid import UUID
from datetime import datetime, date

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import text

from src.database.postgres_connection import PostgresConnection
from src.database.neo4j_connection import Neo4jConnection
from src.middleware.auth import get_current_user_id
from src.mcq_adaptive import MCQAdaptiveService, MCQSelection, AnswerResult
from src.database.postgres_crud import mcq_stats
from src.database.models import MCQPool, VerificationSchedule
from src.spaced_repetition import (
    get_algorithm_for_user,
    CardState,
    PerformanceRating,
)
# Helper functions for verification integration (duplicated from verification.py to avoid circular imports)
def _get_card_state_for_mcq(
    db: Session,
    user_id: UUID,
    learning_progress_id: int,
) -> Optional[CardState]:
    """Load card state from database (for MCQ integration)."""
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


def _save_card_state_for_mcq(db: Session, state: CardState) -> None:
    """Save card state to database (for MCQ integration)."""
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


def _save_review_history_for_mcq(
    db: Session,
    user_id: UUID,
    learning_progress_id: int,
    performance_rating: int,
    response_time_ms: Optional[int],
    review_result: Any,  # ReviewResult from algorithm
    old_state: CardState,
) -> None:
    """Save review to history table (for MCQ integration)."""
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
            'learning_progress_id': learning_progress_id,
            'performance_rating': performance_rating,
            'response_time_ms': response_time_ms,
            'stability_before': old_state.stability,
            'difficulty_before': old_state.difficulty,
            'retention_predicted': review_result.retention_predicted,
            'elapsed_days': (date.today() - old_state.last_review_date).days if old_state.last_review_date else 0,
            'stability_after': review_result.new_state.stability,
            'difficulty_after': review_result.new_state.difficulty,
            'interval_after': review_result.next_interval_days,
            'retention_actual': review_result.was_correct,
            'algorithm_type': review_result.algorithm_type,
        }
    )

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/mcq", tags=["MCQ"])

# Database connections
_postgres_conn: Optional[PostgresConnection] = None
_neo4j_conn: Optional[Neo4jConnection] = None


def get_postgres_conn() -> PostgresConnection:
    global _postgres_conn
    if _postgres_conn is None:
        _postgres_conn = PostgresConnection()
    return _postgres_conn


def get_neo4j_conn() -> Neo4jConnection:
    global _neo4j_conn
    if _neo4j_conn is None:
        _neo4j_conn = Neo4jConnection()
    return _neo4j_conn


def get_db_session() -> Generator[Session, None, None]:
    conn = get_postgres_conn()
    session = conn.get_session()
    try:
        yield session
    finally:
        session.close()


# ============================================
# Request/Response Models
# ============================================

class MCQOptionResponse(BaseModel):
    """A single MCQ option."""
    text: str
    source: str  # 'target', 'confused', 'opposite', 'similar'


class MCQResponse(BaseModel):
    """MCQ for frontend display."""
    mcq_id: str
    sense_id: str
    word: str
    mcq_type: str
    question: str
    context: Optional[str]
    options: List[MCQOptionResponse]
    user_ability: float
    mcq_difficulty: Optional[float]
    selection_reason: str


class SubmitAnswerRequest(BaseModel):
    """Request to submit an MCQ answer."""
    mcq_id: str = Field(..., description="MCQ ID")
    selected_index: int = Field(..., ge=0, le=5, description="Selected option index (0-based)")
    response_time_ms: Optional[int] = Field(None, description="Response time in milliseconds")
    verification_schedule_id: Optional[int] = Field(None, description="Link to spaced rep schedule")


class SubmitAnswerResponse(BaseModel):
    """Response after submitting answer."""
    is_correct: bool
    correct_index: int
    explanation: str
    feedback: str
    ability_before: float
    ability_after: float
    mcq_difficulty: Optional[float]
    # Spaced repetition data (if verification_schedule_id was provided)
    verification_result: Optional[Dict[str, Any]] = None


class GenerateMCQsRequest(BaseModel):
    """Request to generate MCQs."""
    sense_id: Optional[str] = Field(None, description="Specific sense ID")
    word: Optional[str] = Field(None, description="Word to generate MCQs for")
    limit: int = Field(10, ge=1, le=100, description="Number of senses to process")
    store: bool = Field(True, description="Store generated MCQs")


class GenerateMCQsResponse(BaseModel):
    """Response after generating MCQs."""
    generated: int
    stored: int
    by_type: Dict[str, int]


class QualityReportResponse(BaseModel):
    """MCQ quality report."""
    total_mcqs: int
    active_mcqs: int
    needs_review: int
    quality_distribution: Dict[str, int]
    avg_quality_score: Optional[float]
    total_attempts: int


class MCQIssueResponse(BaseModel):
    """MCQ needing attention."""
    mcq_id: str
    word: str
    sense_id: str
    mcq_type: str
    issue: str
    reason: str
    quality_score: Optional[float]


# ============================================
# Endpoints
# ============================================

@router.get("/get", response_model=MCQResponse)
async def get_mcq_for_verification(
    sense_id: str = Query(..., description="Sense ID to get MCQ for"),
    mcq_type: Optional[str] = Query(None, description="MCQ type: meaning, usage, discrimination"),
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db_session),
):
    """
    Get an MCQ for verification testing.
    
    Uses adaptive selection to match MCQ difficulty to user's ability level.
    """
    try:
        service = MCQAdaptiveService(db)
        
        selection = service.get_mcq_for_verification(
            user_id=user_id,
            sense_id=sense_id,
            mcq_type=mcq_type
        )
        
        if not selection:
            raise HTTPException(
                status_code=404, 
                detail=f"No MCQ available for sense {sense_id}"
            )
        
        mcq = selection.mcq
        
        # Format options for frontend (hide is_correct)
        options = [
            MCQOptionResponse(
                text=opt.get('text', ''),
                source=opt.get('source', 'unknown')
            )
            for opt in mcq.options
        ]
        
        return MCQResponse(
            mcq_id=str(mcq.id),
            sense_id=mcq.sense_id,
            word=mcq.word,
            mcq_type=mcq.mcq_type,
            question=mcq.question,
            context=mcq.context,
            options=options,
            user_ability=selection.user_ability,
            mcq_difficulty=selection.mcq_difficulty,
            selection_reason=selection.selection_reason
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get MCQ: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/session", response_model=List[MCQResponse])
async def get_mcqs_for_session(
    sense_id: str = Query(..., description="Sense ID to verify"),
    count: int = Query(3, ge=1, le=5, description="Number of MCQs"),
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db_session),
):
    """
    Get multiple MCQs for a verification session.
    
    Returns a mix of MCQ types (meaning, usage, discrimination).
    """
    try:
        service = MCQAdaptiveService(db)
        
        selections = service.get_mcqs_for_session(
            user_id=user_id,
            sense_id=sense_id,
            count=count
        )
        
        if not selections:
            raise HTTPException(
                status_code=404,
                detail=f"No MCQs available for sense {sense_id}"
            )
        
        responses = []
        for selection in selections:
            mcq = selection.mcq
            options = [
                MCQOptionResponse(
                    text=opt.get('text', ''),
                    source=opt.get('source', 'unknown')
                )
                for opt in mcq.options
            ]
            
            responses.append(MCQResponse(
                mcq_id=str(mcq.id),
                sense_id=mcq.sense_id,
                word=mcq.word,
                mcq_type=mcq.mcq_type,
                question=mcq.question,
                context=mcq.context,
                options=options,
                user_ability=selection.user_ability,
                mcq_difficulty=selection.mcq_difficulty,
                selection_reason=selection.selection_reason
            ))
        
        return responses
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get MCQ session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def _map_mcq_to_performance_rating(
    is_correct: bool,
    response_time_ms: Optional[int],
    mcq_difficulty: Optional[float],
) -> PerformanceRating:
    """
    Map MCQ result to performance rating (0-4).
    
    Logic:
    - Incorrect → AGAIN (0) or HARD (1) based on response time
    - Correct → GOOD (2) or EASY (3) based on response time and difficulty
    """
    if not is_correct:
        # Wrong answer
        if response_time_ms and response_time_ms > 10000:  # > 10 seconds = struggled
            return PerformanceRating.HARD  # They tried but failed
        else:
            return PerformanceRating.AGAIN  # Quick wrong = didn't know
    else:
        # Correct answer
        if response_time_ms and response_time_ms < 2000:  # < 2 seconds = instant recall
            return PerformanceRating.EASY
        elif response_time_ms and response_time_ms < 5000:  # < 5 seconds = quick recall
            # If it's an easy MCQ, might be EASY, otherwise GOOD
            if mcq_difficulty and mcq_difficulty > 0.7:  # Easy MCQ
                return PerformanceRating.EASY
            else:
                return PerformanceRating.GOOD
        else:
            # > 5 seconds = some effort
            return PerformanceRating.GOOD


@router.post("/submit", response_model=SubmitAnswerResponse)
async def submit_answer(
    request: SubmitAnswerRequest,
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db_session),
):
    """
    Submit an MCQ answer.
    
    Records the attempt, updates statistics, and if verification_schedule_id is provided,
    also processes the spaced repetition review.
    """
    try:
        service = MCQAdaptiveService(db)
        
        # Get the MCQ to find correct answer
        mcq = mcq_stats.get_mcq_by_id(db, UUID(request.mcq_id))
        if not mcq:
            raise HTTPException(status_code=404, detail="MCQ not found")
        
        # Process MCQ answer
        result = service.process_answer(
            user_id=user_id,
            mcq_id=UUID(request.mcq_id),
            selected_index=request.selected_index,
            response_time_ms=request.response_time_ms,
            verification_schedule_id=request.verification_schedule_id
        )
        
        # If verification_schedule_id is provided, also process spaced repetition
        verification_result = None
        if request.verification_schedule_id:
            try:
                # Get verification schedule to find learning_progress_id
                schedule = db.query(VerificationSchedule).filter(
                    VerificationSchedule.id == request.verification_schedule_id,
                    VerificationSchedule.user_id == user_id
                ).first()
                
                if schedule:
                    # Get current card state
                    card_state = _get_card_state_for_mcq(db, user_id, schedule.learning_progress_id)
                    
                    if card_state:
                        # Map MCQ result to performance rating
                        rating = _map_mcq_to_performance_rating(
                            result.is_correct,
                            request.response_time_ms,
                            result.mcq_difficulty
                        )
                        
                        # Get algorithm for user
                        algorithm = get_algorithm_for_user(user_id, db)
                        
                        # Process the review
                        review_result = algorithm.process_review(
                            state=card_state,
                            rating=rating,
                            response_time_ms=request.response_time_ms,
                            review_date=date.today(),
                        )
                        
                        # Save updated state
                        _save_card_state_for_mcq(db, review_result.new_state)
                        
                        # Save review history
                        _save_review_history_for_mcq(
                            db,
                            user_id,
                            schedule.learning_progress_id,
                            int(rating),
                            request.response_time_ms,
                            review_result,
                            card_state
                        )
                        
                        # Mark verification schedule as completed
                        schedule.completed = True
                        schedule.completed_at = datetime.now()
                        schedule.passed = result.is_correct
                        schedule.score = 1.0 if result.is_correct else 0.0
                        db.commit()
                        
                        verification_result = {
                            "next_review_date": review_result.next_review_date.isoformat(),
                            "next_interval_days": review_result.next_interval_days,
                            "was_correct": review_result.was_correct,
                            "retention_predicted": review_result.retention_predicted,
                            "mastery_level": review_result.new_state.mastery_level,
                            "mastery_changed": review_result.mastery_changed,
                            "became_leech": review_result.became_leech,
                            "algorithm_type": review_result.algorithm_type,
                        }
                    else:
                        logger.warning(
                            f"Card state not found for verification_schedule_id {request.verification_schedule_id}"
                        )
                else:
                    logger.warning(
                        f"Verification schedule {request.verification_schedule_id} not found for user {user_id}"
                    )
            except Exception as e:
                logger.error(f"Failed to process verification review: {e}")
                # Don't fail the MCQ submission if verification fails
                # Just log the error and continue
        
        return SubmitAnswerResponse(
            is_correct=result.is_correct,
            correct_index=mcq.correct_index,
            explanation=result.explanation,
            feedback=result.feedback,
            ability_before=result.ability_before,
            ability_after=result.ability_after,
            mcq_difficulty=result.mcq_difficulty,
            verification_result=verification_result
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to submit answer: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate", response_model=GenerateMCQsResponse)
async def generate_mcqs(
    request: GenerateMCQsRequest,
    db: Session = Depends(get_db_session),
):
    """
    Generate MCQs from Neo4j enriched content.
    
    Requires admin or backend access (no user auth for internal use).
    """
    try:
        from src.mcq_assembler import MCQAssembler, store_mcqs_to_postgres
        
        neo4j = get_neo4j_conn()
        if not neo4j.verify_connectivity():
            raise HTTPException(status_code=503, detail="Neo4j not available")
        
        assembler = MCQAssembler(neo4j)
        
        if request.sense_id:
            mcqs = assembler.assemble_mcqs_for_sense(request.sense_id)
        elif request.word:
            with neo4j.get_session() as session:
                result = session.run("""
                    MATCH (w:Word {name: $word})-[:HAS_SENSE]->(s:Sense)
                    WHERE s.stage2_enriched = true OR s.enriched = true
                    RETURN s.id as sense_id
                """, word=request.word)
                sense_ids = [r["sense_id"] for r in result]
            
            mcqs = []
            for sid in sense_ids:
                mcqs.extend(assembler.assemble_mcqs_for_sense(sid))
        else:
            mcqs = assembler.assemble_mcqs_batch(limit=request.limit)
        
        # Count by type
        by_type = {}
        for mcq in mcqs:
            mcq_type = mcq.mcq_type.value
            by_type[mcq_type] = by_type.get(mcq_type, 0) + 1
        
        # Store if requested
        stored = 0
        if request.store and mcqs:
            stored = store_mcqs_to_postgres(mcqs, db)
        
        return GenerateMCQsResponse(
            generated=len(mcqs),
            stored=stored,
            by_type=by_type
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate MCQs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/quality", response_model=QualityReportResponse)
async def get_quality_report(
    db: Session = Depends(get_db_session),
):
    """
    Get MCQ quality summary report.
    
    Shows overall quality metrics for the MCQ pool.
    """
    try:
        service = MCQAdaptiveService(db)
        report = service.get_quality_report()
        
        return QualityReportResponse(
            total_mcqs=report['total_mcqs'],
            active_mcqs=report['active_mcqs'],
            needs_review=report['needs_review'],
            quality_distribution=report['quality_distribution'],
            avg_quality_score=report['avg_quality_score'],
            total_attempts=report['total_attempts']
        )
        
    except Exception as e:
        logger.error(f"Failed to get quality report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/needs-attention", response_model=List[MCQIssueResponse])
async def get_mcqs_needing_attention(
    limit: int = Query(20, ge=1, le=100, description="Maximum MCQs to return"),
    db: Session = Depends(get_db_session),
):
    """
    Get MCQs that need attention (low quality or flagged).
    
    Useful for quality assurance review.
    """
    try:
        service = MCQAdaptiveService(db)
        issues = service.get_mcqs_needing_attention(limit=limit)
        
        return [
            MCQIssueResponse(
                mcq_id=item['mcq_id'],
                word=item['word'],
                sense_id=item['sense_id'],
                mcq_type=item['mcq_type'],
                issue=item['issue'],
                reason=item['reason'],
                quality_score=item.get('quality_score')
            )
            for item in issues
        ]
        
    except Exception as e:
        logger.error(f"Failed to get MCQs needing attention: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/recalculate")
async def recalculate_quality_metrics(
    db: Session = Depends(get_db_session),
):
    """
    Trigger recalculation of MCQ quality metrics.
    
    Recalculates difficulty index, discrimination index, and quality score
    for all MCQs with new attempts since last calculation.
    """
    try:
        service = MCQAdaptiveService(db)
        count = service.trigger_quality_recalculation()
        
        return {
            "success": True,
            "recalculated": count,
            "message": f"Recalculated quality for {count} MCQs"
        }
        
    except Exception as e:
        logger.error(f"Failed to recalculate quality: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/user")
async def get_user_mcq_stats(
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db_session),
):
    """
    Get user's MCQ statistics.
    
    Shows total attempts, correct rate, and ability estimate.
    """
    try:
        service = MCQAdaptiveService(db)
        
        # Get overall stats
        total, correct = mcq_stats.count_user_attempts(db, user_id)
        
        # Get ability estimates for recently tested senses
        recent_attempts = mcq_stats.get_user_recent_attempts(db, user_id, limit=50)
        
        # Get unique senses
        sense_ids = list(set(a.sense_id for a in recent_attempts))[:10]
        
        sense_abilities = {}
        for sense_id in sense_ids:
            ability = service.estimate_ability(user_id, sense_id)
            sense_abilities[sense_id] = {
                "ability": ability.ability,
                "confidence": ability.confidence,
                "source": ability.source.value
            }
        
        return {
            "total_attempts": total,
            "correct_attempts": correct,
            "accuracy": correct / total if total > 0 else 0,
            "senses_tested": len(sense_ids),
            "sense_abilities": sense_abilities
        }
        
    except Exception as e:
        logger.error(f"Failed to get user MCQ stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

