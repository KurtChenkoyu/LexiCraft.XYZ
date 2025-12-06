-- Migration: Unified User Model
-- Created: 2024
-- Description: Fresh start with unified user model (everyone is a user, roles via RBAC)
-- NOTE: This migration drops old tables and creates new schema from scratch
-- Only run this if you don't have production data to preserve!

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================
-- STEP 1: Drop old tables (if they exist)
-- ============================================
-- WARNING: This will delete all data in these tables!
DROP TABLE IF EXISTS relationship_discoveries CASCADE;
DROP TABLE IF EXISTS withdrawal_requests CASCADE;
DROP TABLE IF EXISTS points_transactions CASCADE;
DROP TABLE IF EXISTS points_accounts CASCADE;
DROP TABLE IF EXISTS verification_schedule CASCADE;
DROP TABLE IF EXISTS learning_progress CASCADE;
DROP TABLE IF EXISTS children CASCADE;

-- ============================================
-- STEP 2: Update users table (add age, email_confirmed, make password_hash optional)
-- ============================================
-- Update existing users table if it exists, or create new one
DO $$
BEGIN
    -- Add age column if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'users' AND column_name = 'age') THEN
        ALTER TABLE users ADD COLUMN age INTEGER;
    END IF;
    
    -- Add email_confirmed column if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'users' AND column_name = 'email_confirmed') THEN
        ALTER TABLE users ADD COLUMN email_confirmed BOOLEAN DEFAULT FALSE;
    END IF;
    
    -- Add email_confirmed_at column if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'users' AND column_name = 'email_confirmed_at') THEN
        ALTER TABLE users ADD COLUMN email_confirmed_at TIMESTAMP;
    END IF;
    
    -- Make password_hash optional (for Supabase Auth)
    IF EXISTS (SELECT 1 FROM information_schema.columns 
               WHERE table_name = 'users' AND column_name = 'password_hash' 
               AND is_nullable = 'NO') THEN
        ALTER TABLE users ALTER COLUMN password_hash DROP NOT NULL;
    END IF;
END $$;

-- Create users table if it doesn't exist
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT,  -- Optional (Supabase Auth handles passwords)
    name TEXT,
    phone TEXT,
    country TEXT DEFAULT 'TW',
    age INTEGER,  -- Can be NULL for adults
    email_confirmed BOOLEAN DEFAULT FALSE,
    email_confirmed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_email_confirmed ON users(email_confirmed);

-- ============================================
-- STEP 3: Create user_roles table (RBAC)
-- ============================================
CREATE TABLE IF NOT EXISTS user_roles (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role TEXT NOT NULL,  -- 'parent', 'learner', 'admin'
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, role)
);

CREATE INDEX IF NOT EXISTS idx_user_roles_user_id ON user_roles(user_id);
CREATE INDEX IF NOT EXISTS idx_user_roles_role ON user_roles(role);

-- ============================================
-- STEP 4: Create user_relationships table (generic for all relationship types)
-- ============================================
CREATE TABLE IF NOT EXISTS user_relationships (
    id SERIAL PRIMARY KEY,
    from_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    to_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    relationship_type TEXT NOT NULL,  -- 'parent_child', 'coach_student', 'sibling', 'friend', 'classmate', 'tutor_student'
    status TEXT DEFAULT 'active',  -- 'active', 'pending_approval', 'blocked', 'suspended'
    
    -- Permissions (what from_user can do for to_user)
    permissions JSONB DEFAULT '{
        "can_view_progress": false,
        "can_assign_work": false,
        "can_verify_learning": false,
        "can_withdraw": false,
        "can_manage_account": false,
        "can_view_financials": false
    }',
    
    -- Metadata (context-specific)
    metadata JSONB DEFAULT '{}',  -- e.g., {"class_name": "English 101", "subject": "vocabulary", "group_id": "..."}
    
    -- Approval tracking (for relationships requiring consent)
    requested_by UUID REFERENCES users(id),  -- Who requested this relationship
    approved_by UUID REFERENCES users(id),   -- Parent/admin who approved
    approved_at TIMESTAMP,
    rejection_reason TEXT,  -- If rejected
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(from_user_id, to_user_id, relationship_type),
    CHECK (from_user_id != to_user_id)
);

CREATE INDEX IF NOT EXISTS idx_user_relationships_from ON user_relationships(from_user_id);
CREATE INDEX IF NOT EXISTS idx_user_relationships_to ON user_relationships(to_user_id);
CREATE INDEX IF NOT EXISTS idx_user_relationships_type ON user_relationships(relationship_type);
CREATE INDEX IF NOT EXISTS idx_user_relationships_status ON user_relationships(status);

-- Set default permissions for parent_child relationships
-- This will be done via application logic, but we can add a trigger if needed

-- ============================================
-- STEP 5: Create learning_progress table (uses user_id)
-- ============================================
CREATE TABLE IF NOT EXISTS learning_progress (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,  -- Changed from child_id
    learning_point_id TEXT NOT NULL,  -- References Neo4j learning_point.id
    learned_at TIMESTAMP DEFAULT NOW(),
    tier INTEGER NOT NULL,
    status TEXT DEFAULT 'learning',  -- 'learning', 'pending', 'verified', 'failed'
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, learning_point_id, tier)
);

CREATE INDEX IF NOT EXISTS idx_learning_progress_user_id ON learning_progress(user_id);
CREATE INDEX IF NOT EXISTS idx_learning_progress_status ON learning_progress(status);
CREATE INDEX IF NOT EXISTS idx_learning_progress_learned_at ON learning_progress(learned_at);

-- ============================================
-- STEP 6: Create verification_schedule table (uses user_id)
-- ============================================
CREATE TABLE IF NOT EXISTS verification_schedule (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,  -- Changed from child_id
    learning_progress_id INTEGER NOT NULL REFERENCES learning_progress(id) ON DELETE CASCADE,
    test_day INTEGER NOT NULL,  -- 1, 3, or 7
    scheduled_date DATE NOT NULL,
    completed BOOLEAN DEFAULT FALSE,
    completed_at TIMESTAMP,
    passed BOOLEAN,
    score DECIMAL(5, 2),
    questions JSONB,
    answers JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_verification_schedule_user_id ON verification_schedule(user_id);
CREATE INDEX IF NOT EXISTS idx_verification_schedule_scheduled_date ON verification_schedule(scheduled_date);
CREATE INDEX IF NOT EXISTS idx_verification_schedule_completed ON verification_schedule(completed);

-- ============================================
-- STEP 7: Create points_accounts table (uses user_id)
-- ============================================
CREATE TABLE IF NOT EXISTS points_accounts (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,  -- Changed from child_id
    total_earned INTEGER DEFAULT 0,
    available_points INTEGER DEFAULT 0,
    locked_points INTEGER DEFAULT 0,
    withdrawn_points INTEGER DEFAULT 0,
    deficit_points INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_points_accounts_user_id ON points_accounts(user_id);

-- ============================================
-- STEP 8: Create points_transactions table (uses user_id)
-- ============================================
CREATE TABLE IF NOT EXISTS points_transactions (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,  -- Changed from child_id
    learning_progress_id INTEGER REFERENCES learning_progress(id),
    transaction_type TEXT NOT NULL,  -- 'earned', 'unlocked', 'withdrawn', 'deficit', 'bonus'
    bonus_type TEXT,  -- 'relationship_discovery', 'pattern_recognition', etc.
    points INTEGER NOT NULL,
    tier INTEGER,
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_points_transactions_user_id ON points_transactions(user_id);
CREATE INDEX IF NOT EXISTS idx_points_transactions_type ON points_transactions(transaction_type);
CREATE INDEX IF NOT EXISTS idx_points_transactions_created_at ON points_transactions(created_at);

-- ============================================
-- STEP 9: Create withdrawal_requests table (uses user_id for learner)
-- ============================================
CREATE TABLE IF NOT EXISTS withdrawal_requests (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,  -- Changed from child_id (the learner)
    parent_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,  -- The parent requesting
    amount_ntd DECIMAL(10,2) NOT NULL,
    points_amount INTEGER NOT NULL,
    status TEXT DEFAULT 'pending',  -- 'pending', 'processing', 'completed', 'failed'
    bank_account TEXT,
    transaction_id TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_withdrawal_requests_user_id ON withdrawal_requests(user_id);
CREATE INDEX IF NOT EXISTS idx_withdrawal_requests_parent_id ON withdrawal_requests(parent_id);
CREATE INDEX IF NOT EXISTS idx_withdrawal_requests_status ON withdrawal_requests(status);

-- ============================================
-- STEP 10: Create relationship_discoveries table (uses user_id)
-- ============================================
CREATE TABLE IF NOT EXISTS relationship_discoveries (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,  -- Changed from child_id
    source_learning_point_id TEXT NOT NULL,  -- Neo4j ID
    target_learning_point_id TEXT NOT NULL,  -- Neo4j ID
    relationship_type TEXT NOT NULL,
    discovered_at TIMESTAMP DEFAULT NOW(),
    bonus_awarded BOOLEAN DEFAULT FALSE,
    UNIQUE(user_id, source_learning_point_id, target_learning_point_id, relationship_type)
);

CREATE INDEX IF NOT EXISTS idx_relationship_discoveries_user_id ON relationship_discoveries(user_id);
CREATE INDEX IF NOT EXISTS idx_relationship_discoveries_source ON relationship_discoveries(source_learning_point_id);

-- ============================================
-- STEP 11: Helper function to check if user is parent of another user
-- ============================================
CREATE OR REPLACE FUNCTION is_parent_of(parent_user_id UUID, child_user_id UUID)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1 FROM user_relationships
        WHERE from_user_id = parent_user_id 
          AND to_user_id = child_user_id 
          AND relationship_type = 'parent_child'
          AND status = 'active'
    );
END;
$$ LANGUAGE plpgsql STABLE;

-- ============================================
-- STEP 12: Helper function to get user's roles
-- ============================================
CREATE OR REPLACE FUNCTION get_user_roles(user_uuid UUID)
RETURNS TEXT[] AS $$
BEGIN
    RETURN ARRAY(
        SELECT role FROM user_roles WHERE user_id = user_uuid
    );
END;
$$ LANGUAGE plpgsql STABLE;

-- ============================================
-- Migration Complete
-- ============================================
-- All tables now use unified user model:
-- - users: Everyone is a user (parent, child, or learner)
-- - user_roles: RBAC for flexible role management
-- - user_relationships: Generic relationships table (parent_child, coach_student, etc.)
-- - All learning data uses user_id (the learner)

