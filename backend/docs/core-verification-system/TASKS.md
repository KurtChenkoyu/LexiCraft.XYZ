# Core Verification System - Task Checklist

**Status:** 📋 Investigation Phase  
**Priority:** 🔴 CRITICAL

---

## Investigation Tasks

### Phase 1: Understand Current System

#### Task 1.1: Map Word Discovery Flow
**Files to Review:**
- `backend/src/api/survey.py`
- `backend/src/valuation_engine.py`

**Questions:**
- [ ] How does survey identify known words?
- [ ] How are survey results stored?
- [ ] How do survey results feed into learning_progress?
- [ ] What happens after survey completes?

**Deliverable:** Flow diagram: Survey → Discovery → learning_progress

---

#### Task 1.2: Map Deposit → Points Flow
**Files to Review:**
- `backend/src/api/deposits.py`
- `backend/src/database/postgres_crud/progress.py`

**Questions:**
- [ ] How does deposit credit points?
- [ ] What is the deposit → points_accounts relationship?
- [ ] Note: Words are not locked/unlocked - users can verify any word freely (Explorer Mode)

**Deliverable:** Flow diagram: Deposit → Points Credit

---

#### Task 1.3: Map Verification Start → Quiz Flow
**Files to Review:**
- `backend/src/api/verification.py`
- `backend/src/api/mcq.py`
- `backend/src/spaced_repetition/`

**Questions:**
- [ ] How does word move from "pending" to verification?
- [ ] What triggers first verification (algorithm determines interval)?
- [ ] How is verification scheduled?
- [ ] How does verification integrate with MCQ?
- [ ] How are detailed explanations provided when users get answers wrong?

**Deliverable:** Flow diagram: Verification Start → Quiz → Learning/Solidification Through Explanations → Scheduling

---

#### Task 1.4: Map Verification → MCQ Integration
**Files to Review:**
- `backend/src/api/mcq.py`
- `backend/src/api/verification.py`

**Questions:**
- [ ] How does verification trigger MCQ?
- [ ] How does MCQ result update verification?
- [ ] What data flows between systems?
- [ ] How are errors handled?

**Deliverable:** Integration diagram: Verification ↔ MCQ

---

#### Task 1.5: Map Mastery Progression
**Files to Review:**
- `backend/src/api/verification.py`
- `backend/src/spaced_repetition/`

**Questions:**
- [ ] What are exact mastery progression rules?
- [ ] What are tier thresholds?
- [ ] How does status change (learning → familiar → known → mastered)?
- [ ] What triggers mastery level changes?

**Deliverable:** Mastery progression rules document

---

#### Task 1.6: Map Review Prioritization
**Files to Review:**
- `backend/src/api/verification.py`
- `backend/src/services/learning_velocity.py`

**Questions:**
- [ ] How are due cards prioritized?
- [ ] What sorting algorithm is used?
- [ ] How are overdue cards handled?
- [ ] How are review sessions structured?

**Deliverable:** Review prioritization algorithm document

---

### Phase 2: Document Guiding Mechanisms

#### Task 2.1: Document Recommendations
**Files to Review:**
- `backend/src/api/dashboard.py`
- `backend/src/api/analytics.py`

**Questions:**
- [ ] What recommendations are provided?
- [ ] How are "next words" suggested?
- [ ] How are review recommendations made?
- [ ] What algorithms are used?

**Deliverable:** Recommendations system document

---

#### Task 2.2: Document Progress Indicators
**Files to Review:**
- `backend/src/services/vocabulary_size.py`
- `backend/src/services/learning_velocity.py`
- `backend/src/api/dashboard.py`

**Questions:**
- [ ] What progress metrics are tracked?
- [ ] How are they calculated?
- [ ] How are they displayed?
- [ ] What insights do they provide?

**Deliverable:** Progress indicators document

---

#### Task 2.3: Document Learning Path
**Files to Review:**
- All relevant files

**Questions:**
- [ ] How does system guide users through learning?
- [ ] What is the recommended learning path?
- [ ] How are milestones communicated?
- [ ] What guidance is provided?

**Deliverable:** Learning path document

---

### Phase 3: Identify Gaps & Improvements

#### Task 3.1: Identify Missing Features
- [ ] What guiding features are missing?
- [ ] What recommendations are missing?
- [ ] What progress indicators are missing?
- [ ] What integration points are missing?

**Deliverable:** Gap analysis document

---

#### Task 3.2: Identify Improvements
- [ ] What can be improved in verification flow?
- [ ] What can be improved in guiding?
- [ ] What can be improved in recommendations?
- [ ] What can be improved in progress tracking?

**Deliverable:** Improvement recommendations

---

## Documentation Tasks

### Task D.1: Complete System Documentation
- [ ] Update WORD_VERIFICATION_SYSTEM.md with findings
- [ ] Update MCQ_SYSTEM.md with findings
- [ ] Update VERIFICATION_FLOW_GUIDING.md with findings
- [ ] Create integration diagrams
- [ ] Create flow diagrams

### Task D.2: API Documentation
- [ ] Document all verification endpoints
- [ ] Document all MCQ endpoints
- [ ] Document all dashboard endpoints
- [ ] Document request/response formats
- [ ] Document error handling

### Task D.3: Database Schema Documentation
- [ ] Document learning_progress table
- [ ] Document verification_schedule table
- [ ] Document mcq_pool table
- [ ] Document mcq_statistics table
- [ ] Document relationships

---

## Implementation Tasks (After Investigation)

### To Be Determined
Once investigation is complete, specific implementation tasks will be identified.

**Likely Areas:**
- Recommendation algorithms
- Review session management
- Learning path guidance
- Progress milestones
- Integration improvements

---

## Current Status

### ✅ Completed
- Initial documentation structure created
- System overview documented
- Component documentation started

### ⏳ In Progress
- Investigation of current implementation
- Documentation of existing features
- Gap analysis

### 📋 Pending
- Complete flow documentation
- Integration documentation
- Implementation plan
- Task breakdown

---

## Notes

- All investigation should be done by reviewing code
- Document findings as you go
- Update documentation with discoveries
- Create diagrams for complex flows

---

**Document Version:** 1.0  
**Last Updated:** January 2025  
**Status:** Investigation Phase


