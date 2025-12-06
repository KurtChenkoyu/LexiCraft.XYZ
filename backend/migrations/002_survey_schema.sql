-- Migration: Survey Schema for LexiSurvey
-- Created: 2024
-- Description: Creates tables for survey sessions, history, and results

-- 1. Survey Sessions table
CREATE TABLE IF NOT EXISTS survey_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    start_time TIMESTAMP NOT NULL DEFAULT NOW(),
    current_rank INTEGER,
    status TEXT NOT NULL DEFAULT 'active', -- 'active', 'completed', 'abandoned'
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_survey_sessions_user_id ON survey_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_survey_sessions_status ON survey_sessions(status);
CREATE INDEX IF NOT EXISTS idx_survey_sessions_start_time ON survey_sessions(start_time);

-- 2. Survey History table
-- Stores the full list of QuestionHistory objects for each session
CREATE TABLE IF NOT EXISTS survey_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES survey_sessions(id) ON DELETE CASCADE,
    history JSONB NOT NULL, -- Array of QuestionHistory objects: [{rank, correct, time_taken}, ...]
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(session_id)
);

CREATE INDEX IF NOT EXISTS idx_survey_history_session_id ON survey_history(session_id);
CREATE INDEX IF NOT EXISTS idx_survey_history_history_gin ON survey_history USING GIN(history);

-- 3. Survey Results table
-- Stores the final Tri-Metric scores
CREATE TABLE IF NOT EXISTS survey_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES survey_sessions(id) ON DELETE CASCADE,
    volume INTEGER NOT NULL, -- Est. Reserves (資產總量)
    reach INTEGER NOT NULL,  -- Horizon (有效邊界)
    density FLOAT NOT NULL,  -- Solidity (資產密度) 0.0-1.0
    cefr_level TEXT,         -- 'A1' | 'A2' | 'B1' | 'B2' | 'C1' | 'C2'
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(session_id)
);

CREATE INDEX IF NOT EXISTS idx_survey_results_session_id ON survey_results(session_id);
CREATE INDEX IF NOT EXISTS idx_survey_results_cefr_level ON survey_results(cefr_level);

