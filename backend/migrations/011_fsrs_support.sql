-- Migration: FSRS (Free Spaced Repetition Scheduler) Support
-- Created: 2024-12
-- Description: Adds FSRS algorithm support for A/B testing alongside SM-2+

-- ============================================
-- STEP 1: Add FSRS columns to verification_schedule
-- ============================================

DO $$
BEGIN
    -- Algorithm type (sm2_plus or fsrs)
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'verification_schedule' AND column_name = 'algorithm_type'
    ) THEN
        ALTER TABLE verification_schedule ADD COLUMN algorithm_type TEXT DEFAULT 'sm2_plus';
        RAISE NOTICE 'Added algorithm_type column';
    END IF;
    
    -- FSRS: Stability (memory strength, higher = more stable)
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'verification_schedule' AND column_name = 'stability'
    ) THEN
        ALTER TABLE verification_schedule ADD COLUMN stability FLOAT;
        RAISE NOTICE 'Added stability column';
    END IF;
    
    -- FSRS: Difficulty (word difficulty for this user, 0-1)
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'verification_schedule' AND column_name = 'difficulty'
    ) THEN
        ALTER TABLE verification_schedule ADD COLUMN difficulty FLOAT DEFAULT 0.5;
        RAISE NOTICE 'Added difficulty column';
    END IF;
    
    -- FSRS: Predicted retention probability at review time
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'verification_schedule' AND column_name = 'retention_probability'
    ) THEN
        ALTER TABLE verification_schedule ADD COLUMN retention_probability FLOAT;
        RAISE NOTICE 'Added retention_probability column';
    END IF;
    
    -- FSRS: Full state object for the library (JSON serialized)
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'verification_schedule' AND column_name = 'fsrs_state'
    ) THEN
        ALTER TABLE verification_schedule ADD COLUMN fsrs_state JSONB;
        RAISE NOTICE 'Added fsrs_state column';
    END IF;
    
    -- FSRS: Last review date (needed for elapsed time calculation)
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'verification_schedule' AND column_name = 'last_review_date'
    ) THEN
        ALTER TABLE verification_schedule ADD COLUMN last_review_date DATE;
        RAISE NOTICE 'Added last_review_date column';
    END IF;
    
    -- SM-2+: Ease factor (for SM-2+ algorithm)
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'verification_schedule' AND column_name = 'ease_factor'
    ) THEN
        ALTER TABLE verification_schedule ADD COLUMN ease_factor FLOAT DEFAULT 2.5;
        RAISE NOTICE 'Added ease_factor column';
    END IF;
    
    -- SM-2+: Consecutive correct count
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'verification_schedule' AND column_name = 'consecutive_correct'
    ) THEN
        ALTER TABLE verification_schedule ADD COLUMN consecutive_correct INTEGER DEFAULT 0;
        RAISE NOTICE 'Added consecutive_correct column';
    END IF;
    
    -- Current interval in days
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'verification_schedule' AND column_name = 'current_interval'
    ) THEN
        ALTER TABLE verification_schedule ADD COLUMN current_interval INTEGER DEFAULT 1;
        RAISE NOTICE 'Added current_interval column';
    END IF;
    
    -- Mastery level
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'verification_schedule' AND column_name = 'mastery_level'
    ) THEN
        ALTER TABLE verification_schedule ADD COLUMN mastery_level TEXT DEFAULT 'learning';
        RAISE NOTICE 'Added mastery_level column';
    END IF;
    
    -- Is leech (word that repeatedly fails)
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'verification_schedule' AND column_name = 'is_leech'
    ) THEN
        ALTER TABLE verification_schedule ADD COLUMN is_leech BOOLEAN DEFAULT FALSE;
        RAISE NOTICE 'Added is_leech column';
    END IF;
    
    -- Total reviews count
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'verification_schedule' AND column_name = 'total_reviews'
    ) THEN
        ALTER TABLE verification_schedule ADD COLUMN total_reviews INTEGER DEFAULT 0;
        RAISE NOTICE 'Added total_reviews column';
    END IF;
    
    -- Total correct count
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'verification_schedule' AND column_name = 'total_correct'
    ) THEN
        ALTER TABLE verification_schedule ADD COLUMN total_correct INTEGER DEFAULT 0;
        RAISE NOTICE 'Added total_correct column';
    END IF;
    
    -- Response time average (ms)
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'verification_schedule' AND column_name = 'avg_response_time_ms'
    ) THEN
        ALTER TABLE verification_schedule ADD COLUMN avg_response_time_ms INTEGER;
        RAISE NOTICE 'Added avg_response_time_ms column';
    END IF;
END $$;

-- Add index for algorithm_type
CREATE INDEX IF NOT EXISTS idx_verification_schedule_algorithm ON verification_schedule(algorithm_type);
CREATE INDEX IF NOT EXISTS idx_verification_schedule_mastery ON verification_schedule(mastery_level);
CREATE INDEX IF NOT EXISTS idx_verification_schedule_leech ON verification_schedule(is_leech) WHERE is_leech = true;

-- ============================================
-- STEP 2: Create user_algorithm_assignment table
-- ============================================

CREATE TABLE IF NOT EXISTS user_algorithm_assignment (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    algorithm TEXT NOT NULL DEFAULT 'sm2_plus',  -- 'sm2_plus' or 'fsrs'
    assigned_at TIMESTAMP DEFAULT NOW(),
    assignment_reason TEXT DEFAULT 'random',  -- 'random', 'manual', 'migration', 'opt_in'
    can_migrate_to_fsrs BOOLEAN DEFAULT FALSE,  -- True when user has 100+ reviews
    fsrs_parameters JSONB,  -- Custom FSRS parameters after optimization
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    CONSTRAINT valid_algorithm CHECK (algorithm IN ('sm2_plus', 'fsrs'))
);

CREATE INDEX IF NOT EXISTS idx_user_algorithm_user ON user_algorithm_assignment(user_id);
CREATE INDEX IF NOT EXISTS idx_user_algorithm_type ON user_algorithm_assignment(algorithm);

-- ============================================
-- STEP 3: Create fsrs_review_history table
-- ============================================

CREATE TABLE IF NOT EXISTS fsrs_review_history (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    learning_progress_id INTEGER NOT NULL REFERENCES learning_progress(id) ON DELETE CASCADE,
    
    -- Review event data
    review_date TIMESTAMP NOT NULL DEFAULT NOW(),
    performance_rating INTEGER NOT NULL,  -- 0-4 FSRS scale: Again(0), Hard(1), Good(2), Easy(3), Perfect(4)
    response_time_ms INTEGER,
    
    -- State before review
    stability_before FLOAT,
    difficulty_before FLOAT,
    retention_predicted FLOAT,  -- Predicted retention at review time
    elapsed_days FLOAT,  -- Days since last review
    
    -- State after review
    stability_after FLOAT,
    difficulty_after FLOAT,
    interval_after INTEGER,  -- Next interval in days
    
    -- Actual result
    retention_actual BOOLEAN,  -- Did user remember? (rating >= 2)
    
    -- Algorithm used
    algorithm_type TEXT NOT NULL DEFAULT 'sm2_plus',
    
    created_at TIMESTAMP DEFAULT NOW(),
    
    CONSTRAINT valid_rating CHECK (performance_rating >= 0 AND performance_rating <= 4)
);

CREATE INDEX IF NOT EXISTS idx_fsrs_history_user ON fsrs_review_history(user_id);
CREATE INDEX IF NOT EXISTS idx_fsrs_history_learning ON fsrs_review_history(learning_progress_id);
CREATE INDEX IF NOT EXISTS idx_fsrs_history_date ON fsrs_review_history(review_date);
CREATE INDEX IF NOT EXISTS idx_fsrs_history_algorithm ON fsrs_review_history(algorithm_type);

-- ============================================
-- STEP 4: Create word_global_difficulty table
-- ============================================

CREATE TABLE IF NOT EXISTS word_global_difficulty (
    id SERIAL PRIMARY KEY,
    learning_point_id TEXT NOT NULL UNIQUE,  -- References Neo4j learning_point.id
    
    -- Global stats from all users
    total_reviews INTEGER DEFAULT 0,
    total_correct INTEGER DEFAULT 0,
    global_error_rate FLOAT DEFAULT 0.0,  -- 1 - (correct / reviews)
    average_ease_factor FLOAT DEFAULT 2.5,
    average_stability FLOAT,
    average_response_time_ms INTEGER,
    
    -- Difficulty classification
    difficulty_score FLOAT DEFAULT 0.5,  -- 0-1, higher = harder
    difficulty_category TEXT DEFAULT 'average',  -- 'easy', 'average', 'hard', 'leech'
    leech_percentage FLOAT DEFAULT 0.0,  -- % of users who find this a leech
    
    -- Helpful resources (for leeches)
    mnemonics JSONB DEFAULT '[]',  -- [{text, creator_id, upvotes}]
    related_words JSONB DEFAULT '[]',
    visual_aids JSONB DEFAULT '[]',
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_word_difficulty_learning ON word_global_difficulty(learning_point_id);
CREATE INDEX IF NOT EXISTS idx_word_difficulty_category ON word_global_difficulty(difficulty_category);
CREATE INDEX IF NOT EXISTS idx_word_difficulty_score ON word_global_difficulty(difficulty_score DESC);

-- ============================================
-- STEP 5: Create algorithm_comparison_metrics table
-- ============================================

CREATE TABLE IF NOT EXISTS algorithm_comparison_metrics (
    id SERIAL PRIMARY KEY,
    
    -- Aggregation period
    date DATE NOT NULL,
    algorithm_type TEXT NOT NULL,
    
    -- User counts
    total_users INTEGER DEFAULT 0,
    active_users INTEGER DEFAULT 0,  -- Users with reviews in this period
    
    -- Review metrics
    total_reviews INTEGER DEFAULT 0,
    reviews_per_user FLOAT,
    reviews_per_word FLOAT,
    
    -- Retention metrics
    retention_rate FLOAT,  -- % of reviews where user remembered
    
    -- Efficiency metrics
    avg_days_to_mastery FLOAT,  -- Days from first review to mastery
    words_mastered INTEGER DEFAULT 0,
    
    -- User satisfaction (from surveys)
    satisfaction_score FLOAT,
    
    created_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(date, algorithm_type)
);

CREATE INDEX IF NOT EXISTS idx_comparison_date ON algorithm_comparison_metrics(date);
CREATE INDEX IF NOT EXISTS idx_comparison_algorithm ON algorithm_comparison_metrics(algorithm_type);

-- ============================================
-- STEP 6: Helper functions
-- ============================================

-- Function to assign algorithm to new user (50/50 random split)
CREATE OR REPLACE FUNCTION assign_algorithm_to_user(p_user_id UUID)
RETURNS TEXT AS $$
DECLARE
    v_algorithm TEXT;
BEGIN
    -- Check if user already has assignment
    SELECT algorithm INTO v_algorithm
    FROM user_algorithm_assignment
    WHERE user_id = p_user_id;
    
    IF v_algorithm IS NOT NULL THEN
        RETURN v_algorithm;
    END IF;
    
    -- Random 50/50 split
    IF random() < 0.5 THEN
        v_algorithm := 'sm2_plus';
    ELSE
        v_algorithm := 'fsrs';
    END IF;
    
    -- Insert assignment
    INSERT INTO user_algorithm_assignment (user_id, algorithm, assignment_reason)
    VALUES (p_user_id, v_algorithm, 'random');
    
    RETURN v_algorithm;
END;
$$ LANGUAGE plpgsql;

-- Function to check if user can migrate to FSRS (100+ reviews)
CREATE OR REPLACE FUNCTION can_user_migrate_to_fsrs(p_user_id UUID)
RETURNS BOOLEAN AS $$
DECLARE
    v_review_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO v_review_count
    FROM fsrs_review_history
    WHERE user_id = p_user_id;
    
    RETURN v_review_count >= 100;
END;
$$ LANGUAGE plpgsql;

-- Function to get user's algorithm
CREATE OR REPLACE FUNCTION get_user_algorithm(p_user_id UUID)
RETURNS TEXT AS $$
DECLARE
    v_algorithm TEXT;
BEGIN
    SELECT algorithm INTO v_algorithm
    FROM user_algorithm_assignment
    WHERE user_id = p_user_id;
    
    -- If not assigned, assign now
    IF v_algorithm IS NULL THEN
        v_algorithm := assign_algorithm_to_user(p_user_id);
    END IF;
    
    RETURN v_algorithm;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- STEP 7: View for algorithm comparison
-- ============================================

CREATE OR REPLACE VIEW algorithm_performance_comparison AS
WITH user_stats AS (
    SELECT 
        uaa.algorithm,
        uaa.user_id,
        COUNT(fh.id) as review_count,
        AVG(CASE WHEN fh.retention_actual THEN 1 ELSE 0 END) as retention_rate,
        COUNT(DISTINCT fh.learning_progress_id) as words_reviewed
    FROM user_algorithm_assignment uaa
    LEFT JOIN fsrs_review_history fh ON fh.user_id = uaa.user_id
    GROUP BY uaa.algorithm, uaa.user_id
)
SELECT 
    algorithm,
    COUNT(DISTINCT user_id) as total_users,
    SUM(review_count) as total_reviews,
    AVG(review_count) as avg_reviews_per_user,
    AVG(retention_rate) as avg_retention_rate,
    SUM(words_reviewed) as total_words_reviewed,
    AVG(words_reviewed) as avg_words_per_user
FROM user_stats
GROUP BY algorithm;

-- ============================================
-- STEP 8: Comments
-- ============================================

COMMENT ON TABLE user_algorithm_assignment IS 'Tracks which spaced repetition algorithm each user is assigned to (for A/B testing)';
COMMENT ON TABLE fsrs_review_history IS 'Detailed review history for FSRS training and analytics';
COMMENT ON TABLE word_global_difficulty IS 'Global word difficulty statistics from all users';
COMMENT ON TABLE algorithm_comparison_metrics IS 'Daily aggregated metrics for comparing SM-2+ vs FSRS performance';

COMMENT ON FUNCTION assign_algorithm_to_user IS 'Randomly assigns a spaced repetition algorithm to a new user (50/50 split)';
COMMENT ON FUNCTION get_user_algorithm IS 'Gets user assigned algorithm, assigning one if not already assigned';
COMMENT ON FUNCTION can_user_migrate_to_fsrs IS 'Checks if user has 100+ reviews and can migrate to FSRS';

