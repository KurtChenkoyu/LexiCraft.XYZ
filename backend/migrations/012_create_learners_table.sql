-- ============================================
-- Migration: Create Learners Table for Multi-Profile Support
-- Created: 2024-12
-- Description: Separates Authentication (auth.users) from Gameplay (public.learners)
--              Enables parent-child switching and future account migration
-- ============================================

-- Safety Check: Verify auth.users exists
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'auth' AND table_name = 'users') THEN
    RAISE EXCEPTION 'auth.users table does not exist. Ensure Supabase Auth is set up.';
  END IF;
END $$;

-- 1. Create the 'learners' table (The Gameplay Identity)
CREATE TABLE IF NOT EXISTS public.learners (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
  
  -- LINKING STRATEGY
  -- user_id: If this profile logs in (Parent or independent child), links to Auth. NULL for managed children.
  user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
  
  -- guardian_id: Who manages this profile? (The Parent's Auth ID). 
  -- Crucial for "Get My Children" queries and foreign key integrity.
  guardian_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
  
  -- Profile Props (Emoji MVP)
  display_name TEXT NOT NULL,
  avatar_emoji TEXT DEFAULT '🦄', 
  age_group TEXT, -- '3-5', '6-8', '9-12', etc.
  
  -- Flags
  is_parent_profile BOOLEAN DEFAULT FALSE,
  is_independent BOOLEAN DEFAULT FALSE, -- True if learner has their own account (future migration)
  settings JSONB DEFAULT '{}'::jsonb
);

-- 2. Performance Indexes (For fast switching and queries)
CREATE INDEX IF NOT EXISTS idx_learners_guardian ON public.learners(guardian_id);
CREATE INDEX IF NOT EXISTS idx_learners_user ON public.learners(user_id);
CREATE INDEX IF NOT EXISTS idx_learners_is_parent ON public.learners(is_parent_profile);

-- 3. Backfill: Create a Learner Profile for every existing Parent
-- We assume every current User is a Parent managing themselves.
-- This ensures no one loses access during migration.
INSERT INTO public.learners (user_id, guardian_id, display_name, avatar_emoji, is_parent_profile)
SELECT 
  au.id as user_id, 
  au.id as guardian_id,
  COALESCE(
    au.raw_user_meta_data->>'full_name',
    au.raw_user_meta_data->>'name',
    pu.name,
    au.email,
    'Parent'
  ) as display_name,
  '👑' as avatar_emoji,
  true as is_parent_profile
FROM auth.users au
LEFT JOIN public.users pu ON au.id = pu.id
WHERE NOT EXISTS (
  SELECT 1 FROM public.learners WHERE user_id = au.id
)
ON CONFLICT DO NOTHING;

-- 4. Enable RLS (Row Level Security) for Supabase
ALTER TABLE public.learners ENABLE ROW LEVEL SECURITY;

-- Policy: A User can view/edit any learner they are the GUARDIAN of.
DROP POLICY IF EXISTS "Users manage their learners" ON public.learners;
CREATE POLICY "Users manage their learners"
ON public.learners
FOR ALL
USING (auth.uid() = guardian_id);

-- 5. Add learner_id column to learning_progress (Soft Link - No FK constraint yet)
-- We'll add the foreign key constraint later after data migration is verified
ALTER TABLE public.learning_progress 
ADD COLUMN IF NOT EXISTS learner_id UUID;

CREATE INDEX IF NOT EXISTS idx_learning_progress_learner_id ON public.learning_progress(learner_id);

-- 6. Migrate existing progress data (Map user_id -> learner_id)
-- This links existing progress to the parent's learner profile
UPDATE public.learning_progress lp
SET learner_id = l.id
FROM public.learners l
WHERE lp.user_id = l.user_id
  AND lp.learner_id IS NULL;

