# Testing Guide: Unified User Model
## Complete End-to-End Testing Checklist

**Date:** 2024  
**Status:** Ready for Testing

---

## Pre-Testing Setup

### 1. Environment Check

- [ ] Backend API running (`http://localhost:8000`)
- [ ] Frontend running (`http://localhost:3000`)
- [ ] Supabase configured
- [ ] Migrations executed (007 and 008)
- [ ] Stripe configured (for deposits)

### 2. Test Accounts

Create test accounts for different scenarios:
- [ ] Parent account (age 25+)
- [ ] Learner account (age 20+)
- [ ] Parent + Learner account
- [ ] Child account (age < 20)

---

## Test Suite 1: Database & Schema

### 1.1 Verify Tables Exist

```sql
-- Run in Supabase SQL Editor
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
  AND table_name IN (
    'users', 
    'user_roles', 
    'user_relationships',
    'learning_progress',
    'points_accounts',
    'points_transactions',
    'withdrawal_requests'
  );
```

**Expected:** 7 tables returned

### 1.2 Verify Schema Structure

```sql
-- Check users table has age column
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'users' AND column_name = 'age';

-- Check user_relationships has correct columns
SELECT column_name 
FROM information_schema.columns 
WHERE table_name = 'user_relationships';
```

**Expected:** 
- `users.age` exists (INTEGER, nullable)
- `user_relationships` has: `from_user_id`, `to_user_id`, `relationship_type`, `status`, `permissions`

### 1.3 Verify Trigger

```sql
-- Check trigger exists
SELECT trigger_name, event_object_table 
FROM information_schema.triggers 
WHERE trigger_name = 'on_auth_user_created';
```

**Expected:** Trigger exists on `auth.users`

---

## Test Suite 2: User Signup & Onboarding

### 2.1 Signup Flow

**Steps:**
1. Go to `/signup`
2. Sign up with Google OAuth OR email/password
3. Complete authentication

**Expected:**
- [ ] User created in `auth.users` (Supabase)
- [ ] User created in `public.users` (via trigger)
- [ ] 'learner' role assigned automatically
- [ ] Redirected to `/onboarding`

**Verify in Database:**
```sql
SELECT u.id, u.email, u.name, ur.role
FROM users u
LEFT JOIN user_roles ur ON u.id = ur.user_id
ORDER BY u.created_at DESC
LIMIT 1;
```

**Expected:** User exists with `role = 'learner'`

### 2.2 Onboarding - Parent Account

**Steps:**
1. On onboarding page, select "家長帳戶"
2. Enter parent age (25)
3. Enter child name and age (e.g., "小明", 10)
4. Submit

**Expected:**
- [ ] Parent age updated in database
- [ ] 'parent' role added
- [ ] Child account created with placeholder email
- [ ] Parent-child relationship created
- [ ] Redirected to `/dashboard`

**Verify in Database:**
```sql
-- Check parent roles
SELECT role FROM user_roles WHERE user_id = '<parent_id>';

-- Check child created
SELECT id, name, age, email FROM users WHERE email LIKE 'child-%@lexicraft.xyz';

-- Check relationship
SELECT * FROM user_relationships 
WHERE from_user_id = '<parent_id>' 
  AND relationship_type = 'parent_child';
```

**Expected:**
- Parent has roles: `['parent', 'learner']`
- Child exists with placeholder email
- Relationship exists with `status = 'active'`

### 2.3 Onboarding - Learner Account

**Steps:**
1. Sign up new user
2. On onboarding, select "學習者帳戶"
3. Enter age (25)
4. Submit

**Expected:**
- [ ] Age updated
- [ ] Only 'learner' role (no 'parent')
- [ ] Redirected to `/dashboard`

### 2.4 Onboarding - Both (Parent + Learner)

**Steps:**
1. Sign up new user
2. Select "家長 + 學習者"
3. Enter parent age (30) and learner age (30)
4. Optionally create child
5. Submit

**Expected:**
- [ ] Both ages set (same value)
- [ ] Roles: `['parent', 'learner']`
- [ ] Can create child if provided
- [ ] Redirected to `/dashboard`

---

## Test Suite 3: API Endpoints

### 3.1 Get Current User

**Request:**
```bash
GET /api/users/me?user_id=<user_id>
```

**Expected:**
```json
{
  "id": "...",
  "email": "...",
  "name": "...",
  "age": 25,
  "roles": ["learner"],
  "email_confirmed": true
}
```

### 3.2 Get User's Children

**Request:**
```bash
GET /api/users/me/children?user_id=<parent_id>
```

**Expected:**
```json
[
  {
    "id": "...",
    "name": "小明",
    "age": 10,
    "email": "child-<uuid>@lexicraft.xyz"
  }
]
```

**Edge Cases:**
- [ ] Non-parent user → 403 error
- [ ] No children → Empty array `[]`

### 3.3 Onboarding Status

**Request:**
```bash
GET /api/users/onboarding/status?user_id=<user_id>
```

**Expected:**
```json
{
  "completed": true,
  "roles": ["parent", "learner"],
  "missing_info": [],
  "has_age": true
}
```

### 3.4 Complete Onboarding

**Request:**
```bash
POST /api/users/onboarding/complete?user_id=<user_id>
Content-Type: application/json

{
  "account_type": "parent",
  "parent_age": 30,
  "child_name": "小明",
  "child_age": 10
}
```

**Expected:**
```json
{
  "success": true,
  "user_id": "...",
  "roles": ["parent", "learner"],
  "child_id": "...",
  "redirect_to": "/dashboard"
}
```

---

## Test Suite 4: Frontend Integration

### 4.1 Dashboard - Load Children

**Steps:**
1. Login as parent
2. Go to `/dashboard`

**Expected:**
- [ ] Dashboard loads
- [ ] Children fetched from API
- [ ] Child selector appears (if multiple children)
- [ ] First child selected by default
- [ ] Deposit form shows for selected child

**Verify:**
- Check browser console for API calls
- Check Network tab: `GET /api/users/me/children`

### 4.2 Dashboard - No Children

**Steps:**
1. Login as parent with no children
2. Go to `/dashboard`

**Expected:**
- [ ] Message: "您還沒有建立任何孩子的帳戶。"
- [ ] Suggestion to create child account

### 4.3 Deposit Flow

**Steps:**
1. Select child (if multiple)
2. Enter deposit amount
3. Click "存入"
4. Complete Stripe checkout

**Expected:**
- [ ] Checkout session created
- [ ] Stripe metadata includes `learner_id`
- [ ] Redirect to Stripe payment page
- [ ] After payment, webhook confirms deposit
- [ ] Points account updated

**Verify:**
- Check Stripe dashboard for session metadata
- Check database: `points_accounts` updated
- Check database: `points_transactions` created

---

## Test Suite 5: Edge Cases & Error Handling

### 5.1 Age Validation

**Test Cases:**
- [ ] Parent age < 20 → Error: "Parent must be at least 20 years old"
- [ ] Child age >= 20 → Error: "Child must be under 20 years old"
- [ ] Learner age < 20 → Error: "Users under 20 must have a parent account"

### 5.2 Relationship Verification

**Test Cases:**
- [ ] Withdrawal for non-child → 403 error
- [ ] Deposit for non-child → Should work (webhook)
- [ ] Get children as non-parent → 403 error

### 5.3 Onboarding Status

**Test Cases:**
- [ ] New user (no onboarding) → `completed: false`
- [ ] User with age but no role → `completed: false`
- [ ] User with role but no age → `completed: false`
- [ ] Complete user → `completed: true`

### 5.4 Email Confirmation

**Test Cases:**
- [ ] Withdrawal without email confirmation → 403 error
- [ ] Withdrawal with email confirmation → Success

---

## Test Suite 6: Data Integrity

### 6.1 Cascade Deletes

**Test:**
```sql
-- Create test data
-- Delete user
DELETE FROM users WHERE id = '<test_user_id>';

-- Verify cascades
SELECT COUNT(*) FROM user_roles WHERE user_id = '<test_user_id>'; -- Should be 0
SELECT COUNT(*) FROM user_relationships WHERE from_user_id = '<test_user_id>'; -- Should be 0
```

**Expected:** All related data deleted

### 6.2 Unique Constraints

**Test:**
- [ ] Try to create duplicate user-role → Should fail
- [ ] Try to create duplicate relationship → Should fail
- [ ] Try to create user with duplicate email → Should fail

---

## Test Suite 7: Performance

### 7.1 API Response Times

**Test:**
- [ ] `GET /api/users/me/children` < 500ms
- [ ] `GET /api/users/onboarding/status` < 300ms
- [ ] `POST /api/users/onboarding/complete` < 1000ms

### 7.2 Database Queries

**Test:**
- [ ] All queries use indexes
- [ ] No N+1 query problems
- [ ] Relationship queries are efficient

---

## Test Results Template

```
Date: _______________
Tester: _______________
Environment: [ ] Development [ ] Staging [ ] Production

Test Suite 1: Database & Schema
  [ ] 1.1 Tables exist
  [ ] 1.2 Schema structure
  [ ] 1.3 Trigger exists

Test Suite 2: User Signup & Onboarding
  [ ] 2.1 Signup flow
  [ ] 2.2 Parent account
  [ ] 2.3 Learner account
  [ ] 2.4 Both account

Test Suite 3: API Endpoints
  [ ] 3.1 Get current user
  [ ] 3.2 Get children
  [ ] 3.3 Onboarding status
  [ ] 3.4 Complete onboarding

Test Suite 4: Frontend Integration
  [ ] 4.1 Dashboard loads children
  [ ] 4.2 No children case
  [ ] 4.3 Deposit flow

Test Suite 5: Edge Cases
  [ ] 5.1 Age validation
  [ ] 5.2 Relationship verification
  [ ] 5.3 Onboarding status
  [ ] 5.4 Email confirmation

Test Suite 6: Data Integrity
  [ ] 6.1 Cascade deletes
  [ ] 6.2 Unique constraints

Test Suite 7: Performance
  [ ] 7.1 API response times
  [ ] 7.2 Database queries

Issues Found:
1. _______________
2. _______________
3. _______________

Overall Status: [ ] Pass [ ] Fail [ ] Needs Review
```

---

## Common Issues & Solutions

### Issue: Children not loading

**Symptoms:** Dashboard shows "載入中..." forever

**Solutions:**
1. Check API endpoint is accessible
2. Check user has 'parent' role
3. Check browser console for errors
4. Verify `user_id` is being passed correctly

### Issue: Onboarding redirect loop

**Symptoms:** User keeps getting redirected to onboarding

**Solutions:**
1. Check onboarding status API
2. Verify user has age set
3. Verify user has at least one role
4. Check database directly

### Issue: Trigger not creating users

**Symptoms:** User signs up but not in `public.users`

**Solutions:**
1. Check trigger exists
2. Check function `handle_new_user()` exists
3. Check Supabase logs
4. Verify RLS policies allow insert

---

**Status:** Ready for comprehensive testing

