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
    
    def _table_exists(self, table_name: str) -> bool:
        """Check if a table exists."""
        try:
            result = self.db.execute(
                text("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = :table_name
                    )
                """),
                {'table_name': table_name}
            )
            return result.scalar()
        except Exception:
            return False
    
    def get_global_leaderboard(
        self,
        period: str = 'weekly',
        limit: int = 50,
        metric: str = 'xp'
    ) -> List[Dict]:
        """
        Get global leaderboard.
        
        Falls back to calculating from source tables if leaderboard_entries doesn't exist.
        
        Args:
            period: Time period ('weekly', 'monthly', 'all_time')
            limit: Number of entries to return
            metric: Ranking metric ('xp', 'words', 'streak')
            
        Returns:
            List of leaderboard entries with rankings
        """
        # Check if leaderboard_entries table exists
        has_leaderboard_table = self._table_exists('leaderboard_entries')
        
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
                # For all_time words, always calculate from learning_progress
                order_column = None
        elif metric == 'streak':
            order_column = 'longest_streak'
        else:
            raise ValueError(f"Invalid metric: {metric}")
        
        # Try to use leaderboard_entries if it exists and we have a column
        use_leaderboard_table = False
        if has_leaderboard_table and order_column:
            try:
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
                use_leaderboard_table = True
            except Exception:
                # Table exists but query failed, fall back to calculation
                pass
        
        # Fallback: calculate from source tables
        if not use_leaderboard_table:
            if metric == 'xp':
                # Calculate XP from xp_history or user_xp
                if period == 'weekly':
                    xp_query = """
                        SELECT 
                            COALESCE(xh.user_id, ux.user_id) as user_id,
                            COALESCE(SUM(xh.xp_amount), ux.total_xp, 0) as score,
                            0 as longest_streak,
                            0 as current_streak,
                            u.name,
                            u.email
                        FROM (
                            SELECT DISTINCT user_id FROM xp_history
                            WHERE earned_at >= NOW() - INTERVAL '7 days'
                            UNION
                            SELECT DISTINCT user_id FROM user_xp
                        ) users
                        LEFT JOIN xp_history xh ON users.user_id = xh.user_id 
                            AND xh.earned_at >= NOW() - INTERVAL '7 days'
                        LEFT JOIN user_xp ux ON users.user_id = ux.user_id
                        JOIN auth.users u ON COALESCE(xh.user_id, ux.user_id) = u.id
                        GROUP BY COALESCE(xh.user_id, ux.user_id), ux.total_xp, u.name, u.email
                        HAVING COALESCE(SUM(xh.xp_amount), ux.total_xp, 0) > 0
                        ORDER BY score DESC
                        LIMIT :limit
                    """
                elif period == 'monthly':
                    xp_query = """
                        SELECT 
                            COALESCE(xh.user_id, ux.user_id) as user_id,
                            COALESCE(SUM(xh.xp_amount), ux.total_xp, 0) as score,
                            0 as longest_streak,
                            0 as current_streak,
                            u.name,
                            u.email
                        FROM (
                            SELECT DISTINCT user_id FROM xp_history
                            WHERE earned_at >= NOW() - INTERVAL '30 days'
                            UNION
                            SELECT DISTINCT user_id FROM user_xp
                        ) users
                        LEFT JOIN xp_history xh ON users.user_id = xh.user_id 
                            AND xh.earned_at >= NOW() - INTERVAL '30 days'
                        LEFT JOIN user_xp ux ON users.user_id = ux.user_id
                        JOIN auth.users u ON COALESCE(xh.user_id, ux.user_id) = u.id
                        GROUP BY COALESCE(xh.user_id, ux.user_id), ux.total_xp, u.name, u.email
                        HAVING COALESCE(SUM(xh.xp_amount), ux.total_xp, 0) > 0
                        ORDER BY score DESC
                        LIMIT :limit
                    """
                else:  # all_time - now using learner-scoped XP
                    xp_query = """
                        SELECT 
                            l.id as learner_id,
                            COALESCE(ux.total_xp, 0) as score,
                            COUNT(CASE WHEN lp.status = 'verified' THEN 1 END) as words_mastered,
                            COUNT(CASE WHEN lp.status IN ('hollow', 'learning', 'pending') THEN 1 END) as words_in_progress,
                            0 as longest_streak,
                            0 as current_streak,
                            l.display_name as name,
                            u.email
                        FROM public.learners l
                        LEFT JOIN user_xp ux ON ux.learner_id = l.id
                        LEFT JOIN learning_progress lp ON lp.learner_id = l.id
                        JOIN auth.users u ON l.user_id = u.id OR l.guardian_id = u.id
                        WHERE l.id IS NOT NULL
                        GROUP BY l.id, ux.total_xp, l.display_name, u.email
                        HAVING COALESCE(ux.total_xp, 0) > 0 OR COUNT(CASE WHEN lp.status = 'verified' THEN 1 END) > 0
                        ORDER BY score DESC
                        LIMIT :limit
                    """
                
                # Check if xp_history or user_xp tables exist
                has_xp_history = self._table_exists('xp_history')
                has_user_xp = self._table_exists('user_xp')
                
                if has_xp_history or has_user_xp:
                    try:
                        result = self.db.execute(text(xp_query), {'limit': limit})
                    except Exception as e:
                        # Query failed (maybe table structure issue), try simpler query
                        if has_user_xp and period == 'all_time':
                            # Simple fallback for all_time XP - now using learner-scoped XP
                            result = self.db.execute(
                                text("""
                                    SELECT 
                                        l.id as learner_id,
                                        COALESCE(ux.total_xp, 0) as score,
                                        COUNT(CASE WHEN lp.status = 'verified' THEN 1 END) as words_mastered,
                                        COUNT(CASE WHEN lp.status IN ('hollow', 'learning', 'pending') THEN 1 END) as words_in_progress,
                                        0 as longest_streak,
                                        0 as current_streak,
                                        l.display_name as name,
                                        u.email
                                    FROM public.learners l
                                    LEFT JOIN user_xp ux ON ux.learner_id = l.id
                                    LEFT JOIN learning_progress lp ON lp.learner_id = l.id
                                    JOIN auth.users u ON l.user_id = u.id OR l.guardian_id = u.id
                                    WHERE l.id IS NOT NULL
                                    GROUP BY l.id, ux.total_xp, l.display_name, u.email
                                    HAVING COALESCE(ux.total_xp, 0) > 0 OR COUNT(CASE WHEN lp.status = 'verified' THEN 1 END) > 0
                                    ORDER BY score DESC
                                    LIMIT :limit
                                """),
                                {'limit': limit}
                            )
                        else:
                            return []
                else:
                    # No XP data available
                    return []
                    
            elif metric == 'words':
                # Calculate words from learning_progress
                if period == 'weekly':
                    date_filter = "AND lp.learned_at >= NOW() - INTERVAL '7 days'"
                elif period == 'monthly':
                    date_filter = "AND lp.learned_at >= NOW() - INTERVAL '30 days'"
                else:
                    date_filter = ""
                
                result = self.db.execute(
                    text(f"""
                        SELECT 
                            lp.user_id,
                            COUNT(*) as score,
                            0 as longest_streak,
                            0 as current_streak,
                            u.name,
                            u.email
                        FROM learning_progress lp
                        JOIN auth.users u ON lp.user_id = u.id
                        WHERE lp.status = 'verified'
                        {date_filter}
                        GROUP BY lp.user_id, u.name, u.email
                        HAVING COUNT(*) > 0
                        ORDER BY score DESC
                        LIMIT :limit
                    """),
                    {'limit': limit}
                )
            else:  # streak
                # Calculate streak from learning_progress (simplified)
                result = self.db.execute(
                    text("""
                        SELECT 
                            lp.user_id,
                            COUNT(DISTINCT DATE(lp.learned_at)) as score,
                            COUNT(DISTINCT DATE(lp.learned_at)) as longest_streak,
                            COUNT(DISTINCT DATE(lp.learned_at)) as current_streak,
                            u.name,
                            u.email
                        FROM learning_progress lp
                        JOIN auth.users u ON lp.user_id = u.id
                        WHERE lp.status = 'verified'
                        AND lp.learned_at >= NOW() - INTERVAL '90 days'
                        GROUP BY lp.user_id, u.name, u.email
                        HAVING COUNT(DISTINCT DATE(lp.learned_at)) > 0
                        ORDER BY score DESC
                        LIMIT :limit
                    """),
                    {'limit': limit}
                )
        
        # Build leaderboard from results
        rows = result.fetchall()
        if not rows:
            return []
        
        leaderboard = []
        rank = 1
        
        for row in rows:
            # XP queries (all_time) now return: learner_id, score, words_mastered, words_in_progress, longest_streak, current_streak, name, email
            # Other queries still return: user_id, score, longest_streak, current_streak, name, email
            # Check if first column is learner_id (UUID) or user_id by checking row length
            if len(row) >= 8:
                # New learner-scoped XP query format
                learner_id = str(row[0])
                score = row[1]
                words_mastered = row[2] if len(row) > 2 else 0
                words_in_progress = row[3] if len(row) > 3 else 0
                longest_streak = row[4] if len(row) > 4 else 0
                current_streak = row[5] if len(row) > 5 else 0
                name = row[6] or 'Anonymous'  # learner.display_name
                email = row[7] if len(row) > 7 and row[7] else None
                
                # Get user_id from learner for backward compatibility
                learner_result = self.db.execute(
                    text("SELECT COALESCE(user_id, guardian_id) FROM public.learners WHERE id = :learner_id"),
                    {'learner_id': learner_id}
                )
                user_id_row = learner_result.fetchone()
                user_id = str(user_id_row[0]) if user_id_row and user_id_row[0] else learner_id
            else:
                # Legacy query format (words, streak, or old XP queries)
                user_id = str(row[0])
                score = row[1]
                longest_streak = row[2] if len(row) > 2 else 0
                current_streak = row[3] if len(row) > 3 else 0
                words_mastered = 0
                words_in_progress = 0
                
                # Name and email are in columns 4 and 5 (if present)
                if len(row) >= 6:
                    name = row[4] or 'Anonymous'
                    email = row[5] if row[5] else None
                else:
                    # Fallback: fetch user info separately
                    user_result = self.db.execute(
                        text("SELECT name, email FROM auth.users WHERE id = :user_id"),
                        {'user_id': user_id}
                    )
                    user_row = user_result.fetchone()
                    name = user_row[0] if user_row and user_row[0] else 'Anonymous'
                    email = user_row[1] if user_row and user_row[1] else None
            
            leaderboard.append({
                'rank': rank,
                'user_id': user_id,
                'name': name,
                'email': email,
                'score': score,
                'longest_streak': longest_streak,
                'current_streak': current_streak,
                'words_mastered': words_mastered,  # New field for learner-scoped queries
                'words_in_progress': words_in_progress  # New field for learner-scoped queries
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


