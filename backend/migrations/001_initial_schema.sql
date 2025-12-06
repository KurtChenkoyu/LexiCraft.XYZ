-- Migration: Initial Schema for LexiCraft MVP
-- Created: 2024
-- Description: Creates all tables, indexes, and constraints for PostgreSQL user data

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. Users table (Parents)
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    name TEXT,
    phone TEXT,
    country TEXT DEFAULT 'TW',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- 2. Children table
CREATE TABLE IF NOT EXISTS children (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    parent_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    age INTEGER,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_children_parent_id ON children(parent_id);

-- 3. Learning Progress table
CREATE TABLE IF NOT EXISTS learning_progress (
    id SERIAL PRIMARY KEY,
    child_id UUID NOT NULL REFERENCES children(id) ON DELETE CASCADE,
    learning_point_id TEXT NOT NULL, -- References Neo4j learning_point.id
    learned_at TIMESTAMP DEFAULT NOW(),
    tier INTEGER NOT NULL,
    status TEXT DEFAULT 'learning', -- 'learning', 'pending', 'verified', 'failed'
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(child_id, learning_point_id, tier)
);

CREATE INDEX IF NOT EXISTS idx_learning_progress_child_id ON learning_progress(child_id);
CREATE INDEX IF NOT EXISTS idx_learning_progress_status ON learning_progress(status);
CREATE INDEX IF NOT EXISTS idx_learning_progress_learned_at ON learning_progress(learned_at);

-- 4. Verification Schedule table
CREATE TABLE IF NOT EXISTS verification_schedule (
    id SERIAL PRIMARY KEY,
    child_id UUID NOT NULL REFERENCES children(id) ON DELETE CASCADE,
    learning_progress_id INTEGER NOT NULL REFERENCES learning_progress(id) ON DELETE CASCADE,
    test_day INTEGER NOT NULL, -- 1, 3, or 7
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

CREATE INDEX IF NOT EXISTS idx_verification_schedule_child_id ON verification_schedule(child_id);
CREATE INDEX IF NOT EXISTS idx_verification_schedule_scheduled_date ON verification_schedule(scheduled_date);
CREATE INDEX IF NOT EXISTS idx_verification_schedule_completed ON verification_schedule(completed);

-- 5. Points Accounts table
CREATE TABLE IF NOT EXISTS points_accounts (
    id SERIAL PRIMARY KEY,
    child_id UUID NOT NULL UNIQUE REFERENCES children(id) ON DELETE CASCADE,
    total_earned INTEGER DEFAULT 0,
    available_points INTEGER DEFAULT 0,
    locked_points INTEGER DEFAULT 0,
    withdrawn_points INTEGER DEFAULT 0,
    deficit_points INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_points_accounts_child_id ON points_accounts(child_id);

-- 6. Points Transactions table
CREATE TABLE IF NOT EXISTS points_transactions (
    id SERIAL PRIMARY KEY,
    child_id UUID NOT NULL REFERENCES children(id) ON DELETE CASCADE,
    learning_progress_id INTEGER REFERENCES learning_progress(id),
    transaction_type TEXT NOT NULL, -- 'earned', 'unlocked', 'withdrawn', 'deficit', 'bonus'
    bonus_type TEXT, -- 'relationship_discovery', 'pattern_recognition', etc.
    points INTEGER NOT NULL,
    tier INTEGER,
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_points_transactions_child_id ON points_transactions(child_id);
CREATE INDEX IF NOT EXISTS idx_points_transactions_type ON points_transactions(transaction_type);
CREATE INDEX IF NOT EXISTS idx_points_transactions_created_at ON points_transactions(created_at);

-- 7. Withdrawal Requests table
CREATE TABLE IF NOT EXISTS withdrawal_requests (
    id SERIAL PRIMARY KEY,
    child_id UUID NOT NULL REFERENCES children(id) ON DELETE CASCADE,
    parent_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    amount_ntd DECIMAL(10,2) NOT NULL,
    points_amount INTEGER NOT NULL,
    status TEXT DEFAULT 'pending', -- 'pending', 'processing', 'completed', 'failed'
    bank_account TEXT,
    transaction_id TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_withdrawal_requests_child_id ON withdrawal_requests(child_id);
CREATE INDEX IF NOT EXISTS idx_withdrawal_requests_parent_id ON withdrawal_requests(parent_id);
CREATE INDEX IF NOT EXISTS idx_withdrawal_requests_status ON withdrawal_requests(status);

-- 8. Relationship Discoveries table
CREATE TABLE IF NOT EXISTS relationship_discoveries (
    id SERIAL PRIMARY KEY,
    child_id UUID NOT NULL REFERENCES children(id) ON DELETE CASCADE,
    source_learning_point_id TEXT NOT NULL, -- Neo4j ID
    target_learning_point_id TEXT NOT NULL, -- Neo4j ID
    relationship_type TEXT NOT NULL,
    discovered_at TIMESTAMP DEFAULT NOW(),
    bonus_awarded BOOLEAN DEFAULT FALSE,
    UNIQUE(child_id, source_learning_point_id, target_learning_point_id, relationship_type)
);

CREATE INDEX IF NOT EXISTS idx_relationship_discoveries_child_id ON relationship_discoveries(child_id);
CREATE INDEX IF NOT EXISTS idx_relationship_discoveries_source ON relationship_discoveries(source_learning_point_id);

