"""
Level/XP Service

Handles XP awarding, level calculation, and progression tracking.
"""

from typing import Dict, List, Optional
from uuid import UUID
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import text


class LevelService:
    """Service for managing XP and levels."""
    
    # XP rewards by source
    XP_REWARDS = {
        'word_learned': 10,
        'streak': 5,
        'achievement': 0,  # Variable, passed as amount
        'review': 15,
        'goal': 50,
        'daily_review': 20
    }
    
    # Tier-based base XP values
    TIER_BASE_XP = {
        1: 100,   # Basic Block
        2: 250,   # Multi-Block
        3: 500,   # Phrase Block
        4: 1000,  # Idiom Block
        5: 300,   # Pattern Block
        6: 400,   # Register Block
        7: 750,   # Context Block
    }
    
    # Connection bonus XP per connection type
    CONNECTION_BONUS = {
        'RELATED_TO': 10,
        'OPPOSITE_TO': 10,
        'PREREQUISITE_OF': 15,
        'PART_OF': 20,
        'HAS_SENSE': 0,  # No bonus for basic structure
    }
    
    def __init__(self, db: Session):
        self.db = db
    
    def add_xp(
        self,
        user_id: UUID,
        amount: int,
        source: str,
        source_id: Optional[UUID] = None
    ) -> Dict:
        """
        Award XP to a user and check for level-up.
        
        Args:
            user_id: User ID
            amount: XP amount to award
            source: Source of XP ('word_learned', 'streak', 'achievement', etc.)
            source_id: Optional ID of the source (achievement_id, goal_id, etc.)
            
        Returns:
            Dictionary with level info and whether level-up occurred
        """
        # Initialize user XP if not exists
        self._ensure_user_xp(user_id)
        
        # Get current XP
        result = self.db.execute(
            text("SELECT total_xp, current_level FROM user_xp WHERE user_id = :user_id"),
            {'user_id': user_id}
        )
        row = result.fetchone()
        
        if not row:
            raise ValueError(f"User XP record not found for user {user_id}")
        
        old_total_xp = row[0] or 0
        old_level = row[1] or 1
        
        # Add XP
        new_total_xp = old_total_xp + amount
        
        # Calculate new level
        level_info = self.calculate_level(new_total_xp)
        new_level = level_info['level']
        xp_to_next = level_info['xp_to_next']
        xp_in_level = level_info['xp_in_level']
        
        # Update user_xp
        self.db.execute(
            text("""
                UPDATE user_xp
                SET total_xp = :total_xp,
                    current_level = :level,
                    xp_to_next_level = :xp_to_next,
                    xp_in_current_level = :xp_in_level,
                    updated_at = NOW()
                WHERE user_id = :user_id
            """),
            {
                'user_id': user_id,
                'total_xp': new_total_xp,
                'level': new_level,
                'xp_to_next': xp_to_next,
                'xp_in_level': xp_in_level
            }
        )
        
        # Record in XP history
        self.db.execute(
            text("""
                INSERT INTO xp_history (user_id, xp_amount, source, source_id)
                VALUES (:user_id, :amount, :source, :source_id)
            """),
            {
                'user_id': user_id,
                'amount': amount,
                'source': source,
                'source_id': source_id
            }
        )
        
        # Update leaderboard
        self.db.execute(
            text("SELECT update_leaderboard_entry(:user_id)"),
            {'user_id': user_id}
        )
        
        self.db.commit()
        
        level_up = new_level > old_level
        
        return {
            'old_level': old_level,
            'new_level': new_level,
            'old_xp': old_total_xp,
            'new_xp': new_total_xp,
            'xp_added': amount,
            'level_up': level_up,
            'xp_to_next_level': xp_to_next,
            'xp_in_current_level': xp_in_level,
            'progress_percentage': int((xp_in_level / xp_to_next) * 100) if xp_to_next > 0 else 0
        }
    
    def get_level_info(self, user_id: UUID) -> Dict:
        """
        Get current level information for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            Dictionary with level, XP, and progress info
        """
        self._ensure_user_xp(user_id)
        
        result = self.db.execute(
            text("""
                SELECT total_xp, current_level, xp_to_next_level, xp_in_current_level
                FROM user_xp
                WHERE user_id = :user_id
            """),
            {'user_id': user_id}
        )
        
        row = result.fetchone()
        if not row:
            raise ValueError(f"User XP record not found for user {user_id}")
        
        total_xp = row[0] or 0
        level = row[1] or 1
        xp_to_next = row[2] or 100
        xp_in_level = row[3] or 0
        
        return {
            'level': level,
            'total_xp': total_xp,
            'xp_to_next_level': xp_to_next,
            'xp_in_current_level': xp_in_level,
            'progress_percentage': int((xp_in_level / xp_to_next) * 100) if xp_to_next > 0 else 0
        }
    
    def calculate_level(self, total_xp: int) -> Dict:
        """
        Calculate level from total XP using exponential progression.
        
        Formula:
        - Level 1: 0-99 XP (100 XP needed)
        - Level 2: 100-249 XP (150 XP needed)
        - Level 3: 250-449 XP (200 XP needed)
        - Level N: XP needed = 100 + (N-1) * 50
        
        Args:
            total_xp: Total XP amount
            
        Returns:
            Dictionary with level, xp_to_next, and xp_in_level
        """
        # Use database function for consistency
        result = self.db.execute(
            text("SELECT * FROM calculate_level(:total_xp)"),
            {'total_xp': total_xp}
        )
        
        row = result.fetchone()
        if row:
            return {
                'level': row[0],
                'xp_to_next': row[1],
                'xp_in_level': row[2]
            }
        
        # Fallback calculation if function not available
        level = 1
        xp_needed = 100
        remaining_xp = total_xp
        
        while remaining_xp >= xp_needed:
            level += 1
            remaining_xp -= xp_needed
            xp_needed = 100 + (level - 1) * 50
        
        return {
            'level': level,
            'xp_to_next': xp_needed,
            'xp_in_level': remaining_xp
        }
    
    def get_xp_history(self, user_id: UUID, days: int = 30) -> List[Dict]:
        """
        Get XP earning history.
        
        Args:
            user_id: User ID
            days: Number of days to look back
            
        Returns:
            List of XP history entries
        """
        result = self.db.execute(
            text("""
                SELECT xp_amount, source, source_id, earned_at
                FROM xp_history
                WHERE user_id = :user_id
                AND earned_at >= NOW() - INTERVAL ':days days'
                ORDER BY earned_at DESC
            """),
            {'user_id': user_id, 'days': days}
        )
        
        history = []
        for row in result.fetchall():
            history.append({
                'xp_amount': row[0],
                'source': row[1],
                'source_id': str(row[2]) if row[2] else None,
                'earned_at': row[3].isoformat() if row[3] else None
            })
        
        return history
    
    def get_xp_summary(self, user_id: UUID, days: int = 30) -> Dict:
        """
        Get XP summary for a period.
        
        Args:
            user_id: User ID
            days: Number of days to analyze
            
        Returns:
            Dictionary with XP summary statistics
        """
        result = self.db.execute(
            text("""
                SELECT 
                    SUM(xp_amount) as total_xp,
                    COUNT(*) as total_earnings,
                    source,
                    SUM(xp_amount) FILTER (WHERE source = :source) as source_xp
                FROM xp_history
                WHERE user_id = :user_id
                AND earned_at >= NOW() - INTERVAL ':days days'
                GROUP BY source
            """),
            {'user_id': user_id, 'days': days, 'source': 'word_learned'}
        )
        
        total_xp = 0
        total_earnings = 0
        by_source = {}
        
        for row in result.fetchall():
            source_xp = row[3] or 0
            source_count = row[1] or 0
            total_xp += source_xp
            total_earnings += source_count
            by_source[row[2]] = {
                'xp': source_xp,
                'count': source_count
            }
        
        return {
            'total_xp': total_xp,
            'total_earnings': total_earnings,
            'by_source': by_source,
            'period_days': days
        }
    
    def _ensure_user_xp(self, user_id: UUID):
        """Ensure user has an XP record."""
        self.db.execute(
            text("SELECT initialize_user_xp(:user_id)"),
            {'user_id': user_id}
        )
        self.db.commit()


