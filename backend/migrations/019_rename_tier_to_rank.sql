-- ============================================
-- Migration: Rename Tier to Rank
-- Created: 2025-12-20
-- Description: Renames "tier" terminology to "rank" for word complexity categories
--              to distinguish from cache tiers and align with gaming conventions.
--              "Rank" = Word complexity (1-7), "Tier" = Cache layers (Tier 1-3)
-- ============================================

-- ============================================
-- PART 1: Rename Column in learning_progress
-- ============================================

-- Step 1: Rename the column
ALTER TABLE public.learning_progress 
RENAME COLUMN tier TO rank;

-- ============================================
-- PART 2: Update Unique Constraints and Indexes
-- ============================================

-- Step 2: Drop existing unique indexes that reference tier
DROP INDEX IF EXISTS uq_learner_learning_point_tier;
DROP INDEX IF EXISTS uq_user_learning_point_tier_legacy;

-- Step 3: Recreate unique indexes with rank
-- For rows where learner_id IS NOT NULL, enforce uniqueness per learner
CREATE UNIQUE INDEX IF NOT EXISTS uq_learner_learning_point_rank 
ON public.learning_progress(learner_id, learning_point_id, rank)
WHERE learner_id IS NOT NULL;

-- For legacy rows (learner_id IS NULL), keep a constraint on (user_id, learning_point_id, rank)
CREATE UNIQUE INDEX IF NOT EXISTS uq_user_learning_point_rank_legacy
ON public.learning_progress(user_id, learning_point_id, rank)
WHERE learner_id IS NULL;

-- ============================================
-- PART 3: Update Functions
-- ============================================

-- Step 4: Rename the tier_to_frequency_band function
-- Drop the old function and create a new one with rank
DROP FUNCTION IF EXISTS tier_to_frequency_band(INTEGER);

CREATE OR REPLACE FUNCTION rank_to_frequency_band(rank INTEGER)
RETURNS INTEGER AS $$
BEGIN
    -- Mapping: rank 1 → 1000, rank 2 → 2000, etc.
    -- Ranks 1-7 map to bands 1000-7000
    -- Rank 8+ maps to band 8000
    RETURN LEAST(rank, 8) * 1000;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

COMMENT ON FUNCTION rank_to_frequency_band IS 'Maps learning_progress rank (1-8) to frequency band (1000-8000)';

-- ============================================
-- PART 4: Update learning_point table (if it has tier column)
-- ============================================

-- Step 5: Check if learning_point table has tier column and rename it
-- Note: This may not exist depending on schema version
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_schema = 'public' 
        AND table_name = 'learning_point' 
        AND column_name = 'tier'
    ) THEN
        ALTER TABLE public.learning_point RENAME COLUMN tier TO rank;
    END IF;
END $$;

-- ============================================
-- PART 5: Verify Migration
-- ============================================

-- Uncomment to verify:
-- SELECT column_name, data_type 
-- FROM information_schema.columns 
-- WHERE table_schema = 'public' 
--   AND table_name = 'learning_progress' 
--   AND column_name IN ('tier', 'rank');
--
-- SELECT indexname, indexdef 
-- FROM pg_indexes 
-- WHERE tablename = 'learning_progress' 
--   AND indexname LIKE '%rank%';

