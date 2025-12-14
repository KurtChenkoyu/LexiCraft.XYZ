"""
Words API Endpoints

Handles starting verification for words/learning points.

Endpoints:
- POST /api/v1/words/start-verification - Start verification for a word (with gamification)
"""

import logging
from typing import Optional, Generator, List
from uuid import UUID
from datetime import date

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import text

from src.database.postgres_connection import PostgresConnection
from src.middleware.auth import get_current_user_id
from src.database.postgres_crud.progress import (
    create_learning_progress,
    get_learning_progress_by_learning_point,
)
from src.database.postgres_crud.verification import create_verification_schedule
from src.services.levels import LevelService
from src.services.achievements import AchievementService
from src.services.learning_velocity import LearningVelocityService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/words", tags=["Words"])

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

# XP reward for learning a new word
BASE_XP_WORD_LEARNED = 15  # Higher than review (10) since learning is harder


class StartVerificationRequest(BaseModel):
    """Request to start verification for a word."""
    learning_point_id: str = Field(..., description="The learning point ID")
    tier: int = Field(..., ge=1, le=5, description="Initial tier (1-5)")
    initial_difficulty: float = Field(0.5, ge=0.0, le=1.0, description="Initial difficulty")


# Gamification Response Models (consistent with MCQ)
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
    """Gamification data for word learning."""
    xp_gained: int = Field(..., description="XP earned from learning this word")
    total_xp: int = Field(..., description="User's total XP after this action")
    current_level: int = Field(..., description="User's current level")
    xp_to_next_level: int = Field(..., description="XP needed to reach next level")
    xp_in_current_level: int = Field(..., description="XP progress in current level")
    progress_percentage: int = Field(..., description="Progress % toward next level (0-100)")
    streak_extended: bool = Field(False, description="Whether daily streak was extended")
    streak_days: int = Field(0, description="Current streak in days")
    streak_multiplier: Optional[float] = Field(None, description="XP multiplier from streak")
    level_up: Optional[LevelUpInfo] = Field(None, description="Level up info if occurred")
    achievements_unlocked: List[AchievementUnlockedInfo] = Field(
        default_factory=list, 
        description="Newly unlocked achievements"
    )


class StartVerificationResponse(BaseModel):
    """Response after starting verification."""
    success: bool
    learning_progress_id: int
    verification_schedule_id: int
    learning_point_id: str
    status: str
    scheduled_date: str
    algorithm_type: str
    mastery_level: str
    message: str
    # Gamification data (only for new words)
    gamification: Optional[GamificationResult] = None


# Endpoints

@router.post("/start-verification", response_model=StartVerificationResponse)
async def start_verification(
    request: StartVerificationRequest,
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db_session),
):
    """
    Start verification for a word/learning point.
    
    Creates:
    - A learning_progress entry with status='pending'
    - A verification_schedule entry using the user's assigned algorithm
    - Awards XP for learning a new word (with streak multiplier)
    
    The verification schedule will be initialized with the appropriate
    algorithm (SM-2+ or FSRS) and scheduled for the first review.
    """
    try:
        # Initialize services
        level_service = LevelService(db)
        achievement_service = AchievementService(db)
        velocity_service = LearningVelocityService(db)
        
        # Check if learning_progress already exists for this user + learning_point_id
        existing_progress = get_learning_progress_by_learning_point(
            session=db,
            user_id=user_id,
            learning_point_id=request.learning_point_id,
        )
        
        if existing_progress:
            # Check if verification schedule also exists
            result = db.execute(
                text("""
                    SELECT id, algorithm_type, scheduled_date, mastery_level
                    FROM verification_schedule
                    WHERE user_id = :user_id
                    AND learning_progress_id = :learning_progress_id
                """),
                {
                    'user_id': user_id,
                    'learning_progress_id': existing_progress.id,
                }
            )
            schedule_row = result.fetchone()
            
            if schedule_row:
                # Both exist, return existing entry info (no XP - already learned)
                return StartVerificationResponse(
                    success=True,
                    learning_progress_id=existing_progress.id,
                    verification_schedule_id=schedule_row[0],
                    learning_point_id=request.learning_point_id,
                    status=existing_progress.status or 'pending',
                    scheduled_date=schedule_row[2].isoformat() if schedule_row[2] else date.today().isoformat(),
                    algorithm_type=schedule_row[1] or 'sm2_plus',
                    mastery_level=schedule_row[3] or 'learning',
                    message="Verification already exists for this word",
                    gamification=None,  # No XP for existing word
                )
            else:
                # Learning progress exists but no schedule - create schedule only
                schedule = create_verification_schedule(
                    session=db,
                    user_id=user_id,
                    learning_progress_id=existing_progress.id,
                    learning_point_id=request.learning_point_id,
                    initial_difficulty=request.initial_difficulty,
                )
                
                return StartVerificationResponse(
                    success=True,
                    learning_progress_id=existing_progress.id,
                    verification_schedule_id=schedule.id,
                    learning_point_id=request.learning_point_id,
                    status=existing_progress.status or 'pending',
                    scheduled_date=schedule.scheduled_date.isoformat() if schedule.scheduled_date else date.today().isoformat(),
                    algorithm_type=schedule.algorithm_type or 'sm2_plus',
                    mastery_level=schedule.mastery_level or 'learning',
                    message="Verification schedule created for existing learning progress",
                    gamification=None,  # No XP for existing word
                )
        
        # ============================================
        # NEW WORD - Award XP!
        # ============================================
        
        # Create new learning_progress entry with status='pending'
        progress = create_learning_progress(
            session=db,
            user_id=user_id,
            learning_point_id=request.learning_point_id,
            tier=request.tier,
            status='pending',  # Use 'pending' as specified
        )
        
        # Create verification_schedule entry
        # This automatically uses the user's assigned algorithm
        schedule = create_verification_schedule(
            session=db,
            user_id=user_id,
            learning_progress_id=progress.id,
            learning_point_id=request.learning_point_id,
            initial_difficulty=request.initial_difficulty,
        )
        
        # ============================================
        # PRE-GENERATE MCQs (if not exists)
        # ============================================
        try:
            from src.database.postgres_crud.mcq_stats import get_mcqs_for_sense
            from src.mcq_assembler import MCQAssembler, store_mcqs_to_postgres
            from src.services.vocabulary_store import vocabulary_store
            import re
            
            # Normalize sense_id (strip index suffix like _99)
            def normalize_sense_id(sense_id: str) -> str:
                match = re.match(r'^(.+\.\w+\.\d+)_\d+$', sense_id)
                return match.group(1) if match else sense_id
            
            normalized_sense_id = normalize_sense_id(request.learning_point_id)
            
            # Check if MCQs already exist for this sense
            existing_mcqs = get_mcqs_for_sense(db, normalized_sense_id)
            if not existing_mcqs:
                # Generate and store MCQs
                if vocabulary_store.is_loaded:
                    assembler = MCQAssembler()
                    mcqs = assembler.assemble_mcqs_for_sense(normalized_sense_id)
                    if mcqs:
                        stored = store_mcqs_to_postgres(mcqs, db)
                        logger.info(f"Generated {stored} MCQs for {normalized_sense_id}")
                    else:
                        logger.warning(f"No MCQs generated for {normalized_sense_id}")
        except Exception as e:
            # Don't fail the request if MCQ generation fails
            logger.warning(f"Failed to pre-generate MCQs for {request.learning_point_id}: {e}")
        
        # ============================================
        # GAMIFICATION PROCESSING
        # ============================================
        
        # Check streak and get multiplier
        current_streak = 0
        streak_extended = False
        xp_multiplier = 1.0
        try:
            current_streak, streak_extended, xp_multiplier = velocity_service.record_activity_and_check_streak(user_id)
        except Exception as e:
            logger.error(f"Failed to check streak: {e}")
        
        # Calculate XP with streak multiplier
        xp_to_award = int(BASE_XP_WORD_LEARNED * xp_multiplier)
        
        # Award XP
        xp_result = None
        try:
            xp_result = level_service.add_xp(user_id, xp_to_award, 'word_learned')
        except Exception as e:
            logger.error(f"Failed to award XP: {e}")
        
        # Get level info if XP award failed
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
        
        # Check for newly unlocked achievements
        newly_unlocked = []
        try:
            newly_unlocked = achievement_service.check_achievements(user_id)
        except Exception as e:
            logger.error(f"Failed to check achievements: {e}")
        
        # Build level-up info if applicable
        level_up_info = None
        if xp_result.get('level_up'):
            level_up_info = LevelUpInfo(
                old_level=xp_result['old_level'],
                new_level=xp_result['new_level'],
                rewards=[]
            )
        
        # Build achievement unlocked list
        achievements_unlocked = [
            AchievementUnlockedInfo(
                id=str(a.get('achievement_id', '')),
                code=a.get('code', ''),
                name_en=a.get('name_en', ''),
                name_zh=a.get('name_zh'),
                description_en=a.get('description_en'),
                description_zh=a.get('description_zh'),
                icon=a.get('icon'),
                xp_reward=a.get('xp_reward', 0),
                points_bonus=a.get('points_bonus', 0)
            )
            for a in newly_unlocked
        ]
        
        # Build gamification result
        gamification = GamificationResult(
            xp_gained=xp_to_award,
            total_xp=xp_result.get('new_xp', 0),
            current_level=xp_result.get('new_level', 1),
            xp_to_next_level=xp_result.get('xp_to_next_level', 100),
            xp_in_current_level=xp_result.get('xp_in_current_level', 0),
            progress_percentage=xp_result.get('progress_percentage', 0),
            streak_extended=streak_extended,
            streak_days=current_streak,
            streak_multiplier=xp_multiplier if xp_multiplier > 1.0 else None,
            level_up=level_up_info,
            achievements_unlocked=achievements_unlocked,
        )
        
        return StartVerificationResponse(
            success=True,
            learning_progress_id=progress.id,
            verification_schedule_id=schedule.id,
            learning_point_id=request.learning_point_id,
            status=progress.status or 'pending',
            scheduled_date=schedule.scheduled_date.isoformat() if schedule.scheduled_date else date.today().isoformat(),
            algorithm_type=schedule.algorithm_type or 'sm2_plus',
            mastery_level=schedule.mastery_level or 'learning',
            message="Verification started successfully",
            gamification=gamification,  # Include XP data for new word
        )
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Invalid input: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid input: {str(e)}")
    except Exception as e:
        logger.error(f"Failed to start verification: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to start verification: {str(e)}")

