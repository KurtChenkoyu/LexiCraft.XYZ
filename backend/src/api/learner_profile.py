"""
Learner Profile API

Gamified learner profile endpoints - exciting, achievement-focused view.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import text

from ..database.postgres_connection import PostgresConnection
from ..middleware.auth import get_current_user_id
from ..services.achievements import AchievementService
from ..services.levels import LevelService
from ..services.learning_velocity import LearningVelocityService
from ..services.vocabulary_size import VocabularySizeService

router = APIRouter(prefix="/api/v1/profile/learner", tags=["Learner Profile"])


# --- Response Models ---

class AchievementInfo(BaseModel):
    """Achievement information."""
    id: str
    code: str
    name_en: str
    name_zh: Optional[str]
    description_en: Optional[str]
    description_zh: Optional[str]
    icon: Optional[str]
    category: str
    tier: str
    unlocked: bool
    unlocked_at: Optional[str]
    progress: int
    progress_percentage: Optional[int] = None


class LevelInfo(BaseModel):
    """Level information."""
    level: int
    total_xp: int
    xp_to_next_level: int
    xp_in_current_level: int
    progress_percentage: int


class StreakInfo(BaseModel):
    """Streak information."""
    current_streak: int
    longest_streak: int
    streak_at_risk: bool
    days_until_risk: Optional[int] = None


class LearnerProfileResponse(BaseModel):
    """Complete learner profile response."""
    user_id: str
    level: LevelInfo
    vocabulary_size: int
    current_streak: int
    words_learned_this_week: int
    words_learned_this_month: int
    recent_achievements: List[AchievementInfo]
    total_achievements: int
    unlocked_achievements: int


# --- Dependency Injection ---

def get_db_session():
    """Get database session with proper cleanup."""
    conn = PostgresConnection()
    session = conn.get_session()
    try:
        yield session
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


@router.get("", response_model=LearnerProfileResponse)
async def get_learner_profile(
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db_session)
):
    """
    Get complete learner profile (gamified view).
    
    Returns exciting, achievement-focused data for learners.
    """
    try:
        # Initialize services
        level_service = LevelService(db)
        achievement_service = AchievementService(db)
        velocity_service = LearningVelocityService(db)
        vocab_service = VocabularySizeService(db)
        
        # Get level info
        level_info = level_service.get_level_info(user_id)
        
        # Get vocabulary stats
        vocab_stats = vocab_service.get_vocabulary_stats(user_id)
        
        # Get activity stats
        activity_stats = velocity_service.get_activity_summary(user_id)
        
        # Get recent achievements (last 7 days)
        recent_achievements_data = achievement_service.get_recent_achievements(user_id, days=7)
        recent_achievements = [
            AchievementInfo(**ach) for ach in recent_achievements_data
        ]
        
        # Get total achievement counts
        all_achievements = achievement_service.get_user_achievements(user_id)
        total_achievements = len(all_achievements)
        unlocked_achievements = sum(1 for ach in all_achievements if ach['unlocked'])
        
        return LearnerProfileResponse(
            user_id=str(user_id),
            level=LevelInfo(**level_info),
            vocabulary_size=vocab_stats['vocabulary_size'],
            current_streak=activity_stats['activity_streak_days'],
            words_learned_this_week=activity_stats['words_learned_this_week'],
            words_learned_this_month=activity_stats['words_learned_this_month'],
            recent_achievements=recent_achievements,
            total_achievements=total_achievements,
            unlocked_achievements=unlocked_achievements
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to get learner profile: {str(e)}")


@router.get("/achievements", response_model=List[AchievementInfo])
async def get_achievements(
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db_session)
):
    """
    Get all achievements with user's progress.
    
    Returns all achievements, showing which are unlocked and progress toward others.
    """
    try:
        achievement_service = AchievementService(db)
        achievements_data = achievement_service.get_user_achievements(user_id)
        
        achievements = []
        for ach in achievements_data:
            # Calculate progress percentage
            if ach['requirement_value'] > 0:
                progress_pct = min(100, int((ach['progress'] / ach['requirement_value']) * 100))
            else:
                progress_pct = 0
            
            achievements.append(AchievementInfo(
                id=ach['id'],
                code=ach['code'],
                name_en=ach['name_en'],
                name_zh=ach.get('name_zh'),
                description_en=ach.get('description_en'),
                description_zh=ach.get('description_zh'),
                icon=ach.get('icon'),
                category=ach['category'],
                tier=ach['tier'],
                unlocked=ach['unlocked'],
                unlocked_at=ach.get('unlocked_at'),
                progress=ach['progress'],
                progress_percentage=progress_pct
            ))
        
        return achievements
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to get achievements: {str(e)}")


@router.get("/level", response_model=LevelInfo)
async def get_level_info(
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db_session)
):
    """
    Get level and XP information.
    
    Returns current level, XP progress, and progress to next level.
    """
    try:
        level_service = LevelService(db)
        level_info = level_service.get_level_info(user_id)
        
        return LevelInfo(**level_info)
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to get level info: {str(e)}")


@router.get("/streaks", response_model=StreakInfo)
async def get_streaks(
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db_session)
):
    """
    Get streak information.
    
    Returns current streak, longest streak, and risk status.
    """
    try:
        velocity_service = LearningVelocityService(db)
        activity_stats = velocity_service.get_activity_summary(user_id)
        
        current_streak = activity_stats['activity_streak_days']
        
        # Get longest streak (from leaderboard or calculate)
        result = db.execute(
            text("SELECT longest_streak FROM leaderboard_entries WHERE user_id = :user_id"),
            {'user_id': user_id}
        )
        row = result.fetchone()
        longest_streak = row[0] if row else current_streak
        
        # Check if streak is at risk (no activity today)
        today_result = db.execute(
            text("""
                SELECT COUNT(*) FROM learning_progress
                WHERE user_id = :user_id
                AND DATE(learned_at) = CURRENT_DATE
            """),
            {'user_id': user_id}
        )
        has_activity_today = (today_result.scalar() or 0) > 0
        
        # Streak is at risk if no activity today and it's past a certain time
        # For simplicity, we'll say it's at risk if no activity today
        streak_at_risk = not has_activity_today and current_streak > 0
        
        return StreakInfo(
            current_streak=current_streak,
            longest_streak=longest_streak,
            streak_at_risk=streak_at_risk,
            days_until_risk=0 if streak_at_risk else None
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to get streaks: {str(e)}")


@router.post("/check-achievements")
async def check_achievements(
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db_session)
):
    """
    Manually trigger achievement check.
    
    Checks all achievements and unlocks any newly earned ones.
    Returns list of newly unlocked achievements.
    """
    try:
        achievement_service = AchievementService(db)
        newly_unlocked = achievement_service.check_achievements(user_id)
        
        return {
            'newly_unlocked': newly_unlocked,
            'count': len(newly_unlocked)
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to check achievements: {str(e)}")


