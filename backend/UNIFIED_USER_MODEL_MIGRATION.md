# Unified User Model Migration - Fresh Start

**Status:** ✅ Schema & Models Complete | ⏳ CRUD & APIs Pending  
**Date:** 2024  
**Approach:** Fresh start (no data migration needed)

---

## What's Been Done

### ✅ 1. Database Migration Created
**File:** `backend/migrations/007_unified_user_model.sql`

- Drops old `children` table and related constraints
- Creates unified `users` table with `age` field
- Creates `user_roles` table for RBAC
- Creates `parent_child_relationships` table (self-referential)
- Updates all tables to use `user_id` instead of `child_id`
- Adds helper functions: `is_parent_of()` and `get_user_roles()`

### ✅ 2. SQLAlchemy Models Updated
**File:** `backend/src/database/models.py`

**Removed:**
- `Child` model (no longer needed)

**Added:**
- `UserRole` model (RBAC)
- `ParentChildRelationship` model (self-referential)

**Updated:**
- `User` model: Added `age` field, updated relationships
- `LearningProgress`: `child_id` → `user_id`
- `VerificationSchedule`: `child_id` → `user_id`
- `PointsAccount`: `child_id` → `user_id`
- `PointsTransaction`: `child_id` → `user_id`
- `WithdrawalRequest`: `child_id` → `user_id` (learner)
- `RelationshipDiscovery`: `child_id` → `user_id`

---

## What Still Needs to Be Done

### ⏳ 3. Update CRUD Functions

**Files to update:**
- `backend/src/database/postgres_crud/users.py`
  - Remove all `Child` CRUD functions
  - Add `UserRole` CRUD functions
  - Add `ParentChildRelationship` CRUD functions
  - Add helper: `is_parent_of()`, `get_user_roles()`, `get_user_children()`

- `backend/src/database/postgres_crud/progress.py`
  - Change `child_id` → `user_id` in all functions

- `backend/src/database/postgres_crud/points.py`
  - Change `child_id` → `user_id` in all functions

- `backend/src/database/postgres_crud/verification.py`
  - Change `child_id` → `user_id` in all functions

- `backend/src/database/postgres_crud/withdrawals.py`
  - Change `child_id` → `user_id` in all functions
  - Update parent verification to use `parent_child_relationships`

- `backend/src/database/postgres_crud/relationships.py`
  - Change `child_id` → `user_id` in all functions

### ⏳ 4. Update API Endpoints

**Files to update:**
- `backend/src/api/deposits.py`
  - Change `child_id` → `user_id` in request models
  - Update parent verification logic

- `backend/src/api/withdrawals.py`
  - Change `child_id` → `user_id` in request models
  - Update parent verification logic

- `backend/src/api/survey.py`
  - ✅ Already uses `user_id` (no changes needed)

### ⏳ 5. Update Frontend

**Files to check/update:**
- API client interfaces (change `child_id` → `user_id`)
- Deposit forms
- Withdrawal forms
- Dashboard components
- Any components that reference "children" or "child_id"

---

## How to Apply the Migration

### Step 1: Run the Migration

```bash
# Connect to your database
psql -h <host> -U <user> -d <database>

# Run the migration
\i backend/migrations/007_unified_user_model.sql
```

Or via Supabase SQL Editor:
1. Go to Supabase Dashboard → SQL Editor
2. Copy contents of `007_unified_user_model.sql`
3. Paste and run

### Step 2: Verify Migration

```sql
-- Check tables exist
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN ('users', 'user_roles', 'parent_child_relationships', 'learning_progress');

-- Check user_roles table structure
\d user_roles

-- Check parent_child_relationships table structure
\d parent_child_relationships
```

### Step 3: Update Code

After running the migration, update the CRUD functions and APIs as listed above.

---

## New Schema Overview

### Users Table
```sql
users (
    id UUID PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT,  -- Optional (Supabase Auth)
    name TEXT,
    phone TEXT,
    country TEXT DEFAULT 'TW',
    age INTEGER,  -- NEW: Can be NULL for adults
    email_confirmed BOOLEAN,
    email_confirmed_at TIMESTAMP,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
)
```

### User Roles (RBAC)
```sql
user_roles (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    role TEXT NOT NULL,  -- 'parent', 'learner', 'admin'
    UNIQUE(user_id, role)
)
```

### Parent-Child Relationships
```sql
parent_child_relationships (
    id SERIAL PRIMARY KEY,
    parent_id UUID REFERENCES users(id),
    child_id UUID REFERENCES users(id),
    relationship_type TEXT DEFAULT 'parent_child',
    permissions JSONB,
    UNIQUE(parent_id, child_id),
    CHECK (parent_id != child_id)
)
```

### All Learning Data
All tables now use `user_id` instead of `child_id`:
- `learning_progress.user_id`
- `verification_schedule.user_id`
- `points_accounts.user_id`
- `points_transactions.user_id`
- `withdrawal_requests.user_id` (the learner)
- `relationship_discoveries.user_id`

---

## Usage Examples

### Creating a User with Roles

```python
from backend.src.database.postgres_crud.users import create_user, add_user_role

# Create a parent user
parent = create_user(session, email="parent@example.com", name="Parent Name")
add_user_role(session, parent.id, 'parent')

# Create a learner user
learner = create_user(session, email="learner@example.com", name="Learner Name", age=10)
add_user_role(session, learner.id, 'learner')

# Create parent-child relationship
from backend.src.database.postgres_crud.users import create_parent_child_relationship
create_parent_child_relationship(session, parent.id, learner.id)
```

### Checking Permissions

```python
from backend.src.database.postgres_crud.users import is_parent_of, user_has_role

# Check if user is parent of another
if is_parent_of(session, parent_id, child_id):
    # Allow action
    pass

# Check user roles
if user_has_role(session, user_id, 'parent'):
    # Show parent features
    pass
```

---

## Benefits of This Approach

✅ **Flexible**: User can be parent AND learner  
✅ **Scalable**: Easy to add new roles (teacher, tutor, admin)  
✅ **Industry-standard**: Matches best practices (Duolingo, Khan Academy)  
✅ **Simpler**: One user model, not two  
✅ **Clean**: Fresh start, no migration complexity  

---

## Notes

- **Supabase Auth**: Existing Supabase Auth integration should continue working (users.id matches auth.users.id)
- **Surveys**: Already use `user_id`, no changes needed
- **No Data Loss**: Since we're doing a fresh start, no existing data to preserve
- **Future Roles**: Easy to add via `user_roles` table (e.g., 'teacher', 'tutor', 'admin')

---

## Next Steps

1. ✅ Run migration `007_unified_user_model.sql`
2. ⏳ Update CRUD functions (see list above)
3. ⏳ Update API endpoints
4. ⏳ Update frontend
5. ⏳ Test end-to-end

---

**Questions?** Check the migration file comments or review the models in `backend/src/database/models.py`

