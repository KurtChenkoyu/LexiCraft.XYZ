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
        learner_id: UUID,  # CHANGED: was user_id
        amount: int,
        source: str,
        source_id: Optional[UUID] = None
    ) -> Dict:
        """
        Award XP to a learner and check for level-up.
        
        Args:
            learner_id: Learner ID (from public.learners)
            amount: XP amount to award
            source: Source of XP ('word_learned', 'streak', 'achievement', etc.)
            source_id: Optional ID of the source (achievement_id, goal_id, etc.)
            
        Returns:
            Dictionary with level info and whether level-up occurred
        """
        # Initialize learner XP if not exists
        self._ensure_learner_xp(learner_id)
        
        # Get current XP (query by learner_id)
        result = self.db.execute(
            text("SELECT total_xp, current_level FROM user_xp WHERE learner_id = :learner_id"),
            {'learner_id': learner_id}
        )
        row = result.fetchone()
        
        if not row:
            raise ValueError(f"Learner XP record not found for learner {learner_id}")
        
        old_total_xp = row[0] or 0
        old_level = row[1] or 1
        
        # Add XP
        new_total_xp = old_total_xp + amount
        
        # Calculate new level
        level_info = self.calculate_level(new_total_xp)
        new_level = level_info['level']
        xp_to_next = level_info['xp_to_next']
        xp_in_level = level_info['xp_in_level']
        
        # Update user_xp (using learner_id)
        self.db.execute(
            text("""
                UPDATE user_xp
                SET total_xp = :total_xp,
                    current_level = :level,
                    xp_to_next_level = :xp_to_next,
                    xp_in_current_level = :xp_in_level,
                    updated_at = NOW()
                WHERE learner_id = :learner_id
            """),
            {
                'learner_id': learner_id,
                'total_xp': new_total_xp,
                'level': new_level,
                'xp_to_next': xp_to_next,
                'xp_in_level': xp_in_level
            }
        )
        
        # Record in XP history (using learner_id)
        self.db.execute(
            text("""
                INSERT INTO xp_history (learner_id, xp_amount, source, source_id, earned_at)
                VALUES (:learner_id, :amount, :source, :source_id, NOW())
            """),
            {
                'learner_id': learner_id,
                'amount': amount,
                'source': source,
                'source_id': source_id
            }
        )
        
        # Update leaderboard (get user_id from learner for backward compatibility)
        learner_result = self.db.execute(
            text("""
                SELECT COALESCE(user_id, guardian_id) 
                FROM public.learners 
                WHERE id = :learner_id
            """),
            {'learner_id': learner_id}
        )
        user_id_row = learner_result.fetchone()
        if user_id_row and user_id_row[0]:
            self.db.execute(
                text("SELECT update_leaderboard_entry(:user_id)"),
                {'user_id': user_id_row[0]}
            )
        
        self.db.commit()
        
        level_up = new_level > old_level
        
        # Get new unlocks if level up occurred
        new_unlocks = []
        if level_up:
            # Get all unlocks for levels between old and new
            for level in range(old_level + 1, new_level + 1):
                unlocks_at_level = self.get_new_unlocks_for_level(level)
                for unlock in unlocks_at_level:
                    unlock['unlocked_at_level'] = level
                    new_unlocks.append(unlock)
        
        return {
            'old_level': old_level,
            'new_level': new_level,
            'old_xp': old_total_xp,
            'new_xp': new_total_xp,
            'xp_added': amount,
            'level_up': level_up,
            'xp_to_next_level': xp_to_next,
            'xp_in_current_level': xp_in_level,
            'progress_percentage': int((xp_in_level / xp_to_next) * 100) if xp_to_next > 0 else 0,
            'new_unlocks': new_unlocks  # List of features unlocked by this level up
        }
    
    def get_level_info(self, learner_id: UUID) -> Dict:  # CHANGED: was user_id
        """
        Get current level information for a learner.
        
        Args:
            learner_id: Learner ID
            
        Returns:
            Dictionary with level, XP, and progress info
        """
        self._ensure_learner_xp(learner_id)
        
        result = self.db.execute(
            text("""
                SELECT total_xp, current_level, xp_to_next_level, xp_in_current_level
                FROM user_xp
                WHERE learner_id = :learner_id
            """),
            {'learner_id': learner_id}
        )
        
        row = result.fetchone()
        if not row:
            # If record still doesn't exist after _ensure_learner_xp, something went wrong
            # Try to create it again and fetch
            self._ensure_learner_xp(learner_id)
            result = self.db.execute(
                text("""
                    SELECT total_xp, current_level, xp_to_next_level, xp_in_current_level
                    FROM user_xp
                    WHERE learner_id = :learner_id
                """),
                {'learner_id': learner_id}
            )
            row = result.fetchone()
            if not row:
                # Still no record - return default values instead of crashing
                return {
                    'level': 1,
                    'total_xp': 0,
                    'xp_to_next_level': 100,
                    'xp_in_current_level': 0,
                    'progress_percentage': 0
                }
        
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
    
    def get_xp_history(self, learner_id: UUID, days: int = 30) -> List[Dict]:  # CHANGED: was user_id
        """
        Get XP earning history.
        
        Args:
            learner_id: Learner ID
            days: Number of days to look back
            
        Returns:
            List of XP history entries
        """
        result = self.db.execute(
            text("""
                SELECT xp_amount, source, source_id, earned_at
                FROM xp_history
                WHERE learner_id = :learner_id
                AND earned_at >= NOW() - INTERVAL ':days days'
                ORDER BY earned_at DESC
            """),
            {'learner_id': learner_id, 'days': days}
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
    
    def get_xp_summary(self, learner_id: UUID, days: int = 30) -> Dict:  # CHANGED: was user_id
        """
        Get XP summary for a period.
        
        Args:
            learner_id: Learner ID
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
                WHERE learner_id = :learner_id
                AND earned_at >= NOW() - INTERVAL ':days days'
                GROUP BY source
            """),
            {'learner_id': learner_id, 'days': days, 'source': 'word_learned'}
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
        """DEPRECATED: Ensure user has an XP record. Use _ensure_learner_xp instead."""
        # This method is kept for backward compatibility but should not be used
        # after migration to learner-scoped XP
        self.db.execute(
            text("SELECT initialize_user_xp(:user_id)"),
            {'user_id': user_id}
        )
        self.db.commit()
    
    def _ensure_learner_xp(self, learner_id: UUID):
        """Ensure learner has an XP record."""
        # First check if record exists with this learner_id
        result = self.db.execute(
            text("SELECT learner_id FROM user_xp WHERE learner_id = :learner_id"),
            {'learner_id': learner_id}
        )
        if result.fetchone():
            # Record already exists
            return
        
        # Get user_id from learners table (required for user_xp table)
        learner_result = self.db.execute(
            text("""
                SELECT COALESCE(user_id, guardian_id) as user_id
                FROM public.learners
                WHERE id = :learner_id
            """),
            {'learner_id': learner_id}
        )
        learner_row = learner_result.fetchone()
        if not learner_row or not learner_row[0]:
            # Can't create XP record without user_id
            raise ValueError(f"Cannot create XP record for learner {learner_id}: no user_id or guardian_id found")
        
        user_id = learner_row[0]
        
        # During migration (Part 1 complete, Part 3 not yet run), learner_id is nullable
        # and primary key is still on user_id. So we can safely insert.
        # After Part 3, primary key will be on learner_id, so ON CONFLICT will work.
        try:
            # Try insert with ON CONFLICT (works after Part 3 migration)
            self.db.execute(
                text("""
                    INSERT INTO user_xp (learner_id, user_id, total_xp, current_level, xp_to_next_level, xp_in_current_level, updated_at)
                    VALUES (:learner_id, :user_id, 0, 1, 100, 0, NOW())
                    ON CONFLICT (learner_id) DO NOTHING
                """),
                {'learner_id': learner_id, 'user_id': user_id}
            )
            self.db.commit()
        except Exception as e:
            # If ON CONFLICT fails (before Part 3), try simple insert
            # This will fail if record already exists, which is fine
            self.db.rollback()
            try:
                self.db.execute(
                    text("""
                        INSERT INTO user_xp (learner_id, user_id, total_xp, current_level, xp_to_next_level, xp_in_current_level, updated_at)
                        VALUES (:learner_id, :user_id, 0, 1, 100, 0, NOW())
                    """),
                    {'learner_id': learner_id, 'user_id': user_id}
                )
                self.db.commit()
            except Exception as e2:
                # Record might already exist, which is fine
                # But log the error for debugging
                if "duplicate key" not in str(e2).lower() and "unique constraint" not in str(e2).lower():
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.warning(f"Failed to create XP record for learner {learner_id}: {e2}")
                self.db.rollback()
                pass

    # ============================================
    # LEVEL UNLOCK METHODS
    # ============================================
    
    def get_unlocked_features(self, learner_id: UUID) -> List[Dict]:  # CHANGED: was user_id
        """
        Get all features unlocked by learner's current level.
        
        Args:
            learner_id: Learner ID
            
        Returns:
            List of unlocked features with their details
        """
        level_info = self.get_level_info(learner_id)
        user_level = level_info['level']
        
        result = self.db.execute(
            text("""
                SELECT unlock_code, unlock_type, name_en, name_zh, 
                       description_en, description_zh, icon, level
                FROM level_unlocks
                WHERE level <= :user_level
                ORDER BY level, unlock_type
            """),
            {'user_level': user_level}
        )
        
        unlocks = []
        for row in result.fetchall():
            unlocks.append({
                'code': row[0],
                'type': row[1],
                'name_en': row[2],
                'name_zh': row[3],
                'description_en': row[4],
                'description_zh': row[5],
                'icon': row[6],
                'level': row[7]
            })
        
        return unlocks
    
    def has_unlock(self, learner_id: UUID, unlock_code: str) -> bool:  # CHANGED: was user_id
        """
        Check if learner has unlocked a specific feature.
        
        Args:
            learner_id: Learner ID
            unlock_code: The unlock code to check (e.g., 'tier_3_blocks', 'friend_list')
            
        Returns:
            True if unlocked, False otherwise
        """
        # Get user_id from learner_id for backward compatibility with database function
        learner_result = self.db.execute(
            text("""
                SELECT COALESCE(user_id, guardian_id) 
                FROM public.learners 
                WHERE id = :learner_id
            """),
            {'learner_id': learner_id}
        )
        user_id_row = learner_result.fetchone()
        if not user_id_row or not user_id_row[0]:
            return False
        
        result = self.db.execute(
            text("SELECT has_unlock(:user_id, :unlock_code)"),
            {'user_id': user_id_row[0], 'unlock_code': unlock_code}
        )
        return result.scalar() or False
    
    def get_new_unlocks_for_level(self, level: int) -> List[Dict]:
        """
        Get features that unlock at a specific level.
        
        Args:
            level: The level to check
            
        Returns:
            List of features unlocking at that level
        """
        result = self.db.execute(
            text("""
                SELECT unlock_code, unlock_type, name_en, name_zh, 
                       description_en, description_zh, icon
                FROM level_unlocks
                WHERE level = :level
                ORDER BY unlock_type
            """),
            {'level': level}
        )
        
        unlocks = []
        for row in result.fetchall():
            unlocks.append({
                'code': row[0],
                'type': row[1],
                'name_en': row[2],
                'name_zh': row[3],
                'description_en': row[4],
                'description_zh': row[5],
                'icon': row[6]
            })
        
        return unlocks
    
    def get_next_unlock(self, learner_id: UUID) -> Optional[Dict]:  # CHANGED: was user_id
        """
        Get the next feature that will be unlocked.
        
        Args:
            learner_id: Learner ID
            
        Returns:
            Next unlock info or None if all unlocked
        """
        level_info = self.get_level_info(learner_id)
        user_level = level_info['level']
        
        result = self.db.execute(
            text("""
                SELECT unlock_code, unlock_type, name_en, name_zh, 
                       description_en, description_zh, icon, level
                FROM level_unlocks
                WHERE level > :user_level
                ORDER BY level, unlock_type
                LIMIT 1
            """),
            {'user_level': user_level}
        )
        
        row = result.fetchone()
        if not row:
            return None
        
        return {
            'code': row[0],
            'type': row[1],
            'name_en': row[2],
            'name_zh': row[3],
            'description_en': row[4],
            'description_zh': row[5],
            'icon': row[6],
            'level': row[7]
        }
    
    def get_tier_access(self, learner_id: UUID) -> List[int]:  # CHANGED: was user_id
        """
        Get list of block tiers accessible to learner based on level.
        
        Args:
            learner_id: Learner ID
            
        Returns:
            List of accessible tier numbers
        """
        level_info = self.get_level_info(learner_id)
        user_level = level_info['level']
        
        # Tier access based on level
        accessible_tiers = [1, 2]  # Always accessible
        
        if user_level >= 5:
            accessible_tiers.append(3)  # Phrases
        if user_level >= 10:
            accessible_tiers.append(4)  # Idioms
        if user_level >= 15:
            accessible_tiers.extend([5, 6, 7])  # Patterns, Register, Context
        
        return accessible_tiers
    
    # ============================================
    # PRESTIGE METHODS
    # ============================================
    
    def get_prestige_info(self, learner_id: UUID) -> Dict:  # CHANGED: was user_id
        """
        Get learner's prestige information.
        
        Args:
            learner_id: Learner ID
            
        Returns:
            Prestige level and bonus info
        """
        # Get user_id from learner_id for backward compatibility
        learner_result = self.db.execute(
            text("""
                SELECT COALESCE(user_id, guardian_id) 
                FROM public.learners 
                WHERE id = :learner_id
            """),
            {'learner_id': learner_id}
        )
        user_id_row = learner_result.fetchone()
        if not user_id_row or not user_id_row[0]:
            return {
                'prestige_level': 0,
                'total_xp_lifetime': 0,
                'last_prestige_at': None,
                'xp_bonus_multiplier': 1.0,
                'can_prestige': False
            }
        
        user_id = user_id_row[0]
        
        # Ensure prestige record exists
        self.db.execute(
            text("SELECT initialize_user_prestige(:user_id)"),
            {'user_id': user_id}
        )
        
        result = self.db.execute(
            text("""
                SELECT prestige_level, total_xp_earned_lifetime, 
                       last_prestige_at, xp_bonus_multiplier
                FROM user_prestige
                WHERE user_id = :user_id
            """),
            {'user_id': user_id}
        )
        
        row = result.fetchone()
        if not row:
            return {
                'prestige_level': 0,
                'total_xp_lifetime': 0,
                'last_prestige_at': None,
                'xp_bonus_multiplier': 1.0,
                'can_prestige': False
            }
        
        level_info = self.get_level_info(learner_id)
        can_prestige = level_info['level'] >= 60 and row[0] < 10
        
        return {
            'prestige_level': row[0],
            'total_xp_lifetime': row[1],
            'last_prestige_at': row[2].isoformat() if row[2] else None,
            'xp_bonus_multiplier': float(row[3]),
            'can_prestige': can_prestige
        }
    
    def prestige(self, learner_id: UUID) -> Dict:  # CHANGED: was user_id
        """
        Perform prestige reset for learner.
        
        Requirements:
        - Learner must be level 60+
        - Prestige level must be < 10
        
        Args:
            learner_id: Learner ID
            
        Returns:
            New prestige info and rewards
        """
        level_info = self.get_level_info(learner_id)
        prestige_info = self.get_prestige_info(learner_id)
        
        if level_info['level'] < 60:
            raise ValueError("Must be level 60 or higher to prestige")
        
        if prestige_info['prestige_level'] >= 10:
            raise ValueError("Maximum prestige level (10) reached")
        
        # Get user_id from learner_id for backward compatibility
        learner_result = self.db.execute(
            text("""
                SELECT COALESCE(user_id, guardian_id) 
                FROM public.learners 
                WHERE id = :learner_id
            """),
            {'learner_id': learner_id}
        )
        user_id_row = learner_result.fetchone()
        if not user_id_row or not user_id_row[0]:
            raise ValueError(f"No user_id found for learner {learner_id}")
        
        user_id = user_id_row[0]
        
        new_prestige = prestige_info['prestige_level'] + 1
        new_multiplier = 1.0 + (new_prestige * 0.05)  # +5% per prestige
        
        # Update prestige (still uses user_id)
        self.db.execute(
            text("""
                UPDATE user_prestige
                SET prestige_level = :prestige,
                    total_xp_earned_lifetime = total_xp_earned_lifetime + :current_xp,
                    last_prestige_at = NOW(),
                    xp_bonus_multiplier = :multiplier,
                    updated_at = NOW()
                WHERE user_id = :user_id
            """),
            {
                'user_id': user_id,
                'prestige': new_prestige,
                'current_xp': level_info['total_xp'],
                'multiplier': new_multiplier
            }
        )
        
        # Reset XP to 0 (level 1) - now using learner_id
        self.db.execute(
            text("""
                UPDATE user_xp
                SET total_xp = 0,
                    current_level = 1,
                    xp_to_next_level = 100,
                    xp_in_current_level = 0,
                    updated_at = NOW()
                WHERE learner_id = :learner_id
            """),
            {'learner_id': learner_id}
        )
        
        # Award prestige crystals (100 per prestige level)
        crystal_reward = new_prestige * 100
        try:
            self.db.execute(
                text("""
                    SELECT add_crystals(
                        :user_id, :amount, 'prestige', NULL,
                        :desc_en, :desc_zh
                    )
                """),
                {
                    'user_id': user_id,
                    'amount': crystal_reward,
                    'desc_en': f'Prestige {new_prestige} reward',
                    'desc_zh': f'榮耀 {new_prestige} 獎勵'
                }
            )
        except Exception:
            pass  # Crystal tables might not exist yet
        
        self.db.commit()
        
        return {
            'new_prestige_level': new_prestige,
            'xp_bonus_multiplier': new_multiplier,
            'crystal_reward': crystal_reward,
            'new_level': 1,
            'total_xp_lifetime': prestige_info['total_xp_lifetime'] + level_info['total_xp']
        }
    
    def get_xp_multiplier(self, learner_id: UUID) -> float:  # CHANGED: was user_id
        """
        Get learner's total XP multiplier (from prestige).
        
        Args:
            learner_id: Learner ID
            
        Returns:
            XP multiplier (1.0 = no bonus)
        """
        prestige_info = self.get_prestige_info(learner_id)
        return prestige_info.get('xp_bonus_multiplier', 1.0)


