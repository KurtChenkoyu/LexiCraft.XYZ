# Refund Mechanism Implementation Plan

**Status:** Implementation Guide  
**Priority:** High (Required for Beta Launch)  
**Last Updated:** January 2025

---

## Overview

This document outlines the implementation plan for the refund mechanism required by Taiwan's Consumer Protection Act and our enhanced beta refund policy.

### Legal Requirements

1. **7-Day Cooling-Off Period** (Mandatory - Taiwan Consumer Protection Act)
   - Full refund available within 7 days of deposit
   - No questions asked
   - Must be clearly disclosed

2. **Beta Enhanced Refund Policy** (Voluntary - Better than required)
   - Full refund for unused deposits anytime during beta
   - Partial refund for used deposits (unused points only)
   - No questions asked policy

---

## Database Schema Changes

### 1. Add Refund Tracking Table

```sql
CREATE TABLE refund_requests (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    parent_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    deposit_transaction_id INTEGER REFERENCES points_transactions(id),
    refund_type TEXT NOT NULL, -- 'full', 'partial', '7day_cooling_off'
    requested_amount_ntd DECIMAL(10, 2) NOT NULL,
    refunded_amount_ntd DECIMAL(10, 2),
    points_refunded INTEGER,
    reason TEXT,
    status TEXT DEFAULT 'pending', -- 'pending', 'processing', 'completed', 'rejected', 'cancelled'
    stripe_refund_id TEXT, -- Stripe refund ID
    created_at TIMESTAMP DEFAULT NOW(),
    processed_at TIMESTAMP,
    completed_at TIMESTAMP
);

CREATE INDEX idx_refund_requests_user_id ON refund_requests(user_id);
CREATE INDEX idx_refund_requests_parent_id ON refund_requests(parent_id);
CREATE INDEX idx_refund_requests_status ON refund_requests(status);
CREATE INDEX idx_refund_requests_created_at ON refund_requests(created_at);
```

### 2. Add Refund Tracking to Points Transactions

```sql
-- Add refund tracking columns to points_transactions
ALTER TABLE points_transactions 
ADD COLUMN refund_request_id INTEGER REFERENCES refund_requests(id),
ADD COLUMN is_refunded BOOLEAN DEFAULT FALSE,
ADD COLUMN refunded_at TIMESTAMP;

CREATE INDEX idx_points_transactions_refund_request_id ON points_transactions(refund_request_id);
CREATE INDEX idx_points_transactions_is_refunded ON points_transactions(is_refunded);
```

### 3. Add Deposit Metadata

```sql
-- Track deposit date for 7-day cooling-off calculation
ALTER TABLE points_transactions
ADD COLUMN deposit_date TIMESTAMP,
ADD COLUMN stripe_payment_intent_id TEXT,
ADD COLUMN stripe_charge_id TEXT;

CREATE INDEX idx_points_transactions_deposit_date ON points_transactions(deposit_date);
```

---

## API Endpoints

### 1. Create Refund Request

**Endpoint:** `POST /api/refunds/request`

**Request Body:**
```json
{
  "learner_id": "uuid",
  "refund_type": "full" | "partial" | "7day_cooling_off",
  "amount_ntd": 500.00,  // Optional for full refunds
  "reason": "Optional reason text"
}
```

**Response:**
```json
{
  "refund_request_id": 123,
  "status": "pending",
  "requested_amount_ntd": 500.00,
  "estimated_refund_amount_ntd": 500.00,
  "points_to_refund": 500,
  "processing_time": "3-5 business days",
  "message": "Refund request created successfully"
}
```

**Business Logic:**
1. Verify parent-child relationship
2. Check if deposit is within 7 days (for cooling-off)
3. Calculate available points for refund
4. Validate refund amount
5. Create refund request record
6. Return estimated refund amount

### 2. Get Refund Status

**Endpoint:** `GET /api/refunds/{refund_request_id}`

**Response:**
```json
{
  "refund_request_id": 123,
  "status": "processing",
  "requested_amount_ntd": 500.00,
  "refunded_amount_ntd": 500.00,
  "points_refunded": 500,
  "created_at": "2025-01-15T10:00:00Z",
  "processed_at": "2025-01-16T09:00:00Z",
  "completed_at": null,
  "stripe_refund_id": "re_1234567890"
}
```

### 3. Get Refund History

**Endpoint:** `GET /api/refunds/history?learner_id={uuid}`

**Response:**
```json
{
  "refunds": [
    {
      "id": 123,
      "refund_type": "full",
      "amount_ntd": 500.00,
      "status": "completed",
      "created_at": "2025-01-15T10:00:00Z",
      "completed_at": "2025-01-18T14:30:00Z"
    }
  ]
}
```

### 4. Admin: Process Refund

**Endpoint:** `POST /api/admin/refunds/{refund_request_id}/process`

**Request Body:**
```json
{
  "action": "approve" | "reject",
  "admin_notes": "Optional notes"
}
```

**Business Logic:**
1. Verify refund request exists and is pending
2. If approved:
   - Calculate refund amount
   - Process Stripe refund
   - Update points account
   - Create refund transaction records
   - Update refund request status
3. If rejected:
   - Update refund request status
   - Send notification to parent

---

## Backend Implementation

### 1. Refund Service Module

**File:** `backend/src/services/refund_service.py`

```python
"""
Refund Service

Handles refund calculations, validations, and processing.
"""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional, Dict
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import text

class RefundService:
    """Service for handling refunds."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def calculate_refund_amount(
        self,
        learner_id: UUID,
        refund_type: str,
        requested_amount: Optional[Decimal] = None
    ) -> Dict:
        """
        Calculate refund amount based on available points and refund type.
        
        Returns:
            {
                "available_points": int,
                "refundable_amount_ntd": Decimal,
                "points_to_refund": int,
                "is_within_7days": bool,
                "can_full_refund": bool
            }
        """
        # Get available points
        account = self.db.execute(
            text("""
                SELECT available_points, total_earned, withdrawn_points
                FROM points_accounts
                WHERE user_id = :learner_id
            """),
            {"learner_id": str(learner_id)}
        ).fetchone()
        
        if not account:
            raise ValueError("Points account not found")
        
        available_points = account[0] or 0
        
        # Get deposit transactions (not refunded, not withdrawn)
        deposits = self.db.execute(
            text("""
                SELECT 
                    id,
                    points,
                    deposit_date,
                    created_at,
                    stripe_payment_intent_id
                FROM points_transactions
                WHERE user_id = :learner_id
                  AND transaction_type = 'deposit'
                  AND is_refunded = FALSE
                ORDER BY created_at DESC
            """),
            {"learner_id": str(learner_id)}
        ).fetchall()
        
        # Check if within 7-day cooling-off period
        is_within_7days = False
        if deposits:
            latest_deposit = deposits[0]
            deposit_date = latest_deposit[2] or latest_deposit[4]
            if deposit_date:
                days_since_deposit = (datetime.now() - deposit_date).days
                is_within_7days = days_since_deposit <= 7
        
        # Calculate refundable amount
        if refund_type == "full":
            refundable_points = available_points
            refundable_amount = Decimal(refundable_points)
        elif refund_type == "partial":
            if requested_amount:
                refundable_points = min(int(requested_amount), available_points)
                refundable_amount = Decimal(refundable_points)
            else:
                refundable_points = available_points
                refundable_amount = Decimal(refundable_points)
        elif refund_type == "7day_cooling_off":
            # Full refund if within 7 days
            if is_within_7days:
                refundable_points = available_points
                refundable_amount = Decimal(refundable_points)
            else:
                # Partial refund of unused points
                refundable_points = available_points
                refundable_amount = Decimal(refundable_points)
        else:
            raise ValueError(f"Invalid refund type: {refund_type}")
        
        return {
            "available_points": available_points,
            "refundable_amount_ntd": refundable_amount,
            "points_to_refund": refundable_points,
            "is_within_7days": is_within_7days,
            "can_full_refund": is_within_7days or refundable_points == available_points
        }
    
    def create_refund_request(
        self,
        parent_id: UUID,
        learner_id: UUID,
        refund_type: str,
        requested_amount: Optional[Decimal] = None,
        reason: Optional[str] = None
    ) -> int:
        """
        Create a refund request.
        
        Returns refund_request_id
        """
        # Calculate refund amount
        refund_calc = self.calculate_refund_amount(learner_id, refund_type, requested_amount)
        
        # Create refund request
        refund_id = self.db.execute(
            text("""
                INSERT INTO refund_requests (
                    user_id,
                    parent_id,
                    refund_type,
                    requested_amount_ntd,
                    points_refunded,
                    reason,
                    status
                )
                VALUES (
                    :learner_id,
                    :parent_id,
                    :refund_type,
                    :requested_amount,
                    :points_refunded,
                    :reason,
                    'pending'
                )
                RETURNING id
            """),
            {
                "learner_id": str(learner_id),
                "parent_id": str(parent_id),
                "refund_type": refund_type,
                "requested_amount": refund_calc["refundable_amount_ntd"],
                "points_refunded": refund_calc["points_to_refund"],
                "reason": reason
            }
        ).scalar()
        
        self.db.commit()
        return refund_id
    
    def process_refund(
        self,
        refund_request_id: int,
        admin_id: UUID
    ) -> Dict:
        """
        Process a refund request (admin only).
        
        Steps:
        1. Get refund request
        2. Process Stripe refund
        3. Update points account
        4. Mark transactions as refunded
        5. Update refund request status
        """
        import stripe
        
        # Get refund request
        refund = self.db.execute(
            text("""
                SELECT 
                    id,
                    user_id,
                    parent_id,
                    refund_type,
                    requested_amount_ntd,
                    points_refunded,
                    status,
                    deposit_transaction_id
                FROM refund_requests
                WHERE id = :refund_id
            """),
            {"refund_id": refund_request_id}
        ).fetchone()
        
        if not refund:
            raise ValueError("Refund request not found")
        
        if refund[6] != "pending":  # status
            raise ValueError(f"Refund request is not pending (status: {refund[6]})")
        
        learner_id = refund[1]
        refund_amount = refund[4]
        points_to_refund = refund[5]
        
        # Get Stripe payment intent ID from deposit transaction
        deposit_tx = self.db.execute(
            text("""
                SELECT stripe_payment_intent_id, stripe_charge_id
                FROM points_transactions
                WHERE user_id = :learner_id
                  AND transaction_type = 'deposit'
                  AND is_refunded = FALSE
                ORDER BY created_at DESC
                LIMIT 1
            """),
            {"learner_id": str(learner_id)}
        ).fetchone()
        
        if not deposit_tx:
            raise ValueError("Deposit transaction not found")
        
        stripe_payment_intent_id = deposit_tx[0]
        stripe_charge_id = deposit_tx[1]
        
        # Process Stripe refund
        try:
            stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
            
            refund_obj = stripe.Refund.create(
                charge=stripe_charge_id,
                amount=int(refund_amount * 100),  # Convert to cents
                reason="requested_by_customer",
                metadata={
                    "refund_request_id": refund_request_id,
                    "learner_id": str(learner_id),
                    "parent_id": str(refund[2])
                }
            )
            
            stripe_refund_id = refund_obj.id
            
        except Exception as e:
            # Update refund request status to failed
            self.db.execute(
                text("""
                    UPDATE refund_requests
                    SET status = 'rejected',
                        processed_at = NOW()
                    WHERE id = :refund_id
                """),
                {"refund_id": refund_request_id}
            )
            self.db.commit()
            raise Exception(f"Stripe refund failed: {str(e)}")
        
        # Update points account (deduct refunded points)
        self.db.execute(
            text("""
                UPDATE points_accounts
                SET available_points = available_points - :points
                WHERE user_id = :learner_id
            """),
            {
                "learner_id": str(learner_id),
                "points": points_to_refund
            }
        )
        
        # Mark deposit transactions as refunded
        self.db.execute(
            text("""
                UPDATE points_transactions
                SET is_refunded = TRUE,
                    refund_request_id = :refund_id,
                    refunded_at = NOW()
                WHERE user_id = :learner_id
                  AND transaction_type = 'deposit'
                  AND is_refunded = FALSE
                  AND id IN (
                      SELECT id FROM points_transactions
                      WHERE user_id = :learner_id
                        AND transaction_type = 'deposit'
                        AND is_refunded = FALSE
                      ORDER BY created_at DESC
                      LIMIT 1
                  )
            """),
            {
                "learner_id": str(learner_id),
                "refund_id": refund_request_id
            }
        )
        
        # Create refund transaction record
        self.db.execute(
            text("""
                INSERT INTO points_transactions (
                    user_id,
                    transaction_type,
                    points,
                    description
                )
                VALUES (
                    :learner_id,
                    'refund',
                    :points,
                    'Refund request #' || :refund_id
                )
            """),
            {
                "learner_id": str(learner_id),
                "points": -points_to_refund,  # Negative for refund
                "refund_id": refund_request_id
            }
        )
        
        # Update refund request status
        self.db.execute(
            text("""
                UPDATE refund_requests
                SET status = 'completed',
                    refunded_amount_ntd = :amount,
                    stripe_refund_id = :stripe_refund_id,
                    processed_at = NOW(),
                    completed_at = NOW()
                WHERE id = :refund_id
            """),
            {
                "refund_id": refund_request_id,
                "amount": refund_amount,
                "stripe_refund_id": stripe_refund_id
            }
        )
        
        self.db.commit()
        
        return {
            "refund_request_id": refund_request_id,
            "status": "completed",
            "refunded_amount_ntd": float(refund_amount),
            "stripe_refund_id": stripe_refund_id
        }
```

### 2. Refund API Endpoints

**File:** `backend/src/api/refunds.py`

```python
"""
Refund API Endpoints

Handles refund requests from parents.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from decimal import Decimal
from sqlalchemy.orm import Session

from src.database.postgres_connection import PostgresConnection
from src.middleware.auth import get_current_user_id
from src.services.refund_service import RefundService

router = APIRouter(prefix="/api/refunds", tags=["Refunds"])


class CreateRefundRequest(BaseModel):
    learner_id: str
    refund_type: str  # "full", "partial", "7day_cooling_off"
    amount_ntd: Optional[float] = None
    reason: Optional[str] = None


def get_db_session():
    """Get PostgreSQL database session."""
    conn = PostgresConnection()
    return conn.get_session()


@router.post("/request")
async def create_refund_request(
    request: CreateRefundRequest,
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db_session)
):
    """
    Create a refund request.
    
    Requires:
    - Email confirmation
    - Valid parent-child relationship
    - Available points to refund
    """
    try:
        parent_uuid = user_id
        learner_uuid = UUID(request.learner_id)
        
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
            raise HTTPException(403, "Learner not found or you are not their parent")
        
        # Create refund request
        refund_service = RefundService(db)
        refund_id = refund_service.create_refund_request(
            parent_id=parent_uuid,
            learner_id=learner_uuid,
            refund_type=request.refund_type,
            requested_amount=Decimal(request.amount_ntd) if request.amount_ntd else None,
            reason=request.reason
        )
        
        # Get refund calculation for response
        refund_calc = refund_service.calculate_refund_amount(
            learner_uuid,
            request.refund_type,
            Decimal(request.amount_ntd) if request.amount_ntd else None
        )
        
        return {
            "refund_request_id": refund_id,
            "status": "pending",
            "requested_amount_ntd": float(refund_calc["refundable_amount_ntd"]),
            "points_to_refund": refund_calc["points_to_refund"],
            "is_within_7days": refund_calc["is_within_7days"],
            "processing_time": "3-5 business days",
            "message": "Refund request created successfully"
        }
        
    except Exception as e:
        raise HTTPException(500, f"Failed to create refund request: {str(e)}")
    finally:
        db.close()


@router.get("/{refund_request_id}")
async def get_refund_status(
    refund_request_id: int,
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db_session)
):
    """Get refund request status."""
    # Implementation here
    pass


@router.get("/history")
async def get_refund_history(
    learner_id: str = Query(...),
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db_session)
):
    """Get refund history for a learner."""
    # Implementation here
    pass
```

---

## Frontend Implementation

### 1. Refund Request Form Component

**File:** `landing-page/components/refunds/RefundRequestForm.tsx`

```typescript
// Component for requesting refunds
// - Show available points
// - Select refund type (full/partial/7day)
// - Enter amount (for partial)
// - Submit request
// - Show confirmation
```

### 2. Refund History Component

**File:** `landing-page/components/refunds/RefundHistory.tsx`

```typescript
// Component for viewing refund history
// - List all refund requests
// - Show status (pending/processing/completed/rejected)
// - Show amounts and dates
```

### 3. Dashboard Integration

Add refund section to parent dashboard:
- Available balance
- "Request Refund" button
- Refund history link
- 7-day cooling-off indicator

---

## Testing Checklist

- [ ] Test full refund within 7 days
- [ ] Test full refund after 7 days (beta policy)
- [ ] Test partial refund
- [ ] Test refund with insufficient points
- [ ] Test Stripe refund integration
- [ ] Test points deduction
- [ ] Test transaction marking
- [ ] Test email notifications
- [ ] Test admin refund processing
- [ ] Test refund history display

---

## Migration Script

**File:** `backend/migrations/008_add_refund_tables.sql`

```sql
-- Run this migration to add refund support
-- See schema changes above
```

---

## Timeline

- **Week 1:** Database schema + API endpoints
- **Week 2:** Frontend components + testing
- **Week 3:** Integration testing + bug fixes
- **Week 4:** Deploy to beta

---

## Cost Estimates

- **Development:** 2-3 weeks (1 developer)
- **Testing:** 1 week
- **Stripe refund fees:** No fees for refunds (Stripe refunds processing fees)
- **Bank fees:** None (refunds go back to original payment method)

---

## Security Considerations

1. **Authorization:** Only parent can request refund for their child
2. **Validation:** Verify available points before processing
3. **Idempotency:** Prevent duplicate refund requests
4. **Audit Trail:** Log all refund actions
5. **Rate Limiting:** Limit refund requests per day

---

## Monitoring

- Track refund request volume
- Monitor refund processing time
- Alert on failed Stripe refunds
- Track refund reasons
- Monitor 7-day cooling-off usage

