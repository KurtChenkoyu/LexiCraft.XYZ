# Core Verification System Documentation

**Status:** 📋 Documentation in Progress  
**Last Updated:** January 2025

---

## Overview

This directory contains documentation for LexiCraft's core verification system, which consists of three integrated components:

1. **Word Verification System** - Spaced repetition for vocabulary retention
2. **MCQ System** - Adaptive multiple-choice questions for verification
3. **Verification Flow/Guiding** - How users progress through vocabulary verification

---

## Documentation Index

### Main Documents

1. **[CORE_VERIFICATION_SYSTEM_OVERVIEW.md](./CORE_VERIFICATION_SYSTEM_OVERVIEW.md)**
   - System architecture
   - Component overview
   - Integration points
   - Current status

2. **[WORD_VERIFICATION_SYSTEM.md](./WORD_VERIFICATION_SYSTEM.md)**
   - Spaced repetition algorithms (SM-2+, FSRS)
   - Review scheduling
   - Mastery progression
   - API endpoints
   - Database schema

3. **[MCQ_SYSTEM.md](./MCQ_SYSTEM.md)**
   - MCQ types and generation
   - Adaptive difficulty
   - Statistical validation
   - Quality assurance
   - API endpoints

4. **[VERIFICATION_FLOW_GUIDING.md](./VERIFICATION_FLOW_GUIDING.md)**
   - Verification journey stages
   - Guiding mechanisms
   - Progress tracking
   - Recommendations
   - Mastery progression

5. **[GAP_ANALYSIS.md](./GAP_ANALYSIS.md)** 🔍 **NEW**
   - Comprehensive comparison: Documentation vs. Implementation
   - Identified gaps and missing features
   - Action items and priorities

6. **[GAP_ANALYSIS_SUMMARY.md](./GAP_ANALYSIS_SUMMARY.md)** 🔴 **CRITICAL**
   - Critical findings summary
   - Missing verification start API (CRITICAL GAP)
   - Immediate action required

### Related Documentation

- `../ADAPTIVE_STATISTICAL_INTEGRATION.md` - MCQ + Spaced Repetition integration
- `../MCQ_GENERATION_EXPLAINED.md` - MCQ generation details
- `../MCQ_INDUSTRY_STANDARDS_COMPARISON.md` - MCQ quality standards

---

## Quick Reference

### Core Components

| Component | Purpose | Key Files |
|-----------|---------|-----------|
| Word Verification | Spaced repetition scheduling | `src/api/verification.py`, `src/spaced_repetition/` |
| MCQ System | Adaptive questions | `src/api/mcq.py`, `src/mcq_adaptive.py` |
| Verification Flow | Progress tracking & guidance | `src/services/vocabulary_size.py`, `src/services/learning_velocity.py` |

### Key API Endpoints

**Verification:**
- `POST /api/v1/verification/review` - Process review
- `GET /api/v1/verification/due` - Get due cards
- `GET /api/v1/verification/stats` - Get statistics

**MCQ:**
- `GET /api/v1/mcq/get` - Get adaptive MCQ
- `POST /api/v1/mcq/submit` - Submit answer
- `POST /api/v1/mcq/generate` - Generate MCQs

**Verification Flow:**
- `GET /api/v1/dashboard` - Overall progress
- `GET /api/v1/analytics/*` - Verification analytics

---

## Current Status

### ✅ Documented
- System architecture overview
- Word verification system
- MCQ system
- Verification flow structure

### ⚠️ Needs More Detail
- Complete verification flow implementation
- Guiding system details
- Recommendation algorithms
- Review session management

### 🔴 Critical Gaps Identified
- **MISSING: Verification Start API** - No endpoint to start verification for words
- **MISSING: Survey → Verification Integration** - Survey results don't create learning_progress entries

**Vision:** The system verifies and solidifies vocabulary knowledge. Users typically encounter words elsewhere first (school, books, media). We verify what they've encountered and can facilitate learning through MCQ explanations when they get answers wrong, especially with FSRS spaced repetition. We are not a school or curriculum that presents words in complete contexts - users learn from outside sources, and we verify/solidify that knowledge. There is no separate "learn word" step.

**See [GAP_ANALYSIS_SUMMARY.md](./GAP_ANALYSIS_SUMMARY.md) for details.**

### ❓ To Investigate
- How do users currently start verification? (No API found)
- What happens after survey completes?
- How are detailed explanations provided when users get answers wrong?
- Mastery progression thresholds
- Review prioritization logic

---

## Future Tasks

### Documentation Tasks
- [ ] Complete verification flow documentation
- [ ] Document recommendation algorithms
- [ ] Document review session structure
- [ ] Create API documentation
- [ ] Create database schema documentation

### Implementation Tasks
- [ ] Document current implementation gaps
- [ ] Create implementation plan for missing features
- [ ] Prioritize improvements
- [ ] Create task checklist

---

## Related Systems

### Gamification System
- Located in: `../gamification/`
- Depends on: Core learning system (tracks verification activities)
- Integration: XP/achievements triggered by verification actions

### Survey System
- Located in: `src/api/survey.py`
- Purpose: Word discovery (initial vocabulary assessment)
- Integration: Results feed into verification flow (words ready for verification quizzes)

---


**Document Version:** 1.0  
**Last Updated:** January 2025


