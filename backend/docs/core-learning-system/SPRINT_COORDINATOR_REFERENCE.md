# Sprint Coordinator Reference
## Core Verification System - Critical Gaps Implementation

**Date:** January 2025  
**Purpose:** Reference document for sprint coordinator chat  
**Status:** Ready for Implementation Sprint

---

## Context

We just completed a comprehensive gap analysis comparing documentation against actual implementation. This document provides the coordinator with everything needed to manage the implementation sprint.

---

## 🔴 Critical Gaps (Must Fix First)

### 1. Missing Verification Start API ⚠️ BLOCKING

**Problem:** No API endpoint exists to start verification for a word (create `learning_progress` and `verification_schedule`).

**Evidence:**
- ✅ `create_learning_progress()` function exists in `backend/src/database/postgres_crud/progress.py`
- ✅ `create_verification_schedule()` function exists in `backend/src/database/postgres_crud/verification.py`
- ❌ **NO API endpoint calls these functions**
- ❌ Only found in test scripts

**Impact:** Users cannot start verification quizzes for words through the API.

**Vision:** The system verifies and solidifies vocabulary knowledge. Users typically encounter words elsewhere first (school, books, media). We verify what they've encountered and can facilitate learning through MCQ explanations when they get answers wrong, especially with FSRS spaced repetition. We are not a school or curriculum that presents words in complete contexts - users learn from outside sources, and we verify/solidify that knowledge. There is no separate "learn word" step.

**Required Implementation:**
```
POST /api/v1/words/start-verification
- Input: user_id, learning_point_id, tier
- Action: 
  1. Create learning_progress entry (status: 'pending')
  2. Create verification_schedule entry (using algorithm)
  3. Return success with verification schedule info
```

**Files to Create/Modify:**
- `backend/src/api/words.py` (new file)
- Register router in `backend/src/main.py`

**Dependencies:**
- `create_learning_progress()` - exists
- `create_verification_schedule()` - exists
- Algorithm assignment - exists

---

### 2. Survey → Verification Integration ⚠️ BLOCKING

**Problem:** Survey results don't create `learning_progress` entries for verification.

**Current State:**
- Survey completes and returns vocabulary estimate
- No integration to create learning_progress entries

**Required Implementation:**
- After survey completes, create learning_progress for known words (status: 'pending')
- These words can then be verified through MCQs
- Or provide API endpoint to convert survey results to verification-ready entries

**Files to Modify:**
- `backend/src/api/survey.py` - Add integration after survey completion
- Or create new endpoint: `POST /api/v1/survey/convert-to-verification`

---


## 🟠 High Priority Gaps

### 4. Verification Schedule Creation Documentation

**Status:** Function exists, needs API integration

**Action:** Ensure verification start API calls `create_verification_schedule()`

### 5. Mastery Progression Rules

**Status:** Algorithm sets mastery, rules not documented

**Action:** Investigate algorithm logic, document exact rules

---

## 📋 Implementation Checklist

### Phase 1: Critical Fixes (Week 1)

- [ ] **Task 1.1:** Create verification start API endpoint
  - [ ] Create `backend/src/api/words.py`
  - [ ] Implement `POST /api/v1/words/start-verification`
  - [ ] Integrate `create_learning_progress()` (status: 'pending')
  - [ ] Integrate `create_verification_schedule()`
  - [ ] Add authentication middleware
  - [ ] Add request/response models
  - [ ] Test endpoint

- [ ] **Task 1.2:** Survey → Verification integration
  - [ ] Investigate survey completion flow
  - [ ] Add learning_progress creation after survey (status: 'pending')
  - [ ] Words become available for verification quizzes
  - [ ] Or create conversion endpoint
  - [ ] Test integration

### Phase 2: Documentation & Clarification (Week 2)

- [ ] Document mastery progression rules
- [ ] Document verification schedule creation flow
- [ ] Update API documentation
- [ ] Create integration flow diagrams

---

## Key Files Reference

### Existing Functions (Ready to Use)

**Learning Progress:**
- `backend/src/database/postgres_crud/progress.py`
  - `create_learning_progress()`
  - `get_learning_progress_by_user()`

**Verification Schedule:**
- `backend/src/database/postgres_crud/verification.py`
  - `create_verification_schedule()`
  - Uses algorithm to initialize card state

**Algorithm Assignment:**
- `backend/src/spaced_repetition/assignment_service.py`
  - `get_or_assign()` - Gets user's algorithm (SM-2+ or FSRS)

### API Endpoints to Create

**New File:** `backend/src/api/words.py`
```python
router = APIRouter(prefix="/api/v1/words", tags=["Words"])

@router.post("/start-verification")
async def start_verification(...):
    # 1. Create learning_progress (status: 'pending')
    # 2. Create verification_schedule
    # 3. Return success with verification schedule info
    # Note: Learning/solidification happens through MCQ explanations, not here
```

---

## Database Schema Reference

### `learning_progress`
```sql
- id (SERIAL PRIMARY KEY)
- user_id (UUID)
- learning_point_id (TEXT)  -- Neo4j learning_point.id
- learned_at (TIMESTAMPTZ)
- tier (INTEGER)  -- 0-5
- status (TEXT)  -- 'learning', 'pending', 'verified', 'failed'
```

### `verification_schedule`
```sql
- id (SERIAL PRIMARY KEY)
- user_id (UUID)
- learning_progress_id (INTEGER)
- algorithm_type (TEXT)  -- 'sm2_plus' or 'fsrs'
- scheduled_date (DATE)
- mastery_level (TEXT)  -- 'learning', 'familiar', 'known', 'mastered'
- ... (algorithm state fields)
```

---

## Testing Requirements

### Verification Start API
- [ ] Test: Start verification creates learning_progress (status: 'pending')
- [ ] Test: Start verification creates verification_schedule
- [ ] Test: Verification schedule uses correct algorithm
- [ ] Test: Initial interval is algorithm-determined
- [ ] Test: Error handling (duplicate word, invalid learning_point_id)

### Survey Integration
- [ ] Test: Survey completion creates learning_progress (status: 'pending')
- [ ] Test: Only known words are added
- [ ] Test: Verification schedules created
- [ ] Test: Words are ready for verification quizzes

---

## Success Criteria

### Phase 1 Complete When:
- ✅ Users can start verification for words via API
- ✅ Survey results create learning_progress entries (ready for verification)
- ✅ All endpoints tested and working

### Phase 2 Complete When:
- ✅ All flows documented
- ✅ Integration points clear
- ✅ API documentation updated

---

## Related Documentation

**Gap Analysis:**
- `backend/docs/core-learning-system/GAP_ANALYSIS.md` - Full analysis
- `backend/docs/core-learning-system/GAP_ANALYSIS_SUMMARY.md` - Summary

**System Documentation:**
- `backend/docs/core-learning-system/WORD_VERIFICATION_SYSTEM.md`
- `backend/docs/core-learning-system/MCQ_SYSTEM.md`
- `backend/docs/core-learning-system/VERIFICATION_FLOW_GUIDING.md`

---

## Questions for Coordinator

1. **Verification Flow:**
   - Users can look up words anytime (dictionary feature - not learning)
   - System suggests words for verification (Explorer Mode)
   - How do users discover/select words to verify?
   - What guidance/recommendations are provided?

2. **Survey Integration:**
   - Should survey automatically create learning_progress entries?
   - Or manual conversion step?
   - Which words from survey? (all known? top N?)
   - Note: These become available for verification quizzes

---

**Document Version:** 1.0  
**Created:** January 2025  
**For:** Sprint Coordinator Chat

