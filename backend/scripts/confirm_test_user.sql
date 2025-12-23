-- Script: Confirm Test User Email
-- Purpose: Manually confirm email for test users (fake emails that can't receive confirmation links)
-- Usage: Run in Supabase SQL Editor

-- Option 1: Confirm a specific user by email
UPDATE auth.users
SET 
  email_confirmed_at = NOW(),
  email_confirmed = true
WHERE email = '554rrttg@gmail.com';

-- Option 2: Confirm all unconfirmed users (use with caution!)
-- UPDATE auth.users
-- SET 
--   email_confirmed_at = COALESCE(email_confirmed_at, NOW()),
--   email_confirmed = true
-- WHERE email_confirmed_at IS NULL;

-- Verify the update
SELECT 
  id,
  email,
  email_confirmed,
  email_confirmed_at,
  created_at
FROM auth.users
WHERE email = '554rrttg@gmail.com';

-- The trigger should automatically sync this to public.users table
-- Verify sync:
SELECT 
  id,
  email,
  email_confirmed,
  email_confirmed_at
FROM public.users
WHERE email = '554rrttg@gmail.com';

