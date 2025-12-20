-- ============================================
-- Migration: Migrate XP System to Learner-Scoped
-- Created: 2025-01
-- Description: Moves XP from user_id to learner_id to align with progress/inventory system
-- ============================================

-- ============================================
-- PART 1: Add learner_id columns (nullable initially)
-- ============================================

-- Step 1: Add learner_id columns (nullable for now, will be populated by backfill script)
ALTER TABLE user_xp 
ADD COLUMN IF NOT EXISTS learner_id UUID REFERENCES public.learners(id) ON DELETE CASCADE;

ALTER TABLE xp_history 
ADD COLUMN IF NOT EXISTS learner_id UUID REFERENCES public.learners(id) ON DELETE CASCADE;

-- Step 2: Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_user_xp_learner ON user_xp(learner_id);
CREATE INDEX IF NOT EXISTS idx_xp_history_learner ON xp_history(learner_id);
CREATE INDEX IF NOT EXISTS idx_xp_history_learner_date ON xp_history(learner_id, earned_at);

-- Note: Backfill will be done by Python script (see Part 2: backend/scripts/backfill_xp_to_learners.py)
-- After backfill completes, run Part 3 to make columns NOT NULL and update PK

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

-- Step 5: Update xp_history to use learner_id in queries (user_id kept for reference)
-- Note: user_id column remains for audit trail, but queries use learner_id

-- ============================================
-- PART 3B: Update Database Functions
-- ============================================

-- Update initialize_user_xp to use learner_id (deprecated - replaced by Python _ensure_learner_xp)
-- Keeping for backward compatibility but marking as deprecated
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
-- Note: This function may be deprecated if leaderboard logic moves to Python
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
    -- This is a temporary bridge - should be updated to accept learner_id directly
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
    
    -- Update or insert leaderboard entry (still uses user_id for now - may need separate migration)
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

