"""
MCQ API Endpoints

Handles MCQ generation, adaptive selection, and verification testing.

Endpoints:
- POST /api/v1/mcq/generate - Generate MCQs for a sense
- GET /api/v1/mcq/get - Get adaptive MCQ for verification
- GET /api/v1/mcq/session - Get multiple MCQs for a verification session
- POST /api/v1/mcq/bundles - Batch fetch verification bundles for pre-caching
- POST /api/v1/mcq/submit - Submit MCQ answer (with real-time gamification feedback)
- GET /api/v1/mcq/quality - Get MCQ quality report
- POST /api/v1/mcq/recalculate - Trigger quality recalculation
"""

import logging
from typing import Optional, List, Dict, Any, Generator, Tuple
from uuid import UUID
from datetime import datetime, date

from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import text

from src.database.postgres_connection import PostgresConnection
from src.database.neo4j_connection import Neo4jConnection
from src.middleware.auth import get_current_user_id
from src.mcq_adaptive import (
    MCQAdaptiveService,
    MCQSelection,
    AnswerResult,
    select_options_from_pool,
)
from src.database.postgres_crud import mcq_stats
from src.database.models import MCQPool, VerificationSchedule
from src.spaced_repetition import (
    get_algorithm_for_user,
    CardState,
    PerformanceRating,
)
from src.services.levels import LevelService
from src.services.achievements import AchievementService
from src.services.learning_velocity import LearningVelocityService
from src.services.currencies import CurrencyService
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
    pool_index: Optional[int] = Field(
        None,
        description="Index within stored mcq.options pool (used for grading alignment)"
    )


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
    selected_index: int = Field(..., ge=0, le=19, description="Selected option index (0-based, max 20 options)")
    selected_option_pool_index: Optional[int] = Field(
        None,
        ge=0,
        le=30,
        description="Selected option's index within stored mcq.options (preferred for accuracy)"
    )
    served_option_pool_indices: Optional[List[int]] = Field(
        None,
        description="Order of pool indices presented to the user (aligns correct_index in response)"
    )
    response_time_ms: Optional[int] = Field(None, description="Response time in milliseconds")
    verification_schedule_id: Optional[int] = Field(None, description="Link to spaced rep schedule")
    # FAST PATH: Frontend provides these so we skip DB fetch
    is_correct: Optional[bool] = Field(None, description="Frontend-verified correctness (skip DB fetch)")
    sense_id: Optional[str] = Field(None, description="Sense ID for recording (skip DB fetch)")
    correct_index: Optional[int] = Field(None, description="Correct answer index (for response)")


class SubmitBatchRequest(BaseModel):
    """Request to submit multiple MCQ answers in batch."""
    answers: List[SubmitAnswerRequest] = Field(..., description="List of answers to submit")


# ============================================
# Gamification Response Models (One-Shot Payload)
# ============================================

class LevelUpInfo(BaseModel):
    """Info when user levels up."""
    old_level: int
    new_level: int
    rewards: Optional[List[str]] = None


class AchievementUnlockedInfo(BaseModel):
    """Info for a newly unlocked achievement."""
    id: str
    code: str
    name_en: str
    name_zh: Optional[str] = None
    description_en: Optional[str] = None
    description_zh: Optional[str] = None
    icon: Optional[str] = None
    xp_reward: int = 0
    points_bonus: int = 0


class GamificationResult(BaseModel):
    """
    All gamification data returned after an action.
    
    This is the "One-Shot Payload" - everything the frontend needs
    to display immediate feedback (XP bar animation, level-up celebration,
    achievement toasts, etc.) in a single response.
    
    Three-Currency System:
    - sparks: Effort currency (earned from any activity)
    - essence: Skill currency (earned from correct answers)
    - energy: Building currency (earned from level-ups)
    - blocks: Mastered words (earned when word becomes Solid)
    """
    # Legacy XP fields (kept for backwards compatibility)
    xp_gained: int = Field(..., description="XP earned from this action (with multiplier applied)")
    total_xp: int = Field(..., description="User's total XP after this action")
    current_level: int = Field(..., description="User's current level")
    xp_to_next_level: int = Field(..., description="XP needed to reach next level")
    xp_in_current_level: int = Field(..., description="XP progress in current level")
    progress_percentage: int = Field(..., description="Progress % toward next level (0-100)")
    
    # Three-Currency System
    sparks_gained: int = Field(0, description="Sparks earned (effort currency)")
    sparks_total: int = Field(0, description="Total sparks balance")
    essence_gained: int = Field(0, description="Essence earned (skill currency, correct answers only)")
    essence_total: int = Field(0, description="Total essence balance")
    energy_gained: int = Field(0, description="Energy earned (from level-ups only)")
    energy_total: int = Field(0, description="Total energy balance")
    blocks_gained: int = Field(0, description="Blocks earned (word mastery)")
    blocks_total: int = Field(0, description="Total blocks balance")
    
    # Other gamification
    points_earned: int = Field(0, description="Cash points earned (separate from XP, no multiplier)")
    streak_extended: bool = Field(False, description="Whether daily streak was extended")
    streak_days: int = Field(0, description="Current streak in days")
    streak_multiplier: Optional[float] = Field(None, description="XP multiplier from streak (e.g., 2.0 for Day 7)")
    level_up: Optional[LevelUpInfo] = Field(None, description="Level up info if occurred")
    achievements_unlocked: List[AchievementUnlockedInfo] = Field(
        default_factory=list, 
        description="Newly unlocked achievements"
    )
    speed_warning: Optional[str] = Field(None, description="Warning if answered too fast")
    sync_status: Optional[str] = Field(
        None,
        description="Status of background processing: 'processing' indicates achievements are being checked"
    )


class SubmitAnswerResponse(BaseModel):
    """
    Response after submitting answer.
    
    Includes full gamification data for instant frontend feedback.
    """
    is_correct: bool
    correct_index: int
    explanation: str
    feedback: str
    ability_before: float
    ability_after: float
    mcq_difficulty: Optional[float]
    # Spaced repetition data (if verification_schedule_id was provided)
    verification_result: Optional[Dict[str, Any]] = None
    # NEW: Gamification data for instant feedback
    gamification: Optional[GamificationResult] = None


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
        
        # Select 6-option subset (5 distractors + 1 correct) based on user ability
        selected_options, new_correct_idx = select_options_from_pool(
            mcq.options,
            distractor_count=5,  # 5 distractors + 1 correct = 6 options
            user_ability=selection.user_ability
        )
        
        # Format selected options for frontend
        options = [
            MCQOptionResponse(
                text=opt.get('text', ''),
                source=opt.get('source', 'unknown'),
                pool_index=mcq.options.index(opt) if opt in mcq.options else None,
            )
            for opt in selected_options
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
            
            # Select 6-option subset (5 distractors + 1 correct)
            selected_options, new_correct_idx = select_options_from_pool(
                mcq.options,
                distractor_count=5,
                user_ability=selection.user_ability
            )
            
            options = [
                MCQOptionResponse(
                    text=opt.get('text', ''),
                    source=opt.get('source', 'unknown'),
                    pool_index=mcq.options.index(opt) if opt in mcq.options else None,
                )
                for opt in selected_options
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


# ============================================
# Verification Bundle Pre-Cache Endpoint
# ============================================

class VerificationBundleMCQ(BaseModel):
    """MCQ data for client-side caching (includes correct_index)."""
    mcq_id: str
    question: str
    context: Optional[str]
    options: List[MCQOptionResponse]
    correct_index: int  # Included for instant feedback!
    mcq_type: str


class VerificationBundle(BaseModel):
    """Complete verification data for a sense, cached locally."""
    sense_id: str
    word: str
    mcqs: List[VerificationBundleMCQ]


class GetBundlesRequest(BaseModel):
    """Request for batch verification bundles."""
    sense_ids: List[str] = Field(..., max_length=100, description="Sense IDs to get bundles for")


@router.post("/bundles", response_model=Dict[str, VerificationBundle])
async def get_verification_bundles(
    request: GetBundlesRequest,
    db: Session = Depends(get_db_session),
):
    """
    Batch fetch verification bundles for multiple senses.
    
    Returns pre-generated MCQs with correct_index for client-side caching.
    This enables instant MCQ loading and immediate answer feedback.
    
    Returns dict keyed by sense_id. Senses without MCQs are omitted.
    Max 100 senses per request.
    """
    result: Dict[str, VerificationBundle] = {}
    
    for sense_id in request.sense_ids[:100]:  # Enforce limit
        # Normalize sense_id (strip _N suffix if present)
        normalized = MCQAdaptiveService._normalize_sense_id(sense_id)
        
        # Get MCQs for this sense
        mcqs = mcq_stats.get_mcqs_for_sense(db, normalized, active_only=True)
        
        if mcqs and len(mcqs) > 0:
            mcqs_list = []
            for m in mcqs[:5]:  # Max 5 MCQs per sense
                # "Last War" approach: Pre-process at write time
                # Filter to 6 options (1 correct + 5 distractors)
                try:
                    selected_options, new_correct_idx = select_options_from_pool(
                        m.options,
                        distractor_count=5,  # 5 distractors + 1 correct = 6 total
                        user_ability=0.5,  # Default for pre-caching (no user context)
                        shuffle=True
                    )
                    
                    # Validate we have at least 4 options (minimum for valid MCQ)
                    # Accept 4-6 options (4 = 1 correct + 3 distractors, 6 = 1 correct + 5 distractors)
                    if len(selected_options) < 4 or len(selected_options) > 6:
                        logger.warning(
                            f"Skipping MCQ {m.id} for sense {sense_id}: "
                            f"Invalid option count: {len(selected_options)} (need 4-6). "
                            f"MCQ has {len(m.options)} total options in pool."
                        )
                        continue
                    
                    # Validate correct_index is within bounds
                    if new_correct_idx < 0 or new_correct_idx >= len(selected_options):
                        logger.warning(
                            f"Skipping MCQ {m.id} for sense {sense_id}: "
                            f"Invalid correct_index {new_correct_idx} for {len(selected_options)} options"
                        )
                        continue
                    
                    # Format options with pool_index for grading alignment
                    formatted_options = [
                        MCQOptionResponse(
                            text=opt.get('text', ''),
                            source=opt.get('source', 'unknown'),
                            pool_index=m.options.index(opt) if opt in m.options else None,
                        )
                        for opt in selected_options
                    ]
                    
                    mcqs_list.append(VerificationBundleMCQ(
                        mcq_id=str(m.id),
                        question=m.question,
                        context=m.context,
                        options=formatted_options,  # Already filtered to 6!
                        correct_index=new_correct_idx,  # Recalculated after filtering!
                        mcq_type=m.mcq_type,
                    ))
                except (ValueError, IndexError) as e:
                    # Skip MCQs that don't have enough options
                    logger.warning(f"Skipping MCQ {m.id} for sense {sense_id}: {e}")
                    continue
            
            if mcqs_list:
                result[sense_id] = VerificationBundle(
                    sense_id=sense_id,
                    word=mcqs[0].word,
                    mcqs=mcqs_list
                )
                # Log bundle generation for debugging
                logger.info(f"Bundle for {sense_id}: {len(mcqs_list)} MCQs, each with 6 options")
    
    logger.info(f"Returned verification bundles for {len(result)}/{len(request.sense_ids)} senses")
    return result


# ============================================
# Anti-Gaming & XP Calculation Helpers
# ============================================

# Speed trap threshold: answers faster than this are suspicious
MINIMUM_COGNITIVE_TIME_MS = 1500  # 1.5 seconds

# Base XP rewards
BASE_XP_CORRECT = 10
BASE_POINTS_CORRECT = 2


def _calculate_xp_with_speed_trap(
    is_correct: bool,
    response_time_ms: Optional[int],
    base_xp: int = BASE_XP_CORRECT
) -> Tuple[int, Optional[str]]:
    """
    Calculate XP with anti-gaming speed trap.
    
    Rules:
    - < 1500ms = 0 XP (too fast to have read the question - possible cheating)
    - >= 1500ms and correct = base_xp
    - incorrect = 0 XP
    
    Args:
        is_correct: Whether the answer was correct
        response_time_ms: Time taken to answer in milliseconds
        base_xp: Base XP to award for correct answer
        
    Returns:
        Tuple of (xp_amount, warning_message or None)
    """
    if not is_correct:
        return 0, None
    
    # Speed trap: if answer was too fast, they didn't read the question
    if response_time_ms is not None and response_time_ms < MINIMUM_COGNITIVE_TIME_MS:
        return 0, "回答太快了！請仔細閱讀題目。"  # "Too fast! Please read carefully."
    
    return base_xp, None


def _map_mcq_to_performance_rating(
    is_correct: bool,
    response_time_ms: Optional[int],
    mcq_difficulty: Optional[float],
) -> PerformanceRating:
    """
    Map MCQ result to performance rating (0-4) for spaced repetition.
    
    Updated logic with speed trap consideration:
    - < 1500ms correct → AGAIN (penalize gaming, not real knowledge)
    - < 1500ms incorrect → AGAIN (guessing)
    - Incorrect (tried) → AGAIN or HARD based on effort
    - Correct (normal time) → GOOD or EASY based on speed and difficulty
    """
    # Speed trap: too fast = didn't really know
    if response_time_ms is not None and response_time_ms < MINIMUM_COGNITIVE_TIME_MS:
        return PerformanceRating.AGAIN  # Whether correct or not, treat as guess
    
    if not is_correct:
        # Wrong answer
        if response_time_ms and response_time_ms > 10000:  # > 10 seconds = struggled
            return PerformanceRating.HARD  # They tried but failed
        else:
            return PerformanceRating.AGAIN  # Quick wrong = didn't know
    else:
        # Correct answer (and took reasonable time)
        if response_time_ms and response_time_ms < 3000:  # < 3 seconds = quick recall
            # If it's an easy MCQ, might be EASY, otherwise GOOD
            if mcq_difficulty and mcq_difficulty > 0.7:  # Easy MCQ
                return PerformanceRating.EASY
            else:
                return PerformanceRating.GOOD
        elif response_time_ms and response_time_ms < 8000:  # < 8 seconds = normal
            return PerformanceRating.GOOD
        else:
            # > 8 seconds = some effort, still good
            return PerformanceRating.GOOD


# --- Background Task Wrapper (CRITICAL: Must use fresh DB session) ---

def _save_batch_to_db(user_id: UUID, batch_data: List[Dict], total_xp: int):
    """
    Background task: Save batch answers to DB.
    Runs AFTER response is sent to user.
    """
    from src.database.models import MCQAttempt
    
    conn = PostgresConnection()
    db = conn.get_session()
    try:
        # 1. Record all attempts
        for item in batch_data:
            db.add(MCQAttempt(
                user_id=user_id,
                mcq_id=UUID(item['mcq_id']),
                sense_id=item['sense_id'],
                is_correct=item['is_correct'],
                response_time_ms=item['response_time_ms'],
                selected_option_index=item['selected_idx'],
                verification_schedule_id=item['schedule_id'],
                attempt_context='verification'
            ))
            
            # Mark schedule complete
            if item['schedule_id']:
                db.execute(text("""
                    UPDATE verification_schedule 
                    SET completed = true, completed_at = NOW(), passed = :passed
                    WHERE id = :sid AND user_id = :uid
                """), {'sid': item['schedule_id'], 'uid': user_id, 'passed': item['is_correct']})
        
        # 2. Award XP
        if total_xp > 0:
            level_service = LevelService(db)
            level_service.add_xp(user_id, total_xp, 'review')
        
        # 3. Award currencies for correct answers
        correct_count = sum(1 for item in batch_data if item['is_correct'])
        if correct_count > 0:
            currency_service = CurrencyService(db)
            for item in batch_data:
                if item['is_correct']:
                    try:
                        currency_service.award_mcq_result(user_id, True, False, False, None)
                    except:
                        pass
        
        db.commit()
        logger.info(f"✅ Background save: {len(batch_data)} answers, +{total_xp}XP for {user_id}")
        
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Background save failed: {e}")
    finally:
        db.close()


def _process_background_tasks(user_id: UUID, retry_count: int = 0):
    """
    Combined background task: Achievement checking + currency recalculation.
    
    CRITICAL: Uses its own DB session because the request session closes
    after the response is sent. Passing the request 'db' session will cause
    "Session is closed" errors.
    
    Args:
        user_id: User ID to process
        retry_count: Internal retry counter (for transient failures)
    """
    MAX_RETRIES = 2
    conn = PostgresConnection()  # Uses global engine singleton - safe to instantiate per task
    db = conn.get_session()
    try:
        # 1. Check achievements (the slowest part)
        achievement_service = AchievementService(db)
        newly_unlocked = achievement_service.check_achievements(user_id)
        logger.info(f"Background: Checked achievements for user {user_id}, unlocked {len(newly_unlocked)}")
        
        # 2. Update currency totals if needed (optional - can use cached values)
        currency_service = CurrencyService(db)
        # Recalculate totals if needed
        # This is optional - frontend can use cached values from immediate response
        logger.info(f"Background: Updated currency totals for user {user_id}")
        
        # Commit background updates
        db.commit()
        
    except Exception as e:
        db.rollback()
        # Retry on transient failures (connection errors, timeouts)
        if retry_count < MAX_RETRIES and ("connection" in str(e).lower() or "timeout" in str(e).lower()):
            import time
            time.sleep(1)  # Brief delay before retry
            logger.warning(f"Background task failed (attempt {retry_count + 1}/{MAX_RETRIES}), retrying: {e}")
            db.close()
            _process_background_tasks(user_id, retry_count + 1)
        else:
            logger.error(f"Background task failed after {retry_count + 1} attempts: {e}")
    finally:
        db.close()


@router.post("/submit", response_model=SubmitAnswerResponse)
async def submit_answer(
    request: SubmitAnswerRequest,
    background_tasks: BackgroundTasks,  # <--- ADD THIS
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db_session),
):
    """
    Submit an MCQ answer with real-time gamification feedback.
    
    Critical operations (answer, XP, spaced rep) return immediately.
    Heavy operations (achievements) run in background.
    
    This is the "One-Shot Payload" endpoint - returns everything needed for
    instant frontend feedback (XP gained, level-up) in a single response.
    Achievements are processed in background and available via polling endpoint.
    """
    try:
        service = MCQAdaptiveService(db)
        level_service = LevelService(db)
        achievement_service = AchievementService(db)
        
        # Get the MCQ to find correct answer
        mcq = mcq_stats.get_mcq_by_id(db, UUID(request.mcq_id))
        if not mcq:
            raise HTTPException(status_code=404, detail="MCQ not found")
        options = mcq.options or []
        
        # Resolve pool indices to keep grading aligned with served order
        correct_pool_index = next(
            (i for i, opt in enumerate(options) if opt.get("is_correct")),
            mcq.correct_index if mcq.correct_index is not None else 0
        )
        
        selected_pool_index: Optional[int] = None
        if request.selected_option_pool_index is not None:
            selected_pool_index = request.selected_option_pool_index
        elif request.served_option_pool_indices and request.selected_index < len(request.served_option_pool_indices):
            selected_pool_index = request.served_option_pool_indices[request.selected_index]
        elif request.selected_index < len(options):
            # Backward compatibility: assume served order matched stored order
            selected_pool_index = request.selected_index
        else:
            raise HTTPException(status_code=400, detail="Invalid selected option index")
        
        # Map correct index back to the order shown to the user, if provided
        response_correct_index: Optional[int] = None
        if request.served_option_pool_indices:
            try:
                response_correct_index = request.served_option_pool_indices.index(correct_pool_index)
            except ValueError:
                response_correct_index = None
        if response_correct_index is None:
            response_correct_index = mcq.correct_index if mcq.correct_index is not None else correct_pool_index
        
        # Process MCQ answer (existing logic - updates ability estimate, records attempt)
        result = service.process_answer(
            user_id=user_id,
            mcq_id=UUID(request.mcq_id),
            selected_index=request.selected_index,
            selected_pool_index=selected_pool_index,
            served_option_pool_indices=request.served_option_pool_indices,
            response_time_ms=request.response_time_ms,
            verification_schedule_id=request.verification_schedule_id
        )
        
        # ============================================
        # GAMIFICATION PROCESSING (One-Shot Payload)
        # ============================================
        
        velocity_service = LearningVelocityService(db)
        currency_service = CurrencyService(db)
        
        # Check streak and get multiplier
        current_streak = 0
        streak_extended = False
        xp_multiplier = 1.0
        try:
            current_streak, streak_extended, xp_multiplier = velocity_service.record_activity_and_check_streak(user_id)
        except Exception as e:
            logger.error(f"Failed to check streak: {e}")
            # Continue without streak bonus
        
        # Calculate XP with speed trap anti-gaming check
        base_xp, speed_warning = _calculate_xp_with_speed_trap(
            is_correct=result.is_correct,
            response_time_ms=request.response_time_ms,
            base_xp=BASE_XP_CORRECT
        )
        
        # Apply streak multiplier to XP (only if earned base XP)
        xp_to_award = int(base_xp * xp_multiplier) if base_xp > 0 else 0
        
        # ============================================
        # THREE-CURRENCY SYSTEM (Sparks, Essence, Energy, Blocks)
        # ============================================
        
        # Determine if answer was "fast" (< 5 seconds)
        is_fast = request.response_time_ms < 5000 if request.response_time_ms else False
        
        # Award currencies (no speed trap for sparks - everyone gets participation credit)
        currency_result = None
        try:
            # Check if word mastery changed (would need to check verification_result later)
            word_became_solid = False  # Will be updated after verification processing
            
            currency_result = currency_service.award_mcq_result(
                user_id=user_id,
                is_correct=result.is_correct,
                is_fast=is_fast,
                word_became_solid=word_became_solid,
                sense_id=None  # TODO: Get sense_id from MCQ
            )
        except Exception as e:
            logger.error(f"Failed to award currencies: {e}")
            currency_result = None
        
        # Get current currencies if currency_result failed
        if currency_result is None:
            try:
                currencies = currency_service.get_currencies(user_id)
                currency_result = {
                    'sparks': {'sparks_added': 0, 'sparks_total': currencies['sparks']},
                    'essence': {'essence_added': 0, 'essence_total': currencies['essence']},
                    'block': {'blocks_added': 0, 'blocks_total': currencies['blocks']},
                    'level_up': False,
                    'energy_granted': 0,
                }
            except Exception as e:
                logger.error(f"Failed to get currencies: {e}")
                currency_result = {
                    'sparks': {'sparks_added': 0, 'sparks_total': 0},
                    'essence': {'essence_added': 0, 'essence_total': 0},
                    'block': {'blocks_added': 0, 'blocks_total': 0},
                    'level_up': False,
                    'energy_granted': 0,
                }
        
        # Legacy XP awarding (for backwards compatibility)
        xp_result = None
        if xp_to_award > 0:
            try:
                xp_result = level_service.add_xp(user_id, xp_to_award, 'review')
            except Exception as e:
                logger.error(f"Failed to award XP: {e}")
                xp_result = None
        
        # Get current level info (even if no XP awarded)
        if xp_result is None:
            try:
                level_info = level_service.get_level_info(user_id)
                xp_result = {
                    'old_level': level_info['level'],
                    'new_level': level_info['level'],
                    'old_xp': level_info['total_xp'],
                    'new_xp': level_info['total_xp'],
                    'xp_added': 0,
                    'level_up': False,
                    'xp_to_next_level': level_info['xp_to_next_level'],
                    'xp_in_current_level': level_info['xp_in_current_level'],
                    'progress_percentage': level_info['progress_percentage']
                }
            except Exception as e:
                logger.error(f"Failed to get level info: {e}")
                xp_result = {
                    'old_level': 1, 'new_level': 1,
                    'old_xp': 0, 'new_xp': 0,
                    'xp_added': 0, 'level_up': False,
                    'xp_to_next_level': 100, 'xp_in_current_level': 0,
                    'progress_percentage': 0
                }
        
        # Calculate points earned (separate currency from XP - NO multiplier on cash!)
        points_earned = BASE_POINTS_CORRECT if result.is_correct and base_xp > 0 else 0
        
        # Build level-up info if applicable
        level_up_info = None
        if xp_result.get('level_up'):
            level_up_info = LevelUpInfo(
                old_level=xp_result['old_level'],
                new_level=xp_result['new_level'],
                rewards=[]  # TODO: Add level rewards in future
            )
        
        # Get current currencies for totals (use what we have, background will update)
        try:
            current_currencies = currency_service.get_currencies(user_id)
        except Exception as e:
            logger.error(f"Failed to get updated currencies: {e}")
            current_currencies = {'sparks': 0, 'essence': 0, 'energy': 0, 'blocks': 0}
        
        # Build the gamification result (achievements empty - will update in background)
        gamification = GamificationResult(
            # Legacy XP fields
            xp_gained=xp_to_award,
            total_xp=xp_result.get('new_xp', 0),
            current_level=xp_result.get('new_level', 1),
            xp_to_next_level=xp_result.get('xp_to_next_level', 100),
            xp_in_current_level=xp_result.get('xp_in_current_level', 0),
            progress_percentage=xp_result.get('progress_percentage', 0),
            # Three-Currency System
            sparks_gained=currency_result['sparks'].get('sparks_added', 0) if currency_result else 0,
            sparks_total=current_currencies.get('sparks', 0),
            essence_gained=currency_result['essence'].get('essence_added', 0) if currency_result else 0,
            essence_total=current_currencies.get('essence', 0),
            energy_gained=currency_result.get('energy_granted', 0) if currency_result else 0,
            energy_total=current_currencies.get('energy', 0),
            blocks_gained=currency_result['block'].get('blocks_added', 0) if currency_result else 0,
            blocks_total=current_currencies.get('blocks', 0),
            # Other gamification
            points_earned=points_earned,
            streak_extended=streak_extended,
            level_up=level_up_info,
            achievements_unlocked=[],  # Empty - processing in background
            speed_warning=speed_warning,
            streak_days=current_streak,
            streak_multiplier=xp_multiplier if xp_multiplier > 1.0 else None,
            # Don't set sync_status - frontend shouldn't block on background tasks
        )
        
        # ============================================
        # SPACED REPETITION PROCESSING (Existing Logic)
        # ============================================
        
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
                        # Map MCQ result to performance rating (with speed trap)
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
        
        # --- COMMIT CRITICAL TRANSACTION ---
        # Commit all critical updates before background tasks
        db.commit()
        
        # --- DEFERRED PHASE: Background Tasks ---
        # Single combined task runs AFTER the response is sent to the user
        background_tasks.add_task(
            _process_background_tasks,
            user_id  # Only pass user_id, not db session!
        )
        
        # Modify feedback to include speed warning if applicable
        feedback = result.feedback
        if speed_warning:
            feedback = speed_warning
        
        # Return IMMEDIATELY (~100-200ms total latency)
        return SubmitAnswerResponse(
            is_correct=result.is_correct,
            correct_index=response_correct_index,
            explanation=result.explanation,
            feedback=feedback,
            ability_before=result.ability_before,
            ability_after=result.ability_after,
            mcq_difficulty=result.mcq_difficulty,
            verification_result=verification_result,
            gamification=gamification  # One-Shot Payload
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to submit answer: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/submit-batch", response_model=List[SubmitAnswerResponse])
async def submit_batch_answers(
    request: SubmitBatchRequest,
    background_tasks: BackgroundTasks,
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db_session),
):
    """
    DELTA STRATEGY: Return only what changed, not totals.
    Frontend adds deltas to cached values.
    ~50ms response time.
    """
    import time
    start_time = time.time()
    answers = request.answers
    
    if not answers:
        raise HTTPException(status_code=400, detail="Empty batch")
    
    # PURE MATH - No DB reads for user state
    results = []
    total_xp_gained = 0
    total_points_gained = 0
    correct_count = 0
    batch_data = []  # For background processing
    
    # FAST PATH: If frontend provides is_correct and sense_id, skip DB fetch entirely
    # This makes the batch ~50ms instead of ~1500ms
    use_fast_path = all(ans.is_correct is not None and ans.sense_id for ans in answers)
    
    if use_fast_path:
        print(f"  ⚡ FAST PATH: Using frontend-verified data (no DB fetch)", flush=True)
    else:
        # SLOW PATH: Need to fetch MCQs from DB
        t_fetch = time.time()
        mcq_ids = [UUID(ans.mcq_id) for ans in answers if ans.is_correct is None or not ans.sense_id]
        mcqs_map = mcq_stats.get_mcqs_by_ids(db, mcq_ids) if mcq_ids else {}
        print(f"  MCQ batch fetch: {(time.time()-t_fetch)*1000:.0f}ms ({len(mcq_ids)} MCQs)", flush=True)
    
    for ans in answers:
        # FAST PATH: Use frontend-provided data
        if ans.is_correct is not None and ans.sense_id:
            is_correct = ans.is_correct
            sense_id = ans.sense_id
            display_correct_idx = ans.correct_index or 0
        else:
            # SLOW PATH: Look up from DB
            mcq = mcqs_map.get(UUID(ans.mcq_id))
            if not mcq:
                results.append(SubmitAnswerResponse(
                    is_correct=False, correct_index=0, explanation="", feedback="MCQ not found",
                    ability_before=0.5, ability_after=0.5, mcq_difficulty=None, verification_result=None,
                    gamification=GamificationResult(
                        xp_gained=0, total_xp=0, current_level=0, xp_to_next_level=0,
                        xp_in_current_level=0, progress_percentage=0,
                        sparks_gained=0, sparks_total=0, essence_gained=0, essence_total=0,
                        energy_gained=0, energy_total=0, blocks_gained=0, blocks_total=0,
                        points_earned=0, streak_extended=False, level_up=None,
                        achievements_unlocked=[], speed_warning=None, streak_days=0, streak_multiplier=None,
                    )
                ))
                continue
            
            options = mcq.options or []
            correct_idx = next((i for i, o in enumerate(options) if o.get("is_correct")), mcq.correct_index or 0)
            
            # Resolve what user selected
            selected_idx = ans.selected_index
            if ans.served_option_pool_indices and ans.selected_index < len(ans.served_option_pool_indices):
                selected_idx = ans.served_option_pool_indices[ans.selected_index]
            
            is_correct = (selected_idx == correct_idx)
            sense_id = mcq.sense_id
            
            # Map correct index back for frontend
            display_correct_idx = correct_idx
            if ans.served_option_pool_indices:
                try:
                    display_correct_idx = ans.served_option_pool_indices.index(correct_idx)
                except ValueError:
                    pass
        
        # PURE MATH - Calculate deltas
        xp_delta = BASE_XP_CORRECT if is_correct else 0
        points_delta = BASE_POINTS_CORRECT if is_correct else 0
        sparks_delta = 1 if is_correct else 0
        
        if is_correct:
            correct_count += 1
            total_xp_gained += xp_delta
            total_points_gained += points_delta
        
        # Collect for background save
        batch_data.append({
            'mcq_id': ans.mcq_id,
            'sense_id': sense_id,
            'is_correct': is_correct,
            'response_time_ms': ans.response_time_ms,
            'selected_idx': ans.selected_index,
            'schedule_id': ans.verification_schedule_id,
        })
        
        # Build response with DELTAS only (no totals!)
        results.append(SubmitAnswerResponse(
            is_correct=is_correct,
            correct_index=display_correct_idx,
            explanation="",  # Skip explanation for speed
            feedback="Correct!" if is_correct else "Incorrect",
            ability_before=0.5,
            ability_after=0.5,
            mcq_difficulty=None,
            verification_result=None,
            gamification=GamificationResult(
                # DELTAS - Frontend adds these to cached values
                xp_gained=xp_delta,
                points_earned=points_delta,
                sparks_gained=sparks_delta,
                streak_extended=True,  # They played today
                # Zeros for totals - frontend uses cache
                total_xp=0,
                current_level=0,
                xp_to_next_level=0,
                xp_in_current_level=0,
                progress_percentage=0,
                sparks_total=0,
                essence_gained=0,
                essence_total=0,
                energy_gained=0,
                energy_total=0,
                blocks_gained=0,
                blocks_total=0,
                level_up=None,
                achievements_unlocked=[],
                speed_warning=None,
                streak_days=0,
                streak_multiplier=None,
            )
        ))
    
    # Fire-and-forget: Save to DB in background
    background_tasks.add_task(
        _save_batch_to_db,
        user_id,
        batch_data,
        total_xp_gained,
    )
    
    elapsed = time.time() - start_time
    print(f"⚡ DELTA Batch: {len(results)} answers, {correct_count} correct, +{total_xp_gained}XP in {elapsed*1000:.0f}ms", flush=True)
    
    return results


@router.get("/achievements/recent", response_model=List[AchievementUnlockedInfo])
async def get_recent_achievements(
    seconds: int = Query(60, ge=1, le=300, description="Look back window in seconds"),
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db_session),
):
    """
    Get achievements unlocked in the last N seconds.
    
    Used by frontend to poll for achievements after MCQ submission.
    Frontend should call this 2-3 seconds after submission completes.
    """
    try:
        from datetime import timedelta
        cutoff = datetime.now() - timedelta(seconds=seconds)
        
        result = db.execute(
            text("""
                SELECT ua.achievement_id, a.code, a.name_en, a.name_zh,
                       a.description_en, a.description_zh, a.icon,
                       a.xp_reward, a.points_bonus
                FROM user_achievements ua
                JOIN achievements a ON ua.achievement_id = a.id
                WHERE ua.user_id = :user_id
                  AND ua.unlocked_at >= :cutoff
                ORDER BY ua.unlocked_at DESC
            """),
            {'user_id': user_id, 'cutoff': cutoff}
        )
        
        achievements = []
        for row in result.fetchall():
            achievements.append(AchievementUnlockedInfo(
                id=str(row[0]),
                code=row[1],
                name_en=row[2],
                name_zh=row[3],
                description_en=row[4],
                description_zh=row[5],
                icon=row[6],
                xp_reward=row[7] or 0,
                points_bonus=row[8] or 0
            ))
        
        return achievements
        
    except Exception as e:
        logger.error(f"Failed to get recent achievements: {e}")
        return []


@router.post("/generate", response_model=GenerateMCQsResponse)
async def generate_mcqs(
    request: GenerateMCQsRequest,
    db: Session = Depends(get_db_session),
):
    """
    Generate MCQs from VocabularyStore (V3 JSON format).
    
    Uses in-memory vocabulary.json - no Neo4j required.
    Falls back to Neo4j only if VocabularyStore not available.
    
    Requires admin or backend access (no user auth for internal use).
    """
    try:
        from src.mcq_assembler import MCQAssembler, store_mcqs_to_postgres
        from src.services.vocabulary_store import vocabulary_store
        
        # Check VocabularyStore availability
        if not vocabulary_store.is_loaded:
            # Fallback to Neo4j if available
            neo4j = get_neo4j_conn()
            if neo4j and neo4j.verify_connectivity():
                assembler = MCQAssembler(conn=neo4j)
            else:
                raise HTTPException(
                    status_code=503, 
                    detail="VocabularyStore not loaded. Run enrich_vocabulary_v2.py first."
                )
        else:
            # Use VocabularyStore (preferred)
            assembler = MCQAssembler()
        
        if request.sense_id:
            mcqs = assembler.assemble_mcqs_for_sense(request.sense_id)
        elif request.word:
            # Get sense IDs from VocabularyStore
            sense_ids = vocabulary_store.get_sense_ids_for_word(request.word)
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

