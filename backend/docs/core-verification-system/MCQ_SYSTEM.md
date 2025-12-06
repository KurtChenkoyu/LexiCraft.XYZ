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

The MCQ system integrates seamlessly with the spaced repetition verification system, providing two distinct flows for reviewing learning points:

### Two Verification Flows

#### Flow 1: MCQ-Integrated Verification (Recommended)
**Use Case:** When user needs to verify knowledge through a structured question

**Endpoints:**
- `GET /api/v1/mcq/get?sense_id={sense_id}` - Get adaptive MCQ
- `POST /api/v1/mcq/submit` - Submit answer with `verification_schedule_id`

**Advantages:**
- Provides structured assessment
- Offers immediate feedback and explanations
- Maps MCQ performance to spaced repetition ratings automatically
- Tracks detailed statistics (response time, difficulty matching)

#### Flow 2: Direct Review Verification
**Use Case:** When user self-assesses their knowledge directly

**Endpoints:**
- `POST /api/v1/verification/review` - Direct performance rating submission

**Advantages:**
- Faster for confident users
- User controls their own assessment
- No MCQ generation overhead

---

### MCQ-Integrated Flow: Detailed Breakdown

#### Step 1: Get MCQ for Verification

**Endpoint:** `GET /api/v1/mcq/get`

**Query Parameters:**
- `sense_id` (required): The sense ID to verify
- `mcq_type` (optional): Filter by type (meaning, usage, discrimination)

**Process:**
1. System estimates user's ability for the sense (0.0-1.0)
2. Queries `mcq_pool` for available MCQs matching the sense
3. Filters MCQs by difficulty (target: ability ± 0.1)
4. Prefers MCQs with good discrimination (> 0.30)
5. Returns selected MCQ with metadata

**Response Example:**
```json
{
  "mcq_id": "550e8400-e29b-41d4-a716-446655440000",
  "sense_id": "break.n.01",
  "word": "break",
  "mcq_type": "meaning",
  "question": "What does 'break' mean in this context?",
  "context": "I need a break from work.",
  "options": [
    {"text": "休息", "source": "target"},
    {"text": "打破", "source": "confused"},
    {"text": "继续", "source": "opposite"},
    {"text": "开始", "source": "similar"}
  ],
  "user_ability": 0.65,
  "mcq_difficulty": 0.68,
  "selection_reason": "matched_ability"
}
```

#### Step 2: Submit MCQ Answer

**Endpoint:** `POST /api/v1/mcq/submit`

**Request:**
```json
{
  "mcq_id": "550e8400-e29b-41d4-a716-446655440000",
  "selected_index": 0,
  "response_time_ms": 3500,
  "verification_schedule_id": 123  // Optional but recommended
}
```

**Process (When `verification_schedule_id` is provided):**

1. **MCQ Processing:**
   - Validates answer (correct/incorrect)
   - Updates MCQ statistics (attempts, correct count)
   - Updates learner ability estimate
   - Generates explanation and feedback

2. **Verification Schedule Lookup:**
   - Loads `verification_schedule` record by ID
   - Retrieves associated `learning_progress_id`
   - Loads current card state from `verification_schedule` table

3. **Performance Rating Mapping:**
   - Maps MCQ result to spaced repetition rating (0-4):
     ```
     Incorrect:
       - Response time > 10s → HARD (1)
       - Response time ≤ 10s → AGAIN (0)
     
     Correct:
       - Response time < 2s → EASY (3)
       - Response time 2-5s + easy MCQ → EASY (3)
       - Response time 2-5s + hard MCQ → GOOD (2)
       - Response time > 5s → GOOD (2)
     ```

4. **Spaced Repetition Processing:**
   - Gets user's algorithm (SM-2+ or FSRS)
   - Processes review with mapped rating
   - Updates card state (interval, mastery level, etc.)
   - Saves review history to `fsrs_review_history`

5. **Verification Schedule Update:**
   - Marks schedule as `completed = true`
   - Sets `completed_at = NOW()`
   - Sets `passed = is_correct`
   - Sets `score = 1.0` if correct, `0.0` if incorrect

**Response:**
```json
{
  "is_correct": true,
  "correct_index": 0,
  "explanation": "正確答案是「休息」。\n在句子「I need a break from work」中，\"break\" 表示「休息」。",
  "feedback": "Well done!",
  "ability_before": 0.65,
  "ability_after": 0.70,
  "mcq_difficulty": 0.68,
  "verification_result": {
    "next_review_date": "2025-01-15",
    "next_interval_days": 3,
    "was_correct": true,
    "retention_predicted": 0.92,
    "mastery_level": "familiar",
    "mastery_changed": false,
    "became_leech": false,
    "algorithm_type": "fsrs"
  }
}
```

---

### Direct Review Flow: Detailed Breakdown

#### Endpoint: `POST /api/v1/verification/review`

**Use Case:** User self-assesses their knowledge without MCQ

**Request:**
```json
{
  "learning_progress_id": 456,
  "performance_rating": 2,  // 0=Again, 1=Hard, 2=Good, 3=Easy, 4=Perfect
  "response_time_ms": 2000  // Optional
}
```

**Process:**
1. Loads card state from `verification_schedule`
2. Gets user's algorithm (SM-2+ or FSRS)
3. Processes review with provided rating
4. Updates card state and review history
5. Returns next review date and interval

**Response:**
```json
{
  "success": true,
  "next_review_date": "2025-01-15",
  "next_interval_days": 3,
  "was_correct": true,
  "retention_predicted": 0.92,
  "mastery_level": "familiar",
  "mastery_changed": false,
  "became_leech": false,
  "algorithm_type": "fsrs"
}
```

**Note:** This flow does NOT provide explanations or feedback - user already knows the answer.

---

### Key Differences Between Flows

| Aspect | MCQ-Integrated Flow | Direct Review Flow |
|--------|-------------------|-------------------|
| **Assessment Method** | Structured MCQ question | User self-assessment |
| **Explanations** | ✅ Provided automatically | ❌ Not provided |
| **Feedback** | ✅ Immediate feedback | ❌ No feedback |
| **Performance Mapping** | Automatic (MCQ result → rating) | Manual (user provides rating) |
| **Statistics** | Detailed (response time, difficulty) | Basic (rating only) |
| **Use Case** | Learning/verification | Quick review for confident users |
| **Endpoints** | `/mcq/get` + `/mcq/submit` | `/verification/review` |

---

### How Explanations Are Provided

#### Explanation Source

Explanations come from the `mcq_pool.explanation` field, which is generated during MCQ creation by `MCQAssembler`:

**For Translation MCQs:**
```
正確答案是「{correct_definition}」。
在句子「{context_sentence}」中，"{word}" 表示「{correct_definition}」。
```

**For Discrimination MCQs:**
```
正確答案是：「{correct_sentence}」
這個句子中的 "{word}" 表示「{correct_definition}」。
```

**For Context MCQs:**
```
正確答案是 "{word}"。
"{word}" 和 "{confused_word}" 容易混淆（{confusion_reason}）。
```

#### Feedback Generation

Feedback is dynamically generated based on:
- **Correct answers:**
  - Hard MCQ (difficulty < 0.4): "Excellent! That was a challenging one."
  - Easy MCQ (difficulty > 0.7): "Correct! Keep going."
  - Normal: "Well done!"

- **Incorrect answers:**
  - Shows correct answer: "The correct answer was: {correct_option_text}"

#### When Explanations Are Shown

Explanations are **always** included in the `POST /mcq/submit` response, regardless of whether the answer was correct or incorrect. This helps users learn from both successes and mistakes.

**Example Response (Incorrect Answer):**
```json
{
  "is_correct": false,
  "correct_index": 0,
  "explanation": "正確答案是「休息」。\n在句子「I need a break from work」中，\"break\" 表示「休息」。",
  "feedback": "The correct answer was: 休息",
  ...
}
```

---

### Complete Integration Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    VERIFICATION SCHEDULE                    │
│              (Card due for review on Day 3)                  │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
        ┌───────────────────────────────────────┐
        │   USER CHOOSES VERIFICATION METHOD     │
        └───────┬───────────────────┬───────────┘
                │                   │
                ▼                   ▼
    ┌───────────────────┐   ┌──────────────────┐
    │  MCQ-INTEGRATED   │   │  DIRECT REVIEW   │
    │      FLOW         │   │      FLOW        │
    └─────────┬─────────┘   └────────┬─────────┘
              │                       │
              ▼                       ▼
    GET /mcq/get              POST /verification/review
    (sense_id)               (learning_progress_id,
                              performance_rating)
              │                       │
              ▼                       │
    User answers MCQ                 │
              │                       │
              ▼                       │
    POST /mcq/submit                 │
    (mcq_id, selected_index,         │
     verification_schedule_id)       │
              │                       │
              ▼                       │
    ┌─────────────────────────┐      │
    │  MCQ PROCESSING         │      │
    │  - Grade answer         │      │
    │  - Update statistics    │      │
    │  - Update ability       │      │
    │  - Generate explanation │      │
    └───────────┬─────────────┘      │
                │                   │
                ▼                   │
    ┌─────────────────────────┐      │
    │  VERIFICATION PROCESSING│      │
    │  - Load card state      │      │
    │  - Map to rating        │      │
    │  - Process review       │      │
    │  - Update schedule      │      │
    └───────────┬─────────────┘      │
                │                   │
                └─────────┬─────────┘
                          ▼
            ┌─────────────────────┐
            │  UPDATE SCHEDULE     │
            │  - completed = true  │
            │  - Set next review   │
            │  - Save history      │
            └─────────────────────┘
```

---

### Error Handling

**MCQ Submission with Invalid `verification_schedule_id`:**
- MCQ processing still succeeds
- Verification processing fails gracefully
- Error is logged but doesn't fail the request
- Response includes MCQ result but `verification_result = null`

**Missing Card State:**
- If `verification_schedule` exists but card state is missing, verification is skipped
- Warning is logged
- MCQ result is still returned

**Verification Schedule Not Found:**
- If `verification_schedule_id` doesn't exist or belongs to different user
- Verification processing is skipped
- MCQ processing continues normally

---

### Database Updates

When `verification_schedule_id` is provided in MCQ submission:

**Tables Updated:**
1. `mcq_attempts` - New attempt record
2. `mcq_statistics` - Updated metrics
3. `learner_ability` - Updated ability estimate
4. `verification_schedule` - Marked completed, updated state
5. `fsrs_review_history` - New review record

**Transaction Safety:**
- MCQ processing and verification processing are in the same transaction
- If verification fails, MCQ processing still commits (graceful degradation)
- Verification errors are logged but don't fail the request

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


