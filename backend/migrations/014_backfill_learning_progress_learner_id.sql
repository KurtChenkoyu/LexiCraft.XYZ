-- ============================================
-- Migration: Backfill learning_progress.learner_id
-- Created: 2024-12
-- Description: Fixes orphaned learning_progress entries that have user_id but NULL learner_id
-- ============================================

-- Backfill learner_id for all orphaned entries
-- Maps learning_progress.user_id -> learners.id via learners.user_id
UPDATE public.learning_progress lp
SET learner_id = l.id
FROM public.learners l
WHERE lp.learner_id IS NULL     -- Only fix missing ones
  AND lp.user_id = l.user_id   -- Link by User ID
  AND l.is_parent_profile = true;  -- Only parent profiles (children handled separately if needed)

-- Verify: Count remaining orphaned entries (should be 0 or very few)
-- SELECT COUNT(*) FROM public.learning_progress WHERE learner_id IS NULL;

