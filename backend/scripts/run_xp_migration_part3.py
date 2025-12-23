#!/usr/bin/env python3
"""
Run Part 3 of XP migration (finalize constraints).

This makes learner_id NOT NULL and updates the primary key.
ONLY run this AFTER the backfill script has completed successfully.

Usage:
    python scripts/run_xp_migration_part3.py
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import psycopg2
from urllib.parse import urlparse, unquote

# Load .env file
backend_dir = Path(__file__).parent.parent
env_path = backend_dir / '.env'
load_dotenv(env_path)

# Get DATABASE_URL
db_url = os.getenv('DATABASE_URL')
if not db_url:
    print("❌ DATABASE_URL not found in .env")
    sys.exit(1)

# Parse connection string
parsed = urlparse(db_url)
port = 5432 if parsed.port == 6543 else (parsed.port or 5432)
conn_params = {
    'host': parsed.hostname,
    'port': port,
    'database': parsed.path.lstrip('/'),
    'user': unquote(parsed.username) if parsed.username else None,
    'password': unquote(parsed.password) if parsed.password else None,
}

print("=" * 60)
print("XP Migration Part 3: Finalize Constraints")
print("=" * 60)
print(f"Database: {conn_params['database']}@{conn_params['host']}:{conn_params['port']}")
print()
print("⚠️  WARNING: This will make learner_id NOT NULL and change the primary key.")
print("   Make sure the backfill script has completed successfully!")
print()

# Ask for confirmation
response = input("Continue? (yes/no): ")
if response.lower() != 'yes':
    print("❌ Migration cancelled")
    sys.exit(0)

# Part 3 SQL (constraints and function updates)
part3_sql = """
-- ============================================
-- PART 3: Finalize Migration (Run AFTER backfill script completes)
-- ============================================

-- Step 1: Drop old primary key constraint
ALTER TABLE user_xp DROP CONSTRAINT IF EXISTS user_xp_pkey;

-- Step 2: Make learner_id NOT NULL (backfill must be complete)
ALTER TABLE user_xp 
ALTER COLUMN learner_id SET NOT NULL;

ALTER TABLE xp_history 
ALTER COLUMN learner_id SET NOT NULL;

-- Step 3: Create new primary key on learner_id
ALTER TABLE user_xp 
ADD PRIMARY KEY (learner_id);

-- Step 4: Drop old user_id index (no longer needed as PK)
DROP INDEX IF EXISTS idx_user_xp_user;

-- ============================================
-- PART 3B: Update Database Functions
-- ============================================

-- Update initialize_user_xp to use learner_id (deprecated - replaced by Python _ensure_learner_xp)
CREATE OR REPLACE FUNCTION initialize_user_xp(p_user_id UUID)
RETURNS VOID AS $$
BEGIN
    -- This function is deprecated. Use LevelService._ensure_learner_xp(learner_id) instead.
    -- Keeping for backward compatibility only.
    RAISE NOTICE 'initialize_user_xp is deprecated. Use learner-scoped XP functions instead.';
END;
$$ LANGUAGE plpgsql;

-- Create new learner-scoped initialization function
CREATE OR REPLACE FUNCTION initialize_learner_xp(p_learner_id UUID)
RETURNS VOID AS $$
BEGIN
    INSERT INTO user_xp (learner_id, total_xp, current_level, xp_to_next_level, xp_in_current_level, updated_at)
    VALUES (p_learner_id, 0, 1, 100, 0, NOW())
    ON CONFLICT (learner_id) DO NOTHING;
END;
$$ LANGUAGE plpgsql;

-- Update update_leaderboard_entry to use learner_id
CREATE OR REPLACE FUNCTION update_leaderboard_entry(p_user_id UUID)
RETURNS VOID AS $$
DECLARE
    v_learner_id UUID;
    v_weekly_xp INT;
    v_monthly_xp INT;
    v_all_time_xp INT;
    v_weekly_words INT;
    v_monthly_words INT;
    v_longest_streak INT;
    v_current_streak INT;
BEGIN
    -- Get learner_id from user_id (assumes one learner per user for now)
    SELECT id INTO v_learner_id
    FROM public.learners
    WHERE user_id = p_user_id OR guardian_id = p_user_id
    LIMIT 1;
    
    IF v_learner_id IS NULL THEN
        RAISE NOTICE 'No learner found for user_id: %', p_user_id;
        RETURN;
    END IF;
    
    -- Calculate weekly XP (last 7 days) - now using learner_id
    SELECT COALESCE(SUM(xp_amount), 0) INTO v_weekly_xp
    FROM xp_history
    WHERE learner_id = v_learner_id
    AND earned_at >= NOW() - INTERVAL '7 days';
    
    -- Calculate monthly XP (last 30 days)
    SELECT COALESCE(SUM(xp_amount), 0) INTO v_monthly_xp
    FROM xp_history
    WHERE learner_id = v_learner_id
    AND earned_at >= NOW() - INTERVAL '30 days';
    
    -- Get all-time XP - now using learner_id
    SELECT COALESCE(total_xp, 0) INTO v_all_time_xp
    FROM user_xp
    WHERE learner_id = v_learner_id;
    
    -- Calculate weekly words learned - now using learner_id
    SELECT COUNT(*) INTO v_weekly_words
    FROM learning_progress
    WHERE learner_id = v_learner_id
    AND status = 'verified'
    AND learned_at >= NOW() - INTERVAL '7 days';
    
    -- Calculate monthly words learned
    SELECT COUNT(*) INTO v_monthly_words
    FROM learning_progress
    WHERE learner_id = v_learner_id
    AND status = 'verified'
    AND learned_at >= NOW() - INTERVAL '30 days';
    
    -- Get streak info (simplified version)
    SELECT COALESCE(MAX(activity_streak_days), 0) INTO v_longest_streak
    FROM (
        SELECT COUNT(DISTINCT DATE(learned_at)) as activity_streak_days
        FROM learning_progress
        WHERE learner_id = v_learner_id
        AND learned_at >= NOW() - INTERVAL '90 days'
        GROUP BY DATE(learned_at)
    ) sub;
    
    -- Update or insert leaderboard entry (still uses user_id for now)
    INSERT INTO leaderboard_entries (
        user_id, weekly_xp, monthly_xp, all_time_xp,
        weekly_words, monthly_words, longest_streak, current_streak, updated_at
    )
    VALUES (
        p_user_id, v_weekly_xp, v_monthly_xp, v_all_time_xp,
        v_weekly_words, v_monthly_words, v_longest_streak, v_longest_streak, NOW()
    )
    ON CONFLICT (user_id) DO UPDATE SET
        weekly_xp = EXCLUDED.weekly_xp,
        monthly_xp = EXCLUDED.monthly_xp,
        all_time_xp = EXCLUDED.all_time_xp,
        weekly_words = EXCLUDED.weekly_words,
        monthly_words = EXCLUDED.monthly_words,
        longest_streak = EXCLUDED.longest_streak,
        current_streak = EXCLUDED.current_streak,
        updated_at = NOW();
END;
$$ LANGUAGE plpgsql;

-- Update has_unlock to use learner_id
CREATE OR REPLACE FUNCTION has_unlock(p_user_id UUID, p_unlock_code VARCHAR(50))
RETURNS BOOLEAN AS $$
DECLARE
    v_learner_id UUID;
    v_user_level INT;
    v_required_level INT;
BEGIN
    -- Get learner_id from user_id (assumes one learner per user for now)
    SELECT id INTO v_learner_id
    FROM public.learners
    WHERE user_id = p_user_id OR guardian_id = p_user_id
    LIMIT 1;
    
    IF v_learner_id IS NULL THEN
        RETURN FALSE;
    END IF;
    
    -- Get user's current level - now using learner_id
    SELECT current_level INTO v_user_level
    FROM user_xp
    WHERE learner_id = v_learner_id;
    
    IF v_user_level IS NULL THEN
        v_user_level := 1;
    END IF;
    
    -- Get required level for this unlock
    SELECT level INTO v_required_level
    FROM level_unlocks
    WHERE unlock_code = p_unlock_code;
    
    IF v_required_level IS NULL THEN
        RETURN FALSE;  -- Unknown unlock code
    END IF;
    
    RETURN v_user_level >= v_required_level;
END;
$$ LANGUAGE plpgsql;

-- Add comments
COMMENT ON FUNCTION initialize_learner_xp IS 'Initializes XP record for a learner (replaces initialize_user_xp)';
COMMENT ON FUNCTION initialize_user_xp IS 'DEPRECATED: Use initialize_learner_xp or LevelService._ensure_learner_xp instead';
"""

try:
    # Connect and run migration
    print("🔌 Connecting to database...")
    conn = psycopg2.connect(**conn_params)
    conn.autocommit = True
    cursor = conn.cursor()
    
    print("✅ Connected to database")
    print("🚀 Executing Part 3 migration...")
    print("   Making learner_id NOT NULL and updating primary key...")
    
    # Execute the SQL
    cursor.execute(part3_sql)
    
    print()
    print("✅ Part 3 migration completed successfully!")
    print()
    print("Changes applied:")
    print("  ✓ Made learner_id NOT NULL in user_xp and xp_history")
    print("  ✓ Updated primary key to use learner_id")
    print("  ✓ Updated database functions to use learner_id")
    print()
    print("🎉 Migration complete! The XP system is now learner-scoped.")
    
    cursor.close()
    conn.close()
    
except psycopg2.OperationalError as e:
    print(f"❌ Connection error: {e}")
    print()
    print("💡 Tip: If using Supabase connection pooler (port 6543),")
    print("   try using the direct connection port (5432) instead.")
    sys.exit(1)
except Exception as e:
    print(f"❌ Migration failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)


