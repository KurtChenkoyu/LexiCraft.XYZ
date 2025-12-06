# Core Verification System - Overview
## Word Verification, MCQ, and Verification Flow

**Date:** January 2025  
**Status:** 📋 Documentation  
**Priority:** 🔴 CRITICAL - Core functionality of LexiCraft

---

## Executive Summary

This document provides a comprehensive overview of LexiCraft's core verification system, which consists of three integrated components:

1. **Word Verification System** - Spaced repetition for vocabulary retention
2. **MCQ System** - Adaptive multiple-choice questions for verification
3. **Verification Flow/Guiding** - How users progress through vocabulary verification

**Key Principle:** These systems work together to create an effective vocabulary verification and solidification experience with spaced repetition, adaptive difficulty, and statistical validation.

---

## System Role & Positioning

**We are NOT:**
- A school that teaches vocabulary in structured lessons
- A curriculum that presents words in complete contexts (articles, stories)
- A teacher that explains everything from scratch

**We ARE:**
- A verification and solidification platform
- A tool that verifies what users have encountered elsewhere (school, books, media)
- A facilitator that can help users learn through MCQ explanations
- A learning tool users can actively use (but not a structured curriculum)

**Primary Model:**
Users encounter words elsewhere → We verify/solidify that knowledge

**Secondary Model:**
Users can use us as a learning tool → We facilitate learning through explanations (not structured teaching)

---

## System Architecture

```
┌─────────────────────────────────────────────────────────┐
│              USER INTERFACE LAYER                       │
│  Frontend: Verification Page, MCQ Display, Progress     │
└─────────────────────────────────────────────────────────┘
                           ▲
                           │
┌─────────────────────────────────────────────────────────┐
│              API LAYER                                  │
│  /api/v1/verification/*  │  /api/v1/mcq/*              │
└─────────────────────────────────────────────────────────┘
                           ▲
                           │
┌─────────────────────────────────────────────────────────┐
│              CORE LEARNING SYSTEM                        │
│                                                          │
│  ┌──────────────────────────────────────────────────┐  │
│  │  1. WORD VERIFICATION SYSTEM                     │  │
│  │     - Spaced Repetition (SM-2+ / FSRS)          │  │
│  │     - Verification Schedule                     │  │
│  │     - Mastery Tracking                           │  │
│  └──────────────────────────────────────────────────┘  │
│                           │                              │
│  ┌──────────────────────────────────────────────────┐  │
│  │  2. MCQ SYSTEM                                   │  │
│  │     - MCQ Generation                             │  │
│  │     - Adaptive Difficulty Selection              │  │
│  │     - Statistical Validation                    │  │
│  │     - Answer Processing                          │  │
│  └──────────────────────────────────────────────────┘  │
│                           │                              │
│  ┌──────────────────────────────────────────────────┐  │
│  │  3. VERIFICATION FLOW / GUIDING                │  │
│  │     - Word Discovery (Survey)                   │  │
│  │     - Verification Progression                  │  │
│  │     - Mastery Path                               │  │
│  │     - Review Scheduling                          │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
                           ▲
                           │
┌─────────────────────────────────────────────────────────┐
│              DATA LAYER                                  │
│  PostgreSQL: Learning Progress, Verification Schedule    │
│  Neo4j: Word Graph, Learning Points, Relationships      │
└─────────────────────────────────────────────────────────┘
```

---

## Component 1: Word Verification System

### Purpose
Implements spaced repetition to ensure long-term vocabulary retention through systematic review scheduling.

### Key Features
- **Spaced Repetition Algorithms**: 
  - **SM-2+ (Legacy)**: Rule-based, per-word ease factor, works immediately
  - **FSRS (Modern)**: Machine learning-based, learns forgetting curve, 20-30% fewer reviews
- **A/B Testing**: Random 50/50 assignment for new users, comprehensive comparison metrics
- **Review Scheduling**: 
  - SM-2+: Fixed progression (Day 3, 7, 14, 30, 60...)
  - FSRS: Dynamic intervals calculated to maintain 90% retention
- **Mastery Tracking**: Learning → Familiar → Known → Mastered
  - SM-2+: Based on tier progression
  - FSRS: Based on stability thresholds
- **Adaptive Intervals**: Adjusts based on performance
- **Leech Detection**: Identifies problematic words
- **Migration Support**: Users with 100+ reviews can migrate from SM-2+ to FSRS

### Core Flow
```
1. User selects word for verification (from suggestions, search, or survey)
   ↓
2. Word added to learning_progress (status: 'pending')
   ↓
3. Initial verification scheduled:
   - SM-2+: Typically Day 3 (fixed progression)
   - FSRS: Calculated to hit 90% retention (varies by word difficulty)
   ↓
4. User takes verification quiz (MCQ)
   ↓
5. System shows detailed explanation (especially if wrong - THIS IS WHERE LEARNING/SOLIDIFICATION HAPPENS)
   ↓
6. System updates:
   - If pass: Schedule next review
     * SM-2+: Fixed progression (Day 7, 14, 30...) based on ease_factor
     * FSRS: Dynamic interval calculated to maintain 90% retention
   - If fail: Reschedule (algorithm determines interval)
     * SM-2+: Reset to Day 1, decrease ease_factor
     * FSRS: Reset stability, increase difficulty
   - Update mastery level
     * SM-2+: Based on tier progression
     * FSRS: Based on stability thresholds
   - Update algorithm state:
     * SM-2+: ease_factor, consecutive_correct
     * FSRS: stability, difficulty, retention_probability, fsrs_state
   - Update learning_progress status
   ↓
7. Repeat until mastered
```

### API Endpoints
- `POST /api/v1/verification/review` - Process a review (works for both SM-2+ and FSRS)
- `GET /api/v1/verification/due` - Get cards due for review
- `GET /api/v1/verification/stats` - Get review statistics
- `GET /api/v1/verification/algorithm` - Get user's algorithm assignment
- `POST /api/v1/verification/migrate-to-fsrs` - Migrate from SM-2+ to FSRS (requires 100+ reviews)
- `GET /api/v1/analytics/algorithm-comparison` - Compare SM-2+ vs FSRS performance

### Files
- `backend/src/api/verification.py` - API endpoints
- `backend/src/spaced_repetition/` - Algorithm implementations
- `backend/src/spaced_repetition/assignment_service.py` - Algorithm assignment

### Database Tables
- `learning_progress` - Tracks word verification status
- `verification_schedule` - Spaced repetition schedule (supports both SM-2+ and FSRS)
- `user_algorithm_assignment` - SM-2+ vs FSRS assignment (A/B testing)
- `fsrs_review_history` - Detailed review history for FSRS parameter optimization
- `word_global_difficulty` - Global word difficulty statistics (used by FSRS)
- `algorithm_comparison_metrics` - Daily metrics for comparing SM-2+ vs FSRS

---

## Component 2: MCQ System

### Purpose
Provides adaptive multiple-choice questions for verifying word knowledge, with statistical validation to ensure question quality.

### Key Features
- **MCQ Generation**: Multiple question types (translation, discrimination, context)
- **Adaptive Difficulty**: Selects MCQs matching learner ability
- **Statistical Validation**: Tracks discrimination, difficulty, distractor effectiveness
- **Quality Assurance**: Flags poor-quality MCQs for review
- **Answer Processing**: Records attempts, updates statistics

### Core Flow
```
1. Spaced repetition triggers review (Day 3, 7, 14...)
   ↓
2. System estimates learner ability for word/sense
   ↓
3. Adaptive difficulty selects MCQ matching ability
   ↓
4. User answers MCQ
   ↓
5. System processes answer:
   - Grade: Correct/Incorrect
   - Update learner ability estimate
   - Update MCQ statistics (discrimination, difficulty)
   - Update spaced repetition schedule
   ↓
6. Return result to user
```

### MCQ Types
1. **Translation** - "What does 'break' mean?"
2. **Discrimination** - "Which word fits: break vs brake"
3. **Context** - "Complete the sentence: I need a ___ from work"

### API Endpoints
- `POST /api/v1/mcq/generate` - Generate MCQs for a sense
- `GET /api/v1/mcq/get` - Get adaptive MCQ for verification
- `POST /api/v1/mcq/submit` - Submit MCQ answer
- `GET /api/v1/mcq/quality` - Get MCQ quality report

### Files
- `backend/src/api/mcq.py` - API endpoints
- `backend/src/mcq_adaptive.py` - Adaptive difficulty service
- `backend/src/mcq_assembler.py` - MCQ generation
- `backend/src/database/postgres_crud/mcq_stats.py` - MCQ statistics

### Database Tables
- `mcq_pool` - Generated MCQs
- `mcq_statistics` - Quality metrics (discrimination, difficulty)
- `mcq_attempts` - User answer history
- `learner_ability` - Adaptive difficulty tracking

---

## Component 3: Verification Flow / Guiding System

### Purpose
Guides users through the vocabulary verification journey, from initial discovery to mastery.

### Key Features
- **Word Discovery**: Survey system to identify known words
- **Verification Progression**: Tier-based verification (Tier 0 → Tier 5)
- **Mastery Path**: Learning → Familiar → Known → Mastered
- **Review Guidance**: Shows what to review and when
- **Progress Tracking**: Vocabulary size, learning velocity, mastery counts

### Core Verification Flow
```
1. INITIAL DISCOVERY (Survey)
   User takes vocabulary survey
   ↓
   System identifies known words (binary search)
   ↓
   Words added to learning_progress (Tier 0)
   
2. VERIFICATION START PHASE
   User looks up word (dictionary feature - optional, not learning)
   OR
   System suggests word for verification (Explorer Mode)
   ↓
   User starts verification (via API)
   ↓
   Word added to learning_progress (status: 'pending')
   ↓
   Verification schedule created
   ↓
   Initial verification scheduled (algorithm determines interval)
   
3. VERIFICATION PHASE
   Day 3: First verification (MCQ)
   ↓
   If pass: Schedule Day 7
   If fail: Reschedule Day 3
   ↓
   Day 7: Second verification
   ↓
   If pass: Schedule Day 14
   If fail: Reschedule Day 3
   ↓
   Continue until mastered
   
4. MASTERY PHASE
   Word reaches "mastered" status
   ↓
   Long-term reviews (Day 30, 60, 90...)
   ↓
   Maintain retention
```

### Guiding Mechanisms

**1. Due Cards System**
- Shows cards due for review
- Prioritizes overdue cards
- Suggests review sessions

**2. Progress Indicators**
- Vocabulary size (total words verified)
- Mastery distribution (learning/familiar/known/mastered)
- Learning velocity (words verified per week)
- Retention rate

**3. Adaptive Recommendations**
- Suggests words to verify next
- Identifies words at risk (leech detection)
- Recommends review sessions

### API Endpoints
- `GET /api/v1/dashboard` - Overall progress
- `GET /api/v1/verification/due` - What to review
- `GET /api/v1/analytics/*` - Verification analytics

### Files
- `backend/src/services/vocabulary_size.py` - Vocabulary tracking
- `backend/src/services/learning_velocity.py` - Learning rate
- `backend/src/api/dashboard.py` - Progress dashboard
- `backend/src/api/analytics.py` - Verification analytics

---

## Integration Points

### How They Work Together

**1. Verification Start → Quiz**
```
User starts verification for word
  ↓
Added to learning_progress (status: 'pending')
  ↓
Verification scheduled (algorithm determines interval)
  ↓
MCQ system prepares question
  ↓
User takes quiz → Detailed explanation shown (learning/solidification happens here)
```

**2. Verification → MCQ**
```
Review day arrives
  ↓
Adaptive difficulty selects MCQ
  ↓
User answers MCQ
  ↓
Result updates verification schedule
```

**3. MCQ → Verification Flow**
```
MCQ result processed
  ↓
Mastery level updated
  ↓
Next review scheduled
  ↓
Progress tracked
```

---

## Current Implementation Status

### ✅ Working
- Spaced repetition scheduling (SM-2+ and FSRS)
- MCQ generation and storage
- Adaptive difficulty selection
- Statistical validation tracking
- Review processing
- Progress tracking

### ⚠️ Needs Documentation/Clarification
- Complete verification flow documentation
- Guiding system implementation details
- Word discovery flow (survey integration)
- Mastery progression logic
- Review prioritization algorithm

### ❓ Unknown/To Investigate
- How users discover new words (beyond survey)
- How the system guides users to next words to verify (Explorer Mode provides suggestions)
- How mastery progression works in detail
- How detailed explanations are provided when users get answers wrong

---

## Documentation Structure

### Existing Documentation
- `ADAPTIVE_STATISTICAL_INTEGRATION.md` - MCQ + Spaced Repetition integration
- `MCQ_GENERATION_EXPLAINED.md` - How MCQs are generated
- `MCQ_INDUSTRY_STANDARDS_COMPARISON.md` - MCQ quality standards

### Needed Documentation
- [ ] Complete word verification flow
- [ ] MCQ system architecture
- [ ] Verification flow/guiding system
- [ ] Integration between all three systems
- [ ] API documentation
- [ ] Database schema documentation

---

## Next Steps

1. **Document Current State**
   - Map out complete word verification flow
   - Document MCQ system architecture
   - Document verification flow/guiding mechanisms

2. **Identify Gaps**
   - What's missing in the guiding system?
   - Are there gaps in the verification flow?
   - What needs to be improved?

3. **Create Implementation Plan**
   - Document what needs to be built
   - Prioritize improvements
   - Create task checklist

---

**Document Version:** 1.0  
**Last Updated:** January 2025  
**Status:** Initial Documentation


