# Delete and Recreate User Guide

## Option 1: Fix Existing User (Recommended)

Before deleting, try to fix the existing user:

### Step 1: Check Current State
Run this in Supabase SQL Editor:
```sql
-- Find your user
SELECT 
  au.id,
  au.email,
  au.email_confirmed,
  CASE WHEN pu.id IS NULL THEN '❌ Missing in public.users' ELSE '✅ Exists' END as status
FROM auth.users au
LEFT JOIN public.users pu ON au.id = pu.id
WHERE au.email = 'your-email@example.com';
```

### Step 2: Create Missing User Record
If the user is missing in `public.users`, run:
```sql
-- Replace with your actual user ID and email
INSERT INTO public.users (
  id, 
  email, 
  name, 
  country, 
  email_confirmed,
  email_confirmed_at,
  created_at,
  updated_at
)
SELECT 
  au.id,
  au.email,
  COALESCE(au.raw_user_meta_data->>'name', au.raw_user_meta_data->>'full_name', ''),
  COALESCE(au.raw_user_meta_data->>'country', 'TW'),
  COALESCE(au.email_confirmed, FALSE),
  CASE WHEN COALESCE(au.email_confirmed, FALSE) = TRUE THEN au.created_at ELSE NULL END,
  au.created_at,
  NOW()
FROM auth.users au
WHERE au.email = 'your-email@example.com'
  AND NOT EXISTS (SELECT 1 FROM public.users WHERE id = au.id)
ON CONFLICT (id) DO NOTHING;

-- Add default learner role
INSERT INTO public.user_roles (user_id, role, created_at)
SELECT id, 'learner', NOW()
FROM auth.users
WHERE email = 'your-email@example.com'
  AND NOT EXISTS (
    SELECT 1 FROM public.user_roles 
    WHERE user_id = auth.users.id AND role = 'learner'
  )
ON CONFLICT (user_id, role) DO NOTHING;
```

### Step 3: Test
After creating the user record, try accessing the dashboard again.

---

## Option 2: Delete and Recreate (If Option 1 Doesn't Work)

### ⚠️ Warning
Deleting a user will:
- Remove all their data
- Remove all their relationships
- Remove all their learning progress
- Remove all their points/transactions
- **Cannot be undone**

### Step 1: Verify Trigger is Set Up
Run this in Supabase SQL Editor:
```sql
-- Check if trigger exists
SELECT trigger_name, event_object_table
FROM information_schema.triggers
WHERE trigger_name = 'on_auth_user_created';

-- Check if function exists
SELECT routine_name
FROM information_schema.routines
WHERE routine_name = 'handle_new_user';
```

If either is missing, run migration `008_update_trigger_for_roles.sql` in Supabase SQL Editor.

### Step 2: Delete User (Cascade)
```sql
-- Get user ID first
SELECT id, email FROM auth.users WHERE email = 'your-email@example.com';

-- Delete from public tables first (to avoid foreign key issues)
DELETE FROM public.user_roles WHERE user_id = 'USER_ID_HERE';
DELETE FROM public.user_relationships WHERE from_user_id = 'USER_ID_HERE' OR to_user_id = 'USER_ID_HERE';
DELETE FROM public.learning_progress WHERE user_id = 'USER_ID_HERE';
DELETE FROM public.points_accounts WHERE user_id = 'USER_ID_HERE';
DELETE FROM public.points_transactions WHERE user_id = 'USER_ID_HERE';
DELETE FROM public.verification_schedule WHERE user_id = 'USER_ID_HERE';
DELETE FROM public.withdrawal_requests WHERE learner_id = 'USER_ID_HERE';
DELETE FROM public.relationship_discoveries WHERE user_id = 'USER_ID_HERE';
DELETE FROM public.users WHERE id = 'USER_ID_HERE';

-- Finally, delete from auth (this will cascade)
DELETE FROM auth.users WHERE id = 'USER_ID_HERE';
```

### Step 3: Re-sign Up
1. Go to your app's signup page
2. Sign up with Google again
3. The trigger should automatically create the user in `public.users`

### Step 4: Verify User Was Created
```sql
-- Check if user was created
SELECT 
  au.id,
  au.email,
  pu.id as public_user_id,
  CASE WHEN pu.id IS NULL THEN '❌ Trigger failed' ELSE '✅ Created' END as status
FROM auth.users au
LEFT JOIN public.users pu ON au.id = pu.id
WHERE au.email = 'your-email@example.com';
```

---

## Option 3: Test with New Email (Safest)

Instead of deleting, test with a different email:

1. Sign up with a different Google account
2. Check if the trigger creates the user
3. If it works, then delete the old user
4. If it doesn't work, the trigger needs to be fixed

---

## Troubleshooting

### Trigger Not Working?
1. Check if trigger exists (Step 1 above)
2. Check Supabase logs for errors
3. Run migration `008_update_trigger_for_roles.sql` again
4. Test by creating a new user

### Still Getting 401?
1. Check JWT secret is correct
2. Test token with debug endpoint: `/api/users/debug/token`
3. Check backend logs for errors
4. Verify user exists in both `auth.users` and `public.users`

---

## Recommended Approach

1. **First**: Try Option 1 (fix existing user) - it's the safest
2. **If that doesn't work**: Try Option 3 (test with new email)
3. **Last resort**: Option 2 (delete and recreate)

