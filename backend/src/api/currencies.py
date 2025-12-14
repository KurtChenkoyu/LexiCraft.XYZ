"""
Currencies API

Endpoints for the three-currency economy:
- Sparks (✨): Effort currency
- Essence (💧): Skill currency  
- Energy (⚡): Building currency
- Blocks (🧱): Mastered words
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session

from ..database.postgres_connection import PostgresConnection
from ..middleware.auth import get_current_user_id
from ..services.currencies import CurrencyService

router = APIRouter(prefix="/api/v1/currencies", tags=["Currencies"])


# --- Response Models ---

class CurrencyBalances(BaseModel):
    """All currency balances."""
    sparks: int
    essence: int
    energy: int
    blocks: int
    level: int
    total_xp: int
    xp_to_next_level: int
    xp_in_current_level: int
    level_progress: int  # 0-100 percentage


class CurrencyTransaction(BaseModel):
    """A single currency transaction."""
    currency_type: str
    amount: int
    balance_after: int
    source: str
    source_id: Optional[str]
    description: Optional[str]
    created_at: Optional[str]


class TransactionHistoryResponse(BaseModel):
    """Transaction history response."""
    transactions: List[CurrencyTransaction]
    total: int


# --- Dependency Injection ---

def get_db_session():
    """Get database session."""
    conn = PostgresConnection()
    return conn.get_session()


# --- Endpoints ---

@router.get("", response_model=CurrencyBalances)
async def get_currencies(
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db_session)
):
    """
    Get all currency balances for the current user.
    
    Returns:
    - sparks: Effort currency (earned from any activity)
    - essence: Skill currency (earned from correct answers)
    - energy: Building currency (earned from level-ups)
    - blocks: Mastered words (building materials)
    - level: Current level
    - level_progress: Progress to next level (0-100)
    """
    try:
        currency_service = CurrencyService(db)
        currencies = currency_service.get_currencies(user_id)
        
        return CurrencyBalances(**currencies)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get currencies: {str(e)}")
    finally:
        db.close()


@router.get("/history", response_model=TransactionHistoryResponse)
async def get_transaction_history(
    currency_type: Optional[str] = None,
    limit: int = 50,
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db_session)
):
    """
    Get currency transaction history.
    
    Args:
        currency_type: Filter by 'sparks', 'essence', 'energy', or 'blocks'
        limit: Maximum transactions to return (default 50)
    """
    try:
        currency_service = CurrencyService(db)
        transactions = currency_service.get_transaction_history(
            user_id, 
            currency_type=currency_type,
            limit=limit
        )
        
        return TransactionHistoryResponse(
            transactions=[CurrencyTransaction(**t) for t in transactions],
            total=len(transactions)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get history: {str(e)}")
    finally:
        db.close()


@router.get("/level-rewards")
async def get_level_energy_rewards():
    """
    Get the energy rewards for each level-up.
    
    This is static data showing how much Energy users earn when leveling up.
    """
    return {
        'rewards': {
            '2': 30,
            '3': 50,
            '4': 75,
            '5': 100,
            '6+': 125
        },
        'description': 'Energy earned when reaching each level'
    }

