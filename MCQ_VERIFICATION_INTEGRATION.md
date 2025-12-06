# MCQ → Verification API Integration

**Date:** 2024-12  
**Status:** ✅ Complete  
**Version:** 8.2

## Overview

Successfully integrated MCQ submission with the FSRS/SM-2+ verification API. When users submit MCQ answers with a `verification_schedule_id`, the system now automatically processes the spaced repetition review.

## What Was Implemented

### 1. MCQ Submit Endpoint Enhancement ✅

**File:** `backend/src/api/mcq.py`

**Changes:**
- Updated `POST /api/v1/mcq/submit` endpoint
- Added integration with verification API when `verification_schedule_id` is provided
- Maps MCQ results to performance ratings (0-4)
- Processes spaced repetition review automatically
- Returns combined result (MCQ feedback + verification data)

**New Response Field:**
- `verification_result`: Contains spaced repetition data (next review date, mastery level, etc.)

### 2. Performance Rating Mapping ✅

**Function:** `_map_mcq_to_performance_rating()`

Maps MCQ results to spaced repetition performance ratings:

- **Incorrect answers:**
  - Quick wrong (< 10s) → `AGAIN` (0)
  - Struggled (> 10s) → `HARD` (1)

- **Correct answers:**
  - Instant recall (< 2s) → `EASY` (3)
  - Quick recall (< 5s) → `GOOD` (2) or `EASY` (3) based on MCQ difficulty
  - Some effort (> 5s) → `GOOD` (2)

### 3. Helper Functions ✅

**Functions Added:**
- `_get_card_state_for_mcq()` - Load card state from database
- `_save_card_state_for_mcq()` - Save updated card state
- `_save_review_history_for_mcq()` - Save review to history table

**Note:** Functions duplicated from `verification.py` to avoid circular imports. Consider moving to shared module in future.

## Integration Flow

```
User submits MCQ answer
    ↓
MCQ processed (records attempt, updates stats)
    ↓
If verification_schedule_id provided:
    ↓
Get verification schedule
    ↓
Get current card state
    ↓
Map MCQ result → Performance rating (0-4)
    ↓
Get user's algorithm (SM-2+ or FSRS)
    ↓
Process review via algorithm
    ↓
Save updated card state
    ↓
Save review history
    ↓
Mark verification schedule as completed
    ↓
Return combined result (MCQ + Verification)
```

## API Usage

### Submit MCQ Answer with Verification

```bash
POST /api/v1/mcq/submit
{
  "mcq_id": "uuid",
  "selected_index": 2,
  "response_time_ms": 3500,
  "verification_schedule_id": 123  # Optional, triggers spaced rep
}
```

**Response:**
```json
{
  "is_correct": true,
  "correct_index": 2,
  "explanation": "...",
  "feedback": "Well done!",
  "ability_before": 0.65,
  "ability_after": 0.68,
  "mcq_difficulty": 0.55,
  "verification_result": {
    "next_review_date": "2024-12-15",
    "next_interval_days": 7,
    "was_correct": true,
    "retention_predicted": 0.92,
    "mastery_level": "familiar",
    "mastery_changed": false,
    "became_leech": false,
    "algorithm_type": "sm2_plus"
  }
}
```

## Benefits

1. **Seamless Integration:** MCQ submission automatically updates spaced repetition
2. **Single API Call:** Frontend only needs to call MCQ submit, verification happens automatically
3. **Consistent State:** Both MCQ stats and verification schedule stay in sync
4. **Algorithm Support:** Works with both SM-2+ and FSRS algorithms

## Next Steps

1. **Frontend Integration:** Update frontend to use the new `verification_result` field
2. **Testing:** Test the integration with real users
3. **Error Handling:** Add more robust error handling for edge cases
4. **Refactoring:** Consider moving helper functions to shared module

## Files Modified

- `backend/src/api/mcq.py` - Enhanced submit endpoint with verification integration

## Testing

To test the integration:

1. Create a verification schedule
2. Get an MCQ for that schedule
3. Submit the MCQ answer with `verification_schedule_id`
4. Verify that:
   - MCQ attempt is recorded
   - Verification schedule is marked as completed
   - Card state is updated with new interval
   - Review history is saved
   - Response includes verification_result

