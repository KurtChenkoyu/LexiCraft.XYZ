# Adaptive Spaced Repetition System (ASRS)

**Version:** 1.0  
**Date:** 2024-12  
**Status:** Design  
**Module ID:** MOD_ASRS_V1

---

## 1. Problems with Current System

### 1.1 Fixed Intervals Don't Work for Everyone

Current: Day 1, 3, 7, 14, 60

**Problems**:
- "Easy" words tested too often → annoying
- "Hard" words not tested often enough → not learned
- Everyone gets same schedule regardless of performance
- Max interval of 60 days is too short for long-term retention

### 1.2 No Difficulty Tracking

Current: All words treated equally

**Problems**:
- Abstract words (e.g., "subtle") need more reinforcement than concrete words (e.g., "apple")
- User-specific difficulties not tracked (maybe YOU find "ephemeral" easy, but I don't)
- No way to identify "leeches" (words that never stick)

### 1.3 No Mastery Recognition

Current: Keep testing forever

**Problems**:
- User knows "the" → we still test it? Annoying!
- No concept of "this word is fully mastered, stop testing"
- Wastes user's time on things they clearly know

---

## 2. ASRS Design

### 2.1 Core Concept: Per-Word Ease Factor

Every word has an **ease factor (EF)** per user that determines how quickly intervals grow.

```
EF = 2.5 (default, average difficulty)
EF > 2.5 → easy for this user → longer intervals
EF < 2.5 → hard for this user → shorter intervals
EF < 1.5 → "leech" → needs special attention
```

### 2.2 Interval Formula (SM-2+ Algorithm)

```python
def calculate_next_interval(
    current_interval: int,  # days
    ease_factor: float,     # 1.3 - 3.0
    performance: int,       # 0-5 rating
    consecutive_correct: int
) -> tuple[int, float]:
    """
    Calculate next review interval and updated ease factor.
    
    Performance scale:
        5 = Perfect, instant recall
        4 = Correct, some hesitation
        3 = Correct, with difficulty
        2 = Incorrect, but close (remembered after hint)
        1 = Incorrect, vaguely remembered
        0 = Complete blackout
    """
    # Update ease factor based on performance
    new_ef = ease_factor + (0.1 - (5 - performance) * (0.08 + (5 - performance) * 0.02))
    new_ef = max(1.3, min(3.0, new_ef))  # Clamp to [1.3, 3.0]
    
    if performance < 3:
        # Failed - reset to beginning
        next_interval = 1
        consecutive_correct = 0
    else:
        # Passed - extend interval
        if consecutive_correct == 0:
            next_interval = 1
        elif consecutive_correct == 1:
            next_interval = 3
        elif consecutive_correct == 2:
            next_interval = 7
        else:
            # After 3+ correct: multiply by ease factor
            next_interval = int(current_interval * new_ef)
    
    # Cap at maximum interval
    max_interval = 365  # 1 year max
    next_interval = min(next_interval, max_interval)
    
    return next_interval, new_ef
```

### 2.3 Extended Interval Progression

**Easy word (EF = 2.8)**:
```
Day 1 → Day 3 → Day 7 → Day 20 → Day 56 → Day 157 → Day 365 (mastered!)
```

**Average word (EF = 2.5)**:
```
Day 1 → Day 3 → Day 7 → Day 18 → Day 45 → Day 112 → Day 280 → Day 365
```

**Hard word (EF = 1.8)**:
```
Day 1 → Day 3 → Day 7 → Day 13 → Day 23 → Day 41 → Day 74 → Day 133 → Day 239 → Day 365
```

**Leech word (EF = 1.3, keeps failing)**:
```
Day 1 → Day 1 → Day 1 → Day 3 → Day 1 → FLAGGED FOR SPECIAL ATTENTION
```

---

## 3. Difficulty Detection

### 3.1 Per-Word Difficulty Signals

Track these signals to identify difficult words:

| Signal | Weight | Meaning |
|--------|--------|---------|
| Response time | 0.2 | Longer time = harder |
| Hesitation patterns | 0.1 | Changed answer = uncertainty |
| Error rate (global) | 0.2 | All users struggle with this |
| Error rate (user) | 0.3 | This user struggles with this |
| Ease factor | 0.2 | Historical difficulty for this user |

### 3.2 Difficulty Score Calculation

```python
def calculate_difficulty_score(
    word_id: str,
    user_id: str,
    response_time_ms: int,
    changed_answer: bool,
    global_error_rate: float,
    user_error_rate: float,
    ease_factor: float
) -> float:
    """
    Calculate difficulty score (0-1, higher = harder).
    """
    # Normalize response time (3s = 0, 12s = 1)
    time_factor = min(1.0, max(0.0, (response_time_ms - 3000) / 9000))
    
    # Hesitation factor
    hesitation_factor = 1.0 if changed_answer else 0.0
    
    # Normalize error rates
    global_factor = min(1.0, global_error_rate)
    user_factor = min(1.0, user_error_rate)
    
    # Normalize ease factor (2.5 = 0.5, 1.3 = 1.0, 3.0 = 0.0)
    ef_factor = 1.0 - ((ease_factor - 1.3) / 1.7)
    
    # Weighted combination
    difficulty = (
        0.2 * time_factor +
        0.1 * hesitation_factor +
        0.2 * global_factor +
        0.3 * user_factor +
        0.2 * ef_factor
    )
    
    return round(difficulty, 3)
```

### 3.3 Difficulty Categories

| Category | Difficulty Score | Action |
|----------|-----------------|--------|
| Mastered | < 0.1 | Test less often, extend intervals 1.5x |
| Easy | 0.1 - 0.3 | Standard intervals |
| Average | 0.3 - 0.5 | Standard intervals |
| Hard | 0.5 - 0.7 | Shorter intervals, provide hints |
| Leech | > 0.7 | Flag for special attention, different learning approach |

---

## 4. Leech Detection & Handling

### 4.1 What is a Leech?

A word that repeatedly fails despite multiple attempts. Classic signs:
- Failed 3+ times in a row
- Ease factor dropped to < 1.5
- Total time spent on word > 15 minutes without success

### 4.2 Leech Detection

```python
def detect_leech(
    word_id: str,
    user_id: str,
    failure_streak: int,
    ease_factor: float,
    total_time_spent: int,  # seconds
    total_attempts: int
) -> bool:
    """
    Detect if a word is a "leech" for this user.
    """
    # Criteria 1: Consecutive failures
    if failure_streak >= 3:
        return True
    
    # Criteria 2: Very low ease factor
    if ease_factor < 1.5:
        return True
    
    # Criteria 3: Too much time without success
    if total_time_spent > 900 and total_attempts > 5:  # 15 min, 5+ attempts
        return True
    
    return False
```

### 4.3 Leech Handling Strategies

| Strategy | Description | When to Use |
|----------|-------------|-------------|
| **Mnemonics** | Suggest memory aids | First time flagged |
| **Context enrichment** | Show more example sentences | After 3 failures |
| **Related words** | Link to words they DO know | After 5 failures |
| **Visual aids** | Add images/diagrams | If available |
| **Audio support** | Pronunciation + listening | For phonetic learners |
| **Temporary skip** | Put aside for 2 weeks | Persistent leech |
| **Re-learn** | Start from scratch with different approach | Last resort |

### 4.4 Leech Learning Interface

```
┌─────────────────────────────────────────────────────────────────┐
│  😰 DIFFICULT WORD DETECTED: "ephemeral"                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  You've struggled with this word 4 times. Let's try a          │
│  different approach!                                            │
│                                                                 │
│  📖 MEANING: lasting for a very short time                      │
│                                                                 │
│  💡 MEMORY TIP:                                                 │
│  Think of "ephemeral" like an "ephemera-l" butterfly -         │
│  butterflies only live for a short time!                        │
│                                                                 │
│  🔗 RELATED WORDS YOU KNOW:                                     │
│  • temporary (similar meaning)                                  │
│  • eternal (opposite)                                           │
│  • brief (synonym)                                              │
│                                                                 │
│  📝 EXAMPLE:                                                    │
│  "Social media trends are ephemeral - they come and go         │
│   within weeks."                                                │
│                                                                 │
│  [Try Again] [Skip for Now] [Mark as Known]                    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 5. Mastery Detection

### 5.1 When to Stop Testing

A word is "mastered" when:
- Ease factor > 2.8
- 5+ consecutive correct responses
- Current interval > 180 days
- Response time consistently < 3 seconds

### 5.2 Mastery Levels

| Level | Criteria | Testing Frequency |
|-------|----------|-------------------|
| **Learning** | < 3 correct in a row | Every 1-7 days |
| **Familiar** | 3-4 correct in a row | Every 2-4 weeks |
| **Known** | 5+ correct in a row, EF > 2.5 | Every 1-3 months |
| **Mastered** | 5+ correct, EF > 2.8, interval > 180d | Every 6-12 months |
| **Permanent** | Mastered for 2+ years | Once per year (spot check) |

### 5.3 Mastery Recognition in UI

```
┌─────────────────────────────────────────────────────────────────┐
│  🎉 WORD MASTERED: "apple"                                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Great job! You've proven you know "apple" very well.           │
│                                                                 │
│  ✓ 7 correct in a row                                           │
│  ✓ Average response time: 1.8 seconds                           │
│  ✓ Ease factor: 2.9 (easy for you)                              │
│                                                                 │
│  We'll only check this word once a year from now on.            │
│  More time for words you're still learning!                     │
│                                                                 │
│  [Got it!]                                                      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 6. Database Schema

### 6.1 Updated verification_schedule Table

```sql
-- Enhanced verification_schedule with ASRS fields
CREATE TABLE verification_schedule_v2 (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    learning_progress_id INTEGER NOT NULL REFERENCES learning_progress(id) ON DELETE CASCADE,
    
    -- Current scheduling state
    next_review_date DATE NOT NULL,
    current_interval INTEGER NOT NULL DEFAULT 1,  -- days until next review
    
    -- SM-2+ Algorithm fields
    ease_factor FLOAT NOT NULL DEFAULT 2.5,       -- 1.3 - 3.0
    consecutive_correct INTEGER NOT NULL DEFAULT 0,
    total_reviews INTEGER NOT NULL DEFAULT 0,
    total_correct INTEGER NOT NULL DEFAULT 0,
    
    -- Difficulty tracking
    difficulty_score FLOAT DEFAULT 0.5,           -- 0-1
    average_response_time_ms INTEGER,
    is_leech BOOLEAN DEFAULT FALSE,
    leech_count INTEGER DEFAULT 0,                -- Times flagged as leech
    
    -- Mastery tracking
    mastery_level TEXT DEFAULT 'learning',        -- learning, familiar, known, mastered, permanent
    mastered_at TIMESTAMP,
    
    -- Performance history (last 10 reviews)
    recent_performance JSONB DEFAULT '[]',        -- [{date, score, time_ms}, ...]
    
    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_vs2_user_next_review ON verification_schedule_v2(user_id, next_review_date);
CREATE INDEX idx_vs2_leech ON verification_schedule_v2(user_id, is_leech) WHERE is_leech = true;
CREATE INDEX idx_vs2_mastery ON verification_schedule_v2(mastery_level);
```

### 6.2 New Table: word_difficulty

```sql
-- Global word difficulty tracking
CREATE TABLE word_difficulty (
    id SERIAL PRIMARY KEY,
    learning_point_id TEXT NOT NULL UNIQUE,       -- References Neo4j
    
    -- Global stats (all users)
    total_reviews INTEGER DEFAULT 0,
    total_correct INTEGER DEFAULT 0,
    global_error_rate FLOAT DEFAULT 0.0,
    average_ease_factor FLOAT DEFAULT 2.5,
    average_response_time_ms INTEGER,
    
    -- Difficulty classification
    difficulty_category TEXT DEFAULT 'average',   -- easy, average, hard
    leech_percentage FLOAT DEFAULT 0.0,           -- % of users who find this a leech
    
    -- Helpful resources
    mnemonics JSONB DEFAULT '[]',                 -- [{text, upvotes}, ...]
    related_words JSONB DEFAULT '[]',
    visual_aids JSONB DEFAULT '[]',
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_word_difficulty_error ON word_difficulty(global_error_rate DESC);
```

### 6.3 New Table: user_learning_profile

```sql
-- User's overall learning profile
CREATE TABLE user_learning_profile (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    
    -- Learning speed
    average_ease_factor FLOAT DEFAULT 2.5,
    words_mastered INTEGER DEFAULT 0,
    words_learning INTEGER DEFAULT 0,
    words_leech INTEGER DEFAULT 0,
    
    -- Performance patterns
    best_time_of_day TEXT,                        -- 'morning', 'afternoon', 'evening', 'night'
    optimal_session_length INTEGER,               -- minutes
    attention_span INTEGER,                       -- questions before fatigue
    
    -- Difficulty patterns
    struggles_with JSONB DEFAULT '[]',            -- [{category, count}, ...] e.g., idioms, prefixes
    excels_at JSONB DEFAULT '[]',
    
    -- Learning preferences
    prefers_visual BOOLEAN DEFAULT FALSE,
    prefers_audio BOOLEAN DEFAULT FALSE,
    prefers_mnemonics BOOLEAN DEFAULT FALSE,
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

---

## 7. Algorithm Implementation

### 7.1 Review Processing

```python
def process_review(
    user_id: UUID,
    word_id: str,
    is_correct: bool,
    response_time_ms: int,
    changed_answer: bool = False
) -> ReviewResult:
    """
    Process a single review and update all tracking.
    
    Returns:
        ReviewResult with next_review_date, feedback, special_actions
    """
    # 1. Get current state
    schedule = get_verification_schedule(user_id, word_id)
    word_diff = get_word_difficulty(word_id)
    
    # 2. Calculate performance score (0-5 scale for SM-2)
    if is_correct:
        if response_time_ms < 3000:
            performance = 5  # Perfect, instant
        elif response_time_ms < 6000:
            performance = 4  # Good
        else:
            performance = 3  # Correct but slow
    else:
        if changed_answer:
            performance = 2  # Wrong, but tried
        else:
            performance = 1  # Wrong, gave up quickly
    
    # 3. Update ease factor and interval
    new_interval, new_ef = calculate_next_interval(
        schedule.current_interval,
        schedule.ease_factor,
        performance,
        schedule.consecutive_correct if is_correct else 0
    )
    
    # 4. Update consecutive correct count
    if is_correct:
        consecutive = schedule.consecutive_correct + 1
    else:
        consecutive = 0
    
    # 5. Check for leech
    is_leech = detect_leech(
        word_id, user_id,
        failure_streak=0 if is_correct else schedule.consecutive_failures + 1,
        ease_factor=new_ef,
        total_time_spent=schedule.total_time_spent + response_time_ms // 1000,
        total_attempts=schedule.total_reviews + 1
    )
    
    # 6. Check for mastery
    mastery_level = calculate_mastery_level(
        consecutive_correct=consecutive,
        ease_factor=new_ef,
        current_interval=new_interval,
        average_response_time=response_time_ms
    )
    
    # 7. Calculate difficulty score
    difficulty = calculate_difficulty_score(
        word_id, user_id,
        response_time_ms,
        changed_answer,
        word_diff.global_error_rate,
        schedule.user_error_rate,
        new_ef
    )
    
    # 8. Update database
    update_verification_schedule(
        schedule_id=schedule.id,
        next_review_date=today + timedelta(days=new_interval),
        current_interval=new_interval,
        ease_factor=new_ef,
        consecutive_correct=consecutive,
        total_reviews=schedule.total_reviews + 1,
        total_correct=schedule.total_correct + (1 if is_correct else 0),
        difficulty_score=difficulty,
        is_leech=is_leech,
        mastery_level=mastery_level
    )
    
    # 9. Update global word difficulty
    update_word_difficulty(word_id, is_correct, response_time_ms, new_ef)
    
    # 10. Prepare result
    result = ReviewResult(
        next_review_date=today + timedelta(days=new_interval),
        interval_days=new_interval,
        ease_factor=new_ef,
        mastery_level=mastery_level,
        is_leech=is_leech,
        difficulty_score=difficulty,
        feedback=generate_feedback(is_correct, mastery_level, is_leech)
    )
    
    return result
```

### 7.2 Daily Review Queue Generation

```python
def get_daily_review_queue(user_id: UUID, max_reviews: int = 50) -> List[ReviewItem]:
    """
    Get words due for review today, prioritized smartly.
    
    Priority order:
    1. Overdue leeches (most urgent)
    2. Overdue reviews
    3. Due today
    4. Tomorrow's reviews if time permits
    
    Never returns mastered words unless overdue.
    """
    today = date.today()
    
    # 1. Get overdue leeches (highest priority)
    overdue_leeches = db.query("""
        SELECT * FROM verification_schedule_v2
        WHERE user_id = :user_id
        AND is_leech = true
        AND next_review_date < :today
        ORDER BY next_review_date
        LIMIT :limit
    """, user_id=user_id, today=today, limit=max_reviews // 4)
    
    # 2. Get other overdue
    overdue = db.query("""
        SELECT * FROM verification_schedule_v2
        WHERE user_id = :user_id
        AND is_leech = false
        AND next_review_date < :today
        AND mastery_level != 'permanent'
        ORDER BY next_review_date
        LIMIT :limit
    """, user_id=user_id, today=today, limit=max_reviews // 2)
    
    # 3. Get due today
    due_today = db.query("""
        SELECT * FROM verification_schedule_v2
        WHERE user_id = :user_id
        AND next_review_date = :today
        AND mastery_level != 'permanent'
        ORDER BY difficulty_score DESC  -- Harder words first when fresh
        LIMIT :limit
    """, user_id=user_id, today=today, limit=max_reviews)
    
    # Combine and limit
    queue = overdue_leeches + overdue + due_today
    queue = queue[:max_reviews]
    
    # Interleave: don't put all leeches together (frustrating!)
    return interleave_by_difficulty(queue)
```

---

## 8. User-Facing Features

### 8.1 Review Forecast

Show users what's coming:

```
┌─────────────────────────────────────────────────────────────────┐
│  📅 YOUR REVIEW SCHEDULE                                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  TODAY:        15 words (3 need extra attention ⚠️)             │
│  TOMORROW:     8 words                                          │
│  THIS WEEK:    45 words total                                   │
│                                                                 │
│  📊 STATUS BREAKDOWN:                                           │
│  ├── 🟢 Mastered:    120 words (no review needed)               │
│  ├── 🔵 Known:       85 words (monthly review)                  │
│  ├── 🟡 Familiar:    45 words (weekly review)                   │
│  ├── 🟠 Learning:    30 words (daily review)                    │
│  └── 🔴 Struggling:  5 words (extra practice)                   │
│                                                                 │
│  [Start Today's Reviews]                                        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 8.2 Progress Insights

```
┌─────────────────────────────────────────────────────────────────┐
│  📈 YOUR LEARNING INSIGHTS                                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  🎯 STRENGTHS:                                                  │
│  • Basic vocabulary: 92% retention                              │
│  • Concrete nouns: Avg 2.8 ease factor                         │
│  • Morning reviews: 15% better accuracy                         │
│                                                                 │
│  ⚠️  AREAS TO IMPROVE:                                          │
│  • Idioms: 5 words stuck as leeches                            │
│  • Abstract concepts: Takes 2x longer to learn                  │
│  • Evening reviews: Accuracy drops by 20%                       │
│                                                                 │
│  💡 PERSONALIZED TIPS:                                          │
│  1. Try reviewing idioms with visual mnemonics                  │
│  2. Schedule difficult words for mornings                       │
│  3. Take a break after 20 questions (your focus drops)          │
│                                                                 │
│  [View Detailed Stats]                                          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 8.3 "Leave Me Alone" Features

For mastered words:

```
┌─────────────────────────────────────────────────────────────────┐
│  ✅ 120 WORDS MASTERED                                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  These words are in your long-term memory!                      │
│  We'll only check them once or twice a year.                    │
│                                                                 │
│  Recent additions:                                              │
│  • "apple" - Mastered Dec 1 (next check: June 2025)            │
│  • "table" - Mastered Nov 28 (next check: May 2025)            │
│  • "water" - Mastered Nov 25 (next check: May 2025)            │
│                                                                 │
│  [View All Mastered Words]                                      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 9. Configuration

### 9.1 Tuneable Parameters

```python
ASRS_CONFIG = {
    # Ease factor bounds
    "ef_min": 1.3,
    "ef_max": 3.0,
    "ef_default": 2.5,
    
    # Interval bounds
    "interval_min": 1,        # 1 day minimum
    "interval_max": 365,      # 1 year maximum
    
    # Leech detection
    "leech_failure_streak": 3,
    "leech_ef_threshold": 1.5,
    "leech_time_threshold": 900,  # 15 minutes
    
    # Mastery thresholds
    "mastery_ef_threshold": 2.8,
    "mastery_consecutive_threshold": 5,
    "mastery_interval_threshold": 180,  # 6 months
    
    # Review limits
    "max_daily_reviews": 50,
    "max_new_words_per_day": 20,
    
    # Fatigue detection
    "questions_before_break": 20,
    "accuracy_drop_threshold": 0.15,  # 15% drop = suggest break
}
```

### 9.2 Per-User Overrides

Users can customize:
- Max daily reviews (20-100)
- Review reminder time
- Leech notification threshold
- Show/hide mastered words

---

## 10. Implementation Roadmap

### Phase 1: Core Algorithm (Week 1-2)

1. Create database tables (verification_schedule_v2, word_difficulty, user_learning_profile)
2. Implement SM-2+ algorithm in Python
3. Migrate existing verification_schedule data
4. Basic review processing

### Phase 2: Difficulty Tracking (Week 3)

1. Implement difficulty score calculation
2. Add response time tracking to review UI
3. Create word_difficulty aggregation job
4. Leech detection

### Phase 3: Mastery & UI (Week 4)

1. Implement mastery level progression
2. Review queue generation with smart prioritization
3. Review forecast UI
4. Progress insights UI

### Phase 4: Personalization (Week 5+)

1. Learning profile tracking
2. Personalized recommendations
3. Optimal review time detection
4. Leech handling strategies

---

## 11. Migration Path

### From Current System

```sql
-- Migrate existing verification_schedule to v2
INSERT INTO verification_schedule_v2 (
    user_id, learning_progress_id, 
    next_review_date, current_interval,
    ease_factor, consecutive_correct, total_reviews, total_correct,
    mastery_level
)
SELECT 
    user_id, learning_progress_id,
    scheduled_date, 
    CASE 
        WHEN test_day = 3 THEN 3
        WHEN test_day = 7 THEN 7
        WHEN test_day = 14 THEN 14
        ELSE test_day
    END as current_interval,
    2.5 as ease_factor,  -- Default, will adjust based on history
    CASE WHEN passed THEN 1 ELSE 0 END,
    CASE WHEN completed THEN 1 ELSE 0 END,
    CASE WHEN passed THEN 1 ELSE 0 END,
    'learning' as mastery_level
FROM verification_schedule;
```

---

## 12. Summary

| Feature | Current System | ASRS |
|---------|---------------|------|
| **Intervals** | Fixed (1, 3, 7, 14, 60) | Adaptive (1 - 365 days) |
| **Difficulty** | Not tracked | Per-word, per-user |
| **Leeches** | Not handled | Detected + special support |
| **Mastery** | No concept | 5 levels, reduces testing |
| **Max interval** | 60 days | 365 days |
| **Personalization** | None | Learning profile |

### Key Benefits

1. **Less Annoyance**: Mastered words tested rarely (yearly)
2. **More Help Where Needed**: Difficult words get more attention + support
3. **Faster Learning**: Adaptive intervals optimize retention
4. **Leech Handling**: Stuck words get different approaches
5. **Insights**: Users understand their learning patterns

