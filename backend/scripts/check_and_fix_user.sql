-- Script to check and fix user records
-- Run this in Supabase SQL Editor

-- Step 1: Check if trigger exists
SELECT 
  trigger_name,
  event_manipulation,
  event_object_table,
  action_statement
FROM information_schema.triggers
WHERE trigger_name = 'on_auth_user_created';

-- Step 2: Check if function exists
SELECT 
  routine_name,
  routine_type
FROM information_schema.routines
WHERE routine_name = 'handle_new_user';

-- Step 3: Find users in auth.users but not in public.users
SELECT 
  au.id,
  au.email,
  au.email_confirmed,
  au.created_at as auth_created_at,
  CASE WHEN pu.id IS NULL THEN 'MISSING' ELSE 'EXISTS' END as public_user_status
FROM auth.users au
LEFT JOIN public.users pu ON au.id = pu.id
ORDER BY au.created_at DESC
LIMIT 10;

-- Step 4: Fix missing users (run this for each missing user)
-- Replace USER_ID and EMAIL with actual values from Step 3
/*
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
WHERE au.id = 'USER_ID_HERE'
  AND NOT EXISTS (SELECT 1 FROM public.users WHERE id = au.id)
ON CONFLICT (id) DO NOTHING;

-- Add default learner role
INSERT INTO public.user_roles (user_id, role, created_at)
VALUES ('USER_ID_HERE', 'learner', NOW())
ON CONFLICT (user_id, role) DO NOTHING;
*/

-- Step 5: Verify trigger is working (test by checking recent signups)
SELECT 
  au.id,
  au.email,
  au.created_at as auth_created_at,
  pu.created_at as public_created_at,
  CASE 
    WHEN pu.id IS NULL THEN '❌ Trigger failed'
    WHEN pu.created_at - au.created_at > INTERVAL '5 seconds' THEN '⚠️ Delayed'
    ELSE '✅ OK'
  END as status
FROM auth.users au
LEFT JOIN public.users pu ON au.id = pu.id
WHERE au.created_at > NOW() - INTERVAL '1 day'
ORDER BY au.created_at DESC;

