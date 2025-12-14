"""
Learning Velocity Service

Tracks learning speed, activity patterns, and streaks.
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta, date
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import text

from ..database.postgres_crud import progress as progress_crud


# Streak multiplier configuration
STREAK_MULTIPLIERS = {
    7: 2.0,    # Day 7 = "Payout Day" (double XP)
    30: 1.5,   # 30+ days = permanent 1.5x while streak held
    60: 1.75,  # 60+ days = 1.75x
    100: 2.0,  # 100+ days = permanent 2x
}


class LearningVelocityService:
    """Service for tracking learning velocity and activity patterns."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_words_learned_period(
        self, 
        user_id: UUID, 
        start_date: date, 
        end_date: date
    ) -> int:
        """
        Get number of words learned in a specific period.
        
        Args:
            user_id: User ID
            start_date: Start date (inclusive)
            end_date: End date (inclusive)
            
        Returns:
            Number of words verified in the period
        """
        result = self.db.execute(
            text("""
                SELECT COUNT(*)
                FROM learning_progress
                WHERE user_id = :user_id
                AND status = 'verified'
                AND DATE(learned_at) >= :start_date
                AND DATE(learned_at) <= :end_date
            """),
            {
                'user_id': user_id,
                'start_date': start_date,
                'end_date': end_date
            }
        )
        return result.scalar() or 0
    
    def get_words_learned_this_week(self, user_id: UUID) -> int:
        """Get words learned in the current week (Monday to Sunday)."""
        today = date.today()
        # Get Monday of current week
        days_since_monday = today.weekday()
        monday = today - timedelta(days=days_since_monday)
        return self.get_words_learned_period(user_id, monday, today)
    
    def get_words_learned_this_month(self, user_id: UUID) -> int:
        """Get words learned in the current month."""
        today = date.today()
        first_day = today.replace(day=1)
        return self.get_words_learned_period(user_id, first_day, today)
    
    def calculate_activity_streak(self, user_id: UUID) -> int:
        """
        Calculate consecutive days with learning activity.
        
        Activity is defined as:
        - Creating new learning_progress entry
        - Completing a verification review
        
        Args:
            user_id: User ID
            
        Returns:
            Number of consecutive days with activity
        """
        # Get all dates with activity (learning progress or verification)
        result = self.db.execute(
            text("""
                SELECT DISTINCT DATE(learned_at) as activity_date
                FROM learning_progress
                WHERE user_id = :user_id
                AND learned_at >= CURRENT_DATE - INTERVAL '90 days'
                ORDER BY activity_date DESC
            """),
            {'user_id': user_id}
        )
        
        activity_dates = [row[0] for row in result.fetchall()]
        
        if not activity_dates:
            return 0
        
        # Calculate streak
        streak = 0
        today = date.today()
        expected_date = today
        
        for activity_date in activity_dates:
            if activity_date == expected_date:
                streak += 1
                expected_date -= timedelta(days=1)
            elif activity_date < expected_date:
                # Gap in streak
                break
        
        return streak
    
    def get_learning_rate(self, user_id: UUID, days: int = 30) -> float:
        """
        Calculate learning rate (words per week) over a period.
        
        Args:
            user_id: User ID
            days: Number of days to analyze
            
        Returns:
            Words learned per week (average)
        """
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        words_learned = self.get_words_learned_period(user_id, start_date, end_date)
        
        if days == 0:
            return 0.0
        
        words_per_week = (words_learned / days) * 7
        return round(words_per_week, 1)
    
    def get_activity_summary(self, user_id: UUID) -> Dict[str, any]:
        """
        Get comprehensive activity summary.
        
        Args:
            user_id: User ID
            
        Returns:
            Dictionary with activity metrics
        """
        words_this_week = self.get_words_learned_this_week(user_id)
        words_this_month = self.get_words_learned_this_month(user_id)
        streak = self.calculate_activity_streak(user_id)
        learning_rate = self.get_learning_rate(user_id, days=30)
        
        # Get last active date
        last_active_result = self.db.execute(
            text("""
                SELECT MAX(learned_at)
                FROM learning_progress
                WHERE user_id = :user_id
            """),
            {'user_id': user_id}
        )
        last_active = last_active_result.scalar()
        
        return {
            "words_learned_this_week": words_this_week,
            "words_learned_this_month": words_this_month,
            "activity_streak_days": streak,
            "learning_rate_per_week": learning_rate,
            "last_active_date": last_active.isoformat() if last_active else None
        }
    
    def get_weekly_activity(self, user_id: UUID, weeks: int = 12) -> List[Dict[str, any]]:
        """
        Get weekly activity breakdown.
        
        Args:
            user_id: User ID
            weeks: Number of weeks to look back
            
        Returns:
            List of weekly activity summaries
        """
        today = date.today()
        weekly_data = []
        
        for i in range(weeks):
            # Calculate week range (Monday to Sunday)
            days_since_monday = today.weekday()
            week_end = today - timedelta(days=days_since_monday + (i * 7))
            week_start = week_end - timedelta(days=6)
            
            words_learned = self.get_words_learned_period(user_id, week_start, week_end)
            
            weekly_data.append({
                "week_start": week_start.isoformat(),
                "week_end": week_end.isoformat(),
                "words_learned": words_learned
            })
        
        return list(reversed(weekly_data))  # Oldest first
    
    def record_activity_and_check_streak(self, user_id: UUID) -> Tuple[int, bool, float]:
        """
        Record today's activity and check if streak was extended.
        
        This should be called when a user completes a review or learns a word.
        
        Args:
            user_id: User ID
            
        Returns:
            Tuple of (current_streak, streak_extended, xp_multiplier)
            - current_streak: The current streak count
            - streak_extended: True if this is the first activity today (streak extended)
            - xp_multiplier: The XP multiplier to apply based on streak
        """
        today = date.today()
        yesterday = today - timedelta(days=1)
        
        # Check if user already had activity today
        today_activity_result = self.db.execute(
            text("""
                SELECT COUNT(*) FROM (
                    SELECT 1 FROM learning_progress 
                    WHERE user_id = :user_id 
                    AND DATE(learned_at) = :today
                    UNION ALL
                    SELECT 1 FROM fsrs_review_history
                    WHERE user_id = :user_id
                    AND DATE(review_date) = :today
                ) AS today_activities
            """),
            {'user_id': user_id, 'today': today}
        )
        had_activity_today = (today_activity_result.scalar() or 0) > 1  # > 1 because current activity counts
        
        # Calculate current streak
        current_streak = self.calculate_activity_streak(user_id)
        
        # Streak is "extended" if this is the first activity today
        streak_extended = not had_activity_today
        
        # Calculate XP multiplier based on streak
        xp_multiplier = self._get_streak_multiplier(current_streak)
        
        return current_streak, streak_extended, xp_multiplier
    
    def _get_streak_multiplier(self, streak_days: int) -> float:
        """
        Get XP multiplier based on streak length.
        
        Multipliers:
        - Day 7: 2.0x (Payout Day)
        - Day 30+: 1.5x permanent
        - Day 60+: 1.75x permanent
        - Day 100+: 2.0x permanent
        
        Args:
            streak_days: Current streak in days
            
        Returns:
            XP multiplier (1.0 = no multiplier)
        """
        # Special "Payout Day" on day 7
        if streak_days == 7:
            return 2.0
        
        # Permanent multipliers based on streak length
        if streak_days >= 100:
            return 2.0
        elif streak_days >= 60:
            return 1.75
        elif streak_days >= 30:
            return 1.5
        
        return 1.0
    
    def get_streak_info(self, user_id: UUID) -> Dict[str, any]:
        """
        Get comprehensive streak information.
        
        Args:
            user_id: User ID
            
        Returns:
            Dictionary with streak details including multiplier info
        """
        streak = self.calculate_activity_streak(user_id)
        multiplier = self._get_streak_multiplier(streak)
        
        # Calculate next milestone
        next_milestone = None
        next_multiplier = None
        if streak < 7:
            next_milestone = 7
            next_multiplier = 2.0
        elif streak < 30:
            next_milestone = 30
            next_multiplier = 1.5
        elif streak < 60:
            next_milestone = 60
            next_multiplier = 1.75
        elif streak < 100:
            next_milestone = 100
            next_multiplier = 2.0
        
        return {
            "current_streak": streak,
            "current_multiplier": multiplier,
            "is_payout_day": streak == 7,
            "next_milestone": next_milestone,
            "next_multiplier": next_multiplier,
            "days_to_next_milestone": next_milestone - streak if next_milestone else None
        }

