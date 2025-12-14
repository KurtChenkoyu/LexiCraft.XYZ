"""
Achievement Service

Handles achievement checking, unlocking, and progress tracking.
"""

from typing import Dict, List, Optional, Tuple
from uuid import UUID
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import text

from ..database.postgres_crud import progress as progress_crud
from ..services.learning_velocity import LearningVelocityService
from ..services.vocabulary_size import VocabularySizeService


class AchievementService:
    """Service for managing achievements and unlocks."""
    
    def __init__(self, db: Session):
        self.db = db
        self.velocity_service = LearningVelocityService(db)
        self.vocab_service = VocabularySizeService(db)
    
    def check_achievements(self, user_id: UUID) -> List[Dict]:
        """
        Check all achievements and unlock any that are newly earned.
        
        Args:
            user_id: User ID
            
        Returns:
            List of newly unlocked achievements
        """
        newly_unlocked = []
        
        # Get all achievements
        achievements_result = self.db.execute(
            text("SELECT * FROM achievements ORDER BY requirement_value ASC")
        )
        achievements = achievements_result.fetchall()
        
        # Get user's current stats
        vocab_stats = self.vocab_service.get_vocabulary_stats(user_id)
        activity_stats = self.velocity_service.get_activity_summary(user_id)
        
        # Get mastery counts
        mastery_result = self.db.execute(
            text("""
                SELECT mastery_level, COUNT(*) as count
                FROM verification_schedule
                WHERE user_id = :user_id
                GROUP BY mastery_level
            """),
            {'user_id': user_id}
        )
        mastery_counts = {row[0] or 'learning': row[1] for row in mastery_result.fetchall()}
        mastered_count = mastery_counts.get('mastered', 0)
        
        for achievement in achievements:
            achievement_id = achievement[0]
            code = achievement[1]
            requirement_type = achievement[8]
            requirement_value = int(achievement[9])  # Convert to int (comes from DB as string sometimes)
            
            # Check if already unlocked
            existing = self.db.execute(
                text("""
                    SELECT unlocked_at FROM user_achievements
                    WHERE user_id = :user_id AND achievement_id = :achievement_id
                """),
                {'user_id': user_id, 'achievement_id': achievement_id}
            ).fetchone()
            
            if existing and existing[0]:  # Already unlocked
                continue
            
            # Check if requirement is met
            current_value = self._get_current_value(
                user_id, requirement_type, vocab_stats, activity_stats, mastery_counts
            )
            
            if current_value >= requirement_value:
                # Unlock achievement
                self._unlock_achievement(user_id, achievement_id, achievement)
                
                # Get crystal reward (column 12 if exists, else use points_bonus from column 11)
                crystal_reward = achievement[12] if len(achievement) > 12 and achievement[12] else (achievement[11] if len(achievement) > 11 else 0)
                
                newly_unlocked.append({
                    'achievement_id': str(achievement_id),
                    'code': code,
                    'name_en': achievement[2],
                    'name_zh': achievement[3],
                    'description_en': achievement[4],
                    'description_zh': achievement[5],
                    'icon': achievement[6],
                    'category': achievement[7],
                    'tier': achievement[8],
                    'xp_reward': achievement[10] if len(achievement) > 10 else 0,
                    'crystal_reward': crystal_reward,
                    'points_bonus': achievement[11] if len(achievement) > 11 else 0  # Keep for backwards compatibility
                })
        
        return newly_unlocked
    
    def _get_current_value(
        self,
        user_id: UUID,
        requirement_type: str,
        vocab_stats: Dict,
        activity_stats: Dict,
        mastery_counts: Dict
    ) -> int:
        """Get current value for a requirement type."""
        if requirement_type == 'streak_days':
            return activity_stats.get('activity_streak_days', 0)
        elif requirement_type == 'vocabulary_size':
            return vocab_stats.get('vocabulary_size', 0)
        elif requirement_type == 'blocks_learned':
            # Count all learning_progress entries (blocks started)
            result = self.db.execute(
                text("SELECT COUNT(*) FROM learning_progress WHERE user_id = :user_id"),
                {'user_id': user_id}
            )
            return result.scalar() or 0
        elif requirement_type == 'blocks_mastered':
            # Count mastered blocks from verification_schedule
            return mastery_counts.get('mastered', 0)
        elif requirement_type == 'words_this_week':
            return activity_stats.get('words_learned_this_week', 0)
        elif requirement_type == 'words_this_month':
            return activity_stats.get('words_learned_this_month', 0)
        elif requirement_type == 'mastered_count':
            return mastery_counts.get('mastered', 0)
        elif requirement_type == 'survey_complete':
            # Check if user has completed survey
            result = self.db.execute(
                text("""
                    SELECT COUNT(*) FROM survey_responses 
                    WHERE user_id = :user_id
                """),
                {'user_id': user_id}
            )
            return 1 if (result.scalar() or 0) > 0 else 0
        elif requirement_type == 'challenges_completed':
            # For now, return 0 - Challenge Mode not yet implemented
            # This will be tracked when Challenge Mode is added
            return 0
        elif requirement_type == 'total_reviews':
            result = self.db.execute(
                text("SELECT COUNT(*) FROM fsrs_review_history WHERE user_id = :user_id"),
                {'user_id': user_id}
            )
            return result.scalar() or 0
        elif requirement_type == 'perfect_week':
            # Check if all 7 days of the week have activity
            result = self.db.execute(
                text("""
                    SELECT COUNT(DISTINCT DATE(learned_at))
                    FROM learning_progress
                    WHERE user_id = :user_id
                    AND DATE(learned_at) >= DATE_TRUNC('week', CURRENT_DATE)
                    AND DATE(learned_at) < DATE_TRUNC('week', CURRENT_DATE) + INTERVAL '7 days'
                """),
                {'user_id': user_id}
            )
            return result.scalar() or 0
        else:
            return 0
    
    def _unlock_achievement(self, user_id: UUID, achievement_id: UUID, achievement: tuple):
        """Unlock an achievement for a user."""
        # Insert or update user_achievement
        self.db.execute(
            text("""
                INSERT INTO user_achievements (user_id, achievement_id, unlocked_at, progress)
                VALUES (:user_id, :achievement_id, NOW(), :requirement_value)
                ON CONFLICT (user_id, achievement_id) DO UPDATE SET
                    unlocked_at = NOW(),
                    progress = :requirement_value
            """),
            {
                'user_id': user_id,
                'achievement_id': achievement_id,
                'requirement_value': achievement[9]
            }
        )
        
        # Award XP if reward exists (column index 10)
        xp_reward = achievement[10] if len(achievement) > 10 else 0
        if xp_reward and xp_reward > 0:
            from .levels import LevelService
            level_service = LevelService(self.db)
            level_service.add_xp(user_id, xp_reward, 'achievement', achievement_id)
        
        # Award crystals if crystal_reward exists (column index 12 after adding crystal_reward)
        # Try to get crystal_reward, fall back to points_bonus for backwards compatibility
        crystal_reward = 0
        if len(achievement) > 12 and achievement[12]:
            crystal_reward = achievement[12]
        elif len(achievement) > 11 and achievement[11]:
            # Backwards compatibility: use points_bonus as crystal reward
            crystal_reward = achievement[11]
        
        if crystal_reward > 0:
            try:
                self.db.execute(
                    text("""
                        SELECT add_crystals(
                            :user_id, :amount, 'achievement', :achievement_id,
                            :desc_en, :desc_zh
                        )
                    """),
                    {
                        'user_id': user_id,
                        'amount': crystal_reward,
                        'achievement_id': achievement_id,
                        'desc_en': f'Achievement reward: {achievement[2]}',
                        'desc_zh': f'成就獎勵: {achievement[3] or achievement[2]}'
                    }
                )
            except Exception:
                # Crystal tables might not exist yet, silently ignore
                pass
        
        self.db.commit()
    
    def get_user_achievements(self, user_id: UUID) -> List[Dict]:
        """
        Get all achievements with user's progress.
        
        Args:
            user_id: User ID
            
        Returns:
            List of achievements with unlock status and progress
        """
        result = self.db.execute(
            text("""
                SELECT 
                    a.id, a.code, a.name_en, a.name_zh, a.description_en, a.description_zh,
                    a.icon, a.category, a.tier, a.requirement_type, a.requirement_value,
                    a.xp_reward, a.points_bonus,
                    ua.unlocked_at, ua.progress
                FROM achievements a
                LEFT JOIN user_achievements ua ON a.id = ua.achievement_id AND ua.user_id = :user_id
                ORDER BY a.category, a.requirement_value ASC
            """),
            {'user_id': user_id}
        )
        
        achievements = []
        for row in result.fetchall():
            achievements.append({
                'id': str(row[0]),
                'code': row[1],
                'name_en': row[2],
                'name_zh': row[3],
                'description_en': row[4],
                'description_zh': row[5],
                'icon': row[6],
                'category': row[7],
                'tier': row[8],
                'requirement_type': row[9],
                'requirement_value': row[10],
                'xp_reward': row[11],
                'points_bonus': row[12],
                'unlocked': row[13] is not None,
                'unlocked_at': row[13].isoformat() if row[13] else None,
                'progress': row[14] or 0
            })
        
        return achievements
    
    def get_recent_achievements(self, user_id: UUID, days: int = 7) -> List[Dict]:
        """
        Get recently unlocked achievements.
        
        Args:
            user_id: User ID
            days: Number of days to look back
            
        Returns:
            List of recently unlocked achievements
        """
        result = self.db.execute(
            text("""
                SELECT 
                    a.id, a.code, a.name_en, a.name_zh, a.description_en, a.description_zh,
                    a.icon, a.category, a.tier, a.xp_reward, a.points_bonus,
                    ua.unlocked_at
                FROM user_achievements ua
                JOIN achievements a ON ua.achievement_id = a.id
                WHERE ua.user_id = :user_id
                AND ua.unlocked_at >= NOW() - INTERVAL ':days days'
                ORDER BY ua.unlocked_at DESC
            """),
            {'user_id': user_id, 'days': days}
        )
        
        achievements = []
        for row in result.fetchall():
            achievements.append({
                'id': str(row[0]),
                'code': row[1],
                'name_en': row[2],
                'name_zh': row[3],
                'description_en': row[4],
                'description_zh': row[5],
                'icon': row[6],
                'category': row[7],
                'tier': row[8],
                'xp_reward': row[9],
                'points_bonus': row[10],
                'unlocked_at': row[11].isoformat() if row[11] else None
            })
        
        return achievements
    
    def get_achievement_progress(self, user_id: UUID, achievement_id: UUID) -> Optional[Dict]:
        """
        Get progress for a specific achievement.
        
        Args:
            user_id: User ID
            achievement_id: Achievement ID
            
        Returns:
            Achievement progress info or None if not found
        """
        result = self.db.execute(
            text("""
                SELECT 
                    a.id, a.code, a.name_en, a.name_zh, a.description_en, a.description_zh,
                    a.icon, a.category, a.tier, a.requirement_type, a.requirement_value,
                    a.xp_reward, a.points_bonus,
                    ua.unlocked_at, ua.progress
                FROM achievements a
                LEFT JOIN user_achievements ua ON a.id = ua.achievement_id AND ua.user_id = :user_id
                WHERE a.id = :achievement_id
            """),
            {'user_id': user_id, 'achievement_id': achievement_id}
        )
        
        row = result.fetchone()
        if not row:
            return None
        
        return {
            'id': str(row[0]),
            'code': row[1],
            'name_en': row[2],
            'name_zh': row[3],
            'description_en': row[4],
            'description_zh': row[5],
            'icon': row[6],
            'category': row[7],
            'tier': row[8],
            'requirement_type': row[9],
            'requirement_value': row[10],
            'xp_reward': row[11],
            'points_bonus': row[12],
            'unlocked': row[13] is not None,
            'unlocked_at': row[13].isoformat() if row[13] else None,
            'progress': row[14] or 0,
            'progress_percentage': min(100, int((row[14] or 0) / row[10] * 100)) if row[10] > 0 else 0
        }


