-- Migration: Progressive Survey Model (PSM)
-- Created: 2024-12
-- Description: Adds tables and fields to support warm-start surveys and efficiency tracking

-- ============================================
-- STEP 1: Create survey_metadata table
-- ============================================
-- Tracks survey efficiency, prior knowledge, and comparison data for testimonials

CREATE TABLE IF NOT EXISTS survey_metadata (
    id SERIAL PRIMARY KEY,
    session_id UUID NOT NULL REFERENCES survey_sessions(id) ON DELETE CASCADE,
    
    -- Survey mode and context
    survey_mode TEXT NOT NULL DEFAULT 'cold_start',
    -- Values: 'cold_start', 'warm_start', 'quick_validation', 'deep_dive'
    
    -- Prior knowledge at survey time
    prior_verified_words INTEGER DEFAULT 0,
    prior_bands_with_data INTEGER DEFAULT 0,
    prior_confidence FLOAT DEFAULT 0.0,
    
    -- Survey efficiency metrics
    questions_asked INTEGER NOT NULL DEFAULT 0,
    questions_saved_by_prior INTEGER DEFAULT 0,  -- Estimated questions saved by warm-start
    time_taken_seconds INTEGER,
    final_confidence FLOAT,
    
    -- Comparison with previous survey
    previous_session_id UUID REFERENCES survey_sessions(id),
    improvement_volume INTEGER,  -- +/- change from previous
    improvement_reach INTEGER,   -- +/- change from previous
    improvement_density FLOAT,   -- +/- change from previous
    days_since_last_survey INTEGER,
    
    -- Learning efficiency (for testimonials)
    verified_words_between_surveys INTEGER,  -- Words verified between this and last survey
    learning_days_between_surveys INTEGER,   -- Active learning days
    efficiency_score FLOAT,  -- Calculated: improvement / effort
    
    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(session_id)
);

CREATE INDEX IF NOT EXISTS idx_survey_metadata_session ON survey_metadata(session_id);
CREATE INDEX IF NOT EXISTS idx_survey_metadata_mode ON survey_metadata(survey_mode);
CREATE INDEX IF NOT EXISTS idx_survey_metadata_created ON survey_metadata(created_at);

-- ============================================
-- STEP 2: Add prior_knowledge column to survey_sessions
-- ============================================
-- Store the extracted prior knowledge as JSONB for debugging and analysis

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'survey_sessions' AND column_name = 'survey_mode'
    ) THEN
        ALTER TABLE survey_sessions ADD COLUMN survey_mode TEXT DEFAULT 'cold_start';
        RAISE NOTICE 'Added survey_mode column to survey_sessions';
    ELSE
        RAISE NOTICE 'survey_mode column already exists';
    END IF;
    
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'survey_sessions' AND column_name = 'prior_knowledge'
    ) THEN
        ALTER TABLE survey_sessions ADD COLUMN prior_knowledge JSONB;
        RAISE NOTICE 'Added prior_knowledge column to survey_sessions';
    ELSE
        RAISE NOTICE 'prior_knowledge column already exists';
    END IF;
END $$;

-- ============================================
-- STEP 3: Create helper function for tier-to-band mapping
-- ============================================
-- Maps learning_progress tiers to frequency bands

CREATE OR REPLACE FUNCTION tier_to_frequency_band(tier INTEGER)
RETURNS INTEGER AS $$
BEGIN
    -- Mapping: tier 1 → 1000, tier 2 → 2000, etc.
    -- Tiers 1-7 map to bands 1000-7000
    -- Tier 8+ maps to band 8000
    RETURN LEAST(tier, 8) * 1000;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- ============================================
-- STEP 4: Create view for user survey history with progress
-- ============================================

CREATE OR REPLACE VIEW user_survey_progress AS
SELECT 
    ss.user_id,
    ss.id as session_id,
    ss.start_time,
    ss.survey_mode,
    sr.volume,
    sr.reach,
    sr.density,
    sr.cefr_level,
    sm.prior_verified_words,
    sm.prior_confidence,
    sm.questions_asked,
    sm.questions_saved_by_prior,
    sm.time_taken_seconds,
    sm.final_confidence,
    sm.improvement_volume,
    sm.improvement_reach,
    sm.days_since_last_survey,
    sm.efficiency_score,
    -- Calculate rank within user's surveys
    ROW_NUMBER() OVER (PARTITION BY ss.user_id ORDER BY ss.start_time) as survey_number
FROM survey_sessions ss
LEFT JOIN survey_results sr ON sr.session_id = ss.id
LEFT JOIN survey_metadata sm ON sm.session_id = ss.id
WHERE ss.status = 'completed';

-- ============================================
-- STEP 5: Create function to extract prior knowledge for a user
-- ============================================

CREATE OR REPLACE FUNCTION get_user_prior_knowledge(p_user_id UUID)
RETURNS JSONB AS $$
DECLARE
    result JSONB;
BEGIN
    SELECT jsonb_build_object(
        'total_verified', COALESCE(SUM(count), 0),
        'bands', jsonb_object_agg(
            band::text, 
            jsonb_build_object(
                'verified_count', count,
                'last_learned', last_learned
            )
        )
    )
    INTO result
    FROM (
        SELECT 
            tier_to_frequency_band(lp.tier) as band,
            COUNT(*) as count,
            MAX(lp.learned_at) as last_learned
        FROM learning_progress lp
        WHERE lp.user_id = p_user_id
        AND lp.status = 'verified'
        GROUP BY tier_to_frequency_band(lp.tier)
    ) band_stats;
    
    RETURN COALESCE(result, '{"total_verified": 0, "bands": {}}'::jsonb);
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- STEP 6: Create function to get previous survey comparison
-- ============================================

CREATE OR REPLACE FUNCTION get_previous_survey(p_user_id UUID, p_current_session_id UUID)
RETURNS JSONB AS $$
DECLARE
    prev_session RECORD;
    result JSONB;
BEGIN
    -- Find the most recent completed survey before the current one
    SELECT 
        ss.id as session_id,
        ss.start_time,
        sr.volume,
        sr.reach,
        sr.density
    INTO prev_session
    FROM survey_sessions ss
    JOIN survey_results sr ON sr.session_id = ss.id
    WHERE ss.user_id = p_user_id
    AND ss.status = 'completed'
    AND ss.id != p_current_session_id
    ORDER BY ss.start_time DESC
    LIMIT 1;
    
    IF prev_session IS NULL THEN
        RETURN NULL;
    END IF;
    
    result := jsonb_build_object(
        'session_id', prev_session.session_id,
        'date', prev_session.start_time,
        'volume', prev_session.volume,
        'reach', prev_session.reach,
        'density', prev_session.density
    );
    
    RETURN result;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- STEP 7: Create function to calculate verified words between surveys
-- ============================================

CREATE OR REPLACE FUNCTION count_verified_between_surveys(
    p_user_id UUID, 
    p_start_date TIMESTAMP, 
    p_end_date TIMESTAMP
)
RETURNS INTEGER AS $$
BEGIN
    RETURN (
        SELECT COUNT(*)
        FROM learning_progress lp
        WHERE lp.user_id = p_user_id
        AND lp.status = 'verified'
        AND lp.learned_at >= p_start_date
        AND lp.learned_at < p_end_date
    );
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- STEP 8: Create testimonial aggregation view
-- ============================================

CREATE OR REPLACE VIEW survey_efficiency_stats AS
WITH user_journey AS (
    SELECT 
        ss.user_id,
        COUNT(DISTINCT ss.id) as survey_count,
        MIN(sr.volume) as first_volume,
        MAX(sr.volume) as latest_volume,
        MAX(sr.volume) - MIN(sr.volume) as total_growth,
        AVG(sm.questions_asked) as avg_questions,
        AVG(sm.efficiency_score) as avg_efficiency,
        SUM(sm.questions_saved_by_prior) as total_questions_saved
    FROM survey_sessions ss
    JOIN survey_results sr ON sr.session_id = ss.id
    LEFT JOIN survey_metadata sm ON sm.session_id = ss.id
    WHERE ss.status = 'completed'
    GROUP BY ss.user_id
    HAVING COUNT(DISTINCT ss.id) >= 2
)
SELECT 
    user_id,
    survey_count,
    first_volume,
    latest_volume,
    total_growth,
    avg_questions,
    avg_efficiency,
    total_questions_saved,
    CASE 
        WHEN first_volume > 0 THEN 
            ROUND(((latest_volume - first_volume)::numeric / first_volume) * 100, 1)
        ELSE 0 
    END as growth_percentage
FROM user_journey;

-- ============================================
-- STEP 9: Add comments for documentation
-- ============================================

COMMENT ON TABLE survey_metadata IS 'Stores efficiency metrics and comparison data for Progressive Survey Model (PSM)';
COMMENT ON COLUMN survey_metadata.survey_mode IS 'Survey mode: cold_start (new user), warm_start (has learning data), quick_validation (milestone check), deep_dive (thorough re-assessment)';
COMMENT ON COLUMN survey_metadata.questions_saved_by_prior IS 'Estimated number of questions saved due to prior knowledge from learning_progress';
COMMENT ON COLUMN survey_metadata.efficiency_score IS 'Learning efficiency metric: vocabulary improvement relative to verified words between surveys';

COMMENT ON VIEW user_survey_progress IS 'Aggregated view of user survey history with progress tracking for testimonials';
COMMENT ON VIEW survey_efficiency_stats IS 'Platform-wide efficiency statistics for users with 2+ surveys';

COMMENT ON FUNCTION tier_to_frequency_band IS 'Maps learning_progress tier (1-8) to frequency band (1000-8000)';
COMMENT ON FUNCTION get_user_prior_knowledge IS 'Extracts prior knowledge from learning_progress for warm-start surveys';
COMMENT ON FUNCTION get_previous_survey IS 'Retrieves previous survey results for comparison';
COMMENT ON FUNCTION count_verified_between_surveys IS 'Counts verified words between two timestamps for efficiency calculation';

