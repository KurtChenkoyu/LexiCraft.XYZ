"""
Vocabulary Size Calculation Service

Calculates vocabulary size and frequency band coverage from learning progress data.
Based on Nation's Vocabulary Levels Test methodology.
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import text

from ..database.postgres_crud import progress as progress_crud


class VocabularySizeService:
    """Service for calculating vocabulary size and frequency band coverage."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def calculate_vocabulary_size(self, user_id: UUID) -> int:
        """
        Calculate total vocabulary size from verified learning progress.
        
        Args:
            user_id: User ID
            
        Returns:
            Total number of verified learning points (vocabulary size)
        """
        verified_progress = progress_crud.get_learning_progress_by_user(
            self.db, user_id, status='verified'
        )
        return len(verified_progress)
    
    def get_frequency_band_coverage(
        self, 
        user_id: UUID,
        frequency_bands: Optional[Dict[str, Tuple[int, int]]] = None
    ) -> Dict[str, int]:
        """
        Get vocabulary coverage by frequency bands.
        
        Frequency bands (default):
        - 1K: Most common 1,000 words
        - 2K: Next 1,000 words (1,001-2,000)
        - 3K: Next 1,000 words (2,001-3,000)
        - 4K: Next 1,000 words (3,001-4,000)
        - 5K: Next 1,000 words (4,001-5,000)
        - 6K+: Words beyond 5,000
        
        Args:
            user_id: User ID
            frequency_bands: Optional custom frequency bands
                Format: {"1K": (1, 1000), "2K": (1001, 2000), ...}
        
        Returns:
            Dictionary mapping frequency bands to word counts
            Example: {"1K": 850, "2K": 420, "3K": 380, ...}
        """
        if frequency_bands is None:
            # Default frequency bands (can be customized based on your word ranking)
            frequency_bands = {
                "1K": (1, 1000),
                "2K": (1001, 2000),
                "3K": (2001, 3000),
                "4K": (3001, 4000),
                "5K": (5001, 5000),
                "6K+": (5001, 999999)  # Everything beyond 5K
            }
        
        # Get verified learning points
        verified_progress = progress_crud.get_learning_progress_by_user(
            self.db, user_id, status='verified'
        )
        
        # Group by frequency bands
        # Note: This requires learning_point_id to contain frequency rank info
        # or we need to join with Neo4j to get frequency_rank
        # For now, we'll return counts per band if we can determine frequency
        
        # TODO: This requires Neo4j integration to get frequency_rank for each learning_point_id
        # For MVP, we'll return a simplified version that counts all verified words
        
        band_counts = {band: 0 for band in frequency_bands.keys()}
        
        # If we have frequency data in learning_point_id or can query Neo4j:
        # for progress in verified_progress:
        #     frequency_rank = get_frequency_rank(progress.learning_point_id)
        #     for band_name, (min_rank, max_rank) in frequency_bands.items():
        #         if min_rank <= frequency_rank <= max_rank:
        #             band_counts[band_name] += 1
        #             break
        
        # For now, return total count in "All" band
        total = len(verified_progress)
        return {
            "total": total,
            "1K": 0,  # Placeholder - requires Neo4j integration
            "2K": 0,
            "3K": 0,
            "4K": 0,
            "5K": 0,
            "6K+": 0
        }
    
    def get_vocabulary_growth_timeline(
        self, 
        user_id: UUID, 
        days: int = 90
    ) -> List[Dict[str, any]]:
        """
        Get vocabulary growth over time.
        
        Args:
            user_id: User ID
            days: Number of days to look back
            
        Returns:
            List of daily vocabulary size snapshots
            Example: [
                {"date": "2024-12-01", "vocabulary_size": 2100},
                {"date": "2024-12-02", "vocabulary_size": 2115},
                ...
            ]
        """
        start_date = datetime.now() - timedelta(days=days)
        
        # Query verified learning progress grouped by date
        result = self.db.execute(
            text("""
                SELECT 
                    DATE(learned_at) as date,
                    COUNT(*) as words_learned
                FROM learning_progress
                WHERE user_id = :user_id
                AND status = 'verified'
                AND learned_at >= :start_date
                GROUP BY DATE(learned_at)
                ORDER BY DATE(learned_at)
            """),
            {'user_id': user_id, 'start_date': start_date}
        )
        
        timeline = []
        cumulative = 0
        
        # Get baseline (vocabulary size before start_date)
        baseline_result = self.db.execute(
            text("""
                SELECT COUNT(*)
                FROM learning_progress
                WHERE user_id = :user_id
                AND status = 'verified'
                AND learned_at < :start_date
            """),
            {'user_id': user_id, 'start_date': start_date}
        )
        baseline = baseline_result.scalar() or 0
        cumulative = baseline
        
        for row in result.fetchall():
            date = row[0]
            words_learned = row[1]
            cumulative += words_learned
            
            timeline.append({
                "date": date.isoformat() if isinstance(date, datetime) else str(date),
                "vocabulary_size": cumulative,
                "words_learned": words_learned
            })
        
        return timeline
    
    def get_vocabulary_stats(self, user_id: UUID) -> Dict[str, any]:
        """
        Get comprehensive vocabulary statistics.
        
        Args:
            user_id: User ID
            
        Returns:
            Dictionary with vocabulary size, frequency bands, and growth
        """
        vocabulary_size = self.calculate_vocabulary_size(user_id)
        frequency_bands = self.get_frequency_band_coverage(user_id)
        growth_timeline = self.get_vocabulary_growth_timeline(user_id, days=90)
        
        # Calculate growth rate (words per week over last 30 days)
        if len(growth_timeline) >= 2:
            recent_growth = growth_timeline[-1]["vocabulary_size"] - growth_timeline[0]["vocabulary_size"]
            days_span = len(growth_timeline)
            growth_rate_per_week = (recent_growth / days_span) * 7 if days_span > 0 else 0
        else:
            growth_rate_per_week = 0
        
        return {
            "vocabulary_size": vocabulary_size,
            "frequency_bands": frequency_bands,
            "growth_timeline": growth_timeline,
            "growth_rate_per_week": round(growth_rate_per_week, 1)
        }

