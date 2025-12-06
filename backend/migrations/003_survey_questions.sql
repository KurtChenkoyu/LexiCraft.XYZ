-- Migration: Store Question Payloads for Detailed Reports
-- Created: 2024
-- Description: Stores question payloads so we can reconstruct what was asked

CREATE TABLE IF NOT EXISTS survey_questions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES survey_sessions(id) ON DELETE CASCADE,
    question_id TEXT NOT NULL, -- e.g., "q_3500_12345"
    question_number INTEGER NOT NULL, -- 1, 2, 3, etc.
    word TEXT NOT NULL,
    rank INTEGER NOT NULL,
    phase INTEGER NOT NULL, -- 1, 2, or 3
    options JSONB NOT NULL, -- Full options array with all details
    time_limit INTEGER DEFAULT 12,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(session_id, question_id)
);

CREATE INDEX IF NOT EXISTS idx_survey_questions_session_id ON survey_questions(session_id);
CREATE INDEX IF NOT EXISTS idx_survey_questions_question_id ON survey_questions(question_id);
CREATE INDEX IF NOT EXISTS idx_survey_questions_question_number ON survey_questions(session_id, question_number);

