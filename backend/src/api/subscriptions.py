"""
Subscription API Endpoints

Handles subscription activation and updates from Lemon Squeezy webhooks.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import text

from src.database.postgres_connection import PostgresConnection

router = APIRouter(prefix="/api/subscriptions", tags=["Subscriptions"])


# --- Request Models ---
class ActivateSubscriptionRequest(BaseModel):
    user_id: Optional[str] = None  # Primary: Use ID if available (immutable identifier)
    email: Optional[str] = None    # Fallback: Use email if ID not available (backward compatibility)
    subscription_status: str  # 'active', 'inactive', 'trial', 'past_due'
    plan_type: Optional[str] = None  # '6-month-pass', '12-month-pass', etc.
    subscription_end_date: Optional[str] = None  # ISO format timestamp


# --- Dependency Injection ---
def get_db_session():
    """Get PostgreSQL database session."""
    conn = PostgresConnection()
    return conn.get_session()


def map_lemon_squeezy_status(ls_status: str) -> str:
    """
    Map Lemon Squeezy status to our subscription_status values.
    
    Mapping:
    - on_trial -> 'trial'
    - active -> 'active'
    - past_due -> 'past_due'
    - unpaid / cancelled / expired -> 'inactive'
    """
    status_lower = ls_status.lower()
    
    if status_lower == 'on_trial':
        return 'trial'
    elif status_lower == 'active':
        return 'active'
    elif status_lower == 'past_due':
        return 'past_due'
    elif status_lower in ('unpaid', 'cancelled', 'expired'):
        return 'inactive'
    else:
        # Default to inactive for unknown statuses
        return 'inactive'


@router.post("/activate")
async def activate_subscription(
    request: ActivateSubscriptionRequest,
    db: Session = Depends(get_db_session)
):
    """
    Activate or update a user's subscription status.
    
    This endpoint is called by the webhook handler after Lemon Squeezy payment events.
    It:
    1. Finds user by user_id (primary) or email (fallback)
    2. Maps Lemon Squeezy status to our subscription_status
    3. Updates subscription_status, plan_type, and subscription_end_date
    4. Implements idempotency: only updates if new end_date is newer than existing
    
    Idempotency: Prevents old delayed webhooks from overwriting newer subscription status.
    """
    try:
        # Validate: At least one identifier must be provided
        if not request.user_id and not request.email:
            raise HTTPException(status_code=400, detail="Either user_id or email must be provided")
        
        # 1. Find user by ID (primary) or email (fallback)
        if request.user_id:
            # Primary: Match by user_id (immutable, reliable)
            try:
                from uuid import UUID
                user_uuid = UUID(request.user_id)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid user_id format: {request.user_id}")
            
            user = db.execute(
                text("SELECT id, subscription_status, subscription_end_date FROM users WHERE id = :user_id"),
                {"user_id": user_uuid}
            ).fetchone()
            
            if not user:
                raise HTTPException(status_code=404, detail=f"User not found with user_id: {request.user_id}")
        elif request.email:
            # Fallback: Match by email (for backward compatibility)
            user = db.execute(
                text("SELECT id, subscription_status, subscription_end_date FROM users WHERE email = :email"),
                {"email": request.email}
            ).fetchone()
            
            if not user:
                raise HTTPException(status_code=404, detail=f"User not found with email: {request.email}")
        
        user_id = user[0]
        existing_end_date = user[2]  # subscription_end_date (index 2)
        
        # 2. Map Lemon Squeezy status to our subscription_status
        mapped_status = map_lemon_squeezy_status(request.subscription_status)
        
        # 3. Parse subscription_end_date if provided
        new_end_date = None
        if request.subscription_end_date:
            try:
                new_end_date = datetime.fromisoformat(request.subscription_end_date.replace('Z', '+00:00'))
            except (ValueError, AttributeError) as e:
                # Log warning but continue (end_date is optional)
                print(f"⚠️ Warning: Failed to parse subscription_end_date '{request.subscription_end_date}': {e}")
                pass
        
        # 4. Idempotency check: Only update if new end_date is newer than existing
        # Only skip if both dates exist AND new_date is older or equal
        if existing_end_date and new_end_date:
            # Convert existing_end_date to datetime if it's a string
            if isinstance(existing_end_date, str):
                try:
                    existing_end_date = datetime.fromisoformat(existing_end_date.replace('Z', '+00:00'))
                except (ValueError, AttributeError):
                    existing_end_date = None
            
            if existing_end_date and new_end_date <= existing_end_date:
                # Old webhook - don't update, but return success (idempotent)
                return {
                    "message": "Subscription already updated (idempotent - older webhook ignored)",
                    "user_id": str(user_id),
                    "current_status": mapped_status,
                    "skipped": True
                }
        # If existing_end_date is NULL, always update (new subscription)
        # If new_end_date is NULL but existing exists, still update (status change)
        
        # 5. Update subscription fields
        update_params = {
            "user_id": user_id,
            "subscription_status": mapped_status,
            "plan_type": request.plan_type,
            "subscription_end_date": new_end_date  # Store as datetime object, not string
        }
        
        db.execute(
            text("""
                UPDATE users
                SET subscription_status = :subscription_status,
                    plan_type = :plan_type,
                    subscription_end_date = :subscription_end_date,
                    updated_at = NOW()
                WHERE id = :user_id
            """),
            update_params
        )
        
        db.commit()
        
        return {
            "message": "Subscription activated successfully",
            "user_id": str(user_id),
            "subscription_status": mapped_status,
            "plan_type": request.plan_type,
            "subscription_end_date": new_end_date.isoformat() if new_end_date else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to activate subscription: {str(e)}"
        )
    finally:
        db.close()

