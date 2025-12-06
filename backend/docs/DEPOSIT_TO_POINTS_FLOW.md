# Deposit → Points Flow Documentation

## Overview

This document describes how deposits from Stripe payments flow into the points system, and confirms that **words are freely accessible** without requiring deposits or points.

---

## Key Findings

### ✅ Confirmed: No Word Unlocking Mechanism

**Words are freely accessible** - there is no mechanism that requires deposits or points to unlock words. The system operates in "Explorer Mode" where all words are available for learning.

**Evidence:**
- No word access restrictions found in codebase
- `backend/docs/core-verification-system/GAP_ANALYSIS.md` explicitly states:
  - ✅ "Points are earned by verifying words, not spent to unlock words"
  - ✅ "All words are freely accessible (Explorer Mode)"
- No `unlock` or `access_control` logic related to words in API endpoints
- Only "unlock" references found are for achievements, not word access

---

## Deposit Flow

### 1. Stripe Payment Initiation

**Frontend:** `landing-page/app/api/deposits/create-checkout/route.ts`
- Parent creates a Stripe Checkout session
- Session metadata includes:
  - `learner_id`: The child/learner's user ID
  - `user_id`: The parent's user ID
  - `amount`: Deposit amount in NT$

### 2. Stripe Webhook Handler

**Frontend:** `landing-page/app/api/webhooks/stripe/route.ts`
- Listens for `checkout.session.completed` events
- Extracts payment information from Stripe session
- Calls backend API to confirm deposit

**Webhook → Backend Call:**
```typescript
await fetch(`${backendUrl}/api/deposits/confirm`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    session_id: session.id,
    learner_id: session.metadata?.learner_id,
    user_id: session.metadata?.user_id,
    amount: session.amount_total! / 100,  // Convert cents to NT$
  }),
})
```

### 3. Backend Deposit Confirmation

**Backend:** `backend/src/api/deposits.py` - `POST /api/deposits/confirm`

#### Process Flow:

1. **Duplicate Check**
   - Verifies deposit doesn't already exist by checking `points_transactions` for matching `session_id` in description
   - Prevents double-crediting

2. **Learner Validation**
   - Verifies `learner_id` exists in `users` table
   - Raises 404 if learner not found

3. **Points Account Creation/Retrieval**
   - Checks if `points_accounts` entry exists for learner
   - If not, creates new account with all fields initialized to 0:
     ```sql
     INSERT INTO points_accounts (user_id, total_earned, available_points, locked_points, withdrawn_points)
     VALUES (:learner_id, 0, 0, 0, 0)
     ```

4. **Points Conversion**
   - **Conversion Rate:** 1:1 (1 NT$ = 1 point) for MVP
   - Converts deposit amount to integer points
   - Example: NT$ 1,000 → 1,000 points

5. **Transaction Record Creation**
   - Creates entry in `points_transactions` table:
     ```sql
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
     ```

6. **Points Account Update**
   - **Adds points to `available_points`** (not `total_earned`)
   - Points are immediately available for withdrawal
   - SQL:
     ```sql
     UPDATE points_accounts
     SET available_points = available_points + :points
     WHERE user_id = :learner_id
     ```

7. **Commit & Return**
   - Commits transaction
   - Returns confirmation with transaction ID and points added

---

## Database Schema

### `points_accounts` Table

**Schema:** (from `backend/migrations/007_unified_user_model.sql`)

```sql
CREATE TABLE IF NOT EXISTS points_accounts (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    total_earned INTEGER DEFAULT 0,        -- Points earned from learning/verification
    available_points INTEGER DEFAULT 0,   -- Points available for withdrawal (includes deposits)
    locked_points INTEGER DEFAULT 0,      -- Points pending verification
    withdrawn_points INTEGER DEFAULT 0,   -- Points already withdrawn
    deficit_points INTEGER DEFAULT 0,     -- Negative balance from failed verification
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

**Key Fields:**
- `total_earned`: Points earned through learning/verification activities
- `available_points`: **Deposits go here** - immediately withdrawable points
- `locked_points`: Points locked pending verification completion
- `withdrawn_points`: Historical total of withdrawn points
- `deficit_points`: Negative balance from early withdrawals that failed verification

### `points_transactions` Table

**Schema:**

```sql
CREATE TABLE IF NOT EXISTS points_transactions (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    learning_progress_id INTEGER REFERENCES learning_progress(id),
    transaction_type TEXT NOT NULL,  -- 'deposit', 'earned', 'unlocked', 'withdrawn', 'deficit', 'bonus'
    bonus_type TEXT,                 -- 'relationship_discovery', 'pattern_recognition', etc.
    points INTEGER NOT NULL,
    tier INTEGER,
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

**Transaction Types:**
- `'deposit'`: Points added from Stripe payment
- `'earned'`: Points earned from learning activities
- `'unlocked'`: Points unlocked from verification milestones
- `'withdrawn'`: Points withdrawn to bank account
- `'deficit'`: Negative points from failed verification
- `'bonus'`: Bonus points from relationship discoveries, etc.

---

## Deposit → Points Relationship

### Direct Relationship

**Deposits directly credit `available_points`** in the `points_accounts` table:

```
Stripe Payment (NT$)
    ↓
Webhook Handler
    ↓
POST /api/deposits/confirm
    ↓
1. Create points_transaction (type='deposit')
    ↓
2. Update points_accounts.available_points += deposit_amount
```

### No Intermediate Tables

**Important:** There is **no separate `deposits` table**. Deposits are tracked as:
- `points_transactions` with `transaction_type = 'deposit'`
- Balance updates in `points_accounts.available_points`

### Points Flow Summary

```
Deposit Flow:
  Stripe Payment → available_points (immediately withdrawable)

Earning Flow:
  Learn Word → Verify → Points earned → available_points (after unlock milestones)

Withdrawal Flow:
  available_points → withdrawn_points (when withdrawal processed)
```

---

## Key Questions Answered

### 1. How does deposit credit points?

**Answer:**
1. Stripe webhook receives `checkout.session.completed` event
2. Frontend calls `POST /api/deposits/confirm` with session details
3. Backend:
   - Creates `points_transaction` record with `transaction_type='deposit'`
   - Updates `points_accounts.available_points += deposit_amount`
4. Points are **immediately available** for withdrawal (no locking)

**Conversion:** 1 NT$ = 1 point (MVP rate)

### 2. What is the deposit → points_accounts relationship?

**Answer:**
- **Direct relationship:** Deposits directly update `points_accounts.available_points`
- **No separate deposits table:** Deposits are tracked via `points_transactions` with `transaction_type='deposit'`
- **One-to-one mapping:** Each deposit creates one transaction record and one balance update
- **Immediate availability:** Deposited points go directly to `available_points` (not `locked_points`)

**Schema Relationship:**
```
deposits (conceptual) → points_transactions (transaction_type='deposit')
                     → points_accounts.available_points (balance update)
```

### 3. Are there any word-related restrictions?

**Answer:**
**NO** - There are **no word-related restrictions** based on deposits or points.

**Confirmed:**
- ✅ All words are freely accessible (Explorer Mode)
- ✅ Points are **earned** by learning/verifying words, not **spent** to access words
- ✅ No word unlocking mechanism exists
- ✅ No access control based on deposit status
- ✅ No tier restrictions based on points balance

**The system operates as:**
- **Free access:** Users can learn any word without restrictions
- **Earn points:** Users earn points by successfully learning and verifying words
- **Withdraw points:** Users can withdraw earned points (and deposited points) to cash

---

## API Endpoints

### `POST /api/deposits/confirm`

**Purpose:** Confirm a deposit after successful Stripe payment

**Request:**
```json
{
  "session_id": "cs_test_...",
  "learner_id": "uuid-of-learner",
  "user_id": "uuid-of-parent",
  "amount": 1000.0
}
```

**Response:**
```json
{
  "message": "Deposit confirmed",
  "transaction_id": 123,
  "points_added": 1000,
  "amount_ntd": 1000.0
}
```

**Error Handling:**
- 404: Learner not found
- 500: Database error or duplicate deposit

### `GET /api/deposits/{learner_id}/balance`

**Purpose:** Get current points balance for a learner

**Response:**
```json
{
  "total_earned": 500,
  "available_points": 1500,  // Includes deposits + earned points
  "locked_points": 200,
  "withdrawn_points": 300
}
```

---

## Integration Points

### Frontend Integration

1. **Deposit Creation:** `landing-page/app/api/deposits/create-checkout/route.ts`
   - Creates Stripe Checkout session
   - Includes learner_id and user_id in metadata

2. **Webhook Handler:** `landing-page/app/api/webhooks/stripe/route.ts`
   - Processes `checkout.session.completed` events
   - Calls backend `/api/deposits/confirm` endpoint

### Backend Integration

1. **Deposit API:** `backend/src/api/deposits.py`
   - Handles deposit confirmation
   - Updates points accounts

2. **Database Models:** `backend/src/database/models.py`
   - `PointsAccount`: SQLAlchemy model for points_accounts
   - `PointsTransaction`: SQLAlchemy model for points_transactions

3. **CRUD Operations:** `backend/src/database/postgres_crud/points.py`
   - Helper functions for points account operations

---

## Business Logic

### Deposit Purpose

Deposits serve as **parent-controlled funding** for the learning platform:

1. **Parent deposits** points (money) into child's account
2. **Child learns** words (freely accessible)
3. **Child earns** points by successfully verifying words
4. **Child withdraws** earned points (and deposited points) to cash

### Points vs. Money

- **1 point = 1 NT$** (MVP conversion rate)
- Points are a **virtual currency** representing real money
- Deposits add points that can be withdrawn as cash
- Earnings add points that can be withdrawn as cash

### No Word Gating

**Critical Design Decision:** Words are **not gated** by deposits or points.

**Rationale:**
- Lower barrier to entry (users can explore freely)
- Focus on earning through learning, not purchasing access
- Aligns with "Explorer Mode" philosophy
- Points are rewards, not currency for access

---

## Summary

### Deposit → Points Flow

```
┌─────────────────┐
│ Stripe Payment  │
│   (NT$ 1,000)   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Webhook Handler │
│ (Frontend)      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ POST /api/      │
│ deposits/confirm│
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────┐
│ 1. Create points_transaction     │
│    (type='deposit', 1000 pts)   │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│ 2. Update points_accounts       │
│    available_points += 1000     │
└─────────────────────────────────┘
```

### Key Confirmations

✅ **Deposits credit points** directly to `available_points`  
✅ **No word unlocking** - all words are freely accessible  
✅ **Points are earned**, not spent to access content  
✅ **1:1 conversion** - 1 NT$ = 1 point (MVP)  
✅ **Immediate availability** - deposited points can be withdrawn immediately  

---

## Related Documentation

- `backend/docs/core-verification-system/GAP_ANALYSIS.md` - Confirms no word unlocking
- `docs/07-partial-unlock-mechanics.md` - Explains partial unlock system for earned points
- `docs/EXPLORER_MODE_IMPLEMENTATION.md` - Explorer Mode details
- `backend/src/api/deposits.py` - Implementation code
- `backend/src/api/withdrawals.py` - Withdrawal flow

---

**Document Created:** 2024  
**Last Updated:** 2024  
**Status:** ✅ Complete - All questions answered

