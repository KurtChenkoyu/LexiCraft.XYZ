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
    Get comprehensive analytics dashboard for a learner (parent/coach view).
    
    Provides detailed insights, trends, and recommendations.
    """
    try:
        # Verify access
        if not verify_coach_access(coach_id, learner_id, db):
            raise HTTPException(status_code=403, detail="Access denied. You don't have permission to view this learner's data.")
        
        # Initialize services
        vocab_service = VocabularySizeService(db)
        velocity_service = LearningVelocityService(db)
        achievement_service = AchievementService(db)
        level_service = LevelService(db)
        goals_service = GoalsService(db)
        
        # Get vocabulary stats
        vocab_stats = vocab_service.get_vocabulary_stats(learner_id)
        
        # Get activity stats
        activity_stats = velocity_service.get_activity_summary(learner_id)
        
        # Get level info
        level_info = level_service.get_level_info(learner_id)
        
        # Get achievements
        achievements = achievement_service.get_user_achievements(learner_id)
        unlocked_count = sum(1 for a in achievements if a['unlocked'])
        
        # Get goals
        goals = goals_service.get_active_goals(learner_id)
        
        # Get performance metrics
        result = db.execute(
            text("""
                SELECT 
                    COUNT(*) as total_reviews,
                    SUM(CASE WHEN retention_actual THEN 1 ELSE 0 END) as total_correct,
                    AVG(response_time_ms) as avg_response_time
                FROM fsrs_review_history
                WHERE user_id = :user_id
            """),
            {'user_id': learner_id}
        )
        perf_row = result.fetchone()
        total_reviews = perf_row[0] or 0
        total_correct = perf_row[1] or 0
        avg_response_time = perf_row[2] or 0
        retention_rate = total_correct / total_reviews if total_reviews > 0 else 0
        
        # Get learning trends (last 30 days)
        trends_result = db.execute(
            text("""
                SELECT 
                    DATE(learned_at) as date,
                    COUNT(*) FILTER (WHERE status = 'verified') as words_learned,
                    COUNT(DISTINCT DATE(learned_at)) as days_active
                FROM learning_progress
                WHERE user_id = :user_id
                AND learned_at >= NOW() - INTERVAL '30 days'
                GROUP BY DATE(learned_at)
                ORDER BY DATE(learned_at)
            """),
            {'user_id': learner_id}
        )
        
        trends = []
        cumulative_vocab = vocab_stats['vocabulary_size'] - sum(
            row[1] for row in trends_result.fetchall()
        )
        
        # Re-fetch for iteration
        trends_result = db.execute(
            text("""
                SELECT 
                    DATE(learned_at) as date,
                    COUNT(*) FILTER (WHERE status = 'verified') as words_learned
                FROM learning_progress
                WHERE user_id = :user_id
                AND learned_at >= NOW() - INTERVAL '30 days'
                GROUP BY DATE(learned_at)
                ORDER BY DATE(learned_at)
            """),
            {'user_id': learner_id}
        )
        
        for row in trends_result.fetchall():
            cumulative_vocab += row[1]
            trends.append(LearningTrend(
                date=row[0].isoformat() if hasattr(row[0], 'isoformat') else str(row[0]),
                words_learned=row[1],
                vocabulary_size=cumulative_vocab,
                reviews_completed=0  # Could be calculated separately
            ))
        
        # Generate insights
        insights = generate_insights(
            vocab_stats, activity_stats, level_info, retention_rate, goals, db, learner_id
        )
        
        # Get peer comparison (anonymized)
        peer_comparison = get_peer_comparison(learner_id, vocab_stats, activity_stats, db)
        
        return CoachDashboardResponse(
            learner_id=str(learner_id),
            overview={
                'level': level_info['level'],
                'total_xp': level_info['total_xp'],
                'vocabulary_size': vocab_stats['vocabulary_size'],
                'current_streak': activity_stats['activity_streak_days'],
                'unlocked_achievements': unlocked_count,
                'total_achievements': len(achievements)
            },
            vocabulary={
                'vocabulary_size': vocab_stats['vocabulary_size'],
                'frequency_bands': vocab_stats['frequency_bands'],
                'growth_rate_per_week': vocab_stats['growth_rate_per_week'],
                'growth_timeline': vocab_stats.get('growth_timeline', [])
            },
            activity={
                'words_learned_this_week': activity_stats['words_learned_this_week'],
                'words_learned_this_month': activity_stats['words_learned_this_month'],
                'activity_streak_days': activity_stats['activity_streak_days'],
                'learning_rate_per_week': activity_stats['learning_rate_per_week'],
                'last_active_date': activity_stats['last_active_date']
            },
            performance={
                'total_reviews': total_reviews,
                'retention_rate': round(retention_rate, 3),
                'avg_response_time_ms': int(avg_response_time) if avg_response_time else 0,
                'total_correct': total_correct
            },
            trends=trends,
            insights=insights,
            peer_comparison=peer_comparison,
            goals=goals,
            achievements={
                'total': len(achievements),
                'unlocked': unlocked_count,
                'recent': achievement_service.get_recent_achievements(learner_id, days=7)
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get coach dashboard: {str(e)}")
    finally:
        db.close()


@router.get("/{learner_id}/analytics")
async def get_detailed_analytics(
    learner_id: UUID,
    coach_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db_session)
):
    """
    Get detailed learning analytics with trends and predictions.
    
    Provides deeper analysis than the main dashboard.
    """
    try:
        if not verify_coach_access(coach_id, learner_id, db):
            raise HTTPException(status_code=403, detail="Access denied")
        
        vocab_service = VocabularySizeService(db)
        velocity_service = LearningVelocityService(db)
        
        # Get extended vocabulary growth timeline
        vocab_stats = vocab_service.get_vocabulary_stats(learner_id)
        growth_timeline = vocab_service.get_vocabulary_growth_timeline(learner_id, days=90)
        
        # Get weekly activity breakdown
        weekly_activity = velocity_service.get_weekly_activity(learner_id, weeks=12)
        
        # Get XP history
        level_service = LevelService(db)
        xp_history = level_service.get_xp_history(learner_id, days=90)
        xp_summary = level_service.get_xp_summary(learner_id, days=30)
        
        return {
            'vocabulary_growth': {
                'timeline': growth_timeline,
                'current_size': vocab_stats['vocabulary_size'],
                'growth_rate': vocab_stats['growth_rate_per_week']
            },
            'weekly_activity': weekly_activity,
            'xp_earnings': {
                'history': xp_history,
                'summary': xp_summary
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get analytics: {str(e)}")
    finally:
        db.close()


@router.get("/{learner_id}/insights")
async def get_insights(
    learner_id: UUID,
    coach_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db_session)
):
    """
    Get AI-generated insights and intervention suggestions.
    
    Provides actionable recommendations for parents/coaches.
    """
    try:
        if not verify_coach_access(coach_id, learner_id, db):
            raise HTTPException(status_code=403, detail="Access denied")
        
        vocab_service = VocabularySizeService(db)
        velocity_service = LearningVelocityService(db)
        level_service = LevelService(db)
        goals_service = GoalsService(db)
        
        vocab_stats = vocab_service.get_vocabulary_stats(learner_id)
        activity_stats = velocity_service.get_activity_summary(learner_id)
        level_info = level_service.get_level_info(learner_id)
        goals = goals_service.get_active_goals(learner_id)
        
        # Get performance
        result = db.execute(
            text("""
                SELECT 
                    COUNT(*) as total_reviews,
                    SUM(CASE WHEN retention_actual THEN 1 ELSE 0 END) as total_correct
                FROM fsrs_review_history
                WHERE user_id = :user_id
            """),
            {'user_id': learner_id}
        )
        perf_row = result.fetchone()
        total_reviews = perf_row[0] or 0
        total_correct = perf_row[1] or 0
        retention_rate = total_correct / total_reviews if total_reviews > 0 else 0
        
        insights = generate_insights(
            vocab_stats, activity_stats, level_info, retention_rate, goals, db, learner_id
        )
        
        return {
            'insights': [insight.dict() for insight in insights],
            'generated_at': datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get insights: {str(e)}")
    finally:
        db.close()


@router.get("/{learner_id}/compare")
async def get_peer_comparison_endpoint(
    learner_id: UUID,
    coach_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db_session)
):
    """
    Get comparison with peers (anonymized).
    
    Shows how the learner compares to others in similar age groups or cohorts.
    """
    try:
        if not verify_coach_access(coach_id, learner_id, db):
            raise HTTPException(status_code=403, detail="Access denied")
        
        vocab_service = VocabularySizeService(db)
        velocity_service = LearningVelocityService(db)
        
        vocab_stats = vocab_service.get_vocabulary_stats(learner_id)
        activity_stats = velocity_service.get_activity_summary(learner_id)
        
        peer_comparison = get_peer_comparison(learner_id, vocab_stats, activity_stats, db)
        
        return {
            'comparisons': [comp.dict() for comp in peer_comparison],
            'note': 'All peer data is anonymized for privacy'
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get peer comparison: {str(e)}")
    finally:
        db.close()


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

