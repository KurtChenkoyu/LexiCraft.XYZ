-- Migration: Email Confirmation Tracking
-- Created: 2024-12-04
-- Description: Adds email confirmation tracking to users table

-- Add email confirmation fields to users table
ALTER TABLE users 
  ADD COLUMN IF NOT EXISTS email_confirmed BOOLEAN DEFAULT FALSE,
  ADD COLUMN IF NOT EXISTS email_confirmed_at TIMESTAMP;

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_users_email_confirmed ON users(email_confirmed);

-- Update existing users to mark as confirmed if they have verified email in Supabase Auth
-- (This is a one-time migration for existing users)
UPDATE users u
SET 
  email_confirmed = COALESCE(
    (SELECT email_confirmed FROM auth.users WHERE id = u.id),
    FALSE
  ),
  email_confirmed_at = CASE 
    WHEN (SELECT email_confirmed FROM auth.users WHERE id = u.id) = TRUE 
    THEN u.created_at 
    ELSE NULL 
  END
WHERE EXISTS (SELECT 1 FROM auth.users WHERE id = u.id);

-- Note: Future email confirmations will be tracked via Supabase Auth webhook
-- or by checking auth.users.email_confirmed status


