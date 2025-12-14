"""
Crystal Service

Manages the crystal economy - the premium-lite currency earned through skill.
Crystals are used for:
- Streak freeze purchases
- Cosmetic purchases
- Special feature unlocks
"""

from typing import Dict, List, Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import text


class CrystalService:
    """Service for managing crystal currency."""
    
    # Streak freeze cost
    STREAK_FREEZE_COST = 50
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_balance(self, user_id: UUID) -> Dict:
        """
        Get user's crystal balance and stats.
        
        Args:
            user_id: User ID
            
        Returns:
            Dictionary with balance, lifetime earned/spent
        """
        self._ensure_crystal_account(user_id)
        
        result = self.db.execute(
            text("""
                SELECT balance, lifetime_earned, lifetime_spent, updated_at
                FROM user_crystals
                WHERE user_id = :user_id
            """),
            {'user_id': user_id}
        )
        
        row = result.fetchone()
        if not row:
            return {
                'balance': 0,
                'lifetime_earned': 0,
                'lifetime_spent': 0,
                'updated_at': None
            }
        
        return {
            'balance': row[0],
            'lifetime_earned': row[1],
            'lifetime_spent': row[2],
            'updated_at': row[3].isoformat() if row[3] else None
        }
    
    def add_crystals(
        self,
        user_id: UUID,
        amount: int,
        source: str,
        source_id: Optional[UUID] = None,
        description_en: Optional[str] = None,
        description_zh: Optional[str] = None
    ) -> int:
        """
        Add crystals to user's balance.
        
        Args:
            user_id: User ID
            amount: Amount of crystals to add
            source: Source of crystals ('achievement', 'streak_milestone', 'prestige', etc.)
            source_id: Optional reference ID
            description_en: English description
            description_zh: Chinese description
            
        Returns:
            New balance
        """
        result = self.db.execute(
            text("""
                SELECT add_crystals(
                    :user_id, :amount, :source, :source_id,
                    :desc_en, :desc_zh
                )
            """),
            {
                'user_id': user_id,
                'amount': amount,
                'source': source,
                'source_id': source_id,
                'desc_en': description_en,
                'desc_zh': description_zh
            }
        )
        
        self.db.commit()
        return result.scalar() or 0
    
    def spend_crystals(
        self,
        user_id: UUID,
        amount: int,
        source: str,
        source_id: Optional[UUID] = None,
        description_en: Optional[str] = None,
        description_zh: Optional[str] = None
    ) -> bool:
        """
        Spend crystals from user's balance.
        
        Args:
            user_id: User ID
            amount: Amount to spend
            source: What the crystals are being spent on
            source_id: Optional reference ID
            description_en: English description
            description_zh: Chinese description
            
        Returns:
            True if successful, False if insufficient balance
        """
        result = self.db.execute(
            text("""
                SELECT spend_crystals(
                    :user_id, :amount, :source, :source_id,
                    :desc_en, :desc_zh
                )
            """),
            {
                'user_id': user_id,
                'amount': amount,
                'source': source,
                'source_id': source_id,
                'desc_en': description_en,
                'desc_zh': description_zh
            }
        )
        
        success = result.scalar() or False
        if success:
            self.db.commit()
        return success
    
    def purchase_streak_freeze(self, user_id: UUID) -> Dict:
        """
        Purchase a streak freeze with crystals.
        
        Args:
            user_id: User ID
            
        Returns:
            Result dictionary with success status and details
        """
        balance = self.get_balance(user_id)
        
        if balance['balance'] < self.STREAK_FREEZE_COST:
            return {
                'success': False,
                'error': 'insufficient_balance',
                'required': self.STREAK_FREEZE_COST,
                'current': balance['balance']
            }
        
        success = self.spend_crystals(
            user_id,
            self.STREAK_FREEZE_COST,
            'streak_freeze_purchase',
            None,
            'Streak Freeze Purchase',
            '連續保護購買'
        )
        
        if success:
            # Record the streak freeze (would need a streak_freezes table)
            # For now, just return success
            return {
                'success': True,
                'cost': self.STREAK_FREEZE_COST,
                'new_balance': balance['balance'] - self.STREAK_FREEZE_COST
            }
        else:
            return {
                'success': False,
                'error': 'transaction_failed'
            }
    
    def get_transaction_history(
        self,
        user_id: UUID,
        limit: int = 20,
        offset: int = 0
    ) -> List[Dict]:
        """
        Get crystal transaction history.
        
        Args:
            user_id: User ID
            limit: Max number of transactions
            offset: Pagination offset
            
        Returns:
            List of transactions
        """
        result = self.db.execute(
            text("""
                SELECT id, amount, balance_after, source, source_id,
                       description_en, description_zh, created_at
                FROM crystal_transactions
                WHERE user_id = :user_id
                ORDER BY created_at DESC
                LIMIT :limit OFFSET :offset
            """),
            {'user_id': user_id, 'limit': limit, 'offset': offset}
        )
        
        transactions = []
        for row in result.fetchall():
            transactions.append({
                'id': str(row[0]),
                'amount': row[1],
                'balance_after': row[2],
                'source': row[3],
                'source_id': str(row[4]) if row[4] else None,
                'description_en': row[5],
                'description_zh': row[6],
                'created_at': row[7].isoformat() if row[7] else None
            })
        
        return transactions
    
    def _ensure_crystal_account(self, user_id: UUID):
        """Ensure user has a crystal account."""
        self.db.execute(
            text("SELECT initialize_user_crystals(:user_id)"),
            {'user_id': user_id}
        )
        self.db.commit()
    
    # ============================================
    # COSMETIC PURCHASE METHODS
    # ============================================
    
    def get_purchasable_cosmetics(self, user_id: UUID) -> List[Dict]:
        """
        Get cosmetics that can be purchased with crystals.
        
        Args:
            user_id: User ID
            
        Returns:
            List of purchasable cosmetics with ownership status
        """
        result = self.db.execute(
            text("""
                SELECT c.id, c.code, c.type, c.name_en, c.name_zh,
                       c.description_en, c.description_zh, c.icon, c.rarity,
                       c.crystal_cost,
                       uc.unlocked_at IS NOT NULL as owned
                FROM cosmetics c
                LEFT JOIN user_cosmetics uc ON c.id = uc.cosmetic_id AND uc.user_id = :user_id
                WHERE c.unlock_type = 'crystal_purchase'
                AND c.is_active = true
                AND c.crystal_cost IS NOT NULL
                ORDER BY c.type, c.crystal_cost
            """),
            {'user_id': user_id}
        )
        
        cosmetics = []
        for row in result.fetchall():
            cosmetics.append({
                'id': str(row[0]),
                'code': row[1],
                'type': row[2],
                'name_en': row[3],
                'name_zh': row[4],
                'description_en': row[5],
                'description_zh': row[6],
                'icon': row[7],
                'rarity': row[8],
                'crystal_cost': row[9],
                'owned': row[10]
            })
        
        return cosmetics
    
    def purchase_cosmetic(self, user_id: UUID, cosmetic_id: UUID) -> Dict:
        """
        Purchase a cosmetic with crystals.
        
        Args:
            user_id: User ID
            cosmetic_id: Cosmetic ID to purchase
            
        Returns:
            Result dictionary
        """
        # Get cosmetic details
        result = self.db.execute(
            text("""
                SELECT id, code, name_en, name_zh, crystal_cost, unlock_type
                FROM cosmetics
                WHERE id = :cosmetic_id AND is_active = true
            """),
            {'cosmetic_id': cosmetic_id}
        )
        
        cosmetic = result.fetchone()
        if not cosmetic:
            return {
                'success': False,
                'error': 'cosmetic_not_found'
            }
        
        if cosmetic[5] != 'crystal_purchase':
            return {
                'success': False,
                'error': 'not_purchasable'
            }
        
        cost = cosmetic[4]
        if not cost:
            return {
                'success': False,
                'error': 'no_price_set'
            }
        
        # Check if already owned
        owned_check = self.db.execute(
            text("""
                SELECT 1 FROM user_cosmetics
                WHERE user_id = :user_id AND cosmetic_id = :cosmetic_id
            """),
            {'user_id': user_id, 'cosmetic_id': cosmetic_id}
        )
        
        if owned_check.fetchone():
            return {
                'success': False,
                'error': 'already_owned'
            }
        
        # Attempt purchase
        success = self.spend_crystals(
            user_id,
            cost,
            'cosmetic_purchase',
            cosmetic_id,
            f'Purchase: {cosmetic[2]}',
            f'購買: {cosmetic[3] or cosmetic[2]}'
        )
        
        if not success:
            balance = self.get_balance(user_id)
            return {
                'success': False,
                'error': 'insufficient_balance',
                'required': cost,
                'current': balance['balance']
            }
        
        # Grant cosmetic
        self.db.execute(
            text("""
                INSERT INTO user_cosmetics (user_id, cosmetic_id, equipped, unlocked_at)
                VALUES (:user_id, :cosmetic_id, false, NOW())
            """),
            {'user_id': user_id, 'cosmetic_id': cosmetic_id}
        )
        
        self.db.commit()
        
        return {
            'success': True,
            'cosmetic_code': cosmetic[1],
            'cost': cost,
            'new_balance': self.get_balance(user_id)['balance']
        }

