-- ============================================
-- Migration: Add subscription fields to users table
-- Created: 2024-12
-- Description: Add subscription_status, plan_type, and subscription_end_date columns
--              to track Lemon Squeezy subscription lifecycle and access control
-- ============================================

-- Add subscription_status column
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS subscription_status TEXT;

-- Add plan_type column
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS plan_type TEXT;

-- Add subscription_end_date column
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS subscription_end_date TIMESTAMP;

-- Create index on subscription_status for fast lookups (gate checks)
CREATE INDEX IF NOT EXISTS idx_users_subscription_status 
ON users(subscription_status) 
WHERE subscription_status IS NOT NULL;

-- Add comments for documentation
COMMENT ON COLUMN users.subscription_status IS 'Subscription status: active, inactive, trial, past_due, or NULL (free tier)';
COMMENT ON COLUMN users.plan_type IS 'Plan type: 6-month-pass, 12-month-pass, etc.';
COMMENT ON COLUMN users.subscription_end_date IS 'When subscription expires - shows parents how much time is left to verify building blocks';

