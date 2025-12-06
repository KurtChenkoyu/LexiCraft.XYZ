# MCQ ↔ Verification Integration Flow

**Status:** ✅ Documented  
**Component:** Core Verification System - Integration Guide  
**Last Updated:** January 2025

---

## Overview

This document explains how the MCQ (Multiple Choice Question) system integrates with the spaced repetition verification system. There are two distinct flows for verifying learning points, each serving different use cases.

---

## Quick Reference: Key Questions Answered

### 1. How does `POST /mcq/submit` with `verification_schedule_id` work?

**Answer:**
- When `verification_schedule_id` is provided, the endpoint performs **dual processing**:
  1. **MCQ Processing**: Grades answer, updates statistics, updates learner ability
  2. **Verification Processing**: Maps MCQ result to performance rating, processes spaced repetition review, updates verification schedule

**Code Flow:**
```python
# 1. Process MCQ answer
result = service.process_answer(...)

# 2. If verification_schedule_id provided:
if request.verification_schedule_id:
    # Load verification schedule
    schedule = db.query(VerificationSchedule).filter(...).first()
    
    # Load card state
    card_state = _get_card_state_for_mcq(...)
    
    # Map MCQ result to performance rating (0-4)
    rating = _map_mcq_to_performance_rating(
        result.is_correct,
        request.response_time_ms,
        result.mcq_difficulty
    )
    
    # Process spaced repetition review
    review_result = algorithm.process_review(...)
    
    # Update verification schedule
    schedule.completed = True
    schedule.passed = result.is_correct
```

**Response includes both:**
- MCQ result (is_correct, explanation, feedback)
- Verification result (next_review_date, mastery_level, etc.)

---

### 2. How does `POST /verification/review` work?

**Answer:**
- Direct spaced repetition review processing
- User provides their own performance rating (0-4)
- No MCQ involved - pure self-assessment

**Code Flow:**
```python
# 1. Load card state
card_state = _get_card_state(db, user_id, request.learning_progress_id)

# 2. Get algorithm
algorithm = get_algorithm_for_user(user_id, db)

# 3. Process review
rating = PerformanceRating(request.performance_rating)
result = algorithm.process_review(
    state=card_state,
    rating=rating,
    response_time_ms=request.response_time_ms,
    review_date=date.today()
)

# 4. Save updated state
_save_card_state(db, result.new_state)
_save_review_history(db, ...)
```

**Response:**
- Next review date and interval
- Mastery level changes
- No explanations or feedback (user already knows answer)

---

### 3. What's the difference between the two flows?

| Feature | MCQ-Integrated Flow | Direct Review Flow |
|---------|-------------------|-------------------|
| **Entry Point** | `GET /mcq/get` → `POST /mcq/submit` | `POST /verification/review` |
| **Assessment** | Structured MCQ question | User self-rating |
| **Explanations** | ✅ Automatic (from MCQ) | ❌ None |
| **Feedback** | ✅ Immediate feedback | ❌ None |
| **Performance Rating** | Auto-mapped from MCQ result | User-provided (0-4) |
| **Statistics** | Detailed (response time, difficulty) | Basic (rating only) |
| **Use Case** | Learning/verification | Quick review |
| **When to Use** | Need structured assessment | User is confident |

---

### 4. How are explanations provided when users get answers wrong?

**Answer:**
Explanations are **always** provided in MCQ responses, regardless of correctness.

**Source:**
- Stored in `mcq_pool.explanation` field
- Generated during MCQ creation by `MCQAssembler`
- Format varies by MCQ type

**Example Explanations:**

**Translation MCQ:**
```
正確答案是「休息」。
在句子「I need a break from work」中，"break" 表示「休息」。
```

**Discrimination MCQ:**
```
正確答案是：「I need a break from work」
這個句子中的 "break" 表示「休息」。
```

**Context MCQ:**
```
正確答案是 "break"。
"break" 和 "brake" 容易混淆（發音相同但意思不同）。
```

**Feedback (Dynamic):**
- **Correct + Hard MCQ**: "Excellent! That was a challenging one."
- **Correct + Easy MCQ**: "Correct! Keep going."
- **Correct + Normal**: "Well done!"
- **Incorrect**: "The correct answer was: {correct_option_text}"

**Response Structure:**
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

## Detailed Flow Diagrams

### MCQ-Integrated Flow

```
┌─────────────────────────────────────────┐
│  Verification Schedule Due (Day 3)       │
└───────────────┬─────────────────────────┘
                │
                ▼
    ┌───────────────────────────┐
    │  GET /mcq/get             │
    │  ?sense_id=break.n.01     │
    └───────────┬───────────────┘
                │
                ▼
    ┌───────────────────────────┐
    │  Adaptive MCQ Selection    │
    │  - Estimate ability        │
    │  - Match difficulty        │
    │  - Return MCQ              │
    └───────────┬───────────────┘
                │
                ▼
    ┌───────────────────────────┐
    │  User Answers MCQ          │
    └───────────┬───────────────┘
                │
                ▼
    ┌───────────────────────────┐
    │  POST /mcq/submit         │
    │  {                        │
    │    mcq_id: "...",         │
    │    selected_index: 0,     │
    │    response_time_ms: 3500,│
    │    verification_schedule_id: 123
    │  }                        │
    └───────────┬───────────────┘
                │
                ▼
    ┌───────────────────────────┐
    │  MCQ Processing           │
    │  ✓ Grade answer           │
    │  ✓ Update statistics      │
    │  ✓ Update ability         │
    │  ✓ Generate explanation   │
    └───────────┬───────────────┘
                │
                ▼
    ┌───────────────────────────┐
    │  Verification Processing  │
    │  ✓ Load card state        │
    │  ✓ Map to rating (0-4)    │
    │  ✓ Process review         │
    │  ✓ Update schedule        │
    └───────────┬───────────────┘
                │
                ▼
    ┌───────────────────────────┐
    │  Combined Response        │
    │  - MCQ result             │
    │  - Explanation            │
    │  - Verification result    │
    └───────────────────────────┘
```

### Direct Review Flow

```
┌─────────────────────────────────────────┐
│  Verification Schedule Due (Day 3)       │
└───────────────┬─────────────────────────┘
                │
                ▼
    ┌───────────────────────────┐
    │  POST /verification/review│
    │  {                        │
    │    learning_progress_id: 456,
    │    performance_rating: 2,
    │    response_time_ms: 2000
    │  }                        │
    └───────────┬───────────────┘
                │
                ▼
    ┌───────────────────────────┐
    │  Load Card State          │
    └───────────┬───────────────┘
                │
                ▼
    ┌───────────────────────────┐
    │  Process Review           │
    │  ✓ Get algorithm          │
    │  ✓ Process review         │
    │  ✓ Update state           │
    │  ✓ Save history           │
    └───────────┬───────────────┘
                │
                ▼
    ┌───────────────────────────┐
    │  Response                 │
    │  - Next review date       │
    │  - Mastery level          │
    │  - Interval               │
    └───────────────────────────┘
```

---

## Performance Rating Mapping (MCQ → Spaced Repetition)

When MCQ result is mapped to performance rating:

```python
def _map_mcq_to_performance_rating(
    is_correct: bool,
    response_time_ms: Optional[int],
    mcq_difficulty: Optional[float],
) -> PerformanceRating:
    if not is_correct:
        # Wrong answer
        if response_time_ms and response_time_ms > 10000:  # > 10s
            return PerformanceRating.HARD  # 1 - They tried but failed
        else:
            return PerformanceRating.AGAIN  # 0 - Quick wrong = didn't know
    else:
        # Correct answer
        if response_time_ms and response_time_ms < 2000:  # < 2s
            return PerformanceRating.EASY  # 3 - Instant recall
        elif response_time_ms and response_time_ms < 5000:  # 2-5s
            if mcq_difficulty and mcq_difficulty > 0.7:  # Easy MCQ
                return PerformanceRating.EASY  # 3
            else:
                return PerformanceRating.GOOD  # 2
        else:
            return PerformanceRating.GOOD  # 2 - > 5s = some effort
```

**Rating Scale:**
- `0` = AGAIN (Incorrect, quick)
- `1` = HARD (Incorrect, slow - struggled)
- `2` = GOOD (Correct, moderate effort)
- `3` = EASY (Correct, quick recall)
- `4` = PERFECT (Not used in MCQ mapping)

---

## Database Updates

### MCQ-Integrated Flow Updates

**Tables Modified:**
1. `mcq_attempts` - New attempt record
2. `mcq_statistics` - Updated metrics (attempts, correct count)
3. `learner_ability` - Updated ability estimate
4. `verification_schedule` - Marked completed, updated state
5. `fsrs_review_history` - New review record

**Key Fields Updated:**
```sql
-- verification_schedule
UPDATE verification_schedule SET
    completed = true,
    completed_at = NOW(),
    passed = {is_correct},
    score = {1.0 or 0.0},
    -- Plus all spaced repetition fields
    current_interval = ...,
    mastery_level = ...,
    ...
WHERE id = {verification_schedule_id}
```

### Direct Review Flow Updates

**Tables Modified:**
1. `verification_schedule` - Updated state
2. `fsrs_review_history` - New review record

---

## Error Handling

### MCQ Submission with Invalid `verification_schedule_id`

**Behavior:**
- MCQ processing succeeds
- Verification processing fails gracefully
- Error logged but request doesn't fail
- Response includes MCQ result, `verification_result = null`

**Code:**
```python
try:
    # Verification processing
    ...
except Exception as e:
    logger.error(f"Failed to process verification review: {e}")
    # Don't fail the MCQ submission if verification fails
    # Just log the error and continue
```

### Missing Card State

**Behavior:**
- If `verification_schedule` exists but card state missing
- Verification skipped, warning logged
- MCQ result still returned

### Verification Schedule Not Found

**Behavior:**
- If `verification_schedule_id` doesn't exist or wrong user
- Verification processing skipped
- MCQ processing continues normally

---

## API Request/Response Examples

### MCQ-Integrated Flow

**Request 1: Get MCQ**
```http
GET /api/v1/mcq/get?sense_id=break.n.01&mcq_type=meaning
```

**Response 1:**
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

**Request 2: Submit Answer**
```http
POST /api/v1/mcq/submit
Content-Type: application/json

{
  "mcq_id": "550e8400-e29b-41d4-a716-446655440000",
  "selected_index": 0,
  "response_time_ms": 3500,
  "verification_schedule_id": 123
}
```

**Response 2:**
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

### Direct Review Flow

**Request:**
```http
POST /api/v1/verification/review
Content-Type: application/json

{
  "learning_progress_id": 456,
  "performance_rating": 2,
  "response_time_ms": 2000
}
```

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
  "algorithm_type": "fsrs",
  "debug_info": null
}
```

---

## Implementation Files

### Key Files

- **`backend/src/api/mcq.py`**
  - `POST /mcq/submit` endpoint
  - `_map_mcq_to_performance_rating()` function
  - `_get_card_state_for_mcq()` helper
  - `_save_card_state_for_mcq()` helper
  - `_save_review_history_for_mcq()` helper

- **`backend/src/api/verification.py`**
  - `POST /verification/review` endpoint
  - `_get_card_state()` helper
  - `_save_card_state()` helper
  - `_save_review_history()` helper

- **`backend/src/mcq_adaptive.py`**
  - `MCQAdaptiveService.process_answer()` method
  - Explanation and feedback generation

- **`backend/src/mcq_assembler.py`**
  - MCQ generation with explanations

---

## Testing Checklist

### MCQ-Integrated Flow
- [ ] Get MCQ for sense
- [ ] Submit correct answer with `verification_schedule_id`
- [ ] Submit incorrect answer with `verification_schedule_id`
- [ ] Verify explanation is provided
- [ ] Verify feedback is appropriate
- [ ] Verify verification schedule is updated
- [ ] Verify review history is saved
- [ ] Test with different response times
- [ ] Test with invalid `verification_schedule_id` (should not fail)

### Direct Review Flow
- [ ] Submit review with rating 0-4
- [ ] Verify card state is updated
- [ ] Verify review history is saved
- [ ] Test with different ratings
- [ ] Test with missing card state (should fail gracefully)

### Integration Edge Cases
- [ ] MCQ submission without `verification_schedule_id` (MCQ only)
- [ ] Invalid `verification_schedule_id` (wrong user)
- [ ] Missing card state
- [ ] Concurrent submissions

---

## Related Documentation

- **`MCQ_SYSTEM.md`** - Complete MCQ system documentation
- **`WORD_VERIFICATION_SYSTEM.md`** - Verification system overview
- **`VERIFICATION_FLOW_GUIDING.md`** - Verification flow guide

---

**Document Version:** 1.0  
**Last Updated:** January 2025

