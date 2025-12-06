-- Migration: MCQ Statistics & Adaptive Selection Support
-- Created: 2024-12
-- Description: Adds tables for MCQ quality tracking and adaptive selection
-- Works with both SM-2+ and FSRS algorithms

-- ============================================
-- STEP 1: Create mcq_pool table (store generated MCQs)
-- ============================================

CREATE TABLE IF NOT EXISTS mcq_pool (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sense_id VARCHAR(255) NOT NULL,       -- References Neo4j sense.id
    word VARCHAR(255) NOT NULL,           -- The word being tested
    mcq_type VARCHAR(50) NOT NULL,        -- 'meaning', 'usage', 'discrimination'
    
    -- Question content
    question TEXT NOT NULL,
    context TEXT,                         -- Example sentence providing context
    options JSONB NOT NULL,               -- [{text, is_correct, source, source_word}]
    correct_index INTEGER NOT NULL,
    explanation TEXT,                     -- Shown after answering
    metadata JSONB DEFAULT '{}',          -- Additional data
    
    -- Quality tracking (updated from statistics)
    difficulty_index FLOAT,               -- % who get it right (0.0-1.0)
    discrimination_index FLOAT,           -- How well it distinguishes ability levels
    quality_score FLOAT,                  -- Overall quality (0.0-1.0)
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,       -- Can be shown to users
    needs_review BOOLEAN DEFAULT FALSE,   -- Flagged for manual review
    review_reason TEXT,
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_mcq_pool_sense ON mcq_pool(sense_id);
CREATE INDEX IF NOT EXISTS idx_mcq_pool_word ON mcq_pool(word);
CREATE INDEX IF NOT EXISTS idx_mcq_pool_type ON mcq_pool(mcq_type);
CREATE INDEX IF NOT EXISTS idx_mcq_pool_active ON mcq_pool(is_active) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_mcq_pool_difficulty ON mcq_pool(difficulty_index);
CREATE INDEX IF NOT EXISTS idx_mcq_pool_quality ON mcq_pool(quality_score DESC);

-- ============================================
-- STEP 2: Create mcq_statistics table (aggregated per-MCQ stats)
-- ============================================

CREATE TABLE IF NOT EXISTS mcq_statistics (
    id SERIAL PRIMARY KEY,
    mcq_id UUID NOT NULL UNIQUE REFERENCES mcq_pool(id) ON DELETE CASCADE,
    
    -- Basic counts
    total_attempts INTEGER DEFAULT 0,
    correct_attempts INTEGER DEFAULT 0,
    
    -- Timing
    total_response_time_ms BIGINT DEFAULT 0,  -- Sum for calculating average
    avg_response_time_ms INTEGER,
    min_response_time_ms INTEGER,
    max_response_time_ms INTEGER,
    
    -- Distractor effectiveness (how often each distractor is selected)
    -- Format: {"confused": 15, "opposite": 8, "similar": 3, "target": 74}
    distractor_selections JSONB DEFAULT '{}',
    
    -- Quality metrics (recalculated periodically)
    difficulty_index FLOAT,               -- correct_attempts / total_attempts
    discrimination_index FLOAT,           -- Point-biserial correlation
    quality_score FLOAT,                  -- Weighted combination
    
    -- User ability distribution when attempting this MCQ
    -- Used for calculating discrimination index
    ability_sum_correct FLOAT DEFAULT 0,  -- Sum of abilities for correct answers
    ability_sum_wrong FLOAT DEFAULT 0,    -- Sum of abilities for wrong answers
    ability_count_correct INTEGER DEFAULT 0,
    ability_count_wrong INTEGER DEFAULT 0,
    
    -- Flags
    needs_recalculation BOOLEAN DEFAULT FALSE,
    last_calculated_at TIMESTAMP,
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_mcq_stats_mcq ON mcq_statistics(mcq_id);
CREATE INDEX IF NOT EXISTS idx_mcq_stats_quality ON mcq_statistics(quality_score DESC);
CREATE INDEX IF NOT EXISTS idx_mcq_stats_recalc ON mcq_statistics(needs_recalculation) WHERE needs_recalculation = true;

-- ============================================
-- STEP 3: Create mcq_attempts table (detailed attempt tracking)
-- ============================================

CREATE TABLE IF NOT EXISTS mcq_attempts (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    mcq_id UUID NOT NULL REFERENCES mcq_pool(id) ON DELETE CASCADE,
    sense_id VARCHAR(255) NOT NULL,
    
    -- Link to verification schedule (optional - for spaced rep integration)
    verification_schedule_id INTEGER REFERENCES verification_schedule(id) ON DELETE SET NULL,
    
    -- Attempt details
    is_correct BOOLEAN NOT NULL,
    response_time_ms INTEGER,
    selected_option_index INTEGER,
    selected_option_source VARCHAR(50),   -- 'target', 'confused', 'opposite', 'similar'
    
    -- User state at time of attempt (for discrimination calculation)
    user_ability_estimate FLOAT,          -- Estimated ability when attempting
    
    -- Context
    attempt_context VARCHAR(50) DEFAULT 'verification',  -- 'verification', 'practice', 'survey'
    
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_mcq_attempts_user ON mcq_attempts(user_id);
CREATE INDEX IF NOT EXISTS idx_mcq_attempts_mcq ON mcq_attempts(mcq_id);
CREATE INDEX IF NOT EXISTS idx_mcq_attempts_sense ON mcq_attempts(sense_id);
CREATE INDEX IF NOT EXISTS idx_mcq_attempts_date ON mcq_attempts(created_at);
CREATE INDEX IF NOT EXISTS idx_mcq_attempts_correct ON mcq_attempts(is_correct);

-- ============================================
-- STEP 4: Helper functions
-- ============================================

-- Function to update MCQ statistics after an attempt
CREATE OR REPLACE FUNCTION update_mcq_stats_after_attempt()
RETURNS TRIGGER AS $$
BEGIN
    -- Update or insert statistics
    INSERT INTO mcq_statistics (mcq_id, total_attempts, correct_attempts, total_response_time_ms,
                                distractor_selections, ability_sum_correct, ability_sum_wrong,
                                ability_count_correct, ability_count_wrong, needs_recalculation)
    VALUES (NEW.mcq_id, 1, 
            CASE WHEN NEW.is_correct THEN 1 ELSE 0 END,
            COALESCE(NEW.response_time_ms, 0),
            CASE WHEN NEW.selected_option_source IS NOT NULL 
                 THEN jsonb_build_object(NEW.selected_option_source, 1)
                 ELSE '{}'::jsonb END,
            CASE WHEN NEW.is_correct AND NEW.user_ability_estimate IS NOT NULL 
                 THEN NEW.user_ability_estimate ELSE 0 END,
            CASE WHEN NOT NEW.is_correct AND NEW.user_ability_estimate IS NOT NULL 
                 THEN NEW.user_ability_estimate ELSE 0 END,
            CASE WHEN NEW.is_correct AND NEW.user_ability_estimate IS NOT NULL THEN 1 ELSE 0 END,
            CASE WHEN NOT NEW.is_correct AND NEW.user_ability_estimate IS NOT NULL THEN 1 ELSE 0 END,
            TRUE)
    ON CONFLICT (mcq_id) DO UPDATE SET
        total_attempts = mcq_statistics.total_attempts + 1,
        correct_attempts = mcq_statistics.correct_attempts + CASE WHEN NEW.is_correct THEN 1 ELSE 0 END,
        total_response_time_ms = mcq_statistics.total_response_time_ms + COALESCE(NEW.response_time_ms, 0),
        distractor_selections = CASE 
            WHEN NEW.selected_option_source IS NOT NULL THEN
                mcq_statistics.distractor_selections || 
                jsonb_build_object(NEW.selected_option_source, 
                    COALESCE((mcq_statistics.distractor_selections->>NEW.selected_option_source)::int, 0) + 1)
            ELSE mcq_statistics.distractor_selections
        END,
        ability_sum_correct = mcq_statistics.ability_sum_correct + 
            CASE WHEN NEW.is_correct AND NEW.user_ability_estimate IS NOT NULL 
                 THEN NEW.user_ability_estimate ELSE 0 END,
        ability_sum_wrong = mcq_statistics.ability_sum_wrong + 
            CASE WHEN NOT NEW.is_correct AND NEW.user_ability_estimate IS NOT NULL 
                 THEN NEW.user_ability_estimate ELSE 0 END,
        ability_count_correct = mcq_statistics.ability_count_correct + 
            CASE WHEN NEW.is_correct AND NEW.user_ability_estimate IS NOT NULL THEN 1 ELSE 0 END,
        ability_count_wrong = mcq_statistics.ability_count_wrong + 
            CASE WHEN NOT NEW.is_correct AND NEW.user_ability_estimate IS NOT NULL THEN 1 ELSE 0 END,
        needs_recalculation = TRUE,
        updated_at = NOW();
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to auto-update stats
DROP TRIGGER IF EXISTS trg_update_mcq_stats ON mcq_attempts;
CREATE TRIGGER trg_update_mcq_stats
    AFTER INSERT ON mcq_attempts
    FOR EACH ROW
    EXECUTE FUNCTION update_mcq_stats_after_attempt();

-- Function to recalculate quality metrics for an MCQ
CREATE OR REPLACE FUNCTION recalculate_mcq_quality(p_mcq_id UUID)
RETURNS VOID AS $$
DECLARE
    v_stats mcq_statistics%ROWTYPE;
    v_difficulty FLOAT;
    v_discrimination FLOAT;
    v_quality FLOAT;
    v_mean_correct FLOAT;
    v_mean_wrong FLOAT;
BEGIN
    -- Get current stats
    SELECT * INTO v_stats FROM mcq_statistics WHERE mcq_id = p_mcq_id;
    
    IF v_stats IS NULL OR v_stats.total_attempts < 5 THEN
        -- Not enough data yet
        RETURN;
    END IF;
    
    -- Calculate difficulty index (% who get it right)
    v_difficulty := v_stats.correct_attempts::float / v_stats.total_attempts::float;
    
    -- Calculate discrimination index (simplified point-biserial)
    -- D = (mean_ability_correct - mean_ability_wrong) / range
    IF v_stats.ability_count_correct > 0 AND v_stats.ability_count_wrong > 0 THEN
        v_mean_correct := v_stats.ability_sum_correct / v_stats.ability_count_correct;
        v_mean_wrong := v_stats.ability_sum_wrong / v_stats.ability_count_wrong;
        -- Normalize to 0-1 range (assuming ability is 0-1)
        v_discrimination := GREATEST(0, LEAST(1, (v_mean_correct - v_mean_wrong)));
    ELSE
        v_discrimination := NULL;
    END IF;
    
    -- Calculate quality score
    -- Quality = 0.5 * discrimination + 0.5 * (1 - |difficulty - 0.5| * 2)
    -- This rewards both good discrimination AND optimal difficulty (~0.5)
    IF v_discrimination IS NOT NULL THEN
        v_quality := 0.5 * v_discrimination + 0.5 * (1 - ABS(v_difficulty - 0.5) * 2);
    ELSE
        -- If no discrimination data, use difficulty alone
        v_quality := 1 - ABS(v_difficulty - 0.5) * 2;
    END IF;
    
    -- Update statistics
    UPDATE mcq_statistics SET
        difficulty_index = v_difficulty,
        discrimination_index = v_discrimination,
        quality_score = v_quality,
        avg_response_time_ms = CASE 
            WHEN total_attempts > 0 THEN (total_response_time_ms / total_attempts)::int 
            ELSE NULL END,
        needs_recalculation = FALSE,
        last_calculated_at = NOW(),
        updated_at = NOW()
    WHERE mcq_id = p_mcq_id;
    
    -- Also update the mcq_pool table
    UPDATE mcq_pool SET
        difficulty_index = v_difficulty,
        discrimination_index = v_discrimination,
        quality_score = v_quality,
        -- Flag for review if quality is poor
        needs_review = CASE 
            WHEN v_discrimination IS NOT NULL AND v_discrimination < 0.2 THEN TRUE
            WHEN v_difficulty < 0.2 OR v_difficulty > 0.9 THEN TRUE
            ELSE FALSE
        END,
        review_reason = CASE
            WHEN v_discrimination IS NOT NULL AND v_discrimination < 0.2 THEN 'Low discrimination'
            WHEN v_difficulty < 0.2 THEN 'Too difficult'
            WHEN v_difficulty > 0.9 THEN 'Too easy'
            ELSE NULL
        END,
        updated_at = NOW()
    WHERE id = p_mcq_id;
END;
$$ LANGUAGE plpgsql;

-- Function to recalculate all MCQs that need it
CREATE OR REPLACE FUNCTION recalculate_all_mcq_quality()
RETURNS INTEGER AS $$
DECLARE
    v_count INTEGER := 0;
    v_mcq_id UUID;
BEGIN
    FOR v_mcq_id IN 
        SELECT mcq_id FROM mcq_statistics WHERE needs_recalculation = TRUE
    LOOP
        PERFORM recalculate_mcq_quality(v_mcq_id);
        v_count := v_count + 1;
    END LOOP;
    
    RETURN v_count;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- STEP 5: View for MCQ quality dashboard
-- ============================================

CREATE OR REPLACE VIEW mcq_quality_dashboard AS
SELECT 
    p.id as mcq_id,
    p.word,
    p.sense_id,
    p.mcq_type,
    p.is_active,
    p.needs_review,
    p.review_reason,
    s.total_attempts,
    s.correct_attempts,
    s.difficulty_index,
    s.discrimination_index,
    s.quality_score,
    s.avg_response_time_ms,
    s.distractor_selections,
    CASE 
        WHEN s.quality_score >= 0.7 THEN 'excellent'
        WHEN s.quality_score >= 0.5 THEN 'good'
        WHEN s.quality_score >= 0.3 THEN 'fair'
        ELSE 'poor'
    END as quality_category
FROM mcq_pool p
LEFT JOIN mcq_statistics s ON s.mcq_id = p.id
ORDER BY p.needs_review DESC, s.total_attempts DESC;

-- ============================================
-- STEP 6: Comments
-- ============================================

COMMENT ON TABLE mcq_pool IS 'Stores generated MCQs for verification testing';
COMMENT ON TABLE mcq_statistics IS 'Aggregated statistics for each MCQ (updated via trigger)';
COMMENT ON TABLE mcq_attempts IS 'Detailed record of each MCQ attempt by users';

COMMENT ON COLUMN mcq_pool.difficulty_index IS 'Proportion who answer correctly (0.0-1.0, optimal ~0.5)';
COMMENT ON COLUMN mcq_pool.discrimination_index IS 'How well MCQ distinguishes high vs low ability (0.0-1.0, want >0.3)';
COMMENT ON COLUMN mcq_pool.quality_score IS 'Combined quality metric (0.0-1.0, want >0.5)';

COMMENT ON FUNCTION update_mcq_stats_after_attempt IS 'Trigger function to update MCQ statistics after each attempt';
COMMENT ON FUNCTION recalculate_mcq_quality IS 'Recalculates quality metrics for a single MCQ';
COMMENT ON FUNCTION recalculate_all_mcq_quality IS 'Batch recalculation of all MCQs needing update';

