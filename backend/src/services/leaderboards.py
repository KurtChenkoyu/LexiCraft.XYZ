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
        
        **Note:** This method uses learner-scoped data (not user-scoped).
        It queries `xp_history` and `learning_progress` tables using `learner_id`.
        The `leaderboard_entries` table is not used (it's user-scoped and deprecated).
        
        Args:
            period: Time period ('weekly', 'monthly', 'all_time')
            limit: Number of entries to return
            metric: Ranking metric ('xp', 'words', 'streak')
            
        Returns:
            List of leaderboard entries with rankings, including:
            - rank, user_id (learner_id), name, avatar, email, score, streaks
        """
        print(f"🔍 [LEADERBOARD SERVICE] get_global_leaderboard called: period={period}, limit={limit}, metric={metric}")
        # Check if leaderboard_entries table exists
        has_leaderboard_table = self._table_exists('leaderboard_entries')
        print(f"🔍 [LEADERBOARD SERVICE] has_leaderboard_table: {has_leaderboard_table}")
        
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
        # DISABLED: leaderboard_entries uses old user_id approach, we need learner-scoped data
        use_leaderboard_table = False
        # Temporarily disable leaderboard_entries table to force learner-scoped calculation
        # TODO: Update leaderboard_entries to use learner_id instead of user_id
        # if has_leaderboard_table and order_column:
        #     try:
        #         print(f"🔍 [LEADERBOARD SERVICE] Trying leaderboard_entries table with column: {order_column}")
        #         result = self.db.execute(...)
        #         use_leaderboard_table = True
        #     except Exception as e:
        #         print(f"⚠️ [LEADERBOARD SERVICE] leaderboard_entries query failed: {e}, falling back to calculation")
        #         pass
        
        # Fallback: calculate from source tables
        if not use_leaderboard_table:
            print(f"🔍 [LEADERBOARD SERVICE] Using fallback calculation from source tables")
            if metric == 'xp':
                # Calculate XP from xp_history or user_xp
                if period == 'weekly':
                    # Weekly XP from xp_history (learner-scoped)
                    # Only include learners who have xp_history records in the last 7 days
                    print(f"🔍 [LEADERBOARD SERVICE] Building weekly XP query")
                    xp_query = """
                        SELECT 
                            l.id as learner_id,
                            COALESCE(SUM(xh.xp_amount), 0) as score,
                            0 as longest_streak,
                            0 as current_streak,
                            l.display_name as name,
                            COALESCE(l.avatar_emoji, '🦄') as avatar_emoji,
                            COALESCE(u1.email, u2.email) as email
                        FROM public.learners l
                        INNER JOIN xp_history xh ON l.id = xh.learner_id
                        LEFT JOIN auth.users u1 ON l.user_id = u1.id
                        LEFT JOIN auth.users u2 ON l.guardian_id = u2.id
                        WHERE xh.earned_at >= NOW() - INTERVAL '7 days'
                        GROUP BY l.id, l.display_name, l.avatar_emoji, u1.email, u2.email
                        HAVING COALESCE(SUM(xh.xp_amount), 0) > 0
                        ORDER BY score DESC
                        LIMIT :limit
                    """
                    print(f"🔍 [LEADERBOARD SERVICE] Weekly query built, executing...")
                elif period == 'monthly':
                    # Monthly XP from xp_history (learner-scoped)
                    # Only include learners who have xp_history records in the last 30 days
                    xp_query = """
                        SELECT 
                            l.id as learner_id,
                            COALESCE(SUM(xh.xp_amount), 0) as score,
                            0 as longest_streak,
                            0 as current_streak,
                            l.display_name as name,
                            l.avatar_emoji,
                            COALESCE(u1.email, u2.email) as email
                        FROM public.learners l
                        JOIN xp_history xh ON l.id = xh.learner_id
                        LEFT JOIN auth.users u1 ON l.user_id = u1.id
                        LEFT JOIN auth.users u2 ON l.guardian_id = u2.id
                        WHERE xh.earned_at >= NOW() - INTERVAL '30 days'
                        GROUP BY l.id, l.display_name, l.avatar_emoji, u1.email, u2.email
                        HAVING COALESCE(SUM(xh.xp_amount), 0) > 0
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
                            l.avatar_emoji,
                            COALESCE(u1.email, u2.email) as email
                        FROM public.learners l
                        LEFT JOIN user_xp ux ON ux.learner_id = l.id
                        LEFT JOIN learning_progress lp ON lp.learner_id = l.id
                        LEFT JOIN auth.users u1 ON l.user_id = u1.id
                        LEFT JOIN auth.users u2 ON l.guardian_id = u2.id
                        WHERE l.id IS NOT NULL
                        GROUP BY l.id, ux.total_xp, l.display_name, l.avatar_emoji, u1.email, u2.email
                        HAVING COALESCE(ux.total_xp, 0) > 0 OR COUNT(CASE WHEN lp.status = 'verified' THEN 1 END) > 0
                        ORDER BY score DESC
                        LIMIT :limit
                    """
                
                # Check if xp_history or user_xp tables exist
                has_xp_history = self._table_exists('xp_history')
                has_user_xp = self._table_exists('user_xp')
                
                if has_xp_history or has_user_xp:
                    try:
                        print(f"🔍 [LEADERBOARD SERVICE] Executing XP query for period={period}")
                        result = self.db.execute(text(xp_query), {'limit': limit})
                        print(f"🔍 [LEADERBOARD SERVICE] Query executed successfully")
                    except Exception as e:
                        # Log the actual error for debugging
                        print(f"❌ [LEADERBOARD SERVICE] Query failed: {type(e).__name__}: {e}")
                        print(f"❌ [LEADERBOARD SERVICE] Query was:\n{xp_query}")
                        import traceback
                        traceback.print_exc()
                        # Re-raise to be caught by API layer
                        raise
                        # Query failed (maybe table structure issue), try simpler query
                        # For weekly/monthly, if xp_history fails, fall back to all_time query
                        if has_user_xp and period in ('weekly', 'monthly'):
                            # Fallback: Use all_time XP for weekly/monthly if xp_history query fails
                            print(f"⚠️ Falling back to all_time XP for {period} period")
                            result = self.db.execute(
                                text("""
                                    SELECT 
                                        l.id as learner_id,
                                        COALESCE(ux.total_xp, 0) as score,
                                        0 as longest_streak,
                                        0 as current_streak,
                                        l.display_name as name,
                                        l.avatar_emoji,
                                        COALESCE(u1.email, u2.email) as email
                                    FROM public.learners l
                                    LEFT JOIN user_xp ux ON ux.learner_id = l.id
                                    LEFT JOIN auth.users u1 ON l.user_id = u1.id
                                    LEFT JOIN auth.users u2 ON l.guardian_id = u2.id
                                    WHERE l.id IS NOT NULL
                                    GROUP BY l.id, ux.total_xp, l.display_name, l.avatar_emoji, u1.email, u2.email
                                    HAVING COALESCE(ux.total_xp, 0) > 0
                                    ORDER BY score DESC
                                    LIMIT :limit
                                """),
                                {'limit': limit}
                            )
                        elif has_user_xp and period == 'all_time':
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
                                        l.avatar_emoji,
                                        COALESCE(u1.email, u2.email) as email
                                    FROM public.learners l
                                    LEFT JOIN user_xp ux ON ux.learner_id = l.id
                                    LEFT JOIN learning_progress lp ON lp.learner_id = l.id
                                    LEFT JOIN auth.users u1 ON l.user_id = u1.id
                                    LEFT JOIN auth.users u2 ON l.guardian_id = u2.id
                                    WHERE l.id IS NOT NULL
                                    GROUP BY l.id, ux.total_xp, l.display_name, l.avatar_emoji, u1.email, u2.email
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
                # Calculate words from learning_progress (learner-scoped)
                date_filter = ""
                if period == 'weekly':
                    date_filter = "AND lp.learned_at >= NOW() - INTERVAL '7 days'"
                elif period == 'monthly':
                    date_filter = "AND lp.learned_at >= NOW() - INTERVAL '30 days'"
                
                result = self.db.execute(
                    text(f"""
                        SELECT 
                            l.id as learner_id,
                            COUNT(*) as score,
                            0 as longest_streak,
                            0 as current_streak,
                            l.display_name as name,
                            l.avatar_emoji,
                            COALESCE(u1.email, u2.email) as email
                        FROM public.learners l
                        JOIN learning_progress lp ON l.id = lp.learner_id
                        LEFT JOIN auth.users u1 ON l.user_id = u1.id
                        LEFT JOIN auth.users u2 ON l.guardian_id = u2.id
                        WHERE lp.status IN ('verified', 'mastered', 'solid')
                        {date_filter}
                        GROUP BY l.id, l.display_name, l.avatar_emoji, u1.email, u2.email
                        HAVING COUNT(*) > 0
                        ORDER BY score DESC
                        LIMIT :limit
                    """),
                    {'limit': limit}
                )
            else:  # streak
                # Calculate streak from learning_progress (learner-scoped, simplified)
                interval = '90 days'
                result = self.db.execute(
                    text(f"""
                        SELECT 
                            l.id as learner_id,
                            COUNT(DISTINCT DATE(lp.learned_at)) as score,
                            COUNT(DISTINCT DATE(lp.learned_at)) as longest_streak,
                            COUNT(DISTINCT DATE(lp.learned_at)) as current_streak,
                            l.display_name as name,
                            l.avatar_emoji,
                            COALESCE(u1.email, u2.email) as email
                        FROM public.learners l
                        JOIN learning_progress lp ON l.id = lp.learner_id
                        LEFT JOIN auth.users u1 ON l.user_id = u1.id
                        LEFT JOIN auth.users u2 ON l.guardian_id = u2.id
                        WHERE lp.learned_at >= NOW() - INTERVAL '{interval}'
                        GROUP BY l.id, l.display_name, l.avatar_emoji, u1.email, u2.email
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
            # All queries now return: learner_id, score, [optional fields], longest_streak, current_streak, name, avatar_emoji, email
            # XP queries (all_time) include: learner_id, score, words_mastered, words_in_progress, longest_streak, current_streak, name, avatar_emoji, email (9 fields)
            # Other queries: learner_id, score, longest_streak, current_streak, name, avatar_emoji, email (7 fields)
            learner_id = str(row[0])
            score = int(row[1]) if row[1] else 0
            
            # Handle different query formats
            if len(row) >= 9:
                # All-time XP query format: learner_id, score, words_mastered, words_in_progress, longest_streak, current_streak, name, avatar_emoji, email
                words_mastered = int(row[2]) if row[2] else 0
                words_in_progress = int(row[3]) if row[3] else 0
                longest_streak = int(row[4]) if row[4] else 0
                current_streak = int(row[5]) if row[5] else 0
                name = row[6] or 'Anonymous'
                avatar = row[7] or '🦄'  # Default emoji if null
                email = row[8] if len(row) > 8 and row[8] else None
            else:
                # Standard format: learner_id, score, longest_streak, current_streak, name, avatar_emoji, email (7 fields)
                longest_streak = int(row[2]) if len(row) > 2 and row[2] else 0
                current_streak = int(row[3]) if len(row) > 3 and row[3] else 0
                name = row[4] or 'Anonymous' if len(row) > 4 else 'Anonymous'
                avatar = row[5] or '🦄' if len(row) > 5 else '🦄'  # Default emoji if null
                email = row[6] if len(row) > 6 and row[6] else None
                words_mastered = 0
                words_in_progress = 0
            
            # Use learner_id as user_id for frontend compatibility (frontend expects user_id field)
            leaderboard.append({
                'rank': rank,
                'user_id': learner_id,  # Frontend expects user_id, but we're passing learner_id
                'name': name,
                'avatar': avatar,  # Include avatar_emoji as avatar
                'email': email,
                'score': score,
                'longest_streak': longest_streak,
                'current_streak': current_streak,
                'words_mastered': words_mastered,
                'words_in_progress': words_in_progress
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
        
        For MVP, this returns 'Family' leaderboard (user's learners).
        
        Args:
            user_id: User ID
            period: Time period ('weekly', 'monthly', 'all_time')
            metric: Ranking metric ('xp', 'words', 'streak')
            
        Returns:
            List of friend leaderboard entries
        """
        # Get all learners belonging to this parent user
        # This effectively creates a "Family Leaderboard" when 'friends' tab is selected
        learners_result = self.db.execute(
            text("SELECT id FROM public.learners WHERE user_id = :user_id OR guardian_id = :user_id"),
            {'user_id': user_id}
        )
        my_learner_ids = [str(row[0]) for row in learners_result.fetchall()]
        
        if not my_learner_ids:
            return []

        # Get global leaderboard and filter to only show user's learners
        global_list = self.get_global_leaderboard(period, 1000, metric)
        
        friends_list = [entry for entry in global_list if entry['user_id'] in my_learner_ids]
        
        # Re-rank
        for i, entry in enumerate(friends_list):
            entry['rank'] = i + 1
        
        return friends_list
    
    def get_user_rank(
        self,
        user_id: UUID,
        period: str = 'weekly',
        metric: str = 'xp'
    ) -> Optional[Dict]:
        """
        Get the rank of the user's *primary* learner profile.
        
        Args:
            user_id: User ID
            period: Time period ('weekly', 'monthly', 'all_time')
            metric: Ranking metric ('xp', 'words', 'streak')
            
        Returns:
            User's rank information or None if not ranked
        """
        # Find primary learner (parent profile)
        learner_result = self.db.execute(
            text("SELECT id FROM public.learners WHERE user_id = :user_id AND is_parent_profile = true LIMIT 1"),
            {'user_id': user_id}
        )
        row = learner_result.fetchone()
        if not row:
            # Fallback: get any learner associated with this user
            learner_result = self.db.execute(
                text("SELECT id FROM public.learners WHERE user_id = :user_id OR guardian_id = :user_id LIMIT 1"),
                {'user_id': user_id}
            )
            row = learner_result.fetchone()
            if not row:
                return None
        
        primary_learner_id = str(row[0])
        
        # Get global list and find index
        # Efficiency Note: Real production apps calculate rank via SQL COUNT(*),
        # but for this repair, fetching the list is safer logic-wise.
        global_list = self.get_global_leaderboard(period, 1000, metric)
        
        for entry in global_list:
            if entry['user_id'] == primary_learner_id:
                return {
                    'rank': entry['rank'],
                    'user_id': str(user_id),
                    'score': entry['score'],
                    'period': period,
                    'metric': metric
                }
        
        return None
    
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


