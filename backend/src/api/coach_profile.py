"""
Coach/Parent Profile API

Analytics-focused endpoints for parents and coaches - informative, data-driven view.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import text

from ..database.postgres_connection import PostgresConnection
from ..middleware.auth import get_current_user_id
from ..services.vocabulary_size import VocabularySizeService
from ..services.learning_velocity import LearningVelocityService
from ..services.achievements import AchievementService
from ..services.levels import LevelService
from ..services.goals import GoalsService

router = APIRouter(prefix="/api/v1/profile/coach", tags=["Coach Profile"])


# --- Response Models ---

class LearningTrend(BaseModel):
    """Learning trend data point."""
    date: str
    words_learned: int
    vocabulary_size: int
    reviews_completed: int


class PerformanceInsight(BaseModel):
    """Performance insight."""
    type: str  # 'improvement', 'concern', 'milestone', 'recommendation'
    title: str
    message: str
    priority: str  # 'high', 'medium', 'low'
    data: Optional[Dict] = None


class PeerComparison(BaseModel):
    """Peer comparison data (anonymized)."""
    metric: str
    learner_value: float
    peer_average: float
    peer_percentile: int  # 0-100


class CoachDashboardResponse(BaseModel):
    """Complete coach dashboard response."""
    learner_id: str
    overview: Dict[str, Any]
    vocabulary: Dict[str, Any]
    activity: Dict[str, Any]
    performance: Dict[str, Any]
    trends: List[LearningTrend]
    insights: List[PerformanceInsight]
    peer_comparison: List[PeerComparison]
    goals: List[Dict]
    achievements: Dict[str, Any]


# --- Dependency Injection ---

def get_db_session():
    """Get database session."""
    conn = PostgresConnection()
    return conn.get_session()


def verify_coach_access(coach_id: UUID, learner_id: UUID, db: Session) -> bool:
    """
    Verify that coach has access to learner's data.
    
    Checks for:
    - Parent-child relationship
    - Coach-student relationship
    - Same user (self-access)
    """
    # Check if same user
    if coach_id == learner_id:
        return True
    
    # Check for parent-child relationship
    result = db.execute(
        text("""
            SELECT COUNT(*) FROM user_relationships
            WHERE (user_id = :coach_id AND related_user_id = :learner_id AND relationship_type = 'parent')
            OR (user_id = :learner_id AND related_user_id = :coach_id AND relationship_type = 'child')
        """),
        {'coach_id': coach_id, 'learner_id': learner_id}
    )
    
    if result.scalar() > 0:
        return True
    
    # Check for coach-student relationship
    result = db.execute(
        text("""
            SELECT COUNT(*) FROM user_relationships
            WHERE (user_id = :coach_id AND related_user_id = :learner_id AND relationship_type = 'coach')
            OR (user_id = :learner_id AND related_user_id = :coach_id AND relationship_type = 'student')
        """),
        {'coach_id': coach_id, 'learner_id': learner_id}
    )
    
    return result.scalar() > 0


@router.get("/{learner_id}", response_model=CoachDashboardResponse)
async def get_coach_dashboard(
    learner_id: UUID,
    coach_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db_session)
):
    """
    TEMPORARY STUB for Emoji MVP.
    Coach features are disabled - returns empty dashboard data.
    """
    try:
        db.close()  # Close the session immediately since we're not using it
    except:
        pass
    
    # Return minimal valid response to satisfy the schema
    return CoachDashboardResponse(
        learner_id=str(learner_id),
        overview={}, 
        vocabulary={}, 
        activity={}, 
        performance={}, 
        trends=[], 
        insights=[], 
        peer_comparison=[], 
        goals=[], 
        achievements={}
    )


@router.get("/{learner_id}/analytics")
async def get_detailed_analytics(
    learner_id: UUID,
    coach_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db_session)
):
    """
    TEMPORARY STUB for Emoji MVP.
    Coach features are disabled - returns empty analytics data.
    """
    try:
        db.close()  # Close the session immediately since we're not using it
    except:
        pass
    
    # Return minimal valid response structure
    return {
        'vocabulary_growth': {
            'timeline': [],
            'current_size': 0,
            'growth_rate': 0.0
        },
        'weekly_activity': [],
        'xp_earnings': {
            'history': [],
            'summary': {}
        }
    }


@router.get("/{learner_id}/insights")
async def get_insights(
    learner_id: UUID,
    coach_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db_session)
):
    """
    TEMPORARY STUB for Emoji MVP.
    Coach features are disabled - returns empty insights data.
    """
    try:
        db.close()  # Close the session immediately since we're not using it
    except:
        pass
    
    # Return minimal valid response structure
    return {
        'insights': [],
        'generated_at': datetime.now().isoformat()
    }


@router.get("/{learner_id}/compare")
async def get_peer_comparison_endpoint(
    learner_id: UUID,
    coach_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db_session)
):
    """
    TEMPORARY STUB for Emoji MVP.
    Coach features are disabled - returns empty peer comparison data.
    """
    try:
        db.close()  # Close the session immediately since we're not using it
    except:
        pass
    
    # Return minimal valid response structure
    return {
        'comparisons': [],
        'note': 'All peer data is anonymized for privacy'
    }


# --- Helper Functions ---

def generate_insights(
    vocab_stats: Dict,
    activity_stats: Dict,
    level_info: Dict,
    retention_rate: float,
    goals: List[Dict],
    db: Session,
    learner_id: UUID
) -> List[PerformanceInsight]:
    """Generate performance insights."""
    insights = []
    
    # Check streak risk
    if activity_stats['activity_streak_days'] > 0:
        today_result = db.execute(
            text("""
                SELECT COUNT(*) FROM learning_progress
                WHERE user_id = :user_id
                AND DATE(learned_at) = CURRENT_DATE
            """),
            {'user_id': learner_id}
        )
        has_activity_today = (today_result.scalar() or 0) > 0
        
        if not has_activity_today:
            insights.append(PerformanceInsight(
                type='concern',
                title='Streak at Risk',
                message=f"Your learner has a {activity_stats['activity_streak_days']}-day streak but hasn't been active today. Encourage them to complete a review to maintain their streak!",
                priority='high',
                data={'streak_days': activity_stats['activity_streak_days']}
            ))
    
    # Check learning rate
    if activity_stats['learning_rate_per_week'] > 0:
        if activity_stats['learning_rate_per_week'] < 5:
            insights.append(PerformanceInsight(
                type='recommendation',
                title='Increase Learning Pace',
                message=f"Current learning rate is {activity_stats['learning_rate_per_week']:.1f} words/week. Consider setting a goal to increase engagement.",
                priority='medium',
                data={'current_rate': activity_stats['learning_rate_per_week']}
            ))
        elif activity_stats['learning_rate_per_week'] > 20:
            insights.append(PerformanceInsight(
                type='improvement',
                title='Excellent Learning Pace',
                message=f"Great progress! Learning at {activity_stats['learning_rate_per_week']:.1f} words/week is above average.",
                priority='low',
                data={'current_rate': activity_stats['learning_rate_per_week']}
            ))
    
    # Check retention rate
    if retention_rate < 0.7:
        insights.append(PerformanceInsight(
            type='concern',
            title='Review Retention',
            message=f"Retention rate is {retention_rate:.1%}. Consider more frequent reviews or adjusting difficulty.",
            priority='high',
            data={'retention_rate': retention_rate}
        ))
    elif retention_rate > 0.9:
        insights.append(PerformanceInsight(
            type='improvement',
            title='Excellent Retention',
            message=f"Outstanding retention rate of {retention_rate:.1%}! The learner is mastering the material well.",
            priority='low',
            data={'retention_rate': retention_rate}
        ))
    
    # Check goals
    active_goals = [g for g in goals if g['status'] == 'active']
    if not active_goals:
        insights.append(PerformanceInsight(
            type='recommendation',
            title='Set Learning Goals',
            message="No active goals. Setting goals can help maintain motivation and track progress.",
            priority='medium'
        ))
    else:
        for goal in active_goals:
            if goal['progress_percentage'] >= 90:
                insights.append(PerformanceInsight(
                    type='milestone',
                    title=f"Goal Nearly Complete: {goal['goal_type']}",
                    message=f"Goal is {goal['progress_percentage']}% complete! Almost there!",
                    priority='low',
                    data={'goal_id': goal['id'], 'progress': goal['progress_percentage']}
                ))
    
    # Vocabulary milestone
    vocab_size = vocab_stats['vocabulary_size']
    milestones = [100, 500, 1000, 2500, 5000]
    next_milestone = next((m for m in milestones if m > vocab_size), None)
    if next_milestone and vocab_size >= next_milestone * 0.9:
        insights.append(PerformanceInsight(
            type='milestone',
            title=f"Approaching {next_milestone} Words",
            message=f"Only {next_milestone - vocab_size} words away from {next_milestone}!",
            priority='low',
            data={'current': vocab_size, 'target': next_milestone}
        ))
    
    return insights


def get_peer_comparison(
    learner_id: UUID,
    vocab_stats: Dict,
    activity_stats: Dict,
    db: Session
) -> List[PeerComparison]:
    """Get anonymized peer comparison data."""
    comparisons = []
    
    # Vocabulary size comparison
    vocab_size = vocab_stats['vocabulary_size']
    result = db.execute(
        text("""
            SELECT 
                AVG(vocab_size) as avg_size,
                PERCENT_RANK() OVER (ORDER BY vocab_size) * 100 as percentile
            FROM (
                SELECT COUNT(*) as vocab_size
                FROM learning_progress
                WHERE status = 'verified'
                GROUP BY user_id
            ) sub
            WHERE vocab_size <= :learner_size
        """),
        {'learner_size': vocab_size}
    )
    row = result.fetchone()
    
    if row:
        avg_size = row[0] or 0
        percentile = int(row[1] or 50)
        comparisons.append(PeerComparison(
            metric='vocabulary_size',
            learner_value=float(vocab_size),
            peer_average=float(avg_size),
            peer_percentile=percentile
        ))
    
    # Learning rate comparison
    learning_rate = activity_stats['learning_rate_per_week']
    # Simplified comparison - in production, calculate from actual peer data
    comparisons.append(PeerComparison(
        metric='learning_rate',
        learner_value=learning_rate,
        peer_average=10.0,  # Placeholder
        peer_percentile=50  # Placeholder
    ))
    
    return comparisons

