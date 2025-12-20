-- ============================================
-- Migration: Add performance indexes for learning_progress queries
-- Created: 2024-12-21
-- Description: Add composite indexes to speed up activity summary queries
--              that filter by user_id, status, and date ranges
-- ============================================

-- Index for get_words_learned_period queries
-- Filters by user_id, status='verified', and date range on learned_at
CREATE INDEX IF NOT EXISTS idx_learning_progress_user_status_date 
ON public.learning_progress(user_id, status, learned_at)
WHERE status = 'verified';

-- Index for calculate_activity_streak queries
-- Filters by user_id and learned_at (90-day window)
-- Using learned_at directly (not DATE()) for better index usage
CREATE INDEX IF NOT EXISTS idx_learning_progress_user_learned_at_desc 
ON public.learning_progress(user_id, learned_at DESC);

-- Index for get_activity_summary last_active_date query
-- Simple index on user_id and learned_at for MAX() queries
CREATE INDEX IF NOT EXISTS idx_learning_progress_user_learned_at_max 
ON public.learning_progress(user_id, learned_at DESC NULLS LAST);

-- Verify indexes were created
-- SELECT indexname, indexdef 
-- FROM pg_indexes 
-- WHERE tablename = 'learning_progress' 
--   AND schemaname = 'public'
--   AND indexname LIKE 'idx_learning_progress_user%';

