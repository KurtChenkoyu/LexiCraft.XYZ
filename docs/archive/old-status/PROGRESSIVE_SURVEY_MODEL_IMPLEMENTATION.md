# Progressive Survey Model (PSM) Implementation Summary

## What Was Built

The Progressive Survey Model transforms the survey from a standalone assessment tool into an intelligent system that learns from user's learning history.

### Core Concept

```
┌─────────────────────────────────────────────────────────────────┐
│                    PROGRESSIVE SURVEY MODEL                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   COLD START (First Survey)          WARM START (Subsequent)    │
│   ├── No prior data                  ├── Uses learning_progress │
│   ├── 20-35 questions                ├── 10-20 questions         │
│   ├── Confidence: 0 → 0.80          ├── Confidence: 0.4 → 0.85  │
│   └── Full assessment                └── Focus on gaps           │
│                                                                  │
│   ┌──────────────────────────────────────────────────────────┐  │
│   │  Learning Progress ──► Prior Knowledge ──► Warm Start    │  │
│   │       │                      │                    │       │  │
│   │       │                      ▼                    ▼       │  │
│   │       │              Band Performance      Fewer Questions│  │
│   │       │                      │                    │       │  │
│   │       ▼                      ▼                    ▼       │  │
│   │  Survey Results ◄── Survey Metadata ◄── Efficiency Score │  │
│   └──────────────────────────────────────────────────────────┘  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Files Created/Modified

### New Files

1. **`docs/25-progressive-survey-model.md`**
   - Complete specification of the PSM
   - Algorithm details, data models, configuration

2. **`backend/migrations/010_progressive_survey_model.sql`**
   - `survey_metadata` table for tracking efficiency
   - Helper functions: `tier_to_frequency_band`, `get_user_prior_knowledge`
   - Views: `user_survey_progress`, `survey_efficiency_stats`

3. **`backend/src/survey/warm_start.py`**
   - Core warm-start functions
   - `extract_prior_knowledge()` - Get verified words by band
   - `calculate_warm_start_confidence()` - Initial confidence from prior
   - `warm_start_band_performance()` - Pre-populate band data
   - `select_priority_bands()` - Focus on uncertain areas
   - `auto_detect_survey_mode()` - Choose appropriate mode
   - `initialize_warm_start()` - Main entry point

4. **`backend/src/api/testimonials.py`**
   - `/api/v1/testimonials/user/{user_id}` - User progress story
   - `/api/v1/testimonials/platform` - Aggregate stats
   - `/api/v1/testimonials/efficiency/{user_id}` - Efficiency metrics

### Modified Files

1. **`backend/src/api/survey.py`**
   - Added `survey_mode` and `use_prior_knowledge` to `StartSurveyRequest`
   - `/start` endpoint now initializes warm-start if authenticated
   - `/next` endpoint saves `survey_metadata` on completion
   - Added `/history` endpoint for user survey timeline
   - Returns PSM debug info (questions saved, efficiency score, etc.)

2. **`backend/src/main.py`**
   - Added testimonials router
   - Updated version to 8.0

## Survey Modes

| Mode | When | Questions | Prior Data |
|------|------|-----------|------------|
| `cold_start` | First time / anonymous | 15-35 | None |
| `warm_start` | Has 20+ verified words | 8-20 | Yes |
| `quick_validation` | Has 100+ verified words | 5-10 | Yes |
| `deep_dive` | User requested | 25-50 | Optional |

## API Changes

### Start Survey (Enhanced)

```http
POST /api/v1/survey/start
{
  "cefr_level": "B1",
  "user_id": "uuid",
  "survey_mode": null,        // NEW: Auto-detect or force
  "use_prior_knowledge": true // NEW: Enable warm-start
}
```

### Response (Enhanced Debug Info)

```json
{
  "status": "continue",
  "session_id": "...",
  "payload": { ... },
  "debug_info": {
    "survey_mode": "warm_start",
    "prior_verified_words": 150,
    "initial_confidence": 0.45,
    "stopping_config": {
      "min_questions": 8,
      "confidence_threshold": 0.85,
      "max_questions": 20
    }
  }
}
```

### Completion Response (Enhanced)

```json
{
  "status": "complete",
  "metrics": { "volume": 3500, "reach": 4000, "density": 0.85 },
  "debug_info": {
    "survey_metadata": {
      "survey_mode": "warm_start",
      "questions_asked": 12,
      "questions_saved": 13,
      "time_taken_seconds": 180,
      "prior_verified_words": 150,
      "improvement": {
        "volume": 500,
        "reach": 300
      },
      "efficiency_score": 1.25,
      "efficiency_message": "Excellent! Your vocabulary is growing 1.3x faster with LexiCraft!"
    }
  }
}
```

### New Endpoints

```http
GET /api/v1/survey/history?user_id={uuid}
GET /api/v1/testimonials/user/{user_id}
GET /api/v1/testimonials/platform
GET /api/v1/testimonials/efficiency/{user_id}
```

## Database Schema

### survey_metadata Table

```sql
CREATE TABLE survey_metadata (
    id SERIAL PRIMARY KEY,
    session_id UUID REFERENCES survey_sessions(id),
    survey_mode TEXT,                    -- cold_start, warm_start, etc.
    prior_verified_words INTEGER,        -- Words known before survey
    prior_bands_with_data INTEGER,       -- Bands with prior data
    prior_confidence FLOAT,              -- Starting confidence
    questions_asked INTEGER,             -- Actual questions asked
    questions_saved_by_prior INTEGER,    -- Questions saved by warm-start
    time_taken_seconds INTEGER,          -- Total survey time
    final_confidence FLOAT,              -- Ending confidence
    previous_session_id UUID,            -- Previous survey for comparison
    improvement_volume INTEGER,          -- Volume change
    improvement_reach INTEGER,           -- Reach change
    days_since_last_survey INTEGER,
    verified_words_between_surveys INTEGER,
    efficiency_score FLOAT               -- Learning efficiency metric
);
```

## Testimonial Data

### User Progress Story

```json
{
  "headline": "詞彙量增長 1,500 個字！",
  "story": "在 LexiCraft 學習 3 個月以來，我的詞彙量從基礎測驗到現在增長了 1,500 個字，成長幅度達到 42%，系統透過學習記錄讓我的測驗時間大幅縮短，共節省了 35 道題目。",
  "milestones": [
    { "date": "2024-09-01", "volume": 2000, "improvement": 0 },
    { "date": "2024-10-01", "volume": 2800, "improvement": 800 },
    { "date": "2024-12-01", "volume": 3500, "improvement": 700 }
  ]
}
```

### Platform Stats

```json
{
  "total_users_with_surveys": 500,
  "users_with_multiple_surveys": 200,
  "avg_vocabulary_growth": 1200,
  "top_10_percent_growth": 3000,
  "questions_saved_percentage": 40.0
}
```

## Migration Steps

1. Run the migration:
   ```bash
   # In Supabase SQL Editor, run:
   backend/migrations/010_progressive_survey_model.sql
   ```

2. Restart backend:
   ```bash
   cd backend && source venv/bin/activate
   uvicorn src.main:app --reload --port 8000
   ```

3. Test warm-start:
   ```bash
   # Start survey as authenticated user with learning progress
   curl -X POST http://localhost:8000/api/v1/survey/start \
     -H "Content-Type: application/json" \
     -d '{"user_id": "your-uuid", "use_prior_knowledge": true}'
   ```

## Value Proposition

1. **For Users**:
   - Shorter surveys (40% fewer questions after learning)
   - Progress visualization over time
   - Efficiency metrics ("You're learning 1.5x faster!")

2. **For Platform (Testimonials)**:
   - Concrete growth data per user
   - Platform-wide efficiency stats
   - Auto-generated testimonial text

3. **For Methodology Validation**:
   - Prove that time with platform = better assessments
   - Track correlation between learning and survey accuracy
   - Demonstrate warm-start efficiency gains

