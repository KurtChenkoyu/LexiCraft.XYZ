"""
Leaderboard Service

Handles leaderboard rankings and user connections.
"""

from typing import Dict, List, Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import text


class LeaderboardService:
    """Service for managing leaderboards."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_global_leaderboard(
        self,
        period: str = 'weekly',
        limit: int = 50,
        metric: str = 'xp'
    ) -> List[Dict]:
        """
        Get global leaderboard.
        
        Args:
            period: Time period ('weekly', 'monthly', 'all_time')
            limit: Number of entries to return
            metric: Ranking metric ('xp', 'words', 'streak')
            
        Returns:
            List of leaderboard entries with rankings
        """
        # Determine column based on period and metric
        if metric == 'xp':
            if period == 'weekly':
                order_column = 'weekly_xp'
            elif period == 'monthly':
                order_column = 'monthly_xp'
            else:  # all_time
                order_column = 'all_time_xp'
        elif metric == 'words':
            if period == 'weekly':
                order_column = 'weekly_words'
            elif period == 'monthly':
                order_column = 'monthly_words'
            else:
                # For all_time words, we need to calculate from learning_progress
                order_column = None
        elif metric == 'streak':
            order_column = 'longest_streak'
        else:
            raise ValueError(f"Invalid metric: {metric}")
        
        if order_column:
            # Query from leaderboard_entries
            result = self.db.execute(
                text(f"""
                    SELECT 
                        le.user_id,
                        le.{order_column} as score,
                        le.longest_streak,
                        le.current_streak,
                        u.name,
                        u.email
                    FROM leaderboard_entries le
                    JOIN auth.users u ON le.user_id = u.id
                    WHERE le.{order_column} > 0
                    ORDER BY le.{order_column} DESC
                    LIMIT :limit
                """),
                {'limit': limit}
            )
        else:
            # For all_time words, calculate from learning_progress
            result = self.db.execute(
                text("""
                    SELECT 
                        lp.user_id,
                        COUNT(*) as score,
                        COALESCE(le.longest_streak, 0) as longest_streak,
                        COALESCE(le.current_streak, 0) as current_streak,
                        u.name,
                        u.email
                    FROM learning_progress lp
                    JOIN auth.users u ON lp.user_id = u.id
                    LEFT JOIN leaderboard_entries le ON lp.user_id = le.user_id
                    WHERE lp.status = 'verified'
                    GROUP BY lp.user_id, le.longest_streak, le.current_streak, u.name, u.email
                    ORDER BY score DESC
                    LIMIT :limit
                """),
                {'limit': limit}
            )
        
        leaderboard = []
        rank = 1
        for row in result.fetchall():
            leaderboard.append({
                'rank': rank,
                'user_id': str(row[0]),
                'name': row[4] or 'Anonymous',
                'email': row[5] if row[5] else None,
                'score': row[1],
                'longest_streak': row[2] or 0,
                'current_streak': row[3] or 0
            })
            rank += 1
        
        return leaderboard
    
    def get_friends_leaderboard(
        self,
        user_id: UUID,
        period: str = 'weekly',
        metric: str = 'xp'
    ) -> List[Dict]:
        """
        Get leaderboard for user's friends/classmates.
        
        Args:
            user_id: User ID
            period: Time period ('weekly', 'monthly', 'all_time')
            metric: Ranking metric ('xp', 'words', 'streak')
            
        Returns:
            List of friend leaderboard entries
        """
        # Get user's connections
        connections_result = self.db.execute(
            text("""
                SELECT connected_user_id FROM user_connections
                WHERE user_id = :user_id
                UNION
                SELECT user_id FROM user_connections
                WHERE connected_user_id = :user_id
            """),
            {'user_id': user_id}
        )
        
        friend_ids = [row[0] for row in connections_result.fetchall()]
        
        if not friend_ids:
            return []
        
        # Determine column
        if metric == 'xp':
            if period == 'weekly':
                order_column = 'weekly_xp'
            elif period == 'monthly':
                order_column = 'monthly_xp'
            else:
                order_column = 'all_time_xp'
        elif metric == 'words':
            if period == 'weekly':
                order_column = 'weekly_words'
            elif period == 'monthly':
                order_column = 'monthly_words'
            else:
                order_column = None
        elif metric == 'streak':
            order_column = 'longest_streak'
        else:
            raise ValueError(f"Invalid metric: {metric}")
        
        # Include user themselves
        friend_ids.append(user_id)
        
        if order_column:
            result = self.db.execute(
                text(f"""
                    SELECT 
                        le.user_id,
                        le.{order_column} as score,
                        le.longest_streak,
                        le.current_streak,
                        u.name,
                        u.email
                    FROM leaderboard_entries le
                    JOIN auth.users u ON le.user_id = u.id
                    WHERE le.user_id = ANY(:friend_ids)
                    AND le.{order_column} > 0
                    ORDER BY le.{order_column} DESC
                """),
                {'friend_ids': friend_ids}
            )
        else:
            # For all_time words
            result = self.db.execute(
                text("""
                    SELECT 
                        lp.user_id,
                        COUNT(*) as score,
                        COALESCE(le.longest_streak, 0) as longest_streak,
                        COALESCE(le.current_streak, 0) as current_streak,
                        u.name,
                        u.email
                    FROM learning_progress lp
                    JOIN auth.users u ON lp.user_id = u.id
                    LEFT JOIN leaderboard_entries le ON lp.user_id = le.user_id
                    WHERE lp.user_id = ANY(:friend_ids)
                    AND lp.status = 'verified'
                    GROUP BY lp.user_id, le.longest_streak, le.current_streak, u.name, u.email
                    ORDER BY score DESC
                """),
                {'friend_ids': friend_ids}
            )
        
        leaderboard = []
        rank = 1
        for row in result.fetchall():
            is_user = str(row[0]) == str(user_id)
            leaderboard.append({
                'rank': rank,
                'user_id': str(row[0]),
                'name': row[4] or 'Anonymous',
                'email': row[5] if row[5] else None,
                'score': row[1],
                'longest_streak': row[2] or 0,
                'current_streak': row[3] or 0,
                'is_me': is_user
            })
            rank += 1
        
        return leaderboard
    
    def get_user_rank(
        self,
        user_id: UUID,
        period: str = 'weekly',
        metric: str = 'xp'
    ) -> Optional[Dict]:
        """
        Get user's rank in global leaderboard.
        
        Args:
            user_id: User ID
            period: Time period ('weekly', 'monthly', 'all_time')
            metric: Ranking metric ('xp', 'words', 'streak')
            
        Returns:
            User's rank information or None if not ranked
        """
        # Get user's score
        result = self.db.execute(
            text("""
                SELECT weekly_xp, monthly_xp, all_time_xp,
                       weekly_words, monthly_words, longest_streak
                FROM leaderboard_entries
                WHERE user_id = :user_id
            """),
            {'user_id': user_id}
        )
        
        row = result.fetchone()
        if not row:
            return None
        
        # Determine score based on period and metric
        if metric == 'xp':
            if period == 'weekly':
                user_score = row[0] or 0
            elif period == 'monthly':
                user_score = row[1] or 0
            else:
                user_score = row[2] or 0
        elif metric == 'words':
            if period == 'weekly':
                user_score = row[3] or 0
            elif period == 'monthly':
                user_score = row[4] or 0
            else:
                # Count from learning_progress
                count_result = self.db.execute(
                    text("""
                        SELECT COUNT(*) FROM learning_progress
                        WHERE user_id = :user_id AND status = 'verified'
                    """),
                    {'user_id': user_id}
                )
                user_score = count_result.scalar() or 0
        elif metric == 'streak':
            user_score = row[5] or 0
        else:
            raise ValueError(f"Invalid metric: {metric}")
        
        if user_score == 0:
            return None
        
        # Count users with higher scores
        if metric == 'xp':
            if period == 'weekly':
                order_column = 'weekly_xp'
            elif period == 'monthly':
                order_column = 'monthly_xp'
            else:
                order_column = 'all_time_xp'
            
            rank_result = self.db.execute(
                text(f"""
                    SELECT COUNT(*) + 1
                    FROM leaderboard_entries
                    WHERE {order_column} > :user_score
                """),
                {'user_score': user_score}
            )
            rank = rank_result.scalar() or 1
            
        elif metric == 'words':
            if period == 'weekly':
                order_column = 'weekly_words'
            elif period == 'monthly':
                order_column = 'monthly_words'
            else:
                # Count from learning_progress
                rank_result = self.db.execute(
                    text("""
                        SELECT COUNT(DISTINCT user_id) + 1
                        FROM learning_progress
                        WHERE status = 'verified'
                        GROUP BY user_id
                        HAVING COUNT(*) > :user_score
                    """),
                    {'user_score': user_score}
                )
                rank = rank_result.scalar() or 1
                return {
                    'rank': rank,
                    'user_id': str(user_id),
                    'score': user_score,
                    'period': period,
                    'metric': metric
                }
        else:  # streak
            rank_result = self.db.execute(
                text("""
                    SELECT COUNT(*) + 1
                    FROM leaderboard_entries
                    WHERE longest_streak > :user_score
                """),
                {'user_score': user_score}
            )
            rank = rank_result.scalar() or 1
        
        return {
            'rank': rank,
            'user_id': str(user_id),
            'score': user_score,
            'period': period,
            'metric': metric
        }
    
    def update_leaderboard_entry(self, user_id: UUID):
        """
        Update leaderboard entry for a user.
        
        Args:
            user_id: User ID
        """
        self.db.execute(
            text("SELECT update_leaderboard_entry(:user_id)"),
            {'user_id': user_id}
        )
        self.db.commit()
    
    def add_connection(
        self,
        user_id: UUID,
        connected_user_id: UUID,
        connection_type: str = 'friend'
    ) -> bool:
        """
        Add a connection between users.
        
        Args:
            user_id: User ID
            connected_user_id: Connected user ID
            connection_type: Type of connection ('friend', 'classmate')
            
        Returns:
            True if added, False if already exists
        """
        try:
            self.db.execute(
                text("""
                    INSERT INTO user_connections (user_id, connected_user_id, connection_type)
                    VALUES (:user_id, :connected_user_id, :connection_type)
                    ON CONFLICT (user_id, connected_user_id) DO NOTHING
                """),
                {
                    'user_id': user_id,
                    'connected_user_id': connected_user_id,
                    'connection_type': connection_type
                }
            )
            self.db.commit()
            return True
        except Exception:
            self.db.rollback()
            return False
    
    def get_connections(self, user_id: UUID) -> List[Dict]:
        """
        Get user's connections.
        
        Args:
            user_id: User ID
            
        Returns:
            List of connected users
        """
        result = self.db.execute(
            text("""
                SELECT 
                    uc.connected_user_id,
                    uc.connection_type,
                    u.name,
                    u.email
                FROM user_connections uc
                JOIN auth.users u ON uc.connected_user_id = u.id
                WHERE uc.user_id = :user_id
            """),
            {'user_id': user_id}
        )
        
        connections = []
        for row in result.fetchall():
            connections.append({
                'user_id': str(row[0]),
                'connection_type': row[1],
                'name': row[2] or 'Anonymous',
                'email': row[3] if row[3] else None
            })
        
        return connections


