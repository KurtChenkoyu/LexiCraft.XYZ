---
name: FSRS Implementation Plan
overview: ""
todos:
  - id: 42e0740c-d911-4e0b-bedf-9e72e7a70e66
    content: Create database migration for FSRS support (schema updates, user assignment table, review history table)
    status: pending
  - id: e47b467a-64eb-44c7-958e-0d92fb04afe2
    content: Install FSRS Python library and create FSRS service wrapper
    status: pending
  - id: 4e94e8e5-9d77-4155-ac1d-ef78ac08f83c
    content: Create algorithm interface to abstract SM-2+ and FSRS
    status: pending
  - id: 6d54a0ac-0107-4fcd-87ba-22f0e7726aac
    content: Implement user assignment service for A/B testing
    status: pending
  - id: f1e1ff00-12d1-4cf9-afc5-65c2358b05f6
    content: Update verification scheduling logic to use algorithm interface
    status: pending
  - id: e29289ef-3101-4847-af6a-bfec93bdb679
    content: Create API endpoints for review processing and algorithm info
    status: pending
---

# FSRS Implementation Plan

## Overview

Implement FSRS algorithm in parallel with SM-2+ to enable A/B testing. Users will be assigned to either SM-2+ (control) or FSRS (treatment) group. Use the existing Python `fsrs` library from PyPI for faster implementation.

## Phase 1: Database Schema Updates

### 1.1 Extend verification_schedule table

**File:** `backend/migrations/011_fsrs_support.sql`

Add FSRS-specific columns to existing `verification_schedule` table:

- `algorithm_type` TEXT (default 'sm2_plus', values: 'sm2_plus', 'fsrs')
- `stability` FLOAT (FSRS: memory stability)
- `difficulty` FLOAT (FSRS: word difficulty, 0-1)
- `retention_probability` FLOAT (FSRS: predicted retention at review time)
- `fsrs_state` JSONB (FSRS: full state object for the library)
- `last_review_date` DATE (FSRS: needed for elapsed time calculation)

Keep existing columns for SM-2+ compatibility:

- `test_day` (SM-2+ specific, can be NULL for FSRS)
- `ease_factor` (SM-2+ specific, can be NULL for FSRS)

### 1.2 Create user_algorithm_assignment table

**File:** `backend/migrations/011_fsrs_support.sql`

Track which algorithm each user is assigned to:

- `user_id` UUID (FK to users)
- `algorithm` TEXT ('sm2_plus' or 'fsrs')
- `assigned_at` TIMESTAMP
- `assignment_reason` TEXT (e.g., 'random', 'manual', 'migration')

### 1.3 Create fsrs_review_history table

**File:** `backend/migrations/011_fsrs_support.sql`

Store detailed review history for FSRS training:

- `user_id` UUID
- `learning_progress_id` INTEGER
- `review_date` TIMESTAMP
- `performance_rating` INTEGER (0-4, FSRS scale)
- `response_time_ms` INTEGER
- `stability_before` FLOAT
- `stability_after` FLOAT
- `difficulty_before` FLOAT
- `difficulty_after` FLOAT
- `retention_predicted` FLOAT
- `retention_actual` BOOLEAN (did user remember?)

## Phase 2: FSRS Library Integration

### 2.1 Install FSRS library

**File:** `backend/requirements.txt`

Add: `fsrs>=4.0.0` (or latest version from PyPI)

### 2.2 Create FSRS service wrapper

**File:** `backend/src/spaced_repetition/fsrs_service.py` (NEW)

Create service class that wraps the `fsrs` library:

- `FSRSService` class
- Methods:
- `initialize_card()` - Create new FSRS card state
- `schedule_review()` - Calculate next review date
- `process_review()` - Update state after review
- `predict_retention()` - Get retention probability
- `optimize_parameters()` - Retrain model for user (after 100+ reviews)

Handle FSRS-specific concepts:

- Stability (memory strength)
- Difficulty (word difficulty)
- Rating scale (0-4: Again, Hard, Good, Easy)
- State serialization/deserialization

### 2.3 Create algorithm interface

**File:** `backend/src/spaced_repetition/algorithm_interface.py` (NEW)

Abstract interface for both algorithms:

- `SpacedRepetitionAlgorithm` base class
- `SM2PlusAlgorithm` implementation
- `FSRSAlgorithm` implementation
- Factory method: `get_algorithm(user_id)` - returns appropriate algorithm

## Phase 3: User Assignment & A/B Testing

### 3.1 Create assignment service

**File:** `backend/src/spaced_repetition/assignment_service.py` (NEW)

Handle user algorithm assignment:

- `assign_algorithm(user_id)` - Random assignment (50/50 split)
- `get_user_algorithm(user_id)` - Get assigned algorithm
- `can_migrate_to_fsrs(user_id)` - Check if user has 100+ reviews
- `migrate_user_to_fsrs(user_id)` - Migrate from SM-2+ to FSRS

Assignment rules:

- New users: Random 50/50 split
- Existing users: Keep current algorithm unless manually migrated
- Users with 100+ reviews: Can opt-in to FSRS

### 3.2 Update verification scheduling logic

**File:** `backend/src/database/postgres_crud/verification.py` (MODIFY)

Modify `create_verification_schedule()` to:

1. Get user's assigned algorithm
2. Use appropriate algorithm to calculate next review
3. Store algorithm-specific state

## Phase 4: API Updates

### 4.1 Update review processing endpoint

**File:** `backend/src/api/verification.py` (NEW or MODIFY)

Create/update endpoint to process reviews:

- `POST /api/v1/verification/review`
- Accepts: `learning_progress_id`, `performance_rating`, `response_time_ms`
- Uses user's assigned algorithm to:
- Update state
- Calculate next review date
- Store review history

### 4.2 Add algorithm info endpoint

**File:** `backend/src/api/verification.py`

Add: `GET /api/v1/verification/algorithm`

- Returns user's assigned algorithm
- Shows if they can migrate to FSRS
- Shows algorithm-specific stats

## Phase 5: Data Migration

### 5.1 Migrate existing SM-2+ data

**File:** `backend/scripts/migrate_to_fsrs.py` (NEW)

Script to migrate existing users:

- For users assigned to FSRS: Convert SM-2+ state to FSRS state
- Estimate initial stability from ease_factor
- Estimate initial difficulty from error rate
- Preserve review history

### 5.2 Backfill FSRS review history

**File:** `backend/scripts/backfill_fsrs_history.py` (NEW)

For users with existing reviews:

- Convert historical reviews to FSRS format
- Train initial FSRS parameters
- Calculate initial stability/difficulty

## Phase 6: Monitoring & Analytics

### 6.1 Create comparison metrics

**File:** `backend/src/analytics/algorithm_comparison.py` (NEW)

Track metrics for both algorithms:

- Reviews per word (should be lower for FSRS)
- Retention rate (should be same or better for FSRS)
- User satisfaction (surveys/feedback)
- Time to mastery (days to reach "mastered" status)

### 6.2 Add analytics endpoints

**File:** `backend/src/api/analytics.py` (NEW)

- `GET /api/v1/analytics/algorithm-performance` - Compare SM-2+ vs FSRS
- `GET /api/v1/analytics/user-stats` - User's algorithm performance

## Phase 7: Testing

### 7.1 Unit tests

**Files:** `backend/tests/test_fsrs_service.py`, `backend/tests/test_algorithm_interface.py`

Test:

- FSRS state initialization
- Review processing
- Interval calculation
- State serialization
- Algorithm switching

### 7.2 Integration tests

**File:** `backend/tests/test_verification_flow.py`

Test:

- End-to-end review flow with both algorithms
- User assignment
- Data migration
- A/B test data collection

## Implementation Order

1. **Week 1:** Database schema + FSRS library integration
2. **Week 2:** Algorithm interface + assignment service
3. **Week 3:** API updates + review processing
4. **Week 4:** Data migration + testing
5. **Week 5:** Monitoring + analytics

## Key Files to Create/Modify

**New Files:**

- `backend/migrations/011_fsrs_support.sql`
- `backend/src/spaced_repetition/fsrs_service.py`
- `backend/src/spaced_repetition/algorithm_interface.py`
- `backend/src/spaced_repetition/assignment_service.py`
- `backend/src/api/verification.py`
- `backend/src/analytics/algorithm_comparison.py`
- `backend/scripts/migrate_to_fsrs.py`

**Modified Files:**

- `backend/requirements.txt` (add fsrs library)
- `backend/src/database/models.py` (add FSRS columns to VerificationSchedule)
- `backend/src/database/postgres_crud/verification.py` (use algorithm interface)

## Success Criteria

- Both algorithms run in parallel
- Users can be assigned to either algorithm
- FSRS shows 20-30% fewer reviews needed
- Retention rates are same or better with FSRS
- System can migrate users between algorithms
- Analytics show clear comparison data