"""
Notification Service

Handles notifications for achievements, milestones, streak risks, and more.
"""

from typing import Dict, List, Optional
from uuid import UUID
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import text

from .learning_velocity import LearningVelocityService
from .levels import LevelService
from .achievements import AchievementService


class NotificationService:
    """Service for managing notifications."""
    
    def __init__(self, db: Session):
        self.db = db
        self.velocity_service = LearningVelocityService(db)
        self.level_service = LevelService(db)
        self.achievement_service = AchievementService(db)
    
    def create_notification(
        self,
        user_id: UUID,
        notification_type: str,
        title_en: str,
        title_zh: Optional[str] = None,
        message_en: Optional[str] = None,
        message_zh: Optional[str] = None,
        data: Optional[Dict] = None
    ) -> Dict:
        """
        Create a notification.
        
        Args:
            user_id: User ID
            notification_type: Type of notification ('achievement', 'streak_risk', 'goal_progress', 'milestone', 'level_up')
            title_en: English title
            title_zh: Chinese title (optional)
            message_en: English message (optional)
            message_zh: Chinese message (optional)
            data: Additional data as JSON
            
        Returns:
            Created notification dictionary
        """
        import json
        
        result = self.db.execute(
            text("""
                INSERT INTO notifications (
                    user_id, type, title_en, title_zh, message_en, message_zh, data
                ) VALUES (
                    :user_id, :type, :title_en, :title_zh, :message_en, :message_zh, :data
                )
                RETURNING id, created_at
            """),
            {
                'user_id': user_id,
                'type': notification_type,
                'title_en': title_en,
                'title_zh': title_zh,
                'message_en': message_en,
                'message_zh': message_zh,
                'data': json.dumps(data) if data else '{}'
            }
        )
        
        row = result.fetchone()
        notification_id = row[0]
        created_at = row[1]
        
        self.db.commit()
        
        return {
            'id': str(notification_id),
            'user_id': str(user_id),
            'type': notification_type,
            'title_en': title_en,
            'title_zh': title_zh,
            'message_en': message_en,
            'message_zh': message_zh,
            'data': data or {},
            'read': False,
            'created_at': created_at.isoformat() if created_at else None
        }
    
    def get_notifications(
        self,
        user_id: UUID,
        unread_only: bool = False,
        limit: int = 50
    ) -> List[Dict]:
        """
        Get notifications for a user.
        
        Args:
            user_id: User ID
            unread_only: Only return unread notifications
            limit: Maximum number of notifications to return
            
        Returns:
            List of notifications
        """
        import json
        
        query = """
            SELECT id, type, title_en, title_zh, message_en, message_zh, data, read, created_at
            FROM notifications
            WHERE user_id = :user_id
        """
        
        if unread_only:
            query += " AND read = FALSE"
        
        query += " ORDER BY created_at DESC LIMIT :limit"
        
        result = self.db.execute(
            text(query),
            {'user_id': user_id, 'limit': limit}
        )
        
        notifications = []
        for row in result.fetchall():
            data = json.loads(row[6]) if row[6] else {}
            
            notifications.append({
                'id': str(row[0]),
                'type': row[1],
                'title_en': row[2],
                'title_zh': row[3],
                'message_en': row[4],
                'message_zh': row[5],
                'data': data,
                'read': row[7],
                'created_at': row[8].isoformat() if row[8] else None
            })
        
        return notifications
    
    def mark_as_read(self, notification_ids: List[UUID], user_id: UUID) -> int:
        """
        Mark notifications as read.
        
        Args:
            notification_ids: List of notification IDs
            user_id: User ID (for verification)
            
        Returns:
            Number of notifications marked as read
        """
        if not notification_ids:
            return 0
        
        result = self.db.execute(
            text("""
                UPDATE notifications
                SET read = TRUE
                WHERE id = ANY(:notification_ids)
                AND user_id = :user_id
            """),
            {
                'notification_ids': [str(nid) for nid in notification_ids],
                'user_id': user_id
            }
        )
        
        self.db.commit()
        
        return result.rowcount
    
    def mark_all_as_read(self, user_id: UUID) -> int:
        """
        Mark all notifications as read for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            Number of notifications marked as read
        """
        result = self.db.execute(
            text("""
                UPDATE notifications
                SET read = TRUE
                WHERE user_id = :user_id AND read = FALSE
            """),
            {'user_id': user_id}
        )
        
        self.db.commit()
        
        return result.rowcount
    
    def get_unread_count(self, user_id: UUID) -> int:
        """
        Get count of unread notifications.
        
        Args:
            user_id: User ID
            
        Returns:
            Number of unread notifications
        """
        result = self.db.execute(
            text("""
                SELECT COUNT(*) FROM notifications
                WHERE user_id = :user_id AND read = FALSE
            """),
            {'user_id': user_id}
        )
        
        return result.scalar() or 0
    
    def check_streak_risk(self, user_id: UUID) -> Optional[Dict]:
        """
        Check if user's streak is at risk and create notification if needed.
        
        Args:
            user_id: User ID
            
        Returns:
            Notification if created, None otherwise
        """
        activity_stats = self.velocity_service.get_activity_summary(user_id)
        current_streak = activity_stats['activity_streak_days']
        
        if current_streak == 0:
            return None
        
        # Check if there's activity today
        today_result = self.db.execute(
            text("""
                SELECT COUNT(*) FROM learning_progress
                WHERE user_id = :user_id
                AND DATE(learned_at) = CURRENT_DATE
            """),
            {'user_id': user_id}
        )
        has_activity_today = (today_result.scalar() or 0) > 0
        
        # Check if notification already sent today
        today_notification = self.db.execute(
            text("""
                SELECT id FROM notifications
                WHERE user_id = :user_id
                AND type = 'streak_risk'
                AND DATE(created_at) = CURRENT_DATE
            """),
            {'user_id': user_id}
        ).fetchone()
        
        if has_activity_today or today_notification:
            return None
        
        # Create streak risk notification
        notification = self.create_notification(
            user_id=user_id,
            notification_type='streak_risk',
            title_en=f"🔥 Don't lose your {current_streak}-day streak!",
            title_zh=f"🔥 別失去你的{current_streak}天連勝！",
            message_en=f"You have a {current_streak}-day learning streak. Complete a review today to keep it going!",
            message_zh=f"你已經連續學習{current_streak}天了。今天完成一次複習來保持連勝！",
            data={'streak_days': current_streak}
        )
        
        return notification
    
    def check_milestone_notifications(self, user_id: UUID) -> List[Dict]:
        """
        Check for milestone achievements and create notifications.
        
        Args:
            user_id: User ID
            
        Returns:
            List of created notifications
        """
        # Check for newly unlocked achievements
        newly_unlocked = self.achievement_service.check_achievements(user_id)
        
        notifications = []
        for achievement in newly_unlocked:
            notification = self.create_notification(
                user_id=user_id,
                notification_type='achievement',
                title_en=f"🏆 Achievement Unlocked: {achievement['name_en']}",
                title_zh=f"🏆 成就解鎖：{achievement.get('name_zh', achievement['name_en'])}",
                message_en=achievement.get('description_en', ''),
                message_zh=achievement.get('description_zh', ''),
                data={
                    'achievement_id': achievement['achievement_id'],
                    'achievement_code': achievement['code'],
                    'xp_reward': achievement.get('xp_reward', 0),
                    'points_bonus': achievement.get('points_bonus', 0)
                }
            )
            notifications.append(notification)
        
        # Check for level up
        level_info = self.level_service.get_level_info(user_id)
        level = level_info['level']
        
        # Check if level-up notification already sent for this level
        level_notification = self.db.execute(
            text("""
                SELECT id FROM notifications
                WHERE user_id = :user_id
                AND type = 'level_up'
                AND data->>'level' = :level
            """),
            {'user_id': user_id, 'level': str(level)}
        ).fetchone()
        
        # We'll check level-up by comparing with previous level
        # For now, we'll create a notification if level > 1 and no notification exists
        if level > 1 and not level_notification:
            notification = self.create_notification(
                user_id=user_id,
                notification_type='level_up',
                title_en=f"🎉 Level Up! You're now Level {level}",
                title_zh=f"🎉 升級！你現在是第{level}級",
                message_en=f"Congratulations! You've reached Level {level}. Keep learning to level up even more!",
                message_zh=f"恭喜！你已經達到第{level}級。繼續學習以升級更多！",
                data={'level': level, 'total_xp': level_info['total_xp']}
            )
            notifications.append(notification)
        
        return notifications
    
    def check_goal_progress_notifications(self, user_id: UUID) -> List[Dict]:
        """
        Check goal progress and create notifications for milestones.
        
        Args:
            user_id: User ID
            
        Returns:
            List of created notifications
        """
        from .goals import GoalsService
        
        goals_service = GoalsService(self.db)
        goals = goals_service.get_active_goals(user_id)
        
        notifications = []
        for goal in goals:
            if goal['status'] != 'active':
                continue
            
            progress_pct = goal['progress_percentage']
            goal_id = goal['id']
            
            # Notify at 50% and 90% milestones
            milestones = [50, 90]
            for milestone in milestones:
                if progress_pct >= milestone:
                    # Check if notification already sent for this milestone
                    milestone_notification = self.db.execute(
                        text("""
                            SELECT id FROM notifications
                            WHERE user_id = :user_id
                            AND type = 'goal_progress'
                            AND data->>'goal_id' = :goal_id
                            AND data->>'milestone' = :milestone
                        """),
                        {
                            'user_id': user_id,
                            'goal_id': goal_id,
                            'milestone': str(milestone)
                        }
                    ).fetchone()
                    
                    if not milestone_notification:
                        notification = self.create_notification(
                            user_id=user_id,
                            notification_type='goal_progress',
                            title_en=f"🎯 Goal Progress: {milestone}% Complete",
                            title_zh=f"🎯 目標進度：{milestone}% 完成",
                            message_en=f"You're {milestone}% of the way to your goal! Keep it up!",
                            message_zh=f"你已經完成了目標的{milestone}%！繼續加油！",
                            data={
                                'goal_id': goal_id,
                                'goal_type': goal['goal_type'],
                                'milestone': milestone,
                                'progress_percentage': progress_pct
                            }
                        )
                        notifications.append(notification)
        
        return notifications


