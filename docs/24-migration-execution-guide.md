# Migration Execution Guide
## Unified User Model Migration

**Date:** 2024  
**Status:** Ready for Execution

---

## ⚠️ IMPORTANT WARNINGS

1. **This migration drops existing tables** - All data in `children`, `users`, and related tables will be deleted
2. **Fresh start approach** - Only run if you don't have production data to preserve
3. **Backup first** - If you have any data you want to keep, export it first
4. **Test in development** - Always test migrations in a development environment first

---

## Prerequisites

- ✅ Supabase project set up
- ✅ Access to Supabase SQL Editor
- ✅ Database connection configured
- ✅ No critical production data (or backed up)

---

## Step-by-Step Execution

### Step 1: Backup (Optional but Recommended)

If you have any data you want to preserve:

```sql
-- Export users (if any exist)
SELECT * FROM users;

-- Export children (if any exist)
SELECT * FROM children;

-- Export any other data you want to keep
```

Save these exports to a file for reference.

---

### Step 2: Run Migration 007

**File:** `backend/migrations/007_unified_user_model.sql`

1. Open Supabase Dashboard
2. Go to **SQL Editor**
3. Click **New Query**
4. Copy the entire contents of `007_unified_user_model.sql`
5. Paste into SQL Editor
6. Click **Run** (or press Cmd/Ctrl + Enter)

**What it does:**
- Drops old tables (`children`, old `users`, etc.)
- Creates new `users` table with `age` column
- Creates `user_roles` table for RBAC
- Creates `user_relationships` table (generic relationships)
- Recreates all learning/progress tables with `user_id`
- Creates helper functions

**Expected output:**
- ✅ All tables created successfully
- ✅ No errors in execution

**Verification:**
```sql
-- Check that tables exist
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
  AND table_name IN ('users', 'user_roles', 'user_relationships', 'learning_progress');

-- Should return 4 rows
```

---

### Step 3: Run Migration 008

**File:** `backend/migrations/008_update_trigger_for_roles.sql`

1. In the same SQL Editor (or new query)
2. Copy the entire contents of `008_update_trigger_for_roles.sql`
3. Paste into SQL Editor
4. Click **Run**

**What it does:**
- Updates `handle_new_user()` trigger function
- Adds automatic 'learner' role assignment on signup
- Ensures new users get default role

**Expected output:**
- ✅ Function updated successfully
- ✅ Trigger still active

**Verification:**
```sql
-- Check trigger exists
SELECT trigger_name, event_object_table, action_statement
FROM information_schema.triggers
WHERE trigger_name = 'on_auth_user_created';

-- Should return 1 row
```

---

### Step 4: Test Trigger

Test that the trigger works correctly:

```sql
-- This will be done automatically when a user signs up
-- But you can test manually:

-- 1. Create a test user in auth.users (via Supabase Auth UI or API)
-- 2. Check that user was created in public.users:
SELECT id, email, name FROM users ORDER BY created_at DESC LIMIT 1;

-- 3. Check that 'learner' role was assigned:
SELECT ur.user_id, ur.role, u.email
FROM user_roles ur
JOIN users u ON ur.user_id = u.id
ORDER BY ur.created_at DESC
LIMIT 1;

-- Should show role = 'learner'
```

---

### Step 5: Verify Schema

Run these queries to verify everything is set up correctly:

```sql
-- 1. Check users table structure
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'users'
ORDER BY ordinal_position;

-- Should include: id, email, name, age, email_confirmed, etc.

-- 2. Check user_roles table
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'user_roles';

-- Should include: id, user_id, role, created_at

-- 3. Check user_relationships table
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'user_relationships';

-- Should include: id, from_user_id, to_user_id, relationship_type, status, permissions, etc.

-- 4. Check that all learning tables use user_id
SELECT table_name, column_name
FROM information_schema.columns
WHERE table_name IN ('learning_progress', 'points_accounts', 'points_transactions', 'withdrawal_requests')
  AND column_name = 'user_id';

-- Should return multiple rows (one for each table)
```

---

## Troubleshooting

### Error: "relation does not exist"

**Problem:** Trying to drop a table that doesn't exist

**Solution:** This is normal if tables don't exist yet. The migration uses `DROP TABLE IF EXISTS`, so it should be safe. If you see this error, check:
- Are you running migrations in the correct database?
- Do you have the right permissions?

### Error: "permission denied"

**Problem:** Insufficient database permissions

**Solution:** 
- Ensure you're using the service role key or have admin access
- Check that your Supabase project has the correct permissions

### Error: "duplicate key value"

**Problem:** Trying to insert a user that already exists

**Solution:** 
- The trigger uses `ON CONFLICT DO NOTHING`, so this shouldn't happen
- If it does, check for existing users in `auth.users` that conflict

### Trigger Not Working

**Problem:** New users don't get created in `public.users`

**Solution:**
1. Check trigger exists:
   ```sql
   SELECT * FROM information_schema.triggers WHERE trigger_name = 'on_auth_user_created';
   ```
2. Check function exists:
   ```sql
   SELECT routine_name FROM information_schema.routines WHERE routine_name = 'handle_new_user';
   ```
3. Test manually:
   ```sql
   -- Check if function works
   SELECT handle_new_user(NEW) -- This won't work directly, but check function definition
   ```

---

## Post-Migration Checklist

- [ ] Migration 007 executed successfully
- [ ] Migration 008 executed successfully
- [ ] All tables created
- [ ] Trigger function updated
- [ ] Test user signup creates user in `public.users`
- [ ] Test user signup assigns 'learner' role
- [ ] All API endpoints work
- [ ] Frontend can fetch children
- [ ] Onboarding flow works

---

## Rollback Plan

**If something goes wrong:**

1. **Stop the application** - Prevent new users from signing up
2. **Export any new data** - If migration partially completed
3. **Restore from backup** - If you have a backup
4. **Re-run migration** - If it's safe to do so

**Note:** Since this is a "fresh start" migration, rollback means:
- Recreating old schema
- Restoring data from backup
- Or starting fresh again

---

## Next Steps After Migration

1. **Test Signup Flow:**
   - Sign up a new user
   - Verify user created in `public.users`
   - Verify 'learner' role assigned

2. **Test Onboarding:**
   - Complete onboarding for parent account
   - Create child account
   - Verify parent-child relationship created

3. **Test API Endpoints:**
   - `GET /api/users/me/children`
   - `POST /api/users/onboarding/complete`
   - `POST /api/deposits/confirm`

4. **Test Frontend:**
   - Dashboard loads children
   - Deposit flow works
   - All components use new schema

---

## Support

If you encounter issues:
1. Check the error message carefully
2. Verify you're in the correct database
3. Check Supabase logs
4. Review the migration SQL for syntax errors
5. Test in a development environment first

---

**Status:** Ready to execute when you're ready to migrate

