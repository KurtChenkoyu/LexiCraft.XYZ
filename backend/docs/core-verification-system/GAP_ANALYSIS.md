# Core Verification System - Gap Analysis
## Documentation vs. Implementation

**Date:** January 2025  
**Status:** 🔍 Analysis Complete

---

## Executive Summary

This document compares the documentation against the actual implementation to identify:
- ✅ What's correctly documented
- ⚠️ What's documented but needs clarification
- ❌ What's missing from documentation
- 🔴 Critical gaps in understanding

---

## 1. Word Verification System

### ✅ Correctly Documented

1. **API Endpoints**
   - `POST /api/v1/verification/review` - ✅ Exists and matches
   - `GET /api/v1/verification/due` - ✅ Exists and matches
   - `GET /api/v1/verification/stats` - ✅ Exists and matches
   - `GET /api/v1/verification/algorithm` - ✅ Exists and matches
   - `POST /api/v1/verification/migrate-to-fsrs` - ✅ Exists (not documented)

2. **Algorithms**
   - SM-2+ and FSRS support - ✅ Correct
   - Algorithm assignment (50/50 split) - ✅ Correct
   - Migration eligibility (100+ reviews) - ✅ Correct

3. **Database Schema**
   - `verification_schedule` table structure - ✅ Mostly correct
   - `learning_progress` table structure - ✅ Correct

### ⚠️ Needs Clarification

1. **Initial Verification Schedule Creation**
   - **Documented:** "Word added to learning_progress → Initial verification scheduled (Day 3)"
   - **Reality:** `create_verification_schedule()` in `backend/src/database/postgres_crud/verification.py` uses algorithm to initialize card state
   - **Gap:** Documentation doesn't explain that algorithm determines initial interval, not hardcoded "Day 3"
   - **Action:** Update documentation to explain algorithm-based initialization

2. **Review Processing Flow**
   - **Documented:** Shows MCQ integration
   - **Reality:** `POST /api/v1/verification/review` takes `performance_rating` directly, not MCQ result
   - **Gap:** Two separate flows:
     - Direct review: `POST /verification/review` with rating
     - MCQ-integrated: `POST /mcq/submit` with `verification_schedule_id`
   - **Action:** Document both flows clearly

3. **Mastery Progression Rules**
   - **Documented:** "Learning → Familiar → Known → Mastered" with tier mapping
   - **Reality:** Mastery levels are set by algorithm in `process_review()`, exact rules not clear
   - **Gap:** Documentation shows tier-based progression, but actual algorithm logic not documented
   - **Action:** Investigate algorithm mastery progression logic

### ❌ Missing from Documentation

1. **Review History Table**
   - **Missing:** `fsrs_review_history` table not documented
   - **Reality:** Used in dashboard to get review statistics
   - **Action:** Document review history tracking

2. **Card State Management**
   - **Missing:** How `CardState` object is loaded/saved
   - **Reality:** `_get_card_state()` and `_save_card_state()` functions exist
   - **Action:** Document card state lifecycle

3. **Leech Detection Logic**
   - **Missing:** How leeches are identified
   - **Reality:** Algorithm sets `is_leech` flag
   - **Action:** Document leech detection criteria

---

## 2. MCQ System

### ✅ Correctly Documented

1. **API Endpoints**
   - `POST /api/v1/mcq/generate` - ✅ Exists
   - `GET /api/v1/mcq/get` - ✅ Exists
   - `POST /api/v1/mcq/submit` - ✅ Exists
   - `GET /api/v1/mcq/quality` - ✅ Exists (mentioned)

2. **Adaptive Difficulty**
   - Learner ability tracking - ✅ Correct
   - MCQ selection based on ability - ✅ Correct

3. **Statistical Validation**
   - Discrimination and difficulty tracking - ✅ Correct
   - Quality flagging - ✅ Correct

### ⚠️ Needs Clarification

1. **MCQ Integration with Verification**
   - **Documented:** Shows MCQ → Verification flow
   - **Reality:** `POST /mcq/submit` can optionally process verification if `verification_schedule_id` provided
   - **Gap:** Documentation doesn't clearly show this is optional
   - **Action:** Clarify that MCQ can be standalone or integrated

2. **MCQ Generation**
   - **Documented:** Mentions MCQ types (translation, discrimination, context)
   - **Reality:** `MCQAssembler` exists but exact generation logic not clear
   - **Gap:** How MCQs are actually generated not documented
   - **Action:** Document MCQ generation process

3. **Answer Processing**
   - **Documented:** Shows answer → statistics update
   - **Reality:** `process_answer()` in `MCQAdaptiveService` handles this
   - **Gap:** Exact flow not detailed
   - **Action:** Document answer processing flow

### ❌ Missing from Documentation

1. **MCQ Session Endpoint**
   - **Missing:** `GET /api/v1/mcq/session` endpoint not documented
   - **Reality:** Exists in code, returns multiple MCQs for a session
   - **Action:** Document session endpoint

2. **MCQ Recalculation**
   - **Missing:** `POST /api/v1/mcq/recalculate` endpoint not documented
   - **Reality:** Exists for triggering quality recalculation
   - **Action:** Document recalculation endpoint

3. **MCQ Selection Logic**
   - **Missing:** Exact algorithm for selecting MCQs not documented
   - **Reality:** `MCQAdaptiveService.get_adaptive_mcq()` has selection logic
   - **Action:** Document selection algorithm

---

## 3. Verification Flow / Guiding System

### ✅ Correctly Documented

1. **Dashboard API**
   - `GET /api/v1/dashboard` - ✅ Exists and matches
   - Returns vocabulary, activity, performance, points, gamification stats - ✅ Correct

2. **Progress Tracking**
   - Vocabulary size calculation - ✅ Correct
   - Learning velocity - ✅ Correct
   - Activity streaks - ✅ Correct

### ⚠️ Needs Clarification

1. **Word Discovery Flow**
   - **Documented:** "Survey → Discovery → learning_progress"
   - **Reality:** Survey exists (`POST /api/v1/survey/start`, `POST /api/v1/survey/next`)
   - **Gap:** How survey results create `learning_progress` entries not documented
   - **Action:** Document survey → learning_progress flow

2. **Deposit → Points (No Word Unlocking)**
   - **Clarification:** Deposits only credit points to user's account
   - **Reality:** `POST /api/deposits/confirm` correctly credits points
   - **Note:** Words are not locked/unlocked. Users can verify any word freely via Explorer Mode. Learning/solidification happens through MCQ explanations.

3. **Initial Verification Scheduling**
   - **Documented:** "Initial verification scheduled (Day 3)"
   - **Reality:** Need to find where `create_verification_schedule()` is called
   - **Gap:** When/how verification schedules are created not clear
   - **Action:** Find all call sites of `create_verification_schedule()`

### ❌ Missing from Documentation

1. **Onboarding Flow**
   - **Missing:** `POST /api/users/onboarding/complete` not documented
   - **Reality:** Handles user setup, role assignment, child account creation
   - **Action:** Document onboarding process

2. **Verification Start Trigger**
   - **Missing:** What actually creates `learning_progress` entries for verification?
   - **Reality:** `create_learning_progress()` exists but call sites not documented
   - **Action:** Find all places where words are added to learning_progress (status: 'pending')
   - **Note:** Learning/solidification happens through MCQ explanations, not through creating learning_progress

3. **Review Prioritization**
   - **Missing:** Exact algorithm for prioritizing due cards
   - **Reality:** `GET /verification/due` sorts by `scheduled_date ASC`
   - **Action:** Document prioritization logic

4. **Verification Recommendations**
   - **Missing:** How system suggests next words to verify
   - **Reality:** No clear recommendation system found
   - **Action:** Investigate if recommendations exist
   - **Note:** Users can look up words anytime (dictionary), but system suggests words for verification

---

## 4. Integration Points

### ⚠️ Needs Clarification

1. **Survey → Learning Progress**
   - **Gap:** How survey results become learning_progress entries?
   - **Action:** Trace survey completion flow

2. **Deposit → Points**
   - **Clarification:** Deposits credit points only. No word unlocking needed - all words are freely accessible.

3. **Verification Start → Quiz**
   - **Gap:** When is verification schedule created after user starts verification?
   - **Action:** Find trigger for verification schedule creation
   - **Note:** Learning/solidification happens during the quiz through explanations, not before

4. **MCQ → Verification**
   - **Gap:** How does MCQ result update verification schedule?
   - **Reality:** `POST /mcq/submit` with `verification_schedule_id` does this
   - **Action:** Document this integration clearly

---

## 5. Database Schema

### ✅ Correctly Documented

1. **Core Tables**
   - `learning_progress` - ✅ Correct
   - `verification_schedule` - ✅ Mostly correct
   - `mcq_pool` - ✅ Correct
   - `mcq_statistics` - ✅ Correct

### ❌ Missing from Documentation

1. **Review History**
   - `fsrs_review_history` - Not documented
   - Used for review statistics

2. **Survey Tables**
   - `survey_sessions` - Not documented
   - `survey_history` - Not documented
   - `survey_results` - Not documented
   - `survey_metadata` - Not documented

3. **Points System**
   - `points_accounts` - Not documented
   - `points_transactions` - Not documented

---

## Critical Gaps Summary

### 🔴 High Priority

1. **Verification Start Flow** ⚠️ CRITICAL GAP
   - ❌ **How are words added to `learning_progress` for verification?**
     - `create_learning_progress()` function exists but **NO API ENDPOINT FOUND**
     - Only found in test scripts, not in actual API endpoints
     - **This is a major gap - users cannot start verification through the API!**
   - ❌ When is `verification_schedule` created?
     - `create_verification_schedule()` exists but call sites not found in API
   - ❌ What triggers verification start?
     - No clear trigger mechanism found
   - **Vision:** System verifies and solidifies vocabulary knowledge. Users typically encounter words elsewhere first (school, books, media). We verify what they've encountered and can facilitate learning through MCQ explanations when they get answers wrong, especially with FSRS spaced repetition. We are not a school or curriculum that presents words in complete contexts - users learn from outside sources, and we verify/solidify that knowledge. There is no separate "learn word" step.

2. **Survey Integration**
   - ❌ How do survey results create learning_progress entries?
   - ❌ What happens after survey completes?
   - ❌ Are words ready for verification quizzes?

3. **Deposit → Points**
   - ✅ Deposits credit points correctly
   - ✅ Points are earned by verifying words, not spent to unlock words
   - ✅ All words are freely accessible (Explorer Mode)

### 🟠 Medium Priority

1. **Mastery Progression**
   - ⚠️ Exact rules for mastery level changes
   - ⚠️ Tier → Mastery mapping

2. **MCQ Generation**
   - ⚠️ How MCQs are actually generated
   - ⚠️ Distractor selection logic

3. **Review Prioritization**
   - ⚠️ Algorithm for sorting due cards
   - ⚠️ Overdue card handling

### 🟡 Low Priority

1. **Review History**
   - Missing documentation for `fsrs_review_history`

2. **Card State Management**
   - How CardState is loaded/saved

3. **Leech Detection**
   - Criteria for identifying leeches

---

## Action Items

### Immediate (This Week)

1. **Trace Verification Start Flow**
   - [ ] Find all call sites of `create_learning_progress()`
   - [ ] Find all call sites of `create_verification_schedule()`
   - [ ] Document complete flow from survey/suggestions → verification start → quiz → learning through explanations

2. **Document Survey Integration**
   - [ ] Trace survey completion flow
   - [ ] Document how survey results create learning_progress entries (status: 'pending')
   - [ ] Document that words become available for verification quizzes
   - [ ] Update VERIFICATION_FLOW_GUIDING.md

3. **Document Deposit → Points Flow**
   - [ ] Document that deposits only credit points
   - [ ] Clarify that words are not locked/unlocked
   - [ ] Update VERIFICATION_FLOW_GUIDING.md

4. **Document Learning Through Explanations**
   - [ ] Document that learning/solidification happens through MCQ explanations
   - [ ] Clarify that word lookup is dictionary feature (not learning)
   - [ ] Document verification-first approach

### Short-term (This Month)

1. **Clarify Verification Flow**
   - [ ] Document both direct review and MCQ-integrated flows
   - [ ] Document algorithm-based initialization
   - [ ] Update WORD_VERIFICATION_SYSTEM.md

2. **Document MCQ System**
   - [ ] Document MCQ generation process
   - [ ] Document answer processing flow
   - [ ] Document session endpoint
   - [ ] Update MCQ_SYSTEM.md

3. **Document Mastery Progression**
   - [ ] Investigate algorithm mastery rules
   - [ ] Document tier → mastery mapping
   - [ ] Update WORD_VERIFICATION_SYSTEM.md

### Long-term (Next Quarter)

1. **Complete Database Documentation**
   - [ ] Document all tables
   - [ ] Document relationships
   - [ ] Create ER diagram

2. **Document Review Prioritization**
   - [ ] Document sorting algorithm
   - [ ] Document overdue handling

3. **Document Recommendations**
   - [ ] Investigate if recommendation system exists
   - [ ] Document or create recommendation system

---

## Files to Update

### High Priority Updates

1. `core-verification-system/VERIFICATION_FLOW_GUIDING.md`
   - Add verification start trigger documentation
   - Add survey → learning_progress flow (status: 'pending')
   - Clarify that words are freely accessible (no unlocking)
   - Document that learning/solidification happens through MCQ explanations
   - Clarify word lookup vs verification distinction

2. `core-verification-system/WORD_VERIFICATION_SYSTEM.md`
   - Clarify algorithm-based initialization
   - Document both review flows (direct + MCQ)
   - Document mastery progression rules

3. `core-verification-system/MCQ_SYSTEM.md`
   - Document MCQ generation process
   - Document session endpoint
   - Document answer processing flow

### Medium Priority Updates

1. `core-verification-system/CORE_VERIFICATION_SYSTEM_OVERVIEW.md`
   - Update integration points
   - Add missing endpoints
   - Clarify flows

2. Create new documentation:
   - `DATABASE_SCHEMA.md` - Complete database documentation
   - `SURVEY_SYSTEM.md` - Survey system documentation
   - `POINTS_SYSTEM.md` - Points system documentation

---

**Document Version:** 1.0  
**Last Updated:** January 2025  
**Next Review:** After gap fixes

