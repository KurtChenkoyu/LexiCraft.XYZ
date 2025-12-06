"""
Goals Service

Handles learning goal creation, tracking, and completion.
"""

from typing import Dict, List, Optional
from uuid import UUID
from datetime import date, datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import text

from .learning_velocity import LearningVelocityService
from .vocabulary_size import VocabularySizeService


class GoalsService:
    """Service for managing learning goals."""
    
    def __init__(self, db: Session):
        self.db = db
        self.velocity_service = LearningVelocityService(db)
        self.vocab_service = VocabularySizeService(db)
    
    def create_goal(
        self,
        user_id: UUID,
        goal_type: str,
        target_value: int,
        end_date: date
    ) -> Dict:
        """
        Create a new learning goal.
        
        Args:
            user_id: User ID
            goal_type: Type of goal ('daily_words', 'weekly_words', 'monthly_words', 'streak', 'vocabulary_size')
            target_value: Target value to achieve
            end_date: Goal end date
            
        Returns:
            Created goal dictionary
        """
        start_date = date.today()
        
        # Validate goal type
        valid_types = ['daily_words', 'weekly_words', 'monthly_words', 'streak', 'vocabulary_size']
        if goal_type not in valid_types:
            raise ValueError(f"Invalid goal_type. Must be one of: {valid_types}")
        
        # Validate dates
        if end_date <= start_date:
            raise ValueError("end_date must be in the future")
        
        # Insert goal
        result = self.db.execute(
            text("""
                INSERT INTO learning_goals (
                    user_id, goal_type, target_value, current_value,
                    start_date, end_date, status
                ) VALUES (
                    :user_id, :goal_type, :target_value, 0,
                    :start_date, :end_date, 'active'
                )
                RETURNING id, created_at
            """),
            {
                'user_id': user_id,
                'goal_type': goal_type,
                'target_value': target_value,
                'start_date': start_date,
                'end_date': end_date
            }
        )
        
        row = result.fetchone()
        goal_id = row[0]
        created_at = row[1]
        
        self.db.commit()
        
        return {
            'id': str(goal_id),
            'user_id': str(user_id),
            'goal_type': goal_type,
            'target_value': target_value,
            'current_value': 0,
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'status': 'active',
            'created_at': created_at.isoformat() if created_at else None
        }
    
    def update_goal_progress(self, user_id: UUID) -> List[Dict]:
        """
        Update progress for all active goals for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            List of updated goals (including any newly completed)
        """
        # Get all active goals
        goals_result = self.db.execute(
            text("""
                SELECT id, goal_type, target_value, current_value, end_date
                FROM learning_goals
                WHERE user_id = :user_id AND status = 'active'
            """),
            {'user_id': user_id}
        )
        
        goals = goals_result.fetchall()
        updated_goals = []
        completed_goals = []
        
        # Get current stats
        vocab_stats = self.vocab_service.get_vocabulary_stats(user_id)
        activity_stats = self.velocity_service.get_activity_summary(user_id)
        
        for goal in goals:
            goal_id = goal[0]
            goal_type = goal[1]
            target_value = goal[2]
            current_value = goal[3]
            end_date = goal[4]
            
            # Calculate current progress based on goal type
            new_value = self._calculate_goal_progress(user_id, goal_type, end_date)
            
            # Check if goal is completed
            is_completed = new_value >= target_value
            is_expired = end_date < date.today()
            
            if is_completed:
                # Mark as completed
                self.db.execute(
                    text("""
                        UPDATE learning_goals
                        SET current_value = :current_value,
                            status = 'completed',
                            completed_at = NOW(),
                            updated_at = NOW()
                        WHERE id = :goal_id
                    """),
                    {
                        'goal_id': goal_id,
                        'current_value': new_value
                    }
                )
                
                # Award XP for goal completion
                from .levels import LevelService
                level_service = LevelService(self.db)
                level_service.add_xp(user_id, 50, 'goal', goal_id)
                
                completed_goals.append(str(goal_id))
                
            elif is_expired:
                # Mark as failed
                self.db.execute(
                    text("""
                        UPDATE learning_goals
                        SET current_value = :current_value,
                            status = 'failed',
                            updated_at = NOW()
                        WHERE id = :goal_id
                    """),
                    {
                        'goal_id': goal_id,
                        'current_value': new_value
                    }
                )
            else:
                # Update progress
                self.db.execute(
                    text("""
                        UPDATE learning_goals
                        SET current_value = :current_value,
                            updated_at = NOW()
                        WHERE id = :goal_id
                    """),
                    {
                        'goal_id': goal_id,
                        'current_value': new_value
                    }
                )
            
            updated_goals.append({
                'id': str(goal_id),
                'goal_type': goal_type,
                'target_value': target_value,
                'current_value': new_value,
                'progress_percentage': min(100, int((new_value / target_value) * 100)) if target_value > 0 else 0,
                'status': 'completed' if is_completed else ('failed' if is_expired else 'active')
            })
        
        self.db.commit()
        
        return updated_goals
    
    def _calculate_goal_progress(self, user_id: UUID, goal_type: str, end_date: date) -> int:
        """Calculate current progress for a goal type."""
        if goal_type == 'daily_words':
            # Words learned today
            today = date.today()
            result = self.db.execute(
                text("""
                    SELECT COUNT(*) FROM learning_progress
                    WHERE user_id = :user_id
                    AND status = 'verified'
                    AND DATE(learned_at) = :today
                """),
                {'user_id': user_id, 'today': today}
            )
            return result.scalar() or 0
            
        elif goal_type == 'weekly_words':
            # Words learned this week
            activity_stats = self.velocity_service.get_activity_summary(user_id)
            return activity_stats['words_learned_this_week']
            
        elif goal_type == 'monthly_words':
            # Words learned this month
            activity_stats = self.velocity_service.get_activity_summary(user_id)
            return activity_stats['words_learned_this_month']
            
        elif goal_type == 'streak':
            # Current streak
            activity_stats = self.velocity_service.get_activity_summary(user_id)
            return activity_stats['activity_streak_days']
            
        elif goal_type == 'vocabulary_size':
            # Total vocabulary size
            vocab_stats = self.vocab_service.get_vocabulary_stats(user_id)
            return vocab_stats['vocabulary_size']
            
        else:
            return 0
    
    def get_active_goals(self, user_id: UUID) -> List[Dict]:
        """
        Get all active goals for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            List of active goals with progress
        """
        # Update progress first
        self.update_goal_progress(user_id)
        
        # Get goals
        result = self.db.execute(
            text("""
                SELECT id, goal_type, target_value, current_value,
                       start_date, end_date, status, created_at, completed_at
                FROM learning_goals
                WHERE user_id = :user_id
                ORDER BY created_at DESC
            """),
            {'user_id': user_id}
        )
        
        goals = []
        for row in result.fetchall():
            target = row[2]
            current = row[3]
            
            goals.append({
                'id': str(row[0]),
                'goal_type': row[1],
                'target_value': target,
                'current_value': current,
                'start_date': row[4].isoformat() if row[4] else None,
                'end_date': row[5].isoformat() if row[5] else None,
                'status': row[6],
                'created_at': row[7].isoformat() if row[7] else None,
                'completed_at': row[8].isoformat() if row[8] else None,
                'progress_percentage': min(100, int((current / target) * 100)) if target > 0 else 0
            })
        
        return goals
    
    def complete_goal(self, goal_id: UUID, user_id: UUID) -> Dict:
        """
        Manually mark a goal as completed.
        
        Args:
            goal_id: Goal ID
            user_id: User ID (for verification)
            
        Returns:
            Updated goal dictionary
        """
        result = self.db.execute(
            text("""
                UPDATE learning_goals
                SET status = 'completed',
                    completed_at = NOW(),
                    updated_at = NOW()
                WHERE id = :goal_id AND user_id = :user_id
                RETURNING id, goal_type, target_value, current_value, status
            """),
            {'goal_id': goal_id, 'user_id': user_id}
        )
        
        row = result.fetchone()
        if not row:
            raise ValueError("Goal not found or does not belong to user")
        
        self.db.commit()
        
        # Award XP
        from .levels import LevelService
        level_service = LevelService(self.db)
        level_service.add_xp(user_id, 50, 'goal', goal_id)
        
        return {
            'id': str(row[0]),
            'goal_type': row[1],
            'target_value': row[2],
            'current_value': row[3],
            'status': row[4]
        }
    
    def delete_goal(self, goal_id: UUID, user_id: UUID) -> bool:
        """
        Delete a goal.
        
        Args:
            goal_id: Goal ID
            user_id: User ID (for verification)
            
        Returns:
            True if deleted, False if not found
        """
        result = self.db.execute(
            text("""
                DELETE FROM learning_goals
                WHERE id = :goal_id AND user_id = :user_id
            """),
            {'goal_id': goal_id, 'user_id': user_id}
        )
        
        self.db.commit()
        
        return result.rowcount > 0
    
    def get_goal_suggestions(self, user_id: UUID) -> List[Dict]:
        """
        Get AI-suggested goals based on user's learning history.
        
        Args:
            user_id: User ID
            
        Returns:
            List of suggested goals
        """
        # Get user's current stats
        vocab_stats = self.vocab_service.get_vocabulary_stats(user_id)
        activity_stats = self.velocity_service.get_activity_summary(user_id)
        
        suggestions = []
        
        # Suggest based on current learning rate
        weekly_rate = activity_stats['words_learned_this_week']
        if weekly_rate > 0:
            # Suggest 20% increase
            suggested_weekly = int(weekly_rate * 1.2)
            suggestions.append({
                'goal_type': 'weekly_words',
                'target_value': suggested_weekly,
                'end_date': (date.today() + timedelta(days=7)).isoformat(),
                'reason': f'Based on your current rate of {weekly_rate} words/week'
            })
        
        # Suggest streak goal if they have a streak
        current_streak = activity_stats['activity_streak_days']
        if current_streak > 0:
            # Suggest next milestone
            if current_streak < 7:
                suggested_streak = 7
            elif current_streak < 30:
                suggested_streak = 30
            else:
                suggested_streak = current_streak + 7
            
            suggestions.append({
                'goal_type': 'streak',
                'target_value': suggested_streak,
                'end_date': (date.today() + timedelta(days=suggested_streak - current_streak + 1)).isoformat(),
                'reason': f'Extend your {current_streak}-day streak'
            })
        
        # Suggest vocabulary milestone
        vocab_size = vocab_stats['vocabulary_size']
        if vocab_size > 0:
            # Suggest next milestone
            milestones = [100, 500, 1000, 2500, 5000]
            next_milestone = next((m for m in milestones if m > vocab_size), None)
            
            if next_milestone:
                suggestions.append({
                    'goal_type': 'vocabulary_size',
                    'target_value': next_milestone,
                    'end_date': (date.today() + timedelta(days=30)).isoformat(),
                    'reason': f'Reach {next_milestone} words (currently {vocab_size})'
                })
        
        return suggestions


