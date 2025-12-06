"""
Analytics API Endpoints

Provides metrics and comparisons for algorithm A/B testing.

Endpoints:
- GET /api/v1/analytics/algorithm-comparison - Compare SM-2+ vs FSRS
- GET /api/v1/analytics/user-stats - User's algorithm performance
- GET /api/v1/analytics/daily-trend - Daily metrics trend
"""

import logging
from datetime import date, timedelta
from typing import Optional, List, Dict, Any, Generator
from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from src.database.postgres_connection import PostgresConnection
from src.middleware.auth import get_current_user_id
from src.analytics import get_comparison_metrics

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/analytics", tags=["Analytics"])

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


# Response Models

class AlgorithmMetricsResponse(BaseModel):
    """Metrics for a single algorithm."""
    total_users: int
    active_users: int
    total_reviews: int
    avg_reviews_per_user: float
    avg_reviews_per_word: float
    retention_rate: float
    words_mastered: int
    leech_rate: float


class ComparisonResponse(BaseModel):
    """Algorithm comparison response."""
    sm2_plus: AlgorithmMetricsResponse
    fsrs: AlgorithmMetricsResponse
    fsrs_advantage: Dict[str, float]
    recommendation: str
    sample_size_sufficient: bool
    period_days: int


class DailyTrendEntry(BaseModel):
    """Daily metrics for trend analysis."""
    date: str
    algorithm: str
    total_users: int
    active_users: int
    total_reviews: int
    retention_rate: Optional[float]


class UserAlgorithmStatsResponse(BaseModel):
    """User's personal algorithm stats."""
    algorithm: str
    total_reviews: int
    total_correct: int
    retention_rate: float
    avg_interval_days: float
    words_learning: int
    words_mastered: int
    words_leech: int
    percentile_retention: Optional[float]
    percentile_efficiency: Optional[float]


# Endpoints

@router.get("/algorithm-comparison", response_model=ComparisonResponse)
async def get_algorithm_comparison(
    days: int = Query(30, ge=7, le=365, description="Number of days to analyze"),
    db: Session = Depends(get_db_session),
):
    """
    Get comparison between SM-2+ and FSRS algorithms.
    
    Shows:
    - User counts and activity
    - Reviews and retention rates
    - FSRS advantage percentages
    - Recommendation based on data
    """
    try:
        metrics = get_comparison_metrics(db, days)
        
        return ComparisonResponse(
            sm2_plus=AlgorithmMetricsResponse(**metrics['sm2_plus']),
            fsrs=AlgorithmMetricsResponse(**metrics['fsrs']),
            fsrs_advantage=metrics['fsrs_advantage'],
            recommendation=metrics['recommendation'],
            sample_size_sufficient=metrics['sample_size_sufficient'],
            period_days=days,
        )
        
    except Exception as e:
        logger.error(f"Failed to get algorithm comparison: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/daily-trend", response_model=List[DailyTrendEntry])
async def get_daily_trend(
    days: int = Query(14, ge=1, le=90, description="Number of days to show"),
    algorithm: Optional[str] = Query(None, description="Filter by algorithm"),
    db: Session = Depends(get_db_session),
):
    """
    Get daily metrics trend for algorithm comparison.
    
    Useful for visualizing performance over time.
    """
    try:
        start_date = date.today() - timedelta(days=days)
        
        query = """
            SELECT 
                date,
                algorithm_type,
                total_users,
                active_users,
                total_reviews,
                retention_rate
            FROM algorithm_comparison_metrics
            WHERE date >= :start_date
        """
        params = {'start_date': start_date}
        
        if algorithm:
            query += " AND algorithm_type = :algorithm"
            params['algorithm'] = algorithm
        
        query += " ORDER BY date DESC, algorithm_type"
        
        result = db.execute(text(query), params)
        
        entries = []
        for row in result.fetchall():
            entries.append(DailyTrendEntry(
                date=row[0].isoformat() if row[0] else '',
                algorithm=row[1] or '',
                total_users=row[2] or 0,
                active_users=row[3] or 0,
                total_reviews=row[4] or 0,
                retention_rate=float(row[5]) if row[5] else None,
            ))
        
        return entries
        
    except Exception as e:
        logger.error(f"Failed to get daily trend: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/user-stats", response_model=UserAlgorithmStatsResponse)
async def get_user_algorithm_stats(
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db_session),
):
    """
    Get user's personal algorithm stats.
    
    Shows:
    - User's assigned algorithm
    - Personal review and retention stats
    - Comparison to other users (percentiles)
    """
    try:
        # Get user's algorithm
        algo_result = db.execute(
            text("""
                SELECT algorithm
                FROM user_algorithm_assignment
                WHERE user_id = :user_id
            """),
            {'user_id': user_id}
        )
        algo_row = algo_result.fetchone()
        algorithm = algo_row[0] if algo_row else 'sm2_plus'
        
        # Get user's review stats
        review_result = db.execute(
            text("""
                SELECT 
                    COUNT(*) as total_reviews,
                    SUM(CASE WHEN retention_actual THEN 1 ELSE 0 END) as total_correct
                FROM fsrs_review_history
                WHERE user_id = :user_id
            """),
            {'user_id': user_id}
        )
        review_row = review_result.fetchone()
        total_reviews = review_row[0] or 0
        total_correct = review_row[1] or 0
        retention_rate = total_correct / total_reviews if total_reviews > 0 else 0
        
        # Get card stats
        card_result = db.execute(
            text("""
                SELECT 
                    AVG(current_interval) as avg_interval,
                    COUNT(*) FILTER (WHERE mastery_level = 'learning') as learning,
                    COUNT(*) FILTER (WHERE mastery_level IN ('known', 'mastered', 'permanent')) as mastered,
                    COUNT(*) FILTER (WHERE is_leech) as leech
                FROM verification_schedule
                WHERE user_id = :user_id
            """),
            {'user_id': user_id}
        )
        card_row = card_result.fetchone()
        avg_interval = float(card_row[0] or 0)
        words_learning = card_row[1] or 0
        words_mastered = card_row[2] or 0
        words_leech = card_row[3] or 0
        
        # Calculate percentiles (compare to other users with same algorithm)
        percentile_retention = None
        percentile_efficiency = None
        
        if total_reviews >= 10:  # Only calculate if user has enough data
            # Retention percentile
            pct_result = db.execute(
                text("""
                    WITH user_retention AS (
                        SELECT 
                            fh.user_id,
                            AVG(CASE WHEN fh.retention_actual THEN 1 ELSE 0 END) as retention
                        FROM fsrs_review_history fh
                        JOIN user_algorithm_assignment uaa ON fh.user_id = uaa.user_id
                        WHERE uaa.algorithm = :algorithm
                        GROUP BY fh.user_id
                        HAVING COUNT(*) >= 10
                    )
                    SELECT 
                        PERCENT_RANK() OVER (ORDER BY retention) as percentile
                    FROM user_retention
                    WHERE user_id = :user_id
                """),
                {'algorithm': algorithm, 'user_id': user_id}
            )
            pct_row = pct_result.fetchone()
            if pct_row:
                percentile_retention = round(float(pct_row[0]) * 100, 1)
        
        return UserAlgorithmStatsResponse(
            algorithm=algorithm,
            total_reviews=total_reviews,
            total_correct=total_correct,
            retention_rate=round(retention_rate, 4),
            avg_interval_days=round(avg_interval, 1),
            words_learning=words_learning,
            words_mastered=words_mastered,
            words_leech=words_leech,
            percentile_retention=percentile_retention,
            percentile_efficiency=percentile_efficiency,
        )
        
    except Exception as e:
        logger.error(f"Failed to get user stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/word-difficulty/{learning_point_id}")
async def get_word_difficulty(
    learning_point_id: str,
    db: Session = Depends(get_db_session),
):
    """
    Get global difficulty statistics for a word.
    
    Shows how difficult this word is across all users.
    """
    try:
        result = db.execute(
            text("""
                SELECT 
                    total_reviews,
                    total_correct,
                    global_error_rate,
                    average_ease_factor,
                    average_stability,
                    difficulty_score,
                    difficulty_category,
                    leech_percentage,
                    mnemonics,
                    related_words
                FROM word_global_difficulty
                WHERE learning_point_id = :learning_point_id
            """),
            {'learning_point_id': learning_point_id}
        )
        row = result.fetchone()
        
        if not row:
            return {
                'learning_point_id': learning_point_id,
                'total_reviews': 0,
                'difficulty_score': 0.5,
                'difficulty_category': 'unknown',
                'message': 'No data yet for this word',
            }
        
        return {
            'learning_point_id': learning_point_id,
            'total_reviews': row[0] or 0,
            'total_correct': row[1] or 0,
            'global_error_rate': float(row[2] or 0),
            'average_ease_factor': float(row[3] or 2.5),
            'average_stability': float(row[4]) if row[4] else None,
            'difficulty_score': float(row[5] or 0.5),
            'difficulty_category': row[6] or 'average',
            'leech_percentage': float(row[7] or 0),
            'mnemonics': row[8] or [],
            'related_words': row[9] or [],
        }
        
    except Exception as e:
        logger.error(f"Failed to get word difficulty: {e}")
        raise HTTPException(status_code=500, detail=str(e))

