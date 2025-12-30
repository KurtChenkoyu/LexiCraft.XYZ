-- ============================================
-- Fix Billing Customer ID
-- 
-- Purpose: Manually update billing_customer_id for a user
--          when the simulation script used a fake ID
-- 
-- Usage:
--   1. Get the REAL customer_id from Lemon Squeezy Dashboard:
--      - Go to https://app.lemonsqueezy.com/orders
--      - Find your test order
--      - Click on the order to view details
--      - Copy the "Customer ID" (usually a number like 345678)
--   2. Replace 'REPLACE_WITH_REAL_CUSTOMER_ID' below with the actual ID
--   3. Replace 'chenkoyu@gmail.com' with the user's email if different
--   4. Run this script in Supabase SQL Editor
-- ============================================

-- Step 1: Verify current state
SELECT 
  id,
  email,
  billing_customer_id,
  subscription_status,
  plan_type
FROM public.users
WHERE email = 'chenkoyu@gmail.com';

-- Step 2: Update with REAL customer ID from Lemon Squeezy
-- Customer ID found: 7430846 (for chenkoyu@gmail.com)
UPDATE public.users 
SET 
  billing_customer_id = '7430846',
  updated_at = NOW()
WHERE email = 'chenkoyu@gmail.com';

-- Alternative: Update by user ID if email doesn't work
-- UPDATE public.users 
-- SET 
--   billing_customer_id = '7430846',
--   updated_at = NOW()
-- WHERE id = 'a1f68c67-2c2d-45be-9aac-038bf23dd5bd'::uuid;

-- Step 3: Verify the update
SELECT 
  id,
  email,
  billing_customer_id,
  subscription_status,
  plan_type,
  updated_at
FROM public.users
WHERE email = 'chenkoyu@gmail.com';

