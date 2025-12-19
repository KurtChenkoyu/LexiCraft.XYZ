-- ============================================
-- Migration: Add index on learning_progress.learner_id and status
-- Created: 2024-12
-- Description: Speed up learner progress queries to prevent 60s timeouts
-- ============================================

-- Speed up learner progress queries
-- This index helps queries that filter by learner_id and status
CREATE INDEX IF NOT EXISTS idx_learning_progress_learner_id_status 
ON public.learning_progress(learner_id, status);

-- Also add a single-column index on learner_id for general lookups
CREATE INDEX IF NOT EXISTS idx_learning_progress_learner_id 
ON public.learning_progress(learner_id);

-- Verify indexes were created
-- SELECT indexname, indexdef 
-- FROM pg_indexes 
-- WHERE tablename = 'learning_progress' AND schemaname = 'public';

