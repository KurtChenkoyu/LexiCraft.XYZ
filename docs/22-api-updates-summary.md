# API Updates Summary: Unified User Model Migration

**Date:** 2024  
**Status:** ✅ Complete

---

## Overview

Updated all API endpoints to use the unified user model with `user_relationships` table instead of the old `children` table.

---

## Updated Endpoints

### 1. Withdrawals API (`/api/withdrawals`)

**Changes:**
- ✅ `child_id` → `learner_id` (parameter renamed)
- ✅ Uses `user_relationships` to verify parent-child relationship
- ✅ Queries `points_accounts` using `user_id` instead of `child_id`
- ✅ Queries `withdrawal_requests` using `user_id` instead of `child_id`
- ✅ Queries `points_transactions` using `user_id` instead of `child_id`

**Endpoints:**
- `POST /api/withdrawals/request`
  - **Request:** `{ "learner_id": "...", "amount_ntd": 100, ... }`
  - **Query Param:** `user_id` (parent's user ID)
  - **Verifies:** Parent-child relationship via `user_relationships`

- `GET /api/withdrawals/history`
  - **Query Params:** `learner_id`, `user_id` (parent)
  - **Returns:** Withdrawal history for learner

### 2. Deposits API (`/api/deposits`)

**Changes:**
- ✅ `child_id` → `learner_id` (parameter renamed)
- ✅ Queries `points_accounts` using `user_id` instead of `child_id`
- ✅ Queries `points_transactions` using `user_id` instead of `child_id`
- ✅ Removed `metadata` column usage (uses `description` instead)

**Endpoints:**
- `POST /api/deposits/confirm`
  - **Request:** `{ "learner_id": "...", "user_id": "...", "amount": 100, ... }`
  - **Creates:** Points account if doesn't exist
  - **Updates:** Points account balance

- `GET /api/deposits/{learner_id}/balance`
  - **Returns:** Balance for learner

### 3. Users API (`/api/users`) - NEW

**New Endpoints:**
- `GET /api/users/me`
  - **Query Param:** `user_id`
  - **Returns:** Current user information with roles

- `GET /api/users/me/children`
  - **Query Param:** `user_id` (parent)
  - **Returns:** List of children for parent
  - **Verifies:** User has 'parent' role

- `GET /api/users/{user_id}`
  - **Returns:** User information by ID

---

## Breaking Changes

### Request/Response Changes

**Withdrawals:**
```diff
- POST /api/withdrawals/request
-   { "child_id": "...", ... }
+ POST /api/withdrawals/request?user_id=...
+   { "learner_id": "...", ... }
```

**Deposits:**
```diff
- POST /api/deposits/confirm
-   { "child_id": "...", ... }
+ POST /api/deposits/confirm
+   { "learner_id": "...", ... }
```

**Balance:**
```diff
- GET /api/deposits/{child_id}/balance
+ GET /api/deposits/{learner_id}/balance
```

### Database Schema Changes

**Old (removed):**
```sql
SELECT * FROM children WHERE parent_id = :user_id
SELECT * FROM points_accounts WHERE child_id = :child_id
```

**New:**
```sql
SELECT to_user_id FROM user_relationships 
WHERE from_user_id = :parent_id 
  AND relationship_type = 'parent_child'
  AND status = 'active'

SELECT * FROM points_accounts WHERE user_id = :learner_id
```

---

## Migration Guide for Frontend

### 1. Update Withdrawal Requests

**Before:**
```typescript
await axios.post('/api/withdrawals/request', {
  child_id: childId,
  amount_ntd: 100
})
```

**After:**
```typescript
await axios.post(
  `/api/withdrawals/request?user_id=${parentId}`,
  {
    learner_id: learnerId,  // Changed from child_id
    amount_ntd: 100
  }
)
```

### 2. Update Deposit Confirmations

**Before:**
```typescript
await axios.post('/api/deposits/confirm', {
  child_id: childId,
  user_id: userId,
  amount: 100
})
```

**After:**
```typescript
await axios.post('/api/deposits/confirm', {
  learner_id: learnerId,  // Changed from child_id
  user_id: userId,
  amount: 100
})
```

### 3. Update Balance Queries

**Before:**
```typescript
await axios.get(`/api/deposits/${childId}/balance`)
```

**After:**
```typescript
await axios.get(`/api/deposits/${learnerId}/balance`)
```

### 4. Get User's Children

**New:**
```typescript
const response = await axios.get(
  `/api/users/me/children?user_id=${parentId}`
)
// Returns: [{ id, name, age, email }, ...]
```

---

## Security Improvements

1. **Relationship Verification:**
   - All endpoints verify parent-child relationship via `user_relationships`
   - Checks `status = 'active'` to ensure relationship is valid

2. **Role Verification:**
   - `/api/users/me/children` verifies user has 'parent' role
   - Prevents unauthorized access

3. **Email Confirmation:**
   - Withdrawals still require email confirmation
   - Uses existing `check_email_confirmation()` function

---

## Testing Checklist

- [ ] Test withdrawal request with valid parent-child relationship
- [ ] Test withdrawal request with invalid relationship (should fail)
- [ ] Test deposit confirmation
- [ ] Test balance retrieval
- [ ] Test getting user's children
- [ ] Test getting current user info
- [ ] Verify all queries use `user_id` instead of `child_id`
- [ ] Verify relationship checks work correctly

---

## Notes

- **Auth Middleware:** Currently accepts `user_id` as query parameter for MVP
- **Future:** Should extract `user_id` from JWT token in Authorization header
- **Backward Compatibility:** None - this is a breaking change
- **Migration Required:** Frontend must update all API calls

---

**Status:** ✅ All APIs updated and ready for testing

