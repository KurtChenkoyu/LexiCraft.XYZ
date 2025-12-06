"""
Algorithm Comparison Analytics

Compares performance between SM-2+ and FSRS algorithms for A/B testing.

Tracks:
- Reviews per word (efficiency)
- Retention rate (effectiveness)
- Time to mastery (speed)
- User satisfaction (experience)
"""

import logging
from datetime import date, datetime, timedelta
from typing import Optional, Dict, Any, List
from uuid import UUID
from dataclasses import dataclass

from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


@dataclass
class AlgorithmMetrics:
    """Metrics for a single algorithm."""
    algorithm: str
    total_users: int
    active_users: int
    total_reviews: int
    avg_reviews_per_user: float
    avg_reviews_per_word: float
    retention_rate: float
    avg_days_to_mastery: float
    words_mastered: int
    leech_rate: float


@dataclass
class ComparisonResult:
    """Comparison between SM-2+ and FSRS."""
    sm2_plus: AlgorithmMetrics
    fsrs: AlgorithmMetrics
    fsrs_advantage: Dict[str, float]  # Percentage improvement
    recommendation: str
    sample_size_sufficient: bool


class AlgorithmComparisonService:
    """
    Service for comparing algorithm performance.
    
    Calculates metrics for A/B testing and provides recommendations.
    """
    
    # Minimum sample size for statistical significance
    MIN_SAMPLE_SIZE = 30
    MIN_REVIEWS_PER_USER = 50
    
    def __init__(self, db_session: Optional[Session] = None):
        self._db = db_session
    
    def get_comparison(
        self,
        db: Optional[Session] = None,
        days: int = 30,
    ) -> ComparisonResult:
        """
        Get comparison between SM-2+ and FSRS.
        
        Args:
            db: Database session
            days: Number of days to analyze
            
        Returns:
            ComparisonResult with metrics for both algorithms
        """
        db = db or self._db
        if not db:
            raise ValueError("Database session required")
        
        start_date = date.today() - timedelta(days=days)
        
        # Get metrics for each algorithm
        sm2_metrics = self._get_algorithm_metrics(db, 'sm2_plus', start_date)
        fsrs_metrics = self._get_algorithm_metrics(db, 'fsrs', start_date)
        
        # Calculate FSRS advantage
        advantage = self._calculate_advantage(sm2_metrics, fsrs_metrics)
        
        # Check sample size
        total_users = sm2_metrics.active_users + fsrs_metrics.active_users
        sample_sufficient = (
            total_users >= self.MIN_SAMPLE_SIZE and
            sm2_metrics.active_users >= self.MIN_SAMPLE_SIZE // 2 and
            fsrs_metrics.active_users >= self.MIN_SAMPLE_SIZE // 2
        )
        
        # Generate recommendation
        recommendation = self._generate_recommendation(
            sm2_metrics, fsrs_metrics, advantage, sample_sufficient
        )
        
        return ComparisonResult(
            sm2_plus=sm2_metrics,
            fsrs=fsrs_metrics,
            fsrs_advantage=advantage,
            recommendation=recommendation,
            sample_size_sufficient=sample_sufficient,
        )
    
    def _get_algorithm_metrics(
        self,
        db: Session,
        algorithm: str,
        start_date: date,
    ) -> AlgorithmMetrics:
        """Get metrics for a specific algorithm."""
        # Get user counts
        user_result = db.execute(
            text("""
                SELECT 
                    COUNT(*) as total_users,
                    COUNT(*) FILTER (
                        WHERE user_id IN (
                            SELECT DISTINCT user_id 
                            FROM fsrs_review_history 
                            WHERE review_date >= :start_date
                        )
                    ) as active_users
                FROM user_algorithm_assignment
                WHERE algorithm = :algorithm
            """),
            {'algorithm': algorithm, 'start_date': start_date}
        )
        user_row = user_result.fetchone()
        total_users = user_row[0] or 0
        active_users = user_row[1] or 0
        
        # Get review metrics
        review_result = db.execute(
            text("""
                SELECT 
                    COUNT(*) as total_reviews,
                    AVG(CASE WHEN retention_actual THEN 1 ELSE 0 END) as retention_rate,
                    COUNT(DISTINCT learning_progress_id) as unique_words
                FROM fsrs_review_history fh
                JOIN user_algorithm_assignment uaa ON fh.user_id = uaa.user_id
                WHERE uaa.algorithm = :algorithm
                AND fh.review_date >= :start_date
            """),
            {'algorithm': algorithm, 'start_date': start_date}
        )
        review_row = review_result.fetchone()
        total_reviews = review_row[0] or 0
        retention_rate = float(review_row[1] or 0)
        unique_words = review_row[2] or 1
        
        # Calculate averages
        avg_reviews_per_user = total_reviews / active_users if active_users > 0 else 0
        avg_reviews_per_word = total_reviews / unique_words if unique_words > 0 else 0
        
        # Get mastery metrics
        mastery_result = db.execute(
            text("""
                SELECT 
                    COUNT(*) FILTER (WHERE vs.mastery_level = 'mastered') as words_mastered,
                    COUNT(*) FILTER (WHERE vs.is_leech) as leeches,
                    COUNT(*) as total_cards
                FROM verification_schedule vs
                JOIN user_algorithm_assignment uaa ON vs.user_id = uaa.user_id
                WHERE uaa.algorithm = :algorithm
            """),
            {'algorithm': algorithm}
        )
        mastery_row = mastery_result.fetchone()
        words_mastered = mastery_row[0] or 0
        leeches = mastery_row[1] or 0
        total_cards = mastery_row[2] or 1
        leech_rate = leeches / total_cards if total_cards > 0 else 0
        
        # TODO: Calculate actual days to mastery from review history
        avg_days_to_mastery = 0.0
        
        return AlgorithmMetrics(
            algorithm=algorithm,
            total_users=total_users,
            active_users=active_users,
            total_reviews=total_reviews,
            avg_reviews_per_user=round(avg_reviews_per_user, 2),
            avg_reviews_per_word=round(avg_reviews_per_word, 2),
            retention_rate=round(retention_rate, 4),
            avg_days_to_mastery=avg_days_to_mastery,
            words_mastered=words_mastered,
            leech_rate=round(leech_rate, 4),
        )
    
    def _calculate_advantage(
        self,
        sm2: AlgorithmMetrics,
        fsrs: AlgorithmMetrics,
    ) -> Dict[str, float]:
        """Calculate FSRS advantage over SM-2+."""
        def safe_pct(fsrs_val: float, sm2_val: float) -> float:
            if sm2_val == 0:
                return 0.0
            return round((fsrs_val - sm2_val) / sm2_val * 100, 2)
        
        def safe_pct_inverse(fsrs_val: float, sm2_val: float) -> float:
            """For metrics where lower is better (like reviews per word)."""
            if fsrs_val == 0:
                return 0.0
            return round((sm2_val - fsrs_val) / fsrs_val * 100, 2)
        
        return {
            'reviews_per_word': safe_pct_inverse(
                fsrs.avg_reviews_per_word, sm2.avg_reviews_per_word
            ),
            'retention_rate': safe_pct(
                fsrs.retention_rate, sm2.retention_rate
            ),
            'leech_rate': safe_pct_inverse(
                fsrs.leech_rate, sm2.leech_rate
            ),
        }
    
    def _generate_recommendation(
        self,
        sm2: AlgorithmMetrics,
        fsrs: AlgorithmMetrics,
        advantage: Dict[str, float],
        sample_sufficient: bool,
    ) -> str:
        """Generate a recommendation based on comparison."""
        if not sample_sufficient:
            return (
                "Insufficient data for recommendation. "
                f"Need at least {self.MIN_SAMPLE_SIZE} active users in each group."
            )
        
        # Count advantages
        fsrs_wins = sum(1 for v in advantage.values() if v > 5)  # > 5% improvement
        sm2_wins = sum(1 for v in advantage.values() if v < -5)  # > 5% worse
        
        if fsrs_wins > sm2_wins:
            return (
                f"FSRS shows improvement in {fsrs_wins}/3 metrics. "
                f"Consider migrating more users to FSRS. "
                f"Key improvement: {advantage['reviews_per_word']}% fewer reviews per word."
            )
        elif sm2_wins > fsrs_wins:
            return (
                f"SM-2+ performs better in {sm2_wins}/3 metrics. "
                "Continue with current 50/50 split to gather more data."
            )
        else:
            return (
                "Performance is similar between algorithms. "
                "Continue A/B testing to gather more data."
            )
    
    def calculate_daily_metrics(
        self,
        db: Optional[Session] = None,
        target_date: Optional[date] = None,
    ) -> None:
        """
        Calculate and store daily metrics for both algorithms.
        
        Should be run daily via cron job or background task.
        """
        db = db or self._db
        if not db:
            raise ValueError("Database session required")
        
        target_date = target_date or date.today() - timedelta(days=1)
        
        for algorithm in ['sm2_plus', 'fsrs']:
            try:
                # Get daily stats
                result = db.execute(
                    text("""
                        SELECT 
                            COUNT(DISTINCT uaa.user_id) as total_users,
                            COUNT(DISTINCT fh.user_id) as active_users,
                            COUNT(*) as total_reviews,
                            AVG(CASE WHEN fh.retention_actual THEN 1 ELSE 0 END) as retention_rate
                        FROM user_algorithm_assignment uaa
                        LEFT JOIN fsrs_review_history fh ON fh.user_id = uaa.user_id
                            AND DATE(fh.review_date) = :target_date
                        WHERE uaa.algorithm = :algorithm
                    """),
                    {'algorithm': algorithm, 'target_date': target_date}
                )
                row = result.fetchone()
                
                # Insert into metrics table
                db.execute(
                    text("""
                        INSERT INTO algorithm_comparison_metrics (
                            date, algorithm_type, total_users, active_users,
                            total_reviews, retention_rate
                        ) VALUES (
                            :date, :algorithm, :total_users, :active_users,
                            :total_reviews, :retention_rate
                        )
                        ON CONFLICT (date, algorithm_type) DO UPDATE
                        SET total_users = EXCLUDED.total_users,
                            active_users = EXCLUDED.active_users,
                            total_reviews = EXCLUDED.total_reviews,
                            retention_rate = EXCLUDED.retention_rate
                    """),
                    {
                        'date': target_date,
                        'algorithm': algorithm,
                        'total_users': row[0] or 0,
                        'active_users': row[1] or 0,
                        'total_reviews': row[2] or 0,
                        'retention_rate': float(row[3] or 0),
                    }
                )
                db.commit()
                
            except Exception as e:
                logger.error(f"Failed to calculate metrics for {algorithm}: {e}")
                db.rollback()


# Module-level convenience functions

def get_comparison_metrics(
    db_session: Session,
    days: int = 30,
) -> Dict[str, Any]:
    """
    Get comparison metrics as a dictionary.
    
    Convenience function for API endpoints.
    """
    service = AlgorithmComparisonService(db_session)
    result = service.get_comparison(db_session, days)
    
    return {
        'sm2_plus': {
            'total_users': result.sm2_plus.total_users,
            'active_users': result.sm2_plus.active_users,
            'total_reviews': result.sm2_plus.total_reviews,
            'avg_reviews_per_user': result.sm2_plus.avg_reviews_per_user,
            'avg_reviews_per_word': result.sm2_plus.avg_reviews_per_word,
            'retention_rate': result.sm2_plus.retention_rate,
            'words_mastered': result.sm2_plus.words_mastered,
            'leech_rate': result.sm2_plus.leech_rate,
        },
        'fsrs': {
            'total_users': result.fsrs.total_users,
            'active_users': result.fsrs.active_users,
            'total_reviews': result.fsrs.total_reviews,
            'avg_reviews_per_user': result.fsrs.avg_reviews_per_user,
            'avg_reviews_per_word': result.fsrs.avg_reviews_per_word,
            'retention_rate': result.fsrs.retention_rate,
            'words_mastered': result.fsrs.words_mastered,
            'leech_rate': result.fsrs.leech_rate,
        },
        'fsrs_advantage': result.fsrs_advantage,
        'recommendation': result.recommendation,
        'sample_size_sufficient': result.sample_size_sufficient,
    }


def calculate_daily_metrics(db_session: Session, target_date: Optional[date] = None) -> None:
    """Calculate and store daily metrics."""
    service = AlgorithmComparisonService(db_session)
    service.calculate_daily_metrics(db_session, target_date)

