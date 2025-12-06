# Implementation Status: Unified User Model & Onboarding

**Date:** 2024  
**Status:** Core Implementation Complete ✅

---

## ✅ Completed

### 1. Database Schema
- ✅ Migration `007_unified_user_model.sql` - Generic `user_relationships` table
- ✅ Migration `008_update_trigger_for_roles.sql` - Auto-assign 'learner' role on signup
- ✅ All tables use `user_id` instead of `child_id`

### 2. Backend Models & CRUD
- ✅ Updated SQLAlchemy models (`UserRelationship` instead of `ParentChildRelationship`)
- ✅ Updated all CRUD functions to use `user_id`
- ✅ Added `create_child_account()` with placeholder email generation
- ✅ Added relationship management functions

### 3. Onboarding API
- ✅ `POST /api/users/onboarding/complete` - Complete onboarding flow
- ✅ `GET /api/users/onboarding/status` - Check onboarding status
- ✅ Handles: `parent`, `learner`, `both` account types
- ✅ Validates age requirements (20+ for parents/adults)
- ✅ Creates child accounts with placeholder emails

### 4. Frontend Integration
- ✅ Onboarding wizard UI (`/onboarding`)
- ✅ Multi-step form with progress indicator
- ✅ Integrated with Supabase Auth
- ✅ Updated signup flow to redirect to onboarding
- ✅ Updated login flow to check onboarding status
- ✅ Updated auth callback to check onboarding status
- ✅ Dashboard checks onboarding and redirects if needed
- ✅ Created `lib/onboarding.ts` utility functions

### 5. Redirect Flow
- ✅ Signup → Onboarding (if not completed)
- ✅ Login → Onboarding (if not completed) → Dashboard
- ✅ Auth Callback → Onboarding (if not completed) → Dashboard
- ✅ Dashboard → Onboarding (if not completed)

---

## ⏳ Pending (Future Work)

### 1. API Endpoints Needing Updates
These endpoints still reference the old `children` table and need to be updated:

**Withdrawals API** (`backend/src/api/withdrawals.py`):
- ❌ Uses `child_id` - needs to use `user_id` (learner)
- ❌ Queries `children` table - needs to use `user_relationships`
- ❌ Needs to verify parent-child relationship via `user_relationships`

**Deposits API** (`backend/src/api/deposits.py`):
- ❌ Uses `child_id` - needs to use `user_id` (learner)
- ❌ Needs to verify parent-child relationship

**Action Required:**
```python
# Instead of:
SELECT id FROM children WHERE id = :child_id AND parent_id = :user_id

# Use:
SELECT to_user_id FROM user_relationships 
WHERE from_user_id = :user_id 
  AND to_user_id = :child_id 
  AND relationship_type = 'parent_child'
  AND status = 'active'
```

### 2. Auth Middleware
- ❌ `get_current_user_id()` is a placeholder
- ❌ Need to extract user_id from Supabase JWT token
- ❌ Should verify token and return user_id

**Implementation needed:**
```python
from fastapi import Depends, HTTPException
from supabase import create_client

def get_current_user_id(
    authorization: str = Header(None)
) -> str:
    """Extract user_id from Supabase JWT token."""
    if not authorization:
        raise HTTPException(401, "Missing authorization header")
    
    token = authorization.replace("Bearer ", "")
    # Verify token with Supabase
    # Extract user_id from token
    # Return user_id
```

### 3. Frontend Components
Some components may still reference `child_id`:

- ❌ `DepositForm` - may need to fetch children from API
- ❌ `DepositButton` - may need child_id updates
- ❌ Dashboard - needs to fetch real child IDs from database

### 4. Database Migration
- ⚠️ Migration `007` needs to be run in Supabase SQL Editor
- ⚠️ Migration `008` needs to be run after `007`
- ⚠️ Old tables will be dropped (fresh start)

---

## 🧪 Testing Checklist

### Backend
- [ ] Run migration `007_unified_user_model.sql`
- [ ] Run migration `008_update_trigger_for_roles.sql`
- [ ] Test `POST /api/users/onboarding/complete` with all account types
- [ ] Test `GET /api/users/onboarding/status`
- [ ] Verify trigger creates user with 'learner' role
- [ ] Test child account creation with placeholder email

### Frontend
- [ ] Test signup flow → onboarding
- [ ] Test Google OAuth → onboarding
- [ ] Test login → onboarding (if not completed)
- [ ] Test onboarding wizard for each account type
- [ ] Test child account creation
- [ ] Test dashboard redirect if onboarding incomplete

### Integration
- [ ] Verify user created in `public.users` after Supabase signup
- [ ] Verify 'learner' role assigned automatically
- [ ] Verify child account created with placeholder email
- [ ] Verify parent-child relationship created
- [ ] Test full flow: Signup → Onboarding → Dashboard

---

## 📝 Migration Steps

### Step 1: Run Database Migrations

1. Open Supabase SQL Editor
2. Run `backend/migrations/007_unified_user_model.sql`
   - ⚠️ **WARNING:** This drops old tables (fresh start)
3. Run `backend/migrations/008_update_trigger_for_roles.sql`
   - Updates trigger to assign default role

### Step 2: Verify Trigger

```sql
-- Test that trigger works
-- Create a test user via Supabase Auth
-- Check that:
-- 1. User created in public.users
-- 2. 'learner' role assigned in user_roles
```

### Step 3: Test Onboarding Flow

1. Sign up new user
2. Should redirect to `/onboarding`
3. Complete onboarding
4. Should redirect to `/dashboard`

---

## 🔧 Known Issues

### 1. Auth Middleware Placeholder
- Currently accepts `user_id` as query param for MVP
- In production, should extract from JWT token
- **Workaround:** Frontend passes `user_id` from Supabase Auth

### 2. Withdrawals/Deposits Still Use Old Schema
- These endpoints need refactoring
- Can be done incrementally
- **Workaround:** Update these endpoints when needed

### 3. Child ID in Frontend
- Dashboard uses placeholder `'temp-child-id'`
- Need to fetch real child IDs from API
- **Workaround:** Create API endpoint to get user's children

---

## 📚 Related Documentation

- `docs/18-signup-flow-design.md` - Signup flow design
- `docs/19-relationship-ecosystem-design.md` - Relationship ecosystem
- `docs/20-session-summary.md` - Session summary
- `backend/UNIFIED_USER_MODEL_MIGRATION.md` - Migration guide

---

## 🎯 Next Steps

1. **Run migrations** in Supabase
2. **Test onboarding flow** end-to-end
3. **Update withdrawals/deposits APIs** to use new schema
4. **Implement auth middleware** for JWT token extraction
5. **Update frontend components** to fetch real child IDs
6. **Add API endpoint** to get user's children: `GET /api/users/me/children`

---

**Status:** Ready for testing and migration execution

