"""
Deposit API Endpoints

Handles deposit confirmations from Stripe webhooks and deposit management.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import text

from src.database.postgres_connection import PostgresConnection

router = APIRouter(prefix="/api/deposits", tags=["Deposits"])


# --- Request Models ---
class ConfirmDepositRequest(BaseModel):
    session_id: str
    learner_id: str  # Changed from child_id - this is the learner's user_id
    user_id: str  # Parent's user_id
    amount: float  # in NT$


# --- Dependency Injection ---
def get_db_session():
    """Get PostgreSQL database session."""
    conn = PostgresConnection()
    return conn.get_session()


@router.post("/confirm")
async def confirm_deposit(
    request: ConfirmDepositRequest,
    db: Session = Depends(get_db_session)
):
    """
    Confirm a deposit after successful Stripe payment.
    
    This endpoint is called by the webhook handler after payment succeeds.
    It:
    1. Credits the points_accounts table
    2. Creates a points_transaction record
    3. Updates the child's balance
    """
    try:
        # 1. Verify the deposit doesn't already exist
        # Check by description since we don't have metadata column
        existing = db.execute(
            text("""
                SELECT id FROM points_transactions
                WHERE transaction_type = 'deposit'
                AND description LIKE '%' || :session_id || '%'
            """),
            {"session_id": request.session_id}
        ).fetchone()
        
        if existing:
            return {"message": "Deposit already confirmed", "id": existing[0]}
        
        # 2. Verify parent-child relationship (optional check, but good for security)
        # Note: This might be called from webhook, so relationship check is optional
        # But we should verify the learner_id is valid
        learner_exists = db.execute(
            text("SELECT id FROM users WHERE id = :learner_id"),
            {"learner_id": request.learner_id}
        ).fetchone()
        
        if not learner_exists:
            raise HTTPException(status_code=404, detail="Learner not found")
        
        # 3. Get or create points account for learner
        account = db.execute(
            text("""
                SELECT id, available_points, locked_points
                FROM points_accounts
                WHERE user_id = :learner_id
            """),
            {"learner_id": request.learner_id}
        ).fetchone()
        
        if not account:
            # Create new points account
            account_id = db.execute(
                text("""
                    INSERT INTO points_accounts (user_id, total_earned, available_points, locked_points, withdrawn_points)
                    VALUES (:learner_id, 0, 0, 0, 0)
                    RETURNING id
                """),
                {"learner_id": request.learner_id}
            ).scalar()
        else:
            account_id = account[0]
        
        # 4. Convert NT$ to points (1:1 ratio for MVP)
        points_amount = int(request.amount)
        
        # 5. Create deposit transaction
        transaction_id = db.execute(
            text("""
                INSERT INTO points_transactions (
                    user_id,
                    transaction_type,
                    points,
                    description
                )
                VALUES (
                    :learner_id,
                    'deposit',
                    :points,
                    'Deposit from Stripe session ' || :session_id
                )
                RETURNING id
            """),
            {
                "learner_id": request.learner_id,
                "points": points_amount,
                "session_id": request.session_id,
            }
        ).scalar()
        
        # 6. Update points account (add to available_points)
        db.execute(
            text("""
                UPDATE points_accounts
                SET available_points = available_points + :points
                WHERE user_id = :learner_id
            """),
            {
                "learner_id": request.learner_id,
                "points": points_amount,
            }
        )
        
        db.commit()
        
        return {
            "message": "Deposit confirmed",
            "transaction_id": transaction_id,
            "points_added": points_amount,
            "amount_ntd": request.amount,
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to confirm deposit: {str(e)}"
        )
    finally:
        db.close()


@router.get("/{learner_id}/balance")
async def get_balance(
    learner_id: str,  # Changed from child_id
    db: Session = Depends(get_db_session)
):
    """
    Get current balance for a learner.
    """
    try:
        result = db.execute(
            text("""
                SELECT 
                    total_earned,
                    available_points,
                    locked_points,
                    withdrawn_points
                FROM points_accounts
                WHERE user_id = :learner_id
            """),
            {"learner_id": learner_id}
        ).fetchone()
        
        if not result:
            return {
                "total_earned": 0,
                "available_points": 0,
                "locked_points": 0,
                "withdrawn_points": 0,
            }
        
        return {
            "total_earned": result[0] or 0,
            "available_points": result[1] or 0,
            "locked_points": result[2] or 0,
            "withdrawn_points": result[3] or 0,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get balance: {str(e)}"
        )
    finally:
        db.close()

