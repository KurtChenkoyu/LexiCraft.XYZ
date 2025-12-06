# MCQ System Documentation
## Adaptive Multiple-Choice Questions for Verification

**Status:** 📋 Documentation  
**Component:** Core Verification System - Part 2

---

## Overview

The MCQ System provides adaptive multiple-choice questions for verifying word knowledge. It uses adaptive difficulty to match questions to learner ability and statistical validation to ensure question quality.

---

## Architecture

### Three-Layer System

```
Layer 1: MCQ GENERATION
├── Generate questions from learning points
├── Create distractors (similar words)
└── Store in mcq_pool

Layer 2: ADAPTIVE SELECTION
├── Estimate learner ability
├── Select MCQ matching ability
└── Optimize difficulty

Layer 3: STATISTICAL VALIDATION
├── Track performance metrics
├── Calculate discrimination, difficulty
└── Flag poor-quality MCQs
```

---

## MCQ Types

### 1. Translation MCQ
**Question:** "What does 'break' mean?"  
**Options:**
- A. 休息 (correct)
- B. 打破
- C. 继续
- D. 开始

### 2. Discrimination MCQ
**Question:** "Which word fits: I need a ___ from work"  
**Options:**
- A. break (correct)
- B. brake
- C. brake (homophone)
- D. broke

### 3. Context MCQ
**Question:** "Complete: The glass will ___ if you drop it"  
**Options:**
- A. break (correct)
- B. brake
- C. brake
- D. broke

---

## Adaptive Difficulty

### How It Works

1. **Estimate Learner Ability**
   - Track ability per sense/word
   - Range: 0.0 (no knowledge) to 1.0 (perfect)
   - Updated after each MCQ attempt

2. **Select Optimal MCQ**
   - Target difficulty = learner ability ± 0.1
   - Select MCQ with difficulty in range
   - Prefer MCQs with good discrimination (> 0.30)

3. **Update After Answer**
   - If correct: ability += 0.05
   - If wrong: ability -= 0.05
   - Clamp between 0.0 and 1.0

### Ability Estimation

```python
# Initial ability
ability = 0.5  # Unknown, assume 50/50

# After each attempt
if is_correct:
    ability = min(1.0, ability + 0.05)
else:
    ability = max(0.0, ability - 0.05)

# Difficulty matching
target_difficulty = ability
acceptable_range = (ability - 0.1, ability + 0.1)
```

---

## Statistical Validation

### Metrics Tracked

**1. Difficulty Index**
- Percentage of users who answer correctly
- Range: 0.0 (everyone wrong) to 1.0 (everyone correct)
- Optimal: 0.5-0.7 (moderate difficulty)

**2. Discrimination Index**
- How well MCQ distinguishes strong vs weak learners
- Range: -1.0 to 1.0
- Optimal: > 0.30 (good discrimination)

**3. Distractor Analysis**
- Which distractors are selected
- How often each distractor is chosen
- Flag distractors never selected (need replacement)

### Quality Flags

MCQs are flagged for review if:
- Discrimination < 0.30 (poor discrimination)
- Difficulty < 0.20 (too easy) or > 0.80 (too hard)
- Distractor never selected (needs replacement)
- Low attempt count (< 10 attempts)

---

## Data Flow

### 1. MCQ Generation

```
Admin/System generates MCQs for learning point
  ↓
MCQAssembler creates question
  - Question text
  - Correct answer
  - Distractors (3 similar words)
  - MCQ type (translation, discrimination, context)
  ↓
Store in mcq_pool
  - sense_id
  - word
  - question
  - options
  - correct_index
  - mcq_type
```

### 2. MCQ Selection (Adaptive)

```
User needs MCQ for verification
  ↓
Get learner ability for sense
  ↓
Query mcq_pool for sense
  ↓
Filter by difficulty (ability ± 0.1)
  ↓
Prefer MCQs with good discrimination
  ↓
Return selected MCQ
```

### 3. Answer Processing

```
User submits answer
  ↓
Grade answer (correct/incorrect)
  ↓
Update learner ability
  ↓
Update MCQ statistics:
  - total_attempts += 1
  - correct_attempts += (1 if correct else 0)
  - distractor_selections[option] += 1
  ↓
Recalculate metrics:
  - difficulty = correct_attempts / total_attempts
  - discrimination = (high_group_correct - low_group_correct) / n
  ↓
Flag if quality issues
  ↓
If verification_schedule_id provided:
  - Process spaced repetition review
  - Update verification schedule
```

---

## API Endpoints

### `POST /api/v1/mcq/generate`

Generate MCQs for a sense.

**Request:**
```json
{
  "sense_id": "break.n.01",
  "count": 3,
  "mcq_types": ["translation", "discrimination", "context"]
}
```

**Response:**
```json
{
  "generated": 3,
  "mcqs": [
    {
      "mcq_id": "uuid",
      "sense_id": "break.n.01",
      "word": "break",
      "mcq_type": "translation",
      "question": "What does 'break' mean?",
      "options": [...],
      "correct_index": 0
    }
  ]
}
```

### `GET /api/v1/mcq/get`

Get adaptive MCQ for verification.

**Query Parameters:**
- `learning_progress_id`: Required
- `count`: Number of MCQs (default: 1)

**Response:**
```json
{
  "mcq_id": "uuid",
  "sense_id": "break.n.01",
  "word": "break",
  "mcq_type": "translation",
  "question": "What does 'break' mean?",
  "options": [
    {"text": "休息", "source": "translation"},
    {"text": "打破", "source": "distractor"},
    {"text": "继续", "source": "distractor"},
    {"text": "开始", "source": "distractor"}
  ],
  "user_ability": 0.65,
  "mcq_difficulty": 0.68,
  "selection_reason": "matched_ability"
}
```

### `POST /api/v1/mcq/submit`

Submit MCQ answer.

**Request:**
```json
{
  "mcq_id": "uuid",
  "selected_index": 0,
  "response_time_ms": 3500,
  "verification_schedule_id": 123  // Optional: links to verification
}
```

**Response:**
```json
{
  "correct": true,
  "user_ability_before": 0.65,
  "user_ability_after": 0.70,
  "mcq_difficulty": 0.68,
  "mcq_discrimination": 0.45,
  "verification_processed": true,  // If verification_schedule_id provided
  "next_review_date": "2025-01-15"
}
```

---

## Database Schema

### `mcq_pool`
Generated MCQs.

```sql
CREATE TABLE mcq_pool (
    id UUID PRIMARY KEY,
    sense_id TEXT NOT NULL,
    word TEXT,
    mcq_type TEXT,  -- 'translation', 'discrimination', 'context'
    question TEXT,
    options JSONB,  -- Array of options
    correct_index INTEGER,
    context TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### `mcq_statistics`
Quality metrics for each MCQ.

```sql
CREATE TABLE mcq_statistics (
    mcq_id UUID PRIMARY KEY REFERENCES mcq_pool(id),
    total_attempts INTEGER DEFAULT 0,
    correct_attempts INTEGER DEFAULT 0,
    difficulty_index FLOAT,  -- correct_attempts / total_attempts
    discrimination_index FLOAT,
    distractor_selections JSONB,  -- {option_index: count}
    avg_response_time_ms INTEGER,
    flagged_for_review BOOLEAN DEFAULT FALSE,
    last_calculated_at TIMESTAMPTZ
);
```

### `learner_ability`
Adaptive difficulty tracking.

```sql
CREATE TABLE learner_ability (
    user_id UUID,
    sense_id TEXT,
    ability_estimate FLOAT DEFAULT 0.5,  -- 0.0 to 1.0
    total_attempts INTEGER DEFAULT 0,
    last_updated TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (user_id, sense_id)
);
```

### `mcq_attempts`
User answer history.

```sql
CREATE TABLE mcq_attempts (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    mcq_id UUID REFERENCES mcq_pool(id),
    sense_id TEXT,
    verification_schedule_id INTEGER,  -- Links to verification
    is_correct BOOLEAN,
    selected_index INTEGER,
    response_time_ms INTEGER,
    attempted_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## Implementation Details

### File Structure

```
backend/src/
├── api/
│   └── mcq.py                    # API endpoints
├── mcq_adaptive.py               # Adaptive difficulty service
├── mcq_assembler.py              # MCQ generation
└── database/
    └── postgres_crud/
        └── mcq_stats.py          # MCQ statistics CRUD
```

### Key Services

**1. MCQAdaptiveService**
```python
# backend/src/mcq_adaptive.py
class MCQAdaptiveService:
    def get_adaptive_mcq(
        self,
        user_id: UUID,
        sense_id: str,
        learning_progress_id: int
    ) -> MCQSelection:
        # 1. Get learner ability
        # 2. Query available MCQs
        # 3. Select MCQ matching ability
        # 4. Return selection
```

**2. MCQAssembler**
```python
# backend/src/mcq_assembler.py
class MCQAssembler:
    def assemble_mcq(
        self,
        learning_point: dict,
        mcq_type: MCQType
    ) -> MCQ:
        # 1. Generate question based on type
        # 2. Create distractors
        # 3. Assemble MCQ
        # 4. Return MCQ
```

---

## Integration with Verification System

### When Verification Schedule Triggers

1. **Get MCQ**: `GET /api/v1/mcq/get?learning_progress_id=123`
   - Adaptive difficulty selects MCQ
   - Returns MCQ for user to answer

2. **Submit Answer**: `POST /api/v1/mcq/submit`
   - Include `verification_schedule_id` in request
   - System processes both:
     - MCQ statistics update
     - Verification review processing
   - Returns combined result

### Combined Flow

```
Verification schedule triggers (Day 3)
  ↓
Get adaptive MCQ
  ↓
User answers MCQ
  ↓
Submit answer (with verification_schedule_id)
  ↓
System processes:
  1. MCQ statistics update
  2. Learner ability update
  3. Verification review processing
  4. Schedule next review
  ↓
Return combined result
```

---

## Quality Assurance

### MCQ Quality Metrics

**Good MCQ:**
- Discrimination > 0.30
- Difficulty 0.5-0.7
- All distractors selected at least once
- 20+ attempts for reliable metrics

**Poor MCQ (Flagged):**
- Discrimination < 0.30
- Difficulty < 0.20 or > 0.80
- Distractor never selected
- Needs review/replacement

### Quality Report

`GET /api/v1/mcq/quality` returns:
- MCQs flagged for review
- Quality distribution
- Recommendations for improvement

---

## Future Tasks / Improvements Needed

### Documentation Needed
- [ ] Complete MCQ generation algorithm
- [ ] Distractor selection logic
- [ ] Discrimination calculation formula
- [ ] Quality flagging rules

### Implementation Gaps
- [ ] Automatic MCQ generation for new words
- [ ] MCQ quality dashboard
- [ ] Distractor replacement system
- [ ] Batch MCQ generation

### Enhancements
- [ ] More MCQ types (fill-in-blank, matching)
- [ ] Adaptive distractor selection
- [ ] A/B testing different MCQ formats
- [ ] Machine learning for MCQ quality prediction

---

**Document Version:** 1.0  
**Last Updated:** January 2025  
**Related Docs:** `WORD_VERIFICATION_SYSTEM.md`, `VERIFICATION_FLOW_GUIDING.md`


