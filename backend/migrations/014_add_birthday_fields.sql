-- Migration: Add birthday fields to users table
-- For birthday celebration feature (optional, can only edit 3 times)

-- Add birthday columns
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS birth_month INTEGER,
ADD COLUMN IF NOT EXISTS birth_day INTEGER,
ADD COLUMN IF NOT EXISTS birthday_edit_count INTEGER DEFAULT 0 NOT NULL;

-- Add constraints for valid month/day values
ALTER TABLE users 
ADD CONSTRAINT IF NOT EXISTS check_birth_month CHECK (birth_month IS NULL OR (birth_month >= 1 AND birth_month <= 12)),
ADD CONSTRAINT IF NOT EXISTS check_birth_day CHECK (birth_day IS NULL OR (birth_day >= 1 AND birth_day <= 31));

-- Comment
COMMENT ON COLUMN users.birth_month IS 'Birth month (1-12) - optional, for birthday celebrations';
COMMENT ON COLUMN users.birth_day IS 'Birth day (1-31) - optional, for birthday celebrations';
COMMENT ON COLUMN users.birthday_edit_count IS 'Number of times birthday has been edited (max 3 allowed)';

