-- Migration: Add email_confirmed_at column if missing
-- Created: 2024
-- Description: Adds email_confirmed_at column to users table if it doesn't exist

-- Add email_confirmed_at column if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'users' AND column_name = 'email_confirmed_at'
    ) THEN
        ALTER TABLE users ADD COLUMN email_confirmed_at TIMESTAMP;
        RAISE NOTICE 'Added email_confirmed_at column to users table';
    ELSE
        RAISE NOTICE 'email_confirmed_at column already exists';
    END IF;
END $$;

