-- Migration: Gamification Schema (Achievements, Levels, Goals, Leaderboards, Notifications)
-- Created: 2025-01
-- Description: Adds gamification features for learner engagement and parent/coach analytics

-- ============================================
-- STEP 1: Achievement System
-- ============================================

-- Achievement definitions
CREATE TABLE IF NOT EXISTS achievements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(50) UNIQUE NOT NULL,
    name_en VARCHAR(100) NOT NULL,
    name_zh VARCHAR(100),
    description_en TEXT,
    description_zh TEXT,
    icon VARCHAR(50),
    category VARCHAR(30) NOT NULL,  -- 'streak', 'vocabulary', 'mastery', 'social', 'special'
    tier VARCHAR(20) NOT NULL,       -- 'bronze', 'silver', 'gold', 'platinum'
    requirement_type VARCHAR(30) NOT NULL,  -- 'streak_days', 'vocabulary_size', 'mastered_count', etc.
    requirement_value INT NOT NULL,
    xp_reward INT DEFAULT 0,
    points_bonus INT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- User achievements (tracking progress and unlocks)
CREATE TABLE IF NOT EXISTS user_achievements (
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    achievement_id UUID NOT NULL REFERENCES achievements(id) ON DELETE CASCADE,
    unlocked_at TIMESTAMPTZ,
    progress INT DEFAULT 0,
    PRIMARY KEY (user_id, achievement_id)
);

CREATE INDEX IF NOT EXISTS idx_user_achievements_user ON user_achievements(user_id);
CREATE INDEX IF NOT EXISTS idx_user_achievements_achievement ON user_achievements(achievement_id);
CREATE INDEX IF NOT EXISTS idx_achievements_category ON achievements(category);
CREATE INDEX IF NOT EXISTS idx_achievements_code ON achievements(code);

-- ============================================
-- STEP 2: Level/XP System
-- ============================================

CREATE TABLE IF NOT EXISTS user_xp (
    user_id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    total_xp INT DEFAULT 0,
    current_level INT DEFAULT 1,
    xp_to_next_level INT DEFAULT 100,
    xp_in_current_level INT DEFAULT 0,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS xp_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    xp_amount INT NOT NULL,
    source VARCHAR(50) NOT NULL,  -- 'word_learned', 'streak', 'achievement', 'review', 'goal'
    source_id UUID,  -- Optional: reference to achievement_id, goal_id, etc.
    earned_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_xp_history_user ON xp_history(user_id);
CREATE INDEX IF NOT EXISTS idx_xp_history_date ON xp_history(earned_at);
CREATE INDEX IF NOT EXISTS idx_xp_history_source ON xp_history(source);

-- ============================================
-- STEP 3: Goal System
-- ============================================

CREATE TABLE IF NOT EXISTS learning_goals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    goal_type VARCHAR(30) NOT NULL,  -- 'daily_words', 'weekly_words', 'monthly_words', 'streak', 'vocabulary_size'
    target_value INT NOT NULL,
    current_value INT DEFAULT 0,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    status VARCHAR(20) DEFAULT 'active',  -- 'active', 'completed', 'failed', 'cancelled'
    created_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_goals_user ON learning_goals(user_id);
CREATE INDEX IF NOT EXISTS idx_goals_status ON learning_goals(status) WHERE status = 'active';
CREATE INDEX IF NOT EXISTS idx_goals_dates ON learning_goals(start_date, end_date);

-- ============================================
-- STEP 4: Leaderboard Support
-- ============================================

CREATE TABLE IF NOT EXISTS leaderboard_entries (
    user_id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    weekly_xp INT DEFAULT 0,
    monthly_xp INT DEFAULT 0,
    all_time_xp INT DEFAULT 0,
    weekly_words INT DEFAULT 0,
    monthly_words INT DEFAULT 0,
    longest_streak INT DEFAULT 0,
    current_streak INT DEFAULT 0,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- User connections (friends, classmates) - extends existing relationships
CREATE TABLE IF NOT EXISTS user_connections (
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    connected_user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    connection_type VARCHAR(20) NOT NULL,  -- 'friend', 'classmate'
    created_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (user_id, connected_user_id),
    CHECK (user_id != connected_user_id)
);

CREATE INDEX IF NOT EXISTS idx_leaderboard_weekly_xp ON leaderboard_entries(weekly_xp DESC);
CREATE INDEX IF NOT EXISTS idx_leaderboard_monthly_xp ON leaderboard_entries(monthly_xp DESC);
CREATE INDEX IF NOT EXISTS idx_leaderboard_all_time_xp ON leaderboard_entries(all_time_xp DESC);
CREATE INDEX IF NOT EXISTS idx_connections_user ON user_connections(user_id);
CREATE INDEX IF NOT EXISTS idx_connections_connected ON user_connections(connected_user_id);

-- ============================================
-- STEP 5: Notifications
-- ============================================

CREATE TABLE IF NOT EXISTS notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    type VARCHAR(30) NOT NULL,  -- 'achievement', 'streak_risk', 'goal_progress', 'milestone', 'level_up'
    title_en VARCHAR(200),
    title_zh VARCHAR(200),
    message_en TEXT,
    message_zh TEXT,
    data JSONB DEFAULT '{}',
    read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_notifications_user ON notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_notifications_read ON notifications(user_id, read) WHERE read = FALSE;
CREATE INDEX IF NOT EXISTS idx_notifications_created ON notifications(created_at DESC);

-- ============================================
-- STEP 6: Helper Functions
-- ============================================

-- Function to calculate level from total XP (exponential curve)
CREATE OR REPLACE FUNCTION calculate_level(p_total_xp INT)
RETURNS TABLE(level INT, xp_to_next INT, xp_in_level INT) AS $$
DECLARE
    v_level INT := 1;
    v_xp_for_level INT := 0;
    v_xp_needed INT := 100;
    v_remaining_xp INT := p_total_xp;
BEGIN
    -- Exponential progression: each level requires more XP
    -- Level 1: 0-99 XP (100 XP needed)
    -- Level 2: 100-249 XP (150 XP needed)
    -- Level 3: 250-449 XP (200 XP needed)
    -- Formula: XP needed = 100 + (level - 1) * 50
    
    WHILE v_remaining_xp >= v_xp_needed LOOP
        v_level := v_level + 1;
        v_remaining_xp := v_remaining_xp - v_xp_needed;
        v_xp_needed := 100 + (v_level - 1) * 50;
    END LOOP;
    
    RETURN QUERY SELECT v_level, v_xp_needed, v_remaining_xp;
END;
$$ LANGUAGE plpgsql;

-- Function to initialize user XP record
CREATE OR REPLACE FUNCTION initialize_user_xp(p_user_id UUID)
RETURNS VOID AS $$
BEGIN
    INSERT INTO user_xp (user_id, total_xp, current_level, xp_to_next_level, xp_in_current_level)
    VALUES (p_user_id, 0, 1, 100, 0)
    ON CONFLICT (user_id) DO NOTHING;
END;
$$ LANGUAGE plpgsql;

-- Function to update leaderboard entry
CREATE OR REPLACE FUNCTION update_leaderboard_entry(p_user_id UUID)
RETURNS VOID AS $$
DECLARE
    v_weekly_xp INT;
    v_monthly_xp INT;
    v_all_time_xp INT;
    v_weekly_words INT;
    v_monthly_words INT;
    v_longest_streak INT;
    v_current_streak INT;
BEGIN
    -- Calculate weekly XP (last 7 days)
    SELECT COALESCE(SUM(xp_amount), 0) INTO v_weekly_xp
    FROM xp_history
    WHERE user_id = p_user_id
    AND earned_at >= NOW() - INTERVAL '7 days';
    
    -- Calculate monthly XP (last 30 days)
    SELECT COALESCE(SUM(xp_amount), 0) INTO v_monthly_xp
    FROM xp_history
    WHERE user_id = p_user_id
    AND earned_at >= NOW() - INTERVAL '30 days';
    
    -- Get all-time XP
    SELECT COALESCE(total_xp, 0) INTO v_all_time_xp
    FROM user_xp
    WHERE user_id = p_user_id;
    
    -- Calculate weekly words learned
    SELECT COUNT(*) INTO v_weekly_words
    FROM learning_progress
    WHERE user_id = p_user_id
    AND status = 'verified'
    AND learned_at >= NOW() - INTERVAL '7 days';
    
    -- Calculate monthly words learned
    SELECT COUNT(*) INTO v_monthly_words
    FROM learning_progress
    WHERE user_id = p_user_id
    AND status = 'verified'
    AND learned_at >= NOW() - INTERVAL '30 days';
    
    -- Get streak info (from learning_velocity service logic)
    -- This is a simplified version - actual streak calculation is in the service
    SELECT COALESCE(MAX(activity_streak_days), 0) INTO v_longest_streak
    FROM (
        SELECT COUNT(DISTINCT DATE(learned_at)) as activity_streak_days
        FROM learning_progress
        WHERE user_id = p_user_id
        AND learned_at >= NOW() - INTERVAL '90 days'
        GROUP BY DATE(learned_at)
    ) sub;
    
    -- Update or insert leaderboard entry
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

-- ============================================
-- STEP 7: Comments
-- ============================================

COMMENT ON TABLE achievements IS 'Achievement definitions for gamification system';
COMMENT ON TABLE user_achievements IS 'User achievement progress and unlocks';
COMMENT ON TABLE user_xp IS 'User XP and level tracking';
COMMENT ON TABLE xp_history IS 'History of XP earnings for analytics';
COMMENT ON TABLE learning_goals IS 'User-defined learning goals';
COMMENT ON TABLE leaderboard_entries IS 'Leaderboard statistics for ranking';
COMMENT ON TABLE user_connections IS 'User connections (friends, classmates) for social features';
COMMENT ON TABLE notifications IS 'User notifications for achievements, milestones, alerts';

COMMENT ON FUNCTION calculate_level IS 'Calculates level, XP to next level, and XP in current level from total XP';
COMMENT ON FUNCTION initialize_user_xp IS 'Initializes XP record for a new user';
COMMENT ON FUNCTION update_leaderboard_entry IS 'Updates leaderboard statistics for a user';


