# Parallel Tasks While Implementing Verification Start API

**Status:** Ready for parallel work  
**Priority:** Tasks that don't depend on Verification Start API implementation

---

## 🔴 High Priority - Can Start Immediately

### Task 1: Investigate Survey → Verification Integration Flow

**Why:** This is Gap #2 (blocking), but investigation can happen in parallel. Understanding the survey completion flow will inform the integration design.

**What to Investigate:**
- [ ] Review `backend/src/api/survey.py` - survey completion flow (lines 532-700)
- [ ] Understand what data is stored in `survey_results` table
- [ ] Check if survey history contains specific words/learning_points
- [ ] Understand frequency band performance data
- [ ] Determine: Does survey identify specific words, or just vocabulary size estimates?
- [ ] Check if `survey_history` contains word-level data

**Key Questions:**
1. Does survey identify specific known words, or just vocabulary size?
2. What data is available after survey completion?
3. How should we convert survey results to `learning_progress` entries?
4. Should we create entries for all words in known frequency bands, or only specific tested words?

**Files to Review:**
- `backend/src/api/survey.py` (survey completion logic)
- `backend/src/survey/lexisurvey_engine.py` (survey engine)
- `backend/src/survey/models.py` (survey data models)
- Database schema: `survey_results`, `survey_history`, `survey_sessions`

**Deliverable:** 
- Document: Survey completion data available
- Design: Integration approach (automatic vs. conversion endpoint)
- Plan: How to create `learning_progress` entries from survey

**Estimated Time:** 2-3 hours

---

### Task 2: Document Mastery Progression Rules

**Why:** This is documentation/investigation work that doesn't require API implementation. Understanding mastery rules will help with testing and documentation.

**What to Investigate:**
- [ ] Review `backend/src/spaced_repetition/sm2_service.py` - `calculate_mastery_level()` method
- [ ] Review `backend/src/spaced_repetition/fsrs_service.py` - `_calculate_fsrs_mastery()` method
- [ ] Review `backend/src/spaced_repetition/algorithm_interface.py` - `MasteryLevel` enum and base logic
- [ ] Document exact thresholds for each mastery level
- [ ] Document differences between SM-2+ and FSRS mastery calculation
- [ ] Document what triggers mastery level changes

**Key Questions:**
1. What are the exact tier/consecutive_correct thresholds for each mastery level?
2. How does mastery level map to `learning_progress.status`?
3. Are mastery rules the same for SM-2+ and FSRS?
4. What triggers a mastery level change?

**Files to Review:**
- `backend/src/spaced_repetition/sm2_service.py` (lines 171-187)
- `backend/src/spaced_repetition/fsrs_service.py` (lines 273-325)
- `backend/src/spaced_repetition/algorithm_interface.py` (lines 252+)

**Deliverable:**
- Document: `backend/docs/core-verification-system/MASTERY_PROGRESSION_RULES.md`
- Include: Thresholds, rules, examples, algorithm differences

**Estimated Time:** 1-2 hours

---

### Task 3: Investigate Word Selection/Discovery Flow

**Why:** Understanding how users discover and select words will inform Explorer Mode and word suggestion features.

**What to Investigate:**
- [ ] Review Explorer Mode documentation
- [ ] Check if word lookup/dictionary feature exists
- [ ] Understand word suggestion algorithms
- [ ] Review connection-building algorithm
- [ ] Check if there are existing word selection APIs

**Key Questions:**
1. How do users currently select words to verify?
2. What word suggestion mechanisms exist?
3. How does Explorer Mode work?
4. What APIs exist for word discovery?

**Files to Review:**
- `docs/EXPLORER_MODE_SUMMARY.md`
- `docs/EXPLORER_MODE_IMPLEMENTATION.md`
- `docs/connection-building-scope-algorithm.md`
- `backend/src/api/` - search for word-related endpoints

**Deliverable:**
- Document: Word discovery/selection flow
- Identify: Missing APIs or features

**Estimated Time:** 1-2 hours

---

## 🟠 Medium Priority - Documentation & Investigation

### Task 4: Document MCQ ↔ Verification Integration Flow

**Why:** Understanding how MCQ and verification integrate will help with testing and documentation.

**What to Investigate:**
- [ ] Review `backend/src/api/mcq.py` - MCQ submission flow
- [ ] Review `backend/src/api/verification.py` - Review processing
- [ ] Understand: How does MCQ result update verification schedule?
- [ ] Document: Two flows (direct review vs. MCQ-integrated)
- [ ] Check: How are detailed explanations provided?

**Key Questions:**
1. How does `POST /mcq/submit` with `verification_schedule_id` work?
2. How does `POST /verification/review` work?
3. What's the difference between the two flows?
4. How are explanations provided when users get answers wrong?

**Files to Review:**
- `backend/src/api/mcq.py`
- `backend/src/api/verification.py`
- `backend/docs/core-verification-system/MCQ_SYSTEM.md`

**Deliverable:**
- Document: MCQ ↔ Verification integration flow
- Update: `MCQ_SYSTEM.md` with integration details

**Estimated Time:** 1-2 hours

---

### Task 5: Investigate Deposit → Points Flow

**Why:** Lower priority, but understanding the deposit system will complete the picture.

**What to Investigate:**
- [ ] Review `backend/src/api/deposits.py`
- [ ] Understand points_accounts system
- [ ] Document: How deposits credit points
- [ ] Confirm: No word unlocking (words are freely accessible)

**Key Questions:**
1. How does deposit credit points?
2. What is the deposit → points_accounts relationship?
3. Are there any word-related restrictions?

**Files to Review:**
- `backend/src/api/deposits.py`
- Database schema: `deposits`, `points_accounts`

**Deliverable:**
- Document: Deposit → Points flow
- Confirm: No word unlocking mechanism

**Estimated Time:** 1 hour

---

### Task 6: Create Integration Flow Diagrams ✅

**Why:** Visual documentation will help understand the system better.

**What to Create:**
- [x] Survey → Verification Integration Flow
- [x] Word Selection → Verification Start → MCQ Flow
- [x] Mastery Progression Flow
- [x] MCQ ↔ Verification Integration Flow

**Tools:**
- Mermaid diagrams (can be embedded in markdown)
- Or ASCII art flowcharts

**Deliverable:**
- ✅ Added diagrams to `VERIFICATION_FLOW_GUIDING.md` with visual flows
- ✅ Created standalone `INTEGRATION_FLOW_DIAGRAMS.md` for easy reference

**Estimated Time:** 2-3 hours  
**Status:** ✅ Complete

---

## 📋 Recommended Order

### While API is being implemented (Day 1):

1. **Task 1: Survey → Verification Integration Investigation** (2-3 hours)
   - Most critical parallel task
   - Will inform integration design
   - Can start immediately

2. **Task 2: Document Mastery Progression Rules** (1-2 hours)
   - Quick win
   - Useful for testing API later
   - Pure investigation/documentation

### After API implementation starts (Day 2):

3. **Task 3: Word Selection/Discovery Flow** (1-2 hours)
   - Understanding user journey
   - Informs Explorer Mode features

4. **Task 4: MCQ ↔ Verification Integration** (1-2 hours)
   - Understanding existing integrations
   - Helps with testing

### Lower Priority (Day 3+):

5. **Task 5: Deposit → Points Flow** (1 hour)
   - Lower priority
   - Completes the picture

6. **Task 6: Create Flow Diagrams** (2-3 hours)
   - Visual documentation
   - Can be done anytime

---

## 🎯 Success Criteria

**After completing parallel tasks:**
- ✅ Survey integration approach designed
- ✅ Mastery progression rules documented
- ✅ Word discovery flow understood
- ✅ MCQ integration documented
- ✅ Visual flow diagrams created
- ✅ Ready to implement Survey → Verification integration (Gap #2)

---

## 📝 Notes

- All tasks are **independent** of Verification Start API implementation
- Tasks can be done in **any order** (except Task 1 should be prioritized)
- Focus on **investigation and documentation** - implementation can wait
- Use findings to **update existing documentation** files
- Create **new documentation files** only if needed (e.g., mastery rules)

---

**Total Estimated Time:** 8-13 hours of parallel work  
**Can be done:** While Verification Start API is being implemented  
**Blocks:** Nothing - all independent tasks

