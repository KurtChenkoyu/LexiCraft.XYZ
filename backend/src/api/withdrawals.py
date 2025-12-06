"""
Withdrawal API Endpoints

Handles withdrawal requests from parents. Requires email confirmation for security.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import text

from src.database.postgres_connection import PostgresConnection
from src.middleware.auth import get_current_user_id

router = APIRouter(prefix="/api/withdrawals", tags=["Withdrawals"])


# --- Request Models ---
class CreateWithdrawalRequest(BaseModel):
    learner_id: str  # Changed from child_id - this is the learner's user_id
    amount_ntd: float
    bank_account: Optional[str] = None
    bank_name: Optional[str] = None


# --- Dependency Injection ---
def get_db_session():
    """Get PostgreSQL database session."""
    conn = PostgresConnection()
    return conn.get_session()


# Removed get_current_user_id - using query param for MVP


def check_email_confirmation(session: Session, user_id: UUID) -> bool:
    """
    Check if user has confirmed their email.
    
    Returns True if confirmed, raises HTTPException if not.
    """
    result = session.execute(
        text("SELECT email_confirmed FROM users WHERE id = :user_id"),
        {"user_id": str(user_id)}
    ).fetchone()
    
    if not result:
        raise HTTPException(status_code=404, detail="User not found")
    
    email_confirmed = result[0]
    
    if not email_confirmed:
        raise HTTPException(
            status_code=403,
            detail="Please confirm your email address to enable withdrawals. Check your email for the confirmation link."
        )
    
    return True


@router.post("/request")
async def create_withdrawal_request(
    request: CreateWithdrawalRequest,
    user_id: UUID = Depends(get_current_user_id),  # Get from auth middleware
    db: Session = Depends(get_db_session)
):
    """
    Create a withdrawal request.
    
    Requires:
    - Email confirmation (checked)
    - Sufficient available points
    - Valid parent-child relationship (parent requesting for learner)
    
    Steps:
    1. Verify email confirmation
    2. Validate available points >= requested amount
    3. Verify parent-child relationship exists
    4. Create withdrawal_request (status: 'pending')
    5. Deduct from available_points
    6. Create points_transaction (type: 'withdrawn')
    """
    try:
        parent_uuid = user_id
        learner_uuid = UUID(request.learner_id)
        
        # 1. Check email confirmation
        check_email_confirmation(db, parent_uuid)
        
        # 2. Verify parent-child relationship exists
        relationship = db.execute(
            text("""
                SELECT id FROM user_relationships
                WHERE from_user_id = :parent_id
                  AND to_user_id = :learner_id
                  AND relationship_type = 'parent_child'
                  AND status = 'active'
            """),
            {"parent_id": str(parent_uuid), "learner_id": str(learner_uuid)}
        ).fetchone()
        
        if not relationship:
            raise HTTPException(
                status_code=403,
                detail="Learner not found or you are not their parent"
            )
        
        # 3. Get current available points
        account = db.execute(
            text("""
                SELECT available_points, total_earned
                FROM points_accounts
                WHERE user_id = :learner_id
            """),
            {"learner_id": str(learner_uuid)}
        ).fetchone()
        
        if not account:
            raise HTTPException(
                status_code=404,
                detail="Points account not found for this learner"
            )
        
        available_points = account[0] or 0
        points_amount = int(request.amount_ntd)  # 1:1 conversion for MVP
        
        # 4. Validate sufficient points
        if available_points < points_amount:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient points. Available: {available_points}, Requested: {points_amount}"
            )
        
        # 5. Create withdrawal request
        withdrawal_id = db.execute(
            text("""
                INSERT INTO withdrawal_requests (
                    user_id,
                    parent_id,
                    amount_ntd,
                    points_amount,
                    bank_account,
                    status
                )
                VALUES (
                    :learner_id,
                    :parent_id,
                    :amount_ntd,
                    :points_amount,
                    :bank_account,
                    'pending'
                )
                RETURNING id
            """),
            {
                "learner_id": str(learner_uuid),
                "parent_id": str(parent_uuid),
                "amount_ntd": request.amount_ntd,
                "points_amount": points_amount,
                "bank_account": request.bank_account,
            }
        ).scalar()
        
        # 6. Deduct from available_points
        db.execute(
            text("""
                UPDATE points_accounts
                SET 
                    available_points = available_points - :points_amount,
                    withdrawn_points = withdrawn_points + :points_amount
                WHERE user_id = :learner_id
            """),
            {
                "learner_id": str(learner_uuid),
                "points_amount": points_amount,
            }
        )
        
        # 7. Create points transaction
        db.execute(
            text("""
                INSERT INTO points_transactions (
                    user_id,
                    transaction_type,
                    points,
                    description
                )
                VALUES (
                    :learner_id,
                    'withdrawn',
                    :points_amount,
                    'Withdrawal request #' || :withdrawal_id
                )
            """),
            {
                "learner_id": str(learner_uuid),
                "points_amount": points_amount,
                "withdrawal_id": withdrawal_id,
            }
        )
        
        db.commit()
        
        return {
            "message": "Withdrawal request created",
            "withdrawal_id": withdrawal_id,
            "status": "pending",
            "amount_ntd": request.amount_ntd,
            "points_amount": points_amount,
        }
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create withdrawal request: {str(e)}"
        )
    finally:
        db.close()


@router.get("/history")
async def get_withdrawal_history(
    learner_id: str = Query(..., description="Learner user ID"),  # Changed from child_id
    user_id: UUID = Depends(get_current_user_id),  # Get from auth middleware
    db: Session = Depends(get_db_session)
):
    """
    Get withdrawal history for a learner.
    
    Requires email confirmation and parent-child relationship.
    """
    try:
        parent_uuid = user_id
        learner_uuid = UUID(learner_id)
        
        # Check email confirmation
        check_email_confirmation(db, parent_uuid)
        
        # Verify parent-child relationship
        relationship = db.execute(
            text("""
                SELECT id FROM user_relationships
                WHERE from_user_id = :parent_id
                  AND to_user_id = :learner_id
                  AND relationship_type = 'parent_child'
                  AND status = 'active'
            """),
            {"parent_id": str(parent_uuid), "learner_id": str(learner_uuid)}
        ).fetchone()
        
        if not relationship:
            raise HTTPException(status_code=403, detail="Learner not found or you are not their parent")
        
        # Get withdrawal history
        withdrawals = db.execute(
            text("""
                SELECT 
                    id,
                    amount_ntd,
                    points_amount,
                    status,
                    bank_account,
                    created_at,
                    completed_at
                FROM withdrawal_requests
                WHERE user_id = :learner_id
                ORDER BY created_at DESC
            """),
            {"learner_id": str(learner_uuid)}
        ).fetchall()
        
        return {
            "withdrawals": [
                {
                    "id": w[0],
                    "amount_ntd": float(w[1]),
                    "points_amount": w[2],
                    "status": w[3],
                    "bank_account": w[4],
                    "created_at": w[5].isoformat() if w[5] else None,
                    "completed_at": w[6].isoformat() if w[6] else None,
                }
                for w in withdrawals
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get withdrawal history: {str(e)}"
        )
    finally:
        db.close()

