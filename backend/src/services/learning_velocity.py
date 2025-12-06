"""
Learning Velocity Service

Tracks learning speed, activity patterns, and streaks.
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta, date
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import text

from ..database.postgres_crud import progress as progress_crud


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

