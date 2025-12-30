-- ============================================
-- Manual Payment Activation Script
-- Use when: Webhook failed, user paid but subscription_status is NULL
-- Created: 2024-12-30
-- Description: Safely activate user subscriptions manually when webhooks fail
-- ============================================

-- ============================================
-- SECTION 1: HELPER QUERIES (Find User)
-- ============================================

-- Query 1: Find user by email
-- Replace 'USER_EMAIL' with actual email from payment receipt or user report
SELECT 
  id,
  email,
  name,
  subscription_status,
  plan_type,
  subscription_end_date,
  created_at,
  updated_at
FROM public.users
WHERE email = 'USER_EMAIL';  -- 👈 REPLACE WITH ACTUAL EMAIL

-- Query 2: Find user by user_id (UUID)
-- Use this if you already have the UUID from another query
-- Replace 'USER_ID' with actual UUID (format: 'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx')
SELECT 
  id,
  email,
  name,
  subscription_status,
  plan_type,
  subscription_end_date,
  created_at,
  updated_at
FROM public.users
WHERE id = 'USER_ID'::uuid;  -- 👈 REPLACE WITH ACTUAL UUID

-- Query 3: List recent users with NULL subscription_status
-- Use this to find potentially stuck users (users who signed up but haven't been activated)
-- Useful when user email is unknown but you know approximate signup time
SELECT 
  id,
  email,
  name,
  created_at
FROM public.users
WHERE subscription_status IS NULL
ORDER BY created_at DESC
LIMIT 20;

-- Query 4: Show user's full profile (including roles)
-- Useful for verifying user identity before activation
SELECT 
  u.id,
  u.email,
  u.name,
  u.age,
  u.subscription_status,
  u.plan_type,
  u.subscription_end_date,
  u.created_at,
  u.updated_at,
  array_agg(ur.role) as roles
FROM public.users u
LEFT JOIN public.user_roles ur ON u.id = ur.user_id
WHERE u.email = 'USER_EMAIL'  -- 👈 REPLACE WITH ACTUAL EMAIL
GROUP BY u.id, u.email, u.name, u.age, u.subscription_status, u.plan_type, u.subscription_end_date, u.created_at, u.updated_at;

-- ============================================
-- SECTION 2: VERIFICATION (Before Activation)
-- ============================================

-- Step 1: Verify user exists and show current state
-- Run this BEFORE making any changes to confirm you have the right user
-- Replace 'USER_ID' with actual UUID from Query 1 or 2 above

BEGIN;

-- Show current subscription state
SELECT 
  id,
  email,
  name,
  subscription_status,
  plan_type,
  subscription_end_date,
  created_at,
  updated_at
FROM public.users
WHERE id = 'USER_ID'::uuid;  -- 👈 REPLACE WITH ACTUAL UUID

-- If no rows returned, user doesn't exist - STOP HERE and verify the user_id
-- If rows returned, verify:
--   1. Email matches the payment receipt
--   2. Name matches (if available)
--   3. Current subscription_status is NULL (or inactive)
--   4. created_at timestamp makes sense (user signed up before payment)

-- ============================================
-- SECTION 3: MANUAL ACTIVATION
-- ============================================

-- Step 2: Update subscription status
-- Replace all placeholders with actual values:
--   USER_ID: UUID from verification query above
--   SUBSCRIPTION_STATUS: 'active', 'trial', 'inactive', or 'past_due'
--   PLAN_TYPE: '6-month-pass', '12-month-pass', 'lifetime', etc.
--   SUBSCRIPTION_END_DATE: ISO format 'YYYY-MM-DD HH:MM:SS' or NULL for lifetime

-- IMPORTANT: Only run this UPDATE after verifying the user_id is correct!

UPDATE public.users
SET 
  subscription_status = 'SUBSCRIPTION_STATUS',  -- 👈 REPLACE: 'active', 'trial', 'inactive', 'past_due'
  plan_type = 'PLAN_TYPE',                      -- 👈 REPLACE: '6-month-pass', '12-month-pass', 'lifetime', etc.
  subscription_end_date = 'SUBSCRIPTION_END_DATE'::timestamp,  -- 👈 REPLACE: '2025-12-31 23:59:59' or NULL
  updated_at = NOW()
WHERE id = 'USER_ID'::uuid;  -- 👈 REPLACE WITH ACTUAL UUID

-- Step 3: Verify update succeeded
-- Run this immediately after the UPDATE to confirm the changes
SELECT 
  id,
  email,
  name,
  subscription_status,
  plan_type,
  subscription_end_date,
  updated_at
FROM public.users
WHERE id = 'USER_ID'::uuid;  -- 👈 REPLACE WITH ACTUAL UUID

-- If subscription_status is now 'active' or 'trial', activation succeeded
-- If subscription_status is still NULL, the UPDATE didn't work - check user_id

-- Step 4: Commit the transaction
-- Only commit if verification shows the update succeeded
COMMIT;

-- ============================================
-- SECTION 4: ROLLBACK (Emergency Only)
-- ============================================

-- If you made a mistake BEFORE committing:
-- Simply run: ROLLBACK;
-- This will undo all changes in the current transaction

-- If you already committed and need to undo:
-- Run this to reset subscription back to NULL:
-- BEGIN;
-- UPDATE public.users
-- SET 
--   subscription_status = NULL,
--   plan_type = NULL,
--   subscription_end_date = NULL,
--   updated_at = NOW()
-- WHERE id = 'USER_ID'::uuid;  -- 👈 REPLACE WITH ACTUAL UUID
-- COMMIT;

-- ============================================
-- SECTION 5: EXAMPLE USAGE
-- ============================================

-- Example 1: Activate lifetime plan for user
-- Step 1: Find user
-- SELECT id, email, name FROM users WHERE email = 'user@example.com';
-- Result: id = '123e4567-e89b-12d3-a456-426614174000'

-- Step 2: Verify current state
-- BEGIN;
-- SELECT * FROM users WHERE id = '123e4567-e89b-12d3-a456-426614174000'::uuid;
-- Result: subscription_status = NULL

-- Step 3: Activate
-- UPDATE users
-- SET subscription_status = 'active',
--     plan_type = 'lifetime',
--     subscription_end_date = NULL,
--     updated_at = NOW()
-- WHERE id = '123e4567-e89b-12d3-a456-426614174000'::uuid;

-- Step 4: Verify
-- SELECT * FROM users WHERE id = '123e4567-e89b-12d3-a456-426614174000'::uuid;
-- Result: subscription_status = 'active', plan_type = 'lifetime'

-- Step 5: Commit
-- COMMIT;

-- Example 2: Activate 6-month plan with end date
-- UPDATE users
-- SET subscription_status = 'active',
--     plan_type = '6-month-pass',
--     subscription_end_date = '2025-06-30 23:59:59'::timestamp,
--     updated_at = NOW()
-- WHERE id = '123e4567-e89b-12d3-a456-426614174000'::uuid;

-- ============================================
-- SECTION 6: SUBSCRIPTION STATUS VALUES
-- ============================================

-- Valid subscription_status values:
--   'active'     - User has active paid subscription
--   'trial'      - User is on trial period
--   'inactive'   - Subscription expired or cancelled
--   'past_due'   - Payment failed, subscription past due
--   NULL         - No subscription (free tier or not activated)

-- Valid plan_type values (examples):
--   'lifetime'       - Lifetime access (subscription_end_date = NULL)
--   '6-month-pass'   - 6-month subscription
--   '12-month-pass'  - 12-month subscription
--   'monthly'        - Monthly recurring subscription
--   'yearly'         - Yearly recurring subscription

-- subscription_end_date:
--   For lifetime plans: NULL
--   For time-limited plans: ISO timestamp 'YYYY-MM-DD HH:MM:SS'
--   Example: '2025-12-31 23:59:59'

-- ============================================
-- SECTION 7: SAFETY CHECKLIST
-- ============================================

-- Before running the UPDATE, verify:
-- [ ] User exists (Query 1 or 2 returned a row)
-- [ ] Email matches payment receipt
-- [ ] Name matches (if available on receipt)
-- [ ] Current subscription_status is NULL or 'inactive'
-- [ ] You have the correct subscription details from Lemon Squeezy:
--     [ ] subscription_status ('active' or 'trial')
--     [ ] plan_type (from order details)
--     [ ] subscription_end_date (from order details or calculate from plan_type)
-- [ ] You are connected to the correct database (production vs development)

-- After running the UPDATE, verify:
-- [ ] SELECT query shows updated subscription_status
-- [ ] subscription_status is 'active' or 'trial' (not NULL)
-- [ ] plan_type matches the order
-- [ ] subscription_end_date is correct (or NULL for lifetime)
-- [ ] updated_at timestamp is recent

-- Only COMMIT if all verifications pass!

