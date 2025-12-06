# Handoff: Phase 1 - Database Schema

**For:** Phase 1 - Database Schema  
**Feature:** PostgreSQL database schema for MVP  
**Priority:** High (Foundation - Required for all features)  
**Sprint:** MVP Week 1  
**Estimated Time:** 4-6 hours

---

## Your Mission

You are implementing the database schema for the LexiCraft MVP. This is the foundation that all other features depend on.

**Key Decision**: Use PostgreSQL + JSONB (not Neo4j) for MVP speed.

---

## Context

This is part of **Week 1: Foundation** of the MVP build. The database schema must support:
- Learning points (words, definitions, examples)
- User accounts (parents, children)
- Learning progress tracking
- Points system
- Verification scheduling
- Withdrawal requests

**Taiwan Legal Requirement**: Parent must be account owner (age of majority = 20).

---

## What You Need to Read

**1. MVP Strategy:**
- `docs/10-mvp-validation-strategy.md` - Overall MVP plan
- `docs/15-key-decisions-summary.md` - Key decisions

**2. Technical Architecture:**
- `docs/04-technical-architecture.md` - Database design (Section 2)

**3. Legal Requirements:**
- `docs/13-legal-analysis-taiwan.md` - Taiwan compliance requirements

---

## Database Schema Requirements

### Core Tables

#### 1. `learning_points`
Stores vocabulary words and their learning point data.

```sql
CREATE TABLE learning_points (
    id SERIAL PRIMARY KEY,
    word TEXT NOT NULL,
    type TEXT DEFAULT 'word', -- 'word', 'phrase', 'idiom'
    tier INTEGER NOT NULL, -- 1-7
    definition TEXT,
    example TEXT,
    frequency_rank INTEGER,
    difficulty TEXT, -- 'A1', 'A2', 'B1', 'B2', 'C1', 'C2'
    metadata JSONB DEFAULT '{}', -- Store extra data (pronunciation, synonyms, etc.)
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_learning_points_word ON learning_points(word);
CREATE INDEX idx_learning_points_tier ON learning_points(tier);
CREATE INDEX idx_learning_points_frequency ON learning_points(frequency_rank);
CREATE INDEX idx_learning_points_metadata ON learning_points USING GIN(metadata);
```

#### 2. `users` (Parents)
Parent accounts (legal account owners).

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    name TEXT,
    phone TEXT,
    country TEXT DEFAULT 'TW', -- Taiwan default
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_users_email ON users(email);
```

#### 3. `children`
Child accounts linked to parent.

```sql
CREATE TABLE children (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    parent_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    age INTEGER,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_children_parent_id ON children(parent_id);
```

#### 4. `learning_progress`
Track child's learning progress per word.

```sql
CREATE TABLE learning_progress (
    id SERIAL PRIMARY KEY,
    child_id UUID NOT NULL REFERENCES children(id) ON DELETE CASCADE,
    learning_point_id INTEGER NOT NULL REFERENCES learning_points(id) ON DELETE CASCADE,
    learned_at TIMESTAMP DEFAULT NOW(),
    tier INTEGER NOT NULL, -- Which tier they're learning (1 or 2 for MVP)
    status TEXT DEFAULT 'learning', -- 'learning', 'pending', 'verified', 'failed'
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(child_id, learning_point_id, tier)
);

CREATE INDEX idx_learning_progress_child_id ON learning_progress(child_id);
CREATE INDEX idx_learning_progress_status ON learning_progress(status);
CREATE INDEX idx_learning_progress_learned_at ON learning_progress(learned_at);
```

#### 5. `verification_schedule`
Schedule and track verification tests (Day 1, 3, 7).

```sql
CREATE TABLE verification_schedule (
    id SERIAL PRIMARY KEY,
    child_id UUID NOT NULL REFERENCES children(id) ON DELETE CASCADE,
    learning_progress_id INTEGER NOT NULL REFERENCES learning_progress(id) ON DELETE CASCADE,
    test_day INTEGER NOT NULL, -- 1, 3, or 7
    scheduled_date DATE NOT NULL,
    completed BOOLEAN DEFAULT FALSE,
    completed_at TIMESTAMP,
    passed BOOLEAN,
    score FLOAT, -- 0.0 to 1.0
    questions JSONB, -- Store question data
    answers JSONB, -- Store answer data
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_verification_schedule_child_id ON verification_schedule(child_id);
CREATE INDEX idx_verification_schedule_scheduled_date ON verification_schedule(scheduled_date);
CREATE INDEX idx_verification_schedule_completed ON verification_schedule(completed);
```

#### 6. `points_accounts`
Track points balance per child.

```sql
CREATE TABLE points_accounts (
    id SERIAL PRIMARY KEY,
    child_id UUID NOT NULL UNIQUE REFERENCES children(id) ON DELETE CASCADE,
    total_earned INTEGER DEFAULT 0, -- Total points earned
    available_points INTEGER DEFAULT 0, -- Can withdraw
    locked_points INTEGER DEFAULT 0, -- Pending verification
    withdrawn_points INTEGER DEFAULT 0, -- Already withdrawn
    deficit_points INTEGER DEFAULT 0, -- Negative balance (if verification fails)
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_points_accounts_child_id ON points_accounts(child_id);
```

#### 7. `points_transactions`
Track all point transactions.

```sql
CREATE TABLE points_transactions (
    id SERIAL PRIMARY KEY,
    child_id UUID NOT NULL REFERENCES children(id) ON DELETE CASCADE,
    learning_progress_id INTEGER REFERENCES learning_progress(id),
    transaction_type TEXT NOT NULL, -- 'earned', 'unlocked', 'withdrawn', 'deficit'
    points INTEGER NOT NULL, -- Can be negative for deficit
    tier INTEGER, -- Which tier earned
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_points_transactions_child_id ON points_transactions(child_id);
CREATE INDEX idx_points_transactions_type ON points_transactions(transaction_type);
CREATE INDEX idx_points_transactions_created_at ON points_transactions(created_at);
```

#### 8. `withdrawal_requests`
Track withdrawal requests.

```sql
CREATE TABLE withdrawal_requests (
    id SERIAL PRIMARY KEY,
    child_id UUID NOT NULL REFERENCES children(id) ON DELETE CASCADE,
    parent_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    amount_ntd DECIMAL(10,2) NOT NULL, -- Amount in NT$
    points_amount INTEGER NOT NULL, -- Points converted
    status TEXT DEFAULT 'pending', -- 'pending', 'processing', 'completed', 'failed'
    bank_account TEXT, -- Bank account for transfer
    transaction_id TEXT, -- Payment processor transaction ID
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP
);

CREATE INDEX idx_withdrawal_requests_child_id ON withdrawal_requests(child_id);
CREATE INDEX idx_withdrawal_requests_parent_id ON withdrawal_requests(parent_id);
CREATE INDEX idx_withdrawal_requests_status ON withdrawal_requests(status);
```

#### 9. `relationships` (Future - for Learning Point Cloud)
Store relationships between learning points (for Phase 2).

```sql
CREATE TABLE relationships (
    id SERIAL PRIMARY KEY,
    source_learning_point_id INTEGER NOT NULL REFERENCES learning_points(id) ON DELETE CASCADE,
    target_learning_point_id INTEGER NOT NULL REFERENCES learning_points(id) ON DELETE CASCADE,
    relationship_type TEXT NOT NULL, -- 'RELATED_TO', 'OPPOSITE_OF', 'MORPHOLOGICAL', etc.
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(source_learning_point_id, target_learning_point_id, relationship_type)
);

CREATE INDEX idx_relationships_source ON relationships(source_learning_point_id);
CREATE INDEX idx_relationships_target ON relationships(target_learning_point_id);
CREATE INDEX idx_relationships_type ON relationships(relationship_type);
```

---

## Implementation Tasks

### Task 1: Create Migration Files

1. Create `migrations/001_initial_schema.sql` with all tables above
2. Create `migrations/002_add_indexes.sql` with all indexes
3. Test migrations on local database

### Task 2: Create Pydantic Models

Create `src/models/` directory with Pydantic models:

- `learning_point.py` - LearningPoint model
- `user.py` - User, Child models
- `progress.py` - LearningProgress model
- `verification.py` - VerificationSchedule model
- `points.py` - PointsAccount, PointsTransaction models
- `withdrawal.py` - WithdrawalRequest model

### Task 3: Create Database Connection

1. Set up Supabase connection (or local PostgreSQL)
2. Create `src/database/connection.py`
3. Create `src/database/session.py` for SQLAlchemy sessions

### Task 4: Create Basic CRUD Operations

Create `src/database/crud/` directory:

- `learning_points.py` - CRUD for learning points
- `users.py` - CRUD for users/children
- `progress.py` - CRUD for learning progress
- `verification.py` - CRUD for verification schedule
- `points.py` - CRUD for points accounts/transactions
- `withdrawals.py` - CRUD for withdrawal requests

### Task 5: Write Tests

Create `tests/test_database/`:

- `test_schema.py` - Test schema creation
- `test_crud.py` - Test CRUD operations
- `test_relationships.py` - Test foreign key relationships

---

## Success Criteria

- [ ] All tables created with proper constraints
- [ ] All indexes created
- [ ] Foreign key relationships working
- [ ] Pydantic models match schema
- [ ] Basic CRUD operations working
- [ ] Tests passing (>80% coverage)
- [ ] Migration files ready for deployment

---

## Testing Requirements

### Unit Tests
- Test each CRUD operation
- Test foreign key constraints
- Test unique constraints
- Test JSONB queries

### Integration Tests
- Test full user flow (create parent → create child → create progress)
- Test points calculation
- Test verification scheduling

---

## Code Quality

- Follow existing code patterns (if any)
- Use Pydantic for validation
- Add proper error handling
- Include docstrings for all functions
- Add type hints

---

## Dependencies

**You have no blocking dependencies** - you can start immediately.

**You are a dependency for:**
- Phase 2 - User Auth (needs users/children tables)
- Phase 2 - Learning Interface (needs learning_points table)
- Phase 2 - MCQ System (needs learning_points table)
- Phase 3 - All features (need all tables)

---

## Questions?

1. Check `docs/10-mvp-validation-strategy.md` for MVP context
2. Check `docs/04-technical-architecture.md` for technical details
3. Check `docs/13-legal-analysis-taiwan.md` for legal requirements
4. Ask the master planning chat if still unclear

---

## Completion Report Format

When done, create a completion report:

```markdown
# Completion Report: Phase 1 - Database Schema

**Status:** ✅ Complete

## What was done:
- [List of what was implemented]

## Decisions made:
- [Key design decisions]

## Files created:
- [List of files]

## Testing:
- [Test results, coverage]

## Known issues:
- [Any issues]

## Next steps:
- [What Phase 2 needs from this]
```

---

**Good luck! You're building the foundation that makes everything else possible.**

