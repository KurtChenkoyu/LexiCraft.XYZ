# Word Verification System Documentation
## Spaced Repetition for Vocabulary Retention

**Status:** 📋 Documentation  
**Component:** Core Verification System - Part 1

---

## Overview

The Word Verification System implements spaced repetition to ensure long-term vocabulary retention. It schedules reviews at optimal intervals (Day 3, 7, 14, 30, 60) and tracks mastery progression. The system verifies and solidifies vocabulary knowledge that users have typically encountered elsewhere (school, books, media). We are not a school or curriculum that presents words in complete contexts - users learn from outside sources, and we verify/solidify that knowledge.

---

## Architecture

### Algorithms

**1. SM-2+ (Legacy)**
- Modified SuperMemo 2 algorithm
- Ease factor adjustment
- Interval calculation
- Leech detection

**2. FSRS (Modern)**
- Free Spaced Repetition Scheduler
- Neural network-based machine learning algorithm
- More accurate retention prediction (predicts when you'll forget)
- 20-30% fewer reviews needed vs SM-2+ for same retention
- Requires 100+ reviews for personalization (learns your forgetting curve)
- Uses stability (memory strength) and difficulty (word hardness) concepts
- Target retention: 90% (configurable)

### Algorithm Assignment

- **New Users**: Random 50/50 split (SM-2+ vs FSRS)
- **Migration**: Users with 100+ reviews can migrate to FSRS
- **A/B Testing**: Compare algorithm performance
- **Assignment Service**: `backend/src/spaced_repetition/assignment_service.py`
- **Storage**: `user_algorithm_assignment` table tracks assignments

### FSRS Key Concepts

**Stability**: Memory strength - how well you know this word
- Higher stability = longer intervals between reviews
- Increases when you answer correctly
- Decreases when you answer incorrectly
- Measured in days (e.g., stability=30 means you'll remember for ~30 days)

**Difficulty**: Word hardness - how hard this word is (learned from all users)
- Range: 0.0 (easiest) to 1.0 (hardest)
- Global property (same for all users)
- Learned from aggregate review data
- Stored in `word_global_difficulty` table

**Retention Probability**: Predicted probability you'll remember at review time
- Range: 0.0 (forgotten) to 1.0 (remembered)
- Calculated using: `retention = f(stability, difficulty, elapsed_time)`
- Target: 90% retention (reviews scheduled when retention drops below threshold)

**FSRS State**: Complete card state stored in JSONB
- Includes: stability, difficulty, reps, lapses, elapsed_days, scheduled_days, state
- Allows full restoration of FSRS Card object
- Stored in `verification_schedule.fsrs_state` column

---

## Data Flow

### 1. Starting Verification (Initial)

```
User selects word for verification (from suggestions, search, or survey)
  ↓
INSERT INTO learning_progress
  - user_id
  - learning_point_id
  - learned_at
  - tier (0-5)
  - status ('pending')  -- Ready for verification
  ↓
CREATE verification_schedule
  - scheduled_date: calculated by algorithm
    * SM-2+: Typically Day 3 (fixed progression)
    * FSRS: Calculated to hit 90% retention (varies by word difficulty)
  - algorithm_type: user's assigned algorithm (from user_algorithm_assignment)
  - mastery_level: 'learning'
  - For FSRS: Initialize stability=0, difficulty=0.5, fsrs_state={}
  ↓
User takes first MCQ quiz
  ↓
Learning/solidification happens through MCQ explanations (especially when wrong)
```

### 2. Review Processing

```
User requests due cards
  ↓
GET verification_schedule WHERE scheduled_date <= today
  ↓
For each card:
  - Get MCQ (adaptive difficulty)
  - User answers MCQ
  - **Show detailed explanation** (especially if wrong - this is where learning/solidification happens)
  - Process answer
  ↓
UPDATE verification_schedule
  - completed: TRUE
  - completed_at: NOW()
  - passed: is_correct
  - Update algorithm state:
    * SM-2+: Update ease_factor, consecutive_correct, current_interval
    * FSRS: Update stability, difficulty, retention_probability, fsrs_state (full JSONB)
  - Record in fsrs_review_history (if FSRS)
  ↓
If passed:
  - Schedule next review:
    * SM-2+: Fixed progression (Day 7, 14, 30...) based on ease_factor
    * FSRS: Calculated interval to maintain 90% retention (varies based on stability/difficulty)
  - Update mastery_level (based on stability for FSRS, tier for SM-2+)
  - Update learning_progress status to 'verified' if appropriate
If failed:
  - Reschedule (algorithm determines interval):
    * SM-2+: Reset to Day 1, decrease ease_factor
    * FSRS: Reset stability, increase difficulty, reschedule based on new stability
  - Adjust difficulty down (SM-2+) or up (FSRS)
  - **Detailed explanation helps user learn/solidify** (this is the learning/solidification mechanism)
```

### 3. Mastery Progression

```
Mastery Levels:
- learning → Familiar → Known → Mastered

Progression Rules:
- Learning: Initial state, Tier 0-1
- Familiar: Passed Day 3 review, Tier 2
- Known: Passed Day 7 review, Tier 3-4
- Mastered: Passed Day 14+ review, Tier 5+
```

---

## API Endpoints

### `POST /api/v1/verification/review`

Process a review and update spaced repetition schedule.

**Request:**
```json
{
  "learning_progress_id": 123,
  "performance_rating": 2,  // 0-4: Again, Hard, Good, Easy, Perfect
  "response_time_ms": 3500
}
```

**Response:**
```json
{
  "success": true,
  "next_review_date": "2025-01-15",
  "next_interval_days": 7,
  "was_correct": true,
  "retention_predicted": 0.85,
  "mastery_level": "familiar",
  "mastery_changed": true,
  "became_leech": false,
  "algorithm_type": "fsrs"
}
```

### `GET /api/v1/verification/due`

Get cards due for review.

**Query Parameters:**
- `limit`: Number of cards to return (default: 20)

**Response:**
```json
[
  {
    "verification_schedule_id": 123,
    "learning_progress_id": 456,
    "learning_point_id": "break.n.01",
    "word": "break",
    "scheduled_date": "2025-01-10",
    "days_overdue": 2,
    "mastery_level": "learning",
    "retention_predicted": 0.65
  }
]
```

### `GET /api/v1/verification/stats`

Get user's review statistics.

**Response:**
```json
{
  "algorithm": "fsrs",
  "total_reviews": 1250,
  "total_correct": 980,
  "retention_rate": 0.784,
  "cards_learning": 45,
  "cards_familiar": 120,
  "cards_known": 350,
  "cards_mastered": 735,
  "cards_leech": 5,
  "avg_interval_days": 12.5,
  "reviews_today": 15
}
```

### `GET /api/v1/verification/algorithm`

Get user's algorithm assignment and migration eligibility.

**Response:**
```json
{
  "algorithm": "fsrs",
  "can_migrate_to_fsrs": false,
  "review_count": 1250,
  "reviews_needed_for_migration": 0,
  "assignment_date": "2024-12-01T00:00:00Z",
  "assignment_reason": "random",
  "fsrs_parameters": null  // Custom parameters if personalized
}
```

### `POST /api/v1/verification/migrate-to-fsrs`

Migrate user from SM-2+ to FSRS algorithm.

**Requirements:**
- User must have 100+ reviews
- User must currently be on SM-2+

**Request:**
```json
{
  "estimate_parameters": true  // Estimate FSRS parameters from SM-2+ history
}
```

**Response:**
```json
{
  "success": true,
  "algorithm": "fsrs",
  "migrated_cards": 450,
  "estimated_parameters": {
    "w": [...],  // FSRS parameter vector
    "request_retention": 0.9,
    "maximum_interval": 730
  }
}
```

**Process:**
1. Check eligibility (100+ reviews)
2. Convert all SM-2+ cards to FSRS
3. Estimate FSRS parameters from review history (optional)
4. Update `user_algorithm_assignment` table
5. Backfill `fsrs_review_history` from existing reviews

---

## Database Schema

### `learning_progress`
Tracks which words a user is verifying. Learning/solidification happens through MCQ explanations, not through a separate "learn word" step. The system verifies what users have encountered elsewhere and facilitates learning when they encounter unknown words.

```sql
CREATE TABLE learning_progress (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    learning_point_id TEXT NOT NULL,  -- Neo4j learning_point.id
    learned_at TIMESTAMPTZ DEFAULT NOW(),
    tier INTEGER NOT NULL,  -- 0-5, indicates mastery level
    status TEXT DEFAULT 'learning'  -- 'learning', 'pending', 'verified', 'failed'
);
```

### `verification_schedule`
Spaced repetition schedule for each word. Supports both SM-2+ and FSRS algorithms.

```sql
CREATE TABLE verification_schedule (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    learning_progress_id INTEGER REFERENCES learning_progress(id),
    test_day INTEGER,  -- 3, 7, 14, 30, 60... (SM-2+ specific)
    scheduled_date DATE,
    completed BOOLEAN DEFAULT FALSE,
    completed_at TIMESTAMPTZ,
    passed BOOLEAN,
    
    -- Algorithm type
    algorithm_type TEXT DEFAULT 'sm2_plus',  -- 'sm2_plus' or 'fsrs'
    
    -- Algorithm state (SM-2+)
    current_interval INTEGER,  -- Days until next review
    ease_factor FLOAT DEFAULT 2.5,  -- SM-2+ ease factor (1.3-3.0)
    consecutive_correct INTEGER DEFAULT 0,  -- SM-2+ consecutive correct count
    
    -- Algorithm state (FSRS)
    stability FLOAT,  -- FSRS: Memory strength in days
    difficulty FLOAT DEFAULT 0.5,  -- FSRS: Word difficulty (0-1)
    retention_probability FLOAT,  -- FSRS: Predicted retention at review time
    fsrs_state JSONB,  -- FSRS: Complete card state (stability, difficulty, reps, lapses, etc.)
    last_review_date DATE,  -- FSRS: Needed for elapsed time calculation
    
    -- Mastery tracking
    mastery_level TEXT DEFAULT 'learning',  -- 'learning', 'familiar', 'known', 'mastered', 'leech'
    is_leech BOOLEAN DEFAULT FALSE,
    
    -- Performance
    total_reviews INTEGER DEFAULT 0,
    total_correct INTEGER DEFAULT 0,
    avg_response_time_ms INTEGER
);

-- Indexes
CREATE INDEX idx_verification_schedule_algorithm ON verification_schedule(algorithm_type);
CREATE INDEX idx_verification_schedule_mastery ON verification_schedule(mastery_level);
CREATE INDEX idx_verification_schedule_leech ON verification_schedule(is_leech) WHERE is_leech = true;
```

### `user_algorithm_assignment`
Tracks which algorithm each user is assigned to (for A/B testing).

```sql
CREATE TABLE user_algorithm_assignment (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    algorithm TEXT NOT NULL DEFAULT 'sm2_plus',  -- 'sm2_plus' or 'fsrs'
    assigned_at TIMESTAMP DEFAULT NOW(),
    assignment_reason TEXT DEFAULT 'random',  -- 'random', 'manual', 'migration', 'opt_in'
    can_migrate_to_fsrs BOOLEAN DEFAULT FALSE,  -- True when user has 100+ reviews
    fsrs_parameters JSONB,  -- Custom FSRS parameters after optimization (personalized model)
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    CONSTRAINT valid_algorithm CHECK (algorithm IN ('sm2_plus', 'fsrs'))
);

CREATE INDEX idx_user_algorithm_user ON user_algorithm_assignment(user_id);
CREATE INDEX idx_user_algorithm_type ON user_algorithm_assignment(algorithm);
```

### `fsrs_review_history`
Detailed review history for FSRS algorithm (used for parameter optimization and analytics).

```sql
CREATE TABLE fsrs_review_history (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    learning_progress_id INTEGER NOT NULL REFERENCES learning_progress(id) ON DELETE CASCADE,
    
    -- Review event data
    review_date TIMESTAMP NOT NULL DEFAULT NOW(),
    performance_rating INTEGER NOT NULL,  -- 0-4: Again(0), Hard(1), Good(2), Easy(3), Perfect(4)
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
    algorithm_type TEXT NOT NULL DEFAULT 'fsrs',
    
    created_at TIMESTAMP DEFAULT NOW(),
    
    CONSTRAINT valid_rating CHECK (performance_rating >= 0 AND performance_rating <= 4)
);

CREATE INDEX idx_fsrs_history_user ON fsrs_review_history(user_id);
CREATE INDEX idx_fsrs_history_learning ON fsrs_review_history(learning_progress_id);
CREATE INDEX idx_fsrs_history_date ON fsrs_review_history(review_date);
CREATE INDEX idx_fsrs_history_algorithm ON fsrs_review_history(algorithm_type);
```

### `word_global_difficulty`
Global word difficulty statistics (learned from all users, used by FSRS).

```sql
CREATE TABLE word_global_difficulty (
    id SERIAL PRIMARY KEY,
    learning_point_id TEXT NOT NULL UNIQUE,  -- References Neo4j learning_point.id
    
    -- Global stats from all users
    total_reviews INTEGER DEFAULT 0,
    total_correct INTEGER DEFAULT 0,
    global_error_rate FLOAT DEFAULT 0.0,  -- 1 - (correct / reviews)
    average_ease_factor FLOAT DEFAULT 2.5,  -- SM-2+ average
    average_stability FLOAT,  -- FSRS average stability
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

CREATE INDEX idx_word_difficulty_learning ON word_global_difficulty(learning_point_id);
CREATE INDEX idx_word_difficulty_category ON word_global_difficulty(difficulty_category);
CREATE INDEX idx_word_difficulty_score ON word_global_difficulty(difficulty_score DESC);
```

### `algorithm_comparison_metrics`
Daily metrics for comparing SM-2+ vs FSRS performance (A/B testing analytics).

```sql
CREATE TABLE algorithm_comparison_metrics (
    id SERIAL PRIMARY KEY,
    
    -- Aggregation period
    date DATE NOT NULL,
    algorithm_type TEXT NOT NULL,  -- 'sm2_plus' or 'fsrs'
    
    -- User counts
    total_users INTEGER DEFAULT 0,
    active_users INTEGER DEFAULT 0,  -- Users with reviews on this date
    
    -- Review metrics
    total_reviews INTEGER DEFAULT 0,
    total_correct INTEGER DEFAULT 0,
    retention_rate FLOAT DEFAULT 0.0,  -- correct / reviews
    
    -- Efficiency metrics
    avg_reviews_per_user FLOAT DEFAULT 0.0,
    avg_interval_days FLOAT DEFAULT 0.0,
    avg_retention_rate FLOAT DEFAULT 0.0,
    
    -- Mastery metrics
    cards_learning INTEGER DEFAULT 0,
    cards_familiar INTEGER DEFAULT 0,
    cards_known INTEGER DEFAULT 0,
    cards_mastered INTEGER DEFAULT 0,
    cards_leech INTEGER DEFAULT 0,
    
    created_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(date, algorithm_type)
);

CREATE INDEX idx_algorithm_metrics_date ON algorithm_comparison_metrics(date);
CREATE INDEX idx_algorithm_metrics_type ON algorithm_comparison_metrics(algorithm_type);
```

---

## Implementation Details

### File Structure

```
backend/src/
├── api/
│   ├── verification.py          # API endpoints (review, due, stats, algorithm, migrate)
│   └── analytics.py             # Algorithm comparison analytics
├── spaced_repetition/
│   ├── __init__.py
│   ├── algorithm_interface.py   # Abstract base class for algorithms
│   ├── sm2_service.py           # SM-2+ algorithm implementation
│   ├── fsrs_service.py           # FSRS algorithm implementation (wraps fsrs library)
│   └── assignment_service.py     # Algorithm assignment (A/B testing)
├── analytics/
│   └── algorithm_comparison.py  # SM-2+ vs FSRS comparison metrics
└── database/
    ├── models.py                 # Database models (VerificationSchedule, etc.)
    └── postgres_crud/
        └── verification.py       # CRUD operations for verification_schedule
```

### Key Functions

**1. Algorithm Assignment**
```python
# backend/src/spaced_repetition/assignment_service.py
from .assignment_service import AssignmentService

service = AssignmentService(db)
algorithm = service.get_or_assign_algorithm(user_id, db)
# Returns: 'sm2_plus' or 'fsrs'
```

**2. Process Review (Algorithm-Agnostic)**
```python
# backend/src/api/verification.py
from ..spaced_repetition import get_algorithm_for_user

# Get user's algorithm
algorithm = get_algorithm_for_user(user_id, db)

# Process review (works for both SM-2+ and FSRS)
result = algorithm.process_review(
    state=card_state,
    rating=PerformanceRating.GOOD,
    response_time_ms=1500
)

# Result contains:
# - new_state (updated CardState)
# - next_review_date
# - next_interval_days
# - retention_predicted (FSRS only)
# - mastery_changed
# - became_leech
```

**3. FSRS-Specific Operations**
```python
# backend/src/spaced_repetition/fsrs_service.py
from .fsrs_service import FSRSService

fsrs = FSRSService()

# Initialize new FSRS card
card_state = fsrs.initialize_card(
    user_id=user_id,
    learning_progress_id=123,
    learning_point_id="break.n.01",
    initial_difficulty=0.5
)

# Predict retention at future date
retention = fsrs.predict_retention(
    state=card_state,
    target_date=date.today() + timedelta(days=7)
)

# Optimize parameters (after 100+ reviews)
optimized_params = fsrs.optimize_parameters(
    review_history=history,
    current_parameters=None
)
```

### Key Functions

**1. Process Review**
```python
# backend/src/api/verification.py
@router.post("/review")
async def process_review(
    request: ProcessReviewRequest,
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db_session)
):
    # 1. Load card state
    # 2. Process with algorithm (SM-2+ or FSRS)
    # 3. Update schedule
    # 4. Schedule next review
    # 5. Update mastery level
    # 6. Return result
```

**2. Get Due Cards**
```python
# backend/src/api/verification.py
@router.get("/due")
async def get_due_cards(
    limit: int = 20,
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db_session)
):
    # 1. Query verification_schedule
    # 2. Filter: scheduled_date <= today AND completed = FALSE
    # 3. Sort: 
    #    - Overdue first (scheduled_date < today)
    #    - Then by retention_probability (lowest first, for FSRS)
    #    - Then by scheduled_date (earliest first)
    # 4. Return cards with algorithm-specific info
```

**3. Migrate to FSRS**
```python
# backend/src/api/verification.py
@router.post("/migrate-to-fsrs")
async def migrate_to_fsrs(
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db_session)
):
    # 1. Check eligibility (100+ reviews)
    # 2. Get all SM-2+ cards for user
    # 3. Convert each card to FSRS:
    #    - Estimate initial stability from ease_factor
    #    - Estimate difficulty from word_global_difficulty
    #    - Initialize fsrs_state
    # 4. Update user_algorithm_assignment
    # 5. Backfill fsrs_review_history from existing reviews
    # 6. Optionally optimize FSRS parameters
```

---

## FSRS Examples

### Example 1: Initializing a New FSRS Card

```python
# User starts verification for word "break"
fsrs = FSRSService()
card_state = fsrs.initialize_card(
    user_id=user_id,
    learning_progress_id=123,
    learning_point_id="break.n.01",
    initial_difficulty=0.5
)

# Result:
# - stability: 0 (new card)
# - difficulty: 0.5 (default, will be learned)
# - scheduled_date: tomorrow (Day 1)
# - fsrs_state: {stability: 0, difficulty: 0.5, reps: 0, lapses: 0, ...}
```

### Example 2: Processing First Review (Correct Answer)

```python
# User answers correctly (Good rating)
result = fsrs.process_review(
    state=card_state,
    rating=PerformanceRating.GOOD,
    response_time_ms=2000
)

# FSRS updates:
# - stability: 0 → 2.5 days (increased)
# - difficulty: 0.5 → 0.4 (decreased, word is easier)
# - scheduled_date: Day 3 (calculated to maintain 90% retention)
# - retention_predicted: 0.92 (at review time)
```

### Example 3: Processing Review (Incorrect Answer)

```python
# User answers incorrectly (Again rating)
result = fsrs.process_review(
    state=card_state,
    rating=PerformanceRating.AGAIN,
    response_time_ms=5000
)

# FSRS updates:
# - stability: 2.5 → 0.5 days (decreased significantly)
# - difficulty: 0.4 → 0.6 (increased, word is harder)
# - scheduled_date: Day 1 (reset, immediate review)
# - retention_predicted: 0.45 (low, needs review soon)
```

### Example 4: Predicting Retention

```python
# Check if user will remember word in 7 days
retention = fsrs.predict_retention(
    state=card_state,
    target_date=date.today() + timedelta(days=7)
)

# Returns: 0.85 (85% chance of remembering)
# If retention < 0.9, schedule review before target_date
```

## Integration with MCQ System

When a review is due:

1. **Get MCQ**: `GET /api/v1/mcq/get?learning_progress_id=123`
   - Adaptive difficulty selects appropriate MCQ
   - Returns MCQ matching learner ability
   - For FSRS: Can use `retention_probability` to prioritize cards

2. **Submit Answer**: `POST /api/v1/mcq/submit`
   - Records answer
   - Updates MCQ statistics
   - Updates learner ability
   - **Also processes verification review** (if verification_schedule_id provided)
   - For FSRS: Records in `fsrs_review_history` for parameter optimization

3. **Update Schedule**: Verification schedule updated based on result
   - SM-2+: Updates ease_factor, interval
   - FSRS: Updates stability, difficulty, retention_probability, fsrs_state

---

## Mastery Progression Logic

### Tier System
- **Tier 0**: Just learned, not verified
- **Tier 1**: Passed Day 3 review (Familiar)
- **Tier 2**: Passed Day 7 review
- **Tier 3**: Passed Day 14 review (Known)
- **Tier 4**: Passed Day 30 review
- **Tier 5+**: Passed Day 60+ review (Mastered)

### Status Mapping
- `learning`: Tier 0-1
- `familiar`: Tier 2
- `known`: Tier 3-4
- `mastered`: Tier 5+

---

## Algorithm Comparison: SM-2+ vs FSRS

### Key Differences

| Aspect | SM-2+ | FSRS |
|--------|-------|------|
| **Type** | Rule-based formula | Machine learning (neural network) |
| **Personalization** | Per-word ease factor | Per-user forgetting curve + global word difficulty |
| **Interval Calculation** | Fixed multiplication (interval × ease_factor) | Dynamic based on retention prediction |
| **Efficiency** | Good | Better (20-30% fewer reviews) |
| **Data Needed** | Minimal (works immediately) | Needs 100+ reviews for optimization |
| **Complexity** | Simple (~50 lines) | Complex (requires neural network) |
| **State Storage** | ease_factor, consecutive_correct | stability, difficulty, fsrs_state (JSONB) |
| **Mastery Calculation** | Based on tier (Day 3, 7, 14...) | Based on stability thresholds |

### How They Calculate Intervals

**SM-2+ (Rule-Based):**
```
IF performance >= Good:
    new_interval = current_interval × ease_factor
    ease_factor = min(3.0, ease_factor + 0.1)
ELSE:
    new_interval = 1
    ease_factor = max(1.3, ease_factor - 0.2)
```

**FSRS (Machine Learning):**
```
1. Calculate retention = f(stability, difficulty, elapsed_time)
2. IF retention < 0.9 (target):
    Calculate interval to hit 90% retention
    Update stability based on performance
    Update difficulty based on performance
3. ELSE:
    Extend interval (calculate when retention will drop to 90%)
```

### Mastery Progression

**SM-2+ Mastery (Based on Tier):**
- Learning: Tier 0-1 (initial state)
- Familiar: Tier 2 (passed Day 3 review)
- Known: Tier 3-4 (passed Day 7, 14 reviews)
- Mastered: Tier 5+ (passed Day 30+ reviews)

**FSRS Mastery (Based on Stability):**
- Learning: stability < 5 days
- Familiar: 5 ≤ stability < 30 days
- Known: 30 ≤ stability < 180 days (6 months)
- Mastered: 180 ≤ stability < 730 days (2 years)
- Permanent: stability ≥ 730 days

### When to Use Each

**Use SM-2+ when:**
- Simple implementation needed
- Immediate results required (no training data needed)
- Per-word personalization is sufficient

**Use FSRS when:**
- User has 100+ reviews (can optimize parameters)
- Maximum efficiency desired (fewer reviews)
- Better retention prediction needed
- A/B testing to compare algorithms

## Future Tasks / Improvements Needed

### Documentation Needed
- [x] Complete algorithm details (SM-2+ vs FSRS differences) - **DONE**
- [ ] Mastery progression rules (exact thresholds) - **Partially documented above**
- [ ] Leech detection logic
- [ ] Interval calculation formulas - **Documented above**

### Implementation Gaps
- [ ] Automatic review scheduling (currently manual?)
- [ ] Review prioritization algorithm
- [ ] Batch review processing
- [ ] Review session management

### Enhancements
- [ ] Review reminders/notifications
- [ ] Review session analytics
- [x] Algorithm performance comparison - **Implemented via analytics API**
- [x] Migration tool improvements - **Implemented via migrate-to-fsrs endpoint**

## Analytics & Algorithm Comparison

### `GET /api/v1/analytics/algorithm-comparison`

Compare SM-2+ vs FSRS performance metrics.

**Query Parameters:**
- `days`: Number of days to analyze (default: 30)

**Response:**
```json
{
  "period": {
    "start_date": "2024-12-01",
    "end_date": "2024-12-31",
    "days": 30
  },
  "sm2_plus": {
    "total_users": 150,
    "active_users": 120,
    "total_reviews": 15000,
    "retention_rate": 0.78,
    "avg_reviews_per_user": 100.0,
    "avg_interval_days": 8.5,
    "cards_mastered": 3500
  },
  "fsrs": {
    "total_users": 150,
    "active_users": 125,
    "total_reviews": 12000,  // 20% fewer reviews
    "retention_rate": 0.82,  // Better retention
    "avg_reviews_per_user": 80.0,
    "avg_interval_days": 10.2,
    "cards_mastered": 3800  // More cards mastered
  },
  "comparison": {
    "review_efficiency": 0.20,  // FSRS uses 20% fewer reviews
    "retention_improvement": 0.04,  // 4% better retention
    "mastery_improvement": 0.086,  // 8.6% more cards mastered
    "recommendation": "fsrs"  // FSRS performs better
  }
}
```

### `GET /api/v1/analytics/daily-trend`

Get daily metrics trend for algorithm comparison.

**Query Parameters:**
- `days`: Number of days (default: 30)
- `algorithm`: Filter by algorithm (optional)

**Response:**
```json
{
  "trends": [
    {
      "date": "2024-12-01",
      "sm2_plus": {
        "active_users": 120,
        "total_reviews": 500,
        "retention_rate": 0.78
      },
      "fsrs": {
        "active_users": 125,
        "total_reviews": 400,
        "retention_rate": 0.82
      }
    }
    // ... more days
  ]
}
```

### `GET /api/v1/analytics/user-stats`

Get user's algorithm-specific performance statistics.

**Response:**
```json
{
  "algorithm": "fsrs",
  "total_reviews": 1250,
  "retention_rate": 0.84,
  "avg_interval_days": 12.5,
  "cards_by_mastery": {
    "learning": 45,
    "familiar": 120,
    "known": 350,
    "mastered": 735
  },
  "efficiency_metrics": {
    "reviews_per_mastered_card": 1.7,  // Lower is better
    "days_to_mastery": 45.2,
    "retention_at_review": 0.88  // Average retention when reviewing
  }
}
```

---

**Document Version:** 1.0  
**Last Updated:** January 2025  
**Related Docs:** `MCQ_SYSTEM.md`, `VERIFICATION_FLOW_GUIDING.md`


