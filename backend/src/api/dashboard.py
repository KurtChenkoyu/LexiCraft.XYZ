"""
Dashboard API Endpoints

Provides comprehensive learner status in a single API call.
Combines data from multiple sources for complete learner profile.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import text

from ..database.postgres_connection import PostgresConnection
from ..middleware.auth import get_current_user_id
from ..services.vocabulary_size import VocabularySizeService
from ..services.learning_velocity import LearningVelocityService
from ..services.levels import LevelService
from ..services.achievements import AchievementService
from ..spaced_repetition.assignment_service import AssignmentService

router = APIRouter(prefix="/api/v1/dashboard", tags=["Dashboard"])


# --- Response Models ---

class VocabularyStats(BaseModel):
    """Vocabulary statistics."""
    vocabulary_size: int
    frequency_bands: Dict[str, int]
    growth_rate_per_week: float


class ActivityStats(BaseModel):
    """Activity and velocity statistics."""
    words_learned_this_week: int
    words_learned_this_month: int
    activity_streak_days: int
    learning_rate_per_week: float
    last_active_date: Optional[str]


class PerformanceStats(BaseModel):
    """Performance metrics."""
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


class PointsStats(BaseModel):
    """Points and earnings statistics."""
    total_earned: int
    available_points: int
    locked_points: int
    withdrawn_points: int


class GamificationStats(BaseModel):
    """Gamification statistics."""
    level: int
    total_xp: int
    xp_to_next_level: int
    xp_in_current_level: int
    progress_percentage: int
    unlocked_achievements: int
    total_achievements: int
    recent_achievements: List[Dict]


class DashboardResponse(BaseModel):
    """Complete dashboard response."""
    learner_profile: Dict[str, Any]
    vocabulary: VocabularyStats
    activity: ActivityStats
    performance: PerformanceStats
    points: PointsStats
    gamification: GamificationStats


# --- Dependency Injection ---

def get_db_session():
    """Get database session."""
    conn = PostgresConnection()
    return conn.get_session()


@router.get("", response_model=DashboardResponse)
async def get_dashboard(
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db_session)
):
    """
    Get complete learner dashboard data.
    
    Combines:
    - Vocabulary size and growth
    - Learning velocity and activity
    - Performance metrics
    - Points and earnings
    
    Returns comprehensive learner status in a single API call.
    """
    try:
        # 1. Vocabulary Statistics
        vocab_service = VocabularySizeService(db)
        vocab_stats = vocab_service.get_vocabulary_stats(user_id)
        
        # 2. Activity and Velocity
        velocity_service = LearningVelocityService(db)
        activity_stats = velocity_service.get_activity_summary(user_id)
        
        # 3. Gamification (Level, XP, Achievements)
        level_service = LevelService(db)
        achievement_service = AchievementService(db)
        
        level_info = level_service.get_level_info(user_id)
        achievements = achievement_service.get_user_achievements(user_id)
        unlocked_count = sum(1 for a in achievements if a['unlocked'])
        recent_achievements = achievement_service.get_recent_achievements(user_id, days=7)
        
        # 4. Performance Metrics (from verification system)
        assignment_service = AssignmentService(db)
        algorithm = assignment_service.get_or_assign(user_id, db)
        
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
        
        # 5. Points Statistics
        points_result = db.execute(
            text("""
                SELECT 
                    total_earned,
                    available_points,
                    locked_points,
                    withdrawn_points
                FROM points_accounts
                WHERE user_id = :user_id
            """),
            {'user_id': user_id}
        )
        points_row = points_result.fetchone()
        
        if points_row:
            points_stats = {
                "total_earned": points_row[0] or 0,
                "available_points": points_row[1] or 0,
                "locked_points": points_row[2] or 0,
                "withdrawn_points": points_row[3] or 0
            }
        else:
            points_stats = {
                "total_earned": 0,
                "available_points": 0,
                "locked_points": 0,
                "withdrawn_points": 0
            }
        
        # Compile learner profile summary
        learner_profile = {
            "user_id": str(user_id),
            "vocabulary_size": vocab_stats["vocabulary_size"],
            "words_learned_this_week": activity_stats["words_learned_this_week"],
            "words_learned_this_month": activity_stats["words_learned_this_month"],
            "activity_streak": activity_stats["activity_streak_days"],
            "learning_rate": activity_stats["learning_rate_per_week"],
            "retention_rate": round(retention_rate, 3),
            "total_reviews": total_reviews,
            "cards_mastered": mastery_counts['mastered']
        }
        
        return DashboardResponse(
            learner_profile=learner_profile,
            vocabulary=VocabularyStats(
                vocabulary_size=vocab_stats["vocabulary_size"],
                frequency_bands=vocab_stats["frequency_bands"],
                growth_rate_per_week=vocab_stats["growth_rate_per_week"]
            ),
            activity=ActivityStats(**activity_stats),
            performance=PerformanceStats(
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
                reviews_today=reviews_today
            ),
            points=PointsStats(**points_stats),
            gamification=GamificationStats(
                level=level_info['level'],
                total_xp=level_info['total_xp'],
                xp_to_next_level=level_info['xp_to_next_level'],
                xp_in_current_level=level_info['xp_in_current_level'],
                progress_percentage=level_info['progress_percentage'],
                unlocked_achievements=unlocked_count,
                total_achievements=len(achievements),
                recent_achievements=recent_achievements
            )
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get dashboard: {str(e)}")
    finally:
        db.close()

