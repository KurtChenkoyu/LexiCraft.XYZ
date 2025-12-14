"""
Currency Service

Handles the three-currency economy:
- Sparks (✨): Effort currency - earned from any activity
- Essence (💧): Skill currency - earned from correct answers only  
- Energy (⚡): Building currency - earned from level-ups only
- Blocks (🧱): Mastered words - building materials
"""

from typing import Dict, List, Optional, Tuple
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import text


class CurrencyService:
    """Service for managing the three-currency economy."""
    
    # Energy rewards per level-up (level reached -> energy granted)
    LEVEL_ENERGY_REWARDS = {
        2: 30,
        3: 50,
        4: 75,
        5: 100,
        # Level 6+ all get 125
    }
    DEFAULT_ENERGY_REWARD = 125  # For levels 6+
    
    # Sparks rewards by activity
    SPARKS_REWARDS = {
        'view_word': 1,
        'start_mcq': 2,
        'mcq_wrong': 1,
        'mcq_correct': 5,
        'mcq_fast_correct': 8,  # Fast + correct
        'review_start': 2,
        'review_pass': 3,
        'word_hollow': 5,  # Word became Hollow
        'word_solid': 10,  # Word became Solid (also grants block)
        'daily_login': 10,
        'streak_7': 50,
        'streak_30': 200,
    }
    
    # Essence rewards (only from correct answers)
    ESSENCE_REWARDS = {
        'mcq_correct': 1,
        'mcq_fast_correct': 2,
        'review_pass': 1,
    }
    
    def __init__(self, db: Session):
        self.db = db
    
    # ============================================
    # CURRENCY GETTERS
    # ============================================
    
    def get_currencies(self, user_id: UUID) -> Dict:
        """
        Get all currency balances for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            Dictionary with all currency balances and level info
        """
        self._ensure_user_currencies(user_id)
        
        result = self.db.execute(
            text("""
                SELECT sparks, essence, energy, solid_blocks,
                       total_xp, current_level, xp_to_next_level, xp_in_current_level
                FROM user_xp
                WHERE user_id = :user_id
            """),
            {'user_id': user_id}
        )
        
        row = result.fetchone()
        if not row:
            return self._default_currencies()
        
        xp_to_next = row[6] or 100
        xp_in_level = row[7] or 0
        
        return {
            'sparks': row[0] or 0,
            'essence': row[1] or 0,
            'energy': row[2] or 0,
            'blocks': row[3] or 0,
            'level': row[5] or 1,
            'total_xp': row[4] or 0,
            'xp_to_next_level': xp_to_next,
            'xp_in_current_level': xp_in_level,
            'level_progress': int((xp_in_level / xp_to_next) * 100) if xp_to_next > 0 else 0
        }
    
    def _default_currencies(self) -> Dict:
        """Return default currency values for new users."""
        return {
            'sparks': 0,
            'essence': 0,
            'energy': 0,
            'blocks': 0,
            'level': 1,
            'total_xp': 0,
            'xp_to_next_level': 100,
            'xp_in_current_level': 0,
            'level_progress': 0
        }
    
    # ============================================
    # SPARKS (EFFORT CURRENCY)
    # ============================================
    
    def add_sparks(
        self,
        user_id: UUID,
        amount: int,
        source: str,
        source_id: Optional[UUID] = None,
        description: Optional[str] = None
    ) -> Dict:
        """
        Add sparks and check for level-up with energy reward.
        
        Sparks contribute to leveling. When user levels up, they receive Energy.
        
        Args:
            user_id: User ID
            amount: Sparks to add
            source: Source type ('mcq_correct', 'view_word', etc.)
            source_id: Optional reference ID
            description: Optional description
            
        Returns:
            Dictionary with updated currencies and level-up info
        """
        self._ensure_user_currencies(user_id)
        
        # Get current state
        result = self.db.execute(
            text("""
                SELECT sparks, energy, current_level, total_xp, xp_to_next_level
                FROM user_xp
                WHERE user_id = :user_id
            """),
            {'user_id': user_id}
        )
        row = result.fetchone()
        
        old_sparks = row[0] or 0
        old_energy = row[1] or 0
        old_level = row[2] or 1
        old_total_xp = row[3] or 0
        
        # Calculate new values
        new_sparks = old_sparks + amount
        new_total_xp = old_total_xp + amount  # Sparks = XP for leveling
        
        # Calculate new level
        level_info = self._calculate_level(new_total_xp)
        new_level = level_info['level']
        
        # Check for level-up and grant energy
        level_up = new_level > old_level
        energy_granted = 0
        
        if level_up:
            # Grant energy for each level gained
            for lvl in range(old_level + 1, new_level + 1):
                energy_granted += self.LEVEL_ENERGY_REWARDS.get(lvl, self.DEFAULT_ENERGY_REWARD)
        
        new_energy = old_energy + energy_granted
        
        # Update database
        self.db.execute(
            text("""
                UPDATE user_xp
                SET sparks = :sparks,
                    energy = :energy,
                    total_xp = :total_xp,
                    current_level = :level,
                    xp_to_next_level = :xp_to_next,
                    xp_in_current_level = :xp_in_level,
                    updated_at = NOW()
                WHERE user_id = :user_id
            """),
            {
                'user_id': user_id,
                'sparks': new_sparks,
                'energy': new_energy,
                'total_xp': new_total_xp,
                'level': new_level,
                'xp_to_next': level_info['xp_to_next'],
                'xp_in_level': level_info['xp_in_level']
            }
        )
        
        # Record transaction
        self._record_transaction(user_id, 'sparks', amount, new_sparks, source, source_id, description)
        
        if energy_granted > 0:
            self._record_transaction(
                user_id, 'energy', energy_granted, new_energy, 
                'level_up', None, f'Level up to {new_level}'
            )
        
        # Also record in xp_history for backwards compatibility
        self.db.execute(
            text("""
                INSERT INTO xp_history (user_id, xp_amount, source, source_id)
                VALUES (:user_id, :amount, :source, :source_id)
            """),
            {'user_id': user_id, 'amount': amount, 'source': source, 'source_id': source_id}
        )
        
        self.db.commit()
        
        return {
            'sparks_added': amount,
            'sparks_total': new_sparks,
            'level_up': level_up,
            'old_level': old_level,
            'new_level': new_level,
            'energy_granted': energy_granted,
            'energy_total': new_energy,
            'xp_to_next_level': level_info['xp_to_next'],
            'xp_in_current_level': level_info['xp_in_level'],
            'level_progress': int((level_info['xp_in_level'] / level_info['xp_to_next']) * 100) if level_info['xp_to_next'] > 0 else 0
        }
    
    # ============================================
    # ESSENCE (SKILL CURRENCY)
    # ============================================
    
    def add_essence(
        self,
        user_id: UUID,
        amount: int,
        source: str,
        source_id: Optional[UUID] = None,
        description: Optional[str] = None
    ) -> Dict:
        """
        Add essence (skill currency from correct answers).
        
        Args:
            user_id: User ID
            amount: Essence to add
            source: Source type
            source_id: Optional reference ID
            description: Optional description
            
        Returns:
            Dictionary with updated essence balance
        """
        self._ensure_user_currencies(user_id)
        
        # Update essence
        result = self.db.execute(
            text("""
                UPDATE user_xp
                SET essence = essence + :amount,
                    updated_at = NOW()
                WHERE user_id = :user_id
                RETURNING essence
            """),
            {'user_id': user_id, 'amount': amount}
        )
        
        new_essence = result.scalar()
        
        # Record transaction
        self._record_transaction(user_id, 'essence', amount, new_essence, source, source_id, description)
        
        self.db.commit()
        
        return {
            'essence_added': amount,
            'essence_total': new_essence
        }
    
    # ============================================
    # BLOCKS (MASTERED WORDS)
    # ============================================
    
    def add_block(
        self,
        user_id: UUID,
        source_id: Optional[UUID] = None,
        description: Optional[str] = None
    ) -> Dict:
        """
        Add a solid block (mastered word).
        
        Args:
            user_id: User ID
            source_id: Optional word/sense ID
            description: Optional description
            
        Returns:
            Dictionary with updated block count
        """
        self._ensure_user_currencies(user_id)
        
        # Update blocks
        result = self.db.execute(
            text("""
                UPDATE user_xp
                SET solid_blocks = solid_blocks + 1,
                    updated_at = NOW()
                WHERE user_id = :user_id
                RETURNING solid_blocks
            """),
            {'user_id': user_id}
        )
        
        new_blocks = result.scalar()
        
        # Record transaction
        self._record_transaction(user_id, 'blocks', 1, new_blocks, 'word_mastered', source_id, description)
        
        self.db.commit()
        
        return {
            'blocks_added': 1,
            'blocks_total': new_blocks
        }
    
    # ============================================
    # MCQ REWARD HELPER
    # ============================================
    
    def award_mcq_result(
        self,
        user_id: UUID,
        is_correct: bool,
        is_fast: bool = False,
        word_became_solid: bool = False,
        sense_id: Optional[UUID] = None
    ) -> Dict:
        """
        Award currencies for an MCQ result.
        
        This is the main entry point for MCQ submissions.
        
        Args:
            user_id: User ID
            is_correct: Whether answer was correct
            is_fast: Whether answered quickly (< 5 seconds)
            word_became_solid: Whether this answer caused word to become Solid
            sense_id: The sense ID being tested
            
        Returns:
            Combined result with all currency changes
        """
        sparks_source = 'mcq_fast_correct' if (is_correct and is_fast) else ('mcq_correct' if is_correct else 'mcq_wrong')
        sparks_amount = self.SPARKS_REWARDS.get(sparks_source, 0)
        
        # Add sparks (everyone gets sparks)
        sparks_result = self.add_sparks(user_id, sparks_amount, sparks_source, sense_id)
        
        essence_result = {'essence_added': 0, 'essence_total': 0}
        block_result = {'blocks_added': 0, 'blocks_total': 0}
        
        # Add essence (only for correct answers)
        if is_correct:
            essence_source = 'mcq_fast_correct' if is_fast else 'mcq_correct'
            essence_amount = self.ESSENCE_REWARDS.get(essence_source, 0)
            if essence_amount > 0:
                essence_result = self.add_essence(user_id, essence_amount, essence_source, sense_id)
        
        # Add block if word became solid
        if word_became_solid:
            block_result = self.add_block(user_id, sense_id, f'Mastered word')
            # Also add bonus sparks for mastery
            mastery_sparks = self.SPARKS_REWARDS.get('word_solid', 0)
            if mastery_sparks > 0:
                self.add_sparks(user_id, mastery_sparks, 'word_solid', sense_id)
                sparks_result['sparks_added'] += mastery_sparks
                sparks_result['sparks_total'] += mastery_sparks
        
        return {
            'sparks': sparks_result,
            'essence': essence_result,
            'block': block_result,
            'level_up': sparks_result.get('level_up', False),
            'energy_granted': sparks_result.get('energy_granted', 0)
        }
    
    # ============================================
    # SPENDING CURRENCIES
    # ============================================
    
    def spend_currencies(
        self,
        user_id: UUID,
        energy: int = 0,
        essence: int = 0,
        blocks: int = 0,
        source: str = 'item_upgrade',
        source_id: Optional[UUID] = None,
        description: Optional[str] = None
    ) -> Tuple[bool, Dict]:
        """
        Attempt to spend currencies.
        
        Args:
            user_id: User ID
            energy: Energy to spend
            essence: Essence to spend
            blocks: Blocks to spend
            source: What the spending is for
            source_id: Reference ID
            description: Description
            
        Returns:
            Tuple of (success, result_dict)
        """
        currencies = self.get_currencies(user_id)
        
        # Check if can afford
        if currencies['energy'] < energy:
            return False, {'error': 'INSUFFICIENT_ENERGY', 'have': currencies['energy'], 'need': energy}
        if currencies['essence'] < essence:
            return False, {'error': 'INSUFFICIENT_ESSENCE', 'have': currencies['essence'], 'need': essence}
        if currencies['blocks'] < blocks:
            return False, {'error': 'INSUFFICIENT_BLOCKS', 'have': currencies['blocks'], 'need': blocks}
        
        # Deduct currencies
        self.db.execute(
            text("""
                UPDATE user_xp
                SET energy = energy - :energy,
                    essence = essence - :essence,
                    solid_blocks = solid_blocks - :blocks,
                    updated_at = NOW()
                WHERE user_id = :user_id
            """),
            {'user_id': user_id, 'energy': energy, 'essence': essence, 'blocks': blocks}
        )
        
        # Get new balances
        new_currencies = self.get_currencies(user_id)
        
        # Record transactions
        if energy > 0:
            self._record_transaction(user_id, 'energy', -energy, new_currencies['energy'], source, source_id, description)
        if essence > 0:
            self._record_transaction(user_id, 'essence', -essence, new_currencies['essence'], source, source_id, description)
        if blocks > 0:
            self._record_transaction(user_id, 'blocks', -blocks, new_currencies['blocks'], source, source_id, description)
        
        self.db.commit()
        
        return True, {
            'energy_spent': energy,
            'essence_spent': essence,
            'blocks_spent': blocks,
            'energy_after': new_currencies['energy'],
            'essence_after': new_currencies['essence'],
            'blocks_after': new_currencies['blocks']
        }
    
    # ============================================
    # HELPER METHODS
    # ============================================
    
    def _ensure_user_currencies(self, user_id: UUID):
        """Ensure user has currency columns initialized."""
        self.db.execute(
            text("""
                INSERT INTO user_xp (user_id, sparks, essence, energy, solid_blocks, total_xp, current_level, xp_to_next_level, xp_in_current_level)
                VALUES (:user_id, 0, 0, 0, 0, 0, 1, 100, 0)
                ON CONFLICT (user_id) DO UPDATE SET
                    sparks = COALESCE(user_xp.sparks, 0),
                    essence = COALESCE(user_xp.essence, 0),
                    energy = COALESCE(user_xp.energy, 0),
                    solid_blocks = COALESCE(user_xp.solid_blocks, 0)
            """),
            {'user_id': user_id}
        )
        self.db.commit()
    
    def _calculate_level(self, total_xp: int) -> Dict:
        """
        Calculate level from total XP (same as Sparks).
        
        Formula: Level N requires 100 + (N-1) * 50 XP
        - Level 2: 100 XP (100 total)
        - Level 3: 150 XP (250 total)
        - Level 4: 200 XP (450 total)
        etc.
        """
        level = 1
        xp_needed = 100
        remaining_xp = total_xp
        
        while remaining_xp >= xp_needed:
            remaining_xp -= xp_needed
            level += 1
            xp_needed = 100 + (level - 1) * 50
        
        return {
            'level': level,
            'xp_to_next': xp_needed,
            'xp_in_level': remaining_xp
        }
    
    def _record_transaction(
        self,
        user_id: UUID,
        currency_type: str,
        amount: int,
        balance_after: int,
        source: str,
        source_id: Optional[UUID],
        description: Optional[str]
    ):
        """Record a currency transaction."""
        try:
            self.db.execute(
                text("""
                    INSERT INTO currency_transactions 
                    (user_id, currency_type, amount, balance_after, source, source_id, description)
                    VALUES (:user_id, :type, :amount, :balance, :source, :source_id, :desc)
                """),
                {
                    'user_id': user_id,
                    'type': currency_type,
                    'amount': amount,
                    'balance': balance_after,
                    'source': source,
                    'source_id': source_id,
                    'desc': description
                }
            )
        except Exception:
            # Table might not exist yet
            pass
    
    def get_transaction_history(
        self,
        user_id: UUID,
        currency_type: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict]:
        """
        Get currency transaction history.
        
        Args:
            user_id: User ID
            currency_type: Optional filter by type
            limit: Max records to return
            
        Returns:
            List of transactions
        """
        query = """
            SELECT currency_type, amount, balance_after, source, source_id, description, created_at
            FROM currency_transactions
            WHERE user_id = :user_id
        """
        params = {'user_id': user_id, 'limit': limit}
        
        if currency_type:
            query += " AND currency_type = :type"
            params['type'] = currency_type
        
        query += " ORDER BY created_at DESC LIMIT :limit"
        
        try:
            result = self.db.execute(text(query), params)
            
            transactions = []
            for row in result.fetchall():
                transactions.append({
                    'currency_type': row[0],
                    'amount': row[1],
                    'balance_after': row[2],
                    'source': row[3],
                    'source_id': str(row[4]) if row[4] else None,
                    'description': row[5],
                    'created_at': row[6].isoformat() if row[6] else None
                })
            
            return transactions
        except Exception:
            return []

