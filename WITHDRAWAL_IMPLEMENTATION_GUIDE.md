# Withdrawal System Implementation Guide

**Status:** 🟡 **Not Yet Implemented**  
**Priority:** High (needed for MVP)

---

## Overview

Parents need to withdraw money from their escrow account when children earn points. This guide covers how to implement the withdrawal system.

---

## Current Status

### ✅ What Exists
- Database schema: `withdrawal_requests` table
- CRUD functions: `backend/src/database/postgres_crud/withdrawals.py`
- Points tracking: `points_accounts` table with `available_points`
- Deposit system: Stripe integration for deposits (money in)

### ❌ What's Missing
- Withdrawal API endpoints
- Payment processor integration (Stripe Connect or bank transfer)
- Frontend withdrawal UI
- Bank account linking
- Tax reporting integration

---

## Payment Methods for Withdrawals

### Option 1: Stripe Connect (Recommended for MVP)

**How it works:**
1. Parent links bank account via Stripe Connect
2. Platform initiates payout to parent's bank account
3. Stripe handles compliance and transfers
4. 2-5 business days to arrive

**Pros:**
- ✅ Automated
- ✅ Stripe handles compliance
- ✅ Works internationally
- ✅ Already using Stripe for deposits

**Cons:**
- ⚠️ Stripe Connect may require Taiwan entity
- ⚠️ Fees: ~0.25% + $0.25 per payout
- ⚠️ 2-5 day processing time

**Setup:**
```bash
# Stripe Connect requires:
1. Stripe Connect account setup
2. OAuth flow for parent to link account
3. Payout API integration
```

### Option 2: Manual Bank Transfer (Simplest for MVP)

**How it works:**
1. Parent provides bank account info in dashboard
2. Parent requests withdrawal
3. Admin processes manually (or automated script)
4. Bank transfer initiated from your business account
5. Update status in database

**Pros:**
- ✅ Simple to implement
- ✅ No additional payment processor needed
- ✅ Works with any Taiwan bank
- ✅ Full control

**Cons:**
- ⚠️ Manual processing (or need to build automation)
- ⚠️ Bank transfer fees (varies by bank)
- ⚠️ 1-2 business days processing

**Implementation:**
```python
# Backend API endpoint
POST /api/withdrawals/request
{
  "child_id": "uuid",
  "amount_ntd": 500.00,
  "bank_account": "1234567890",
  "bank_name": "Taiwan Bank"
}

# Admin processes manually or via bank API
# Update status: pending → processing → completed
```

### Option 3: ECPay / TapPay (Taiwan Local Processors)

**How it works:**
- Similar to Stripe Connect but Taiwan-specific
- Requires Taiwan business entity
- Better for local market

**Pros:**
- ✅ Taiwan-specific features
- ✅ Lower fees for local transfers
- ✅ Faster processing (same-day possible)

**Cons:**
- ⚠️ Requires Taiwan entity
- ⚠️ More complex setup
- ⚠️ Less documentation

**Best for:** Phase 2 (after MVP validation)

---

## Recommended Approach: Manual Bank Transfer (MVP)

**For MVP, start with manual bank transfer:**
1. ✅ Simple to implement
2. ✅ No additional payment processor setup
3. ✅ Full control over process
4. ✅ Can automate later with Stripe Connect

---

## Implementation Plan

### Phase 1: Basic Withdrawal Request (Week 1)

#### Backend API

**1. Create Withdrawal Request Endpoint**
```python
# backend/src/api/withdrawals.py
@router.post("/request")
async def create_withdrawal_request(
    request: WithdrawalRequestCreate,
    current_user: User = Depends(get_current_user)
):
    """
    Parent requests withdrawal of available points.
    
    Steps:
    1. Validate available points >= requested amount
    2. Create withdrawal_request (status: 'pending')
    3. Deduct from available_points
    4. Create points_transaction (type: 'withdrawal')
    5. Return withdrawal request ID
    """
```

**2. Get Withdrawal History**
```python
@router.get("/history")
async def get_withdrawal_history(
    child_id: UUID,
    current_user: User = Depends(get_current_user)
):
    """Get all withdrawal requests for a child."""
```

**3. Update Withdrawal Status (Admin)**
```python
@router.patch("/{request_id}/status")
async def update_withdrawal_status(
    request_id: int,
    status: str,  # 'processing', 'completed', 'failed'
    transaction_id: Optional[str] = None,
    admin_user: User = Depends(get_admin_user)
):
    """Admin updates withdrawal status after processing."""
```

#### Frontend UI

**1. Withdrawal Form Component**
```typescript
// landing-page/components/withdrawal/WithdrawalForm.tsx
- Show available points
- Input withdrawal amount
- Input bank account info (if not saved)
- Submit withdrawal request
- Show pending withdrawals
```

**2. Withdrawal History Component**
```typescript
// landing-page/components/withdrawal/WithdrawalHistory.tsx
- List all withdrawal requests
- Show status (pending, processing, completed, failed)
- Show amount and date
```

**3. Dashboard Integration**
```typescript
// Add to dashboard page
- Withdrawal section
- Available balance
- Request withdrawal button
- Withdrawal history
```

### Phase 2: Bank Account Management (Week 2)

**1. Save Bank Account**
```python
# Add to users table or separate table
bank_accounts:
  - user_id
  - bank_name
  - account_number
  - account_holder_name
  - is_default
```

**2. Bank Account UI**
```typescript
// landing-page/components/withdrawal/BankAccountForm.tsx
- Add/edit bank account
- Set default account
- Delete account
```

### Phase 3: Automation (Future)

**1. Stripe Connect Integration**
- OAuth flow for bank linking
- Automated payouts
- Webhook handling

**2. Bank API Integration**
- Direct bank transfers via API
- Real-time status updates

---

## Database Schema (Already Exists)

```sql
CREATE TABLE withdrawal_requests (
    id SERIAL PRIMARY KEY,
    child_id UUID NOT NULL,
    parent_id UUID NOT NULL,
    amount_ntd DECIMAL(10, 2) NOT NULL,
    points_amount INTEGER NOT NULL,
    status TEXT DEFAULT 'pending',  -- 'pending', 'processing', 'completed', 'failed'
    bank_account TEXT,
    transaction_id TEXT,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (child_id) REFERENCES children(id),
    FOREIGN KEY (parent_id) REFERENCES users(id)
);
```

---

## Withdrawal Flow

### 1. Parent Requests Withdrawal

```
Parent Dashboard
  ↓
Click "Request Withdrawal"
  ↓
Enter amount (max: available_points)
  ↓
Enter/Select bank account
  ↓
Submit request
  ↓
Backend validates:
  - available_points >= amount
  - bank_account exists
  - no pending withdrawals (optional)
  ↓
Create withdrawal_request (status: 'pending')
  ↓
Deduct from available_points
  ↓
Create points_transaction (type: 'withdrawal')
  ↓
Return success
```

### 2. Admin Processes Withdrawal

```
Admin Dashboard (or automated)
  ↓
View pending withdrawals
  ↓
Initiate bank transfer:
  - Use bank account from request
  - Transfer amount_ntd
  - Get transaction_id from bank
  ↓
Update withdrawal_request:
  - status: 'processing' → 'completed'
  - transaction_id: bank_transaction_id
  - completed_at: NOW()
  ↓
Send notification to parent
```

### 3. Failed Withdrawal Handling

```
If transfer fails:
  ↓
Update withdrawal_request:
  - status: 'failed'
  - completed_at: NOW()
  ↓
Refund points:
  - Add back to available_points
  - Create points_transaction (type: 'refund')
  ↓
Notify parent of failure
```

---

## Legal Compliance (Taiwan)

### Tax Reporting

**Requirements:**
- Rewards ≥NT$1,000: Collect ID
- Rewards ≥NT$20,010: Withhold 10% tax

**Implementation:**
```python
# Before processing withdrawal
if annual_reward_value >= 20010:
    tax_amount = withdrawal_amount * 0.10
    net_amount = withdrawal_amount - tax_amount
    # Withhold tax
    # File tax report
elif annual_reward_value >= 1000:
    # Collect ID (if not already collected)
    # File tax report
```

### 7-Day Refund Right

**Implementation:**
```python
# Check if deposit was within 7 days
if deposit_date > (now() - 7 days):
    # Allow full refund
    # Process refund via Stripe
    # Update withdrawal_request
```

---

## API Endpoints Needed

### Parent Endpoints

```python
POST   /api/withdrawals/request          # Create withdrawal request
GET    /api/withdrawals/history          # Get withdrawal history
GET    /api/withdrawals/{request_id}     # Get withdrawal details
POST   /api/withdrawals/bank-account     # Save bank account
GET    /api/withdrawals/bank-accounts    # Get saved bank accounts
DELETE /api/withdrawals/bank-account/{id} # Delete bank account
```

### Admin Endpoints

```python
GET    /api/admin/withdrawals/pending    # Get pending withdrawals
PATCH  /api/admin/withdrawals/{id}/status # Update withdrawal status
POST   /api/admin/withdrawals/{id}/process # Process withdrawal
```

---

## Frontend Components Needed

### 1. WithdrawalForm.tsx
```typescript
- Available balance display
- Amount input
- Bank account selector
- Submit button
- Validation
```

### 2. WithdrawalHistory.tsx
```typescript
- List of withdrawals
- Status badges
- Amount and date
- Transaction ID (if completed)
```

### 3. BankAccountForm.tsx
```typescript
- Bank name input
- Account number input
- Account holder name
- Save/Edit/Delete
```

### 4. Dashboard Integration
```typescript
// Add to dashboard page
<WithdrawalSection>
  <AvailableBalance />
  <WithdrawalForm />
  <WithdrawalHistory />
</WithdrawalSection>
```

---

## Testing Checklist

- [ ] Parent can request withdrawal
- [ ] Validation: Cannot withdraw more than available
- [ ] Validation: Cannot withdraw if deficit exists
- [ ] Points deducted from available_points
- [ ] Withdrawal request created with 'pending' status
- [ ] Points transaction created
- [ ] Admin can view pending withdrawals
- [ ] Admin can update status
- [ ] Bank transfer processed (manual or automated)
- [ ] Status updated to 'completed'
- [ ] Parent notified of completion
- [ ] Failed withdrawals refund points
- [ ] Tax reporting for large amounts
- [ ] 7-day refund handling

---

## Next Steps

1. **Implement basic withdrawal request API** (Week 1)
2. **Build withdrawal UI components** (Week 1)
3. **Add bank account management** (Week 2)
4. **Set up manual processing workflow** (Week 2)
5. **Add notifications** (Week 2)
6. **Test end-to-end flow** (Week 2)
7. **Consider Stripe Connect for automation** (Phase 2)

---

## Cost Estimates

### Manual Bank Transfer
- Bank transfer fees: ~NT$10-30 per transfer
- Processing time: 1-2 business days
- Admin time: ~5 minutes per withdrawal

### Stripe Connect
- Setup: Free
- Fees: 0.25% + $0.25 per payout
- Processing: 2-5 business days
- Automation: Full

---

## References

- `backend/src/database/postgres_crud/withdrawals.py` - CRUD functions
- `backend/src/database/models.py` - WithdrawalRequest model
- `docs/13-legal-analysis-taiwan.md` - Legal requirements
- `STRIPE_INTEGRATION_COMPLETE.md` - Stripe setup (for deposits)

---

**Status:** Ready to implement. Start with manual bank transfer for MVP, then automate with Stripe Connect in Phase 2.

