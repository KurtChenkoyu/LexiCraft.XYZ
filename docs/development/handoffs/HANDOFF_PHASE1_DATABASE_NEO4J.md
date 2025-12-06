# Handoff: Phase 1 - Database Schema (Neo4j + PostgreSQL)

**For:** Phase 1 - Database Schema  
**Feature:** Neo4j for Learning Point Cloud, PostgreSQL for user data  
**Priority:** High (Foundation - Required for all features)  
**Sprint:** MVP Week 1  
**Estimated Time:** 8-10 hours

---

## Your Mission

You are implementing the database schema for the LexiCraft MVP using a **hybrid approach**:
- **Neo4j**: Learning Point Cloud (relationships, multi-hop queries)
- **PostgreSQL**: User data (users, progress, points, transactions)

**Key Decision**: Use Neo4j for Learning Point Cloud because relationships are core to the value proposition, even in MVP.

---

## Context

This is part of **Week 1: Foundation** of the MVP build. The database schema must support:
- Learning points with relationships (Neo4j)
- User accounts (parents, children) - PostgreSQL
- Learning progress tracking - PostgreSQL
- Points system - PostgreSQL
- Verification scheduling - PostgreSQL
- Withdrawal requests - PostgreSQL

**Taiwan Legal Requirement**: Parent must be account owner (age of majority = 20).

---

## What You Need to Read

**1. MVP Strategy:**
- `docs/10-mvp-validation-strategy.md` - Overall MVP plan
- `docs/15-key-decisions-summary.md` - Key decisions (updated for Neo4j)

**2. Technical Architecture:**
- `docs/04-technical-architecture.md` - Database design (Section 1: Neo4j, Section 2: PostgreSQL)
- `docs/development/NEO4J_VS_POSTGRESQL_ANALYSIS.md` - Why Neo4j

**3. Legal Requirements:**
- `docs/13-legal-analysis-taiwan.md` - Taiwan compliance requirements

---

## Neo4j Schema: Learning Point Cloud

### Node Schema

```cypher
// Learning Point nodes
CREATE CONSTRAINT learning_point_id IF NOT EXISTS
FOR (lp:LearningPoint) REQUIRE lp.id IS UNIQUE;

CREATE CONSTRAINT learning_point_word IF NOT EXISTS
FOR (lp:LearningPoint) REQUIRE lp.word IS UNIQUE;
```

**Node Properties**:
```cypher
(:LearningPoint {
    id: String,              // Unique identifier (e.g., "beat_around_the_bush")
    word: String,            // The word/phrase itself
    type: String,            // "word", "phrase", "idiom", "prefix", "suffix"
    tier: Integer,           // 1-7 (earning tier)
    definition: String,      // Primary definition
    example: String,         // Usage example
    frequency_rank: Integer, // Corpus frequency rank
    difficulty: String,       // "A1", "A2", "B1", "B2", "C1", "C2"
    register: String,        // "formal", "informal", "both"
    contexts: [String],      // ["financial", "geographic", "idiomatic"]
    metadata: Map            // Additional data (pronunciation, synonyms, etc.)
})
```

### Relationship Types

```cypher
// Prerequisites (A → B: need A before B)
(:LearningPoint)-[:PREREQUISITE_OF]->(:LearningPoint)

// Collocations (A ↔ B: often used together)
(:LearningPoint)-[:COLLOCATES_WITH]->(:LearningPoint)

// Related concepts (A ↔ B: similar/related)
(:LearningPoint)-[:RELATED_TO]->(:LearningPoint)

// Part-of relationships (A → B: A is part of B)
(:LearningPoint)-[:PART_OF]->(:LearningPoint)

// Opposites (A ↔ B: antonyms)
(:LearningPoint)-[:OPPOSITE_OF]->(:LearningPoint)

// Morphological (A → B: A is prefix/suffix of B)
(:LearningPoint)-[:MORPHOLOGICAL {type: "prefix"|"suffix"}]->(:LearningPoint)

// Register variants (A → B: A is formal, B is informal)
(:LearningPoint)-[:REGISTER_VARIANT]->(:LearningPoint)

// Frequency ranking (A → B: A is more common than B)
(:LearningPoint)-[:FREQUENCY_RANK]->(:LearningPoint)
```

### Key Queries

```cypher
// Find all components related to a learning point within N degrees
MATCH path = (target:LearningPoint {id: $id})-[*1..3]-(component:LearningPoint)
RETURN component.id, length(path) as degrees, relationships(path)
ORDER BY degrees, component.frequency_rank

// Find prerequisites
MATCH (prereq:LearningPoint)-[:PREREQUISITE_OF]->(target:LearningPoint {id: $id})
RETURN prereq

// Find collocations
MATCH (word:LearningPoint {id: $id})-[:COLLOCATES_WITH]-(colloc:LearningPoint)
RETURN colloc

// Find morphological relationships
MATCH (word:LearningPoint)-[:MORPHOLOGICAL {type: "prefix"}]->(prefix:LearningPoint {id: "in-"})
RETURN word

// Check relationship discovery (for bonuses)
MATCH (source:LearningPoint {id: $source_id})-[r]-(target:LearningPoint)
WHERE target.id IN $user_known_components
RETURN target.id, type(r) as relationship_type
```

---

## PostgreSQL Schema: User Data

### Core Tables

#### 1. `users` (Parents)
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    name TEXT,
    phone TEXT,
    country TEXT DEFAULT 'TW',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_users_email ON users(email);
```

#### 2. `children`
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

#### 3. `learning_progress`
```sql
CREATE TABLE learning_progress (
    id SERIAL PRIMARY KEY,
    child_id UUID NOT NULL REFERENCES children(id) ON DELETE CASCADE,
    learning_point_id TEXT NOT NULL, -- References Neo4j learning_point.id
    learned_at TIMESTAMP DEFAULT NOW(),
    tier INTEGER NOT NULL,
    status TEXT DEFAULT 'learning', -- 'learning', 'pending', 'verified', 'failed'
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(child_id, learning_point_id, tier)
);

CREATE INDEX idx_learning_progress_child_id ON learning_progress(child_id);
CREATE INDEX idx_learning_progress_status ON learning_progress(status);
CREATE INDEX idx_learning_progress_learned_at ON learning_progress(learned_at);
```

#### 4. `verification_schedule`
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
    score FLOAT,
    questions JSONB,
    answers JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_verification_schedule_child_id ON verification_schedule(child_id);
CREATE INDEX idx_verification_schedule_scheduled_date ON verification_schedule(scheduled_date);
CREATE INDEX idx_verification_schedule_completed ON verification_schedule(completed);
```

#### 5. `points_accounts`
```sql
CREATE TABLE points_accounts (
    id SERIAL PRIMARY KEY,
    child_id UUID NOT NULL UNIQUE REFERENCES children(id) ON DELETE CASCADE,
    total_earned INTEGER DEFAULT 0,
    available_points INTEGER DEFAULT 0,
    locked_points INTEGER DEFAULT 0,
    withdrawn_points INTEGER DEFAULT 0,
    deficit_points INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_points_accounts_child_id ON points_accounts(child_id);
```

#### 6. `points_transactions`
```sql
CREATE TABLE points_transactions (
    id SERIAL PRIMARY KEY,
    child_id UUID NOT NULL REFERENCES children(id) ON DELETE CASCADE,
    learning_progress_id INTEGER REFERENCES learning_progress(id),
    transaction_type TEXT NOT NULL, -- 'earned', 'unlocked', 'withdrawn', 'deficit', 'bonus'
    bonus_type TEXT, -- 'relationship_discovery', 'pattern_recognition', etc.
    points INTEGER NOT NULL,
    tier INTEGER,
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_points_transactions_child_id ON points_transactions(child_id);
CREATE INDEX idx_points_transactions_type ON points_transactions(transaction_type);
CREATE INDEX idx_points_transactions_created_at ON points_transactions(created_at);
```

#### 7. `withdrawal_requests`
```sql
CREATE TABLE withdrawal_requests (
    id SERIAL PRIMARY KEY,
    child_id UUID NOT NULL REFERENCES children(id) ON DELETE CASCADE,
    parent_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    amount_ntd DECIMAL(10,2) NOT NULL,
    points_amount INTEGER NOT NULL,
    status TEXT DEFAULT 'pending', -- 'pending', 'processing', 'completed', 'failed'
    bank_account TEXT,
    transaction_id TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP
);

CREATE INDEX idx_withdrawal_requests_child_id ON withdrawal_requests(child_id);
CREATE INDEX idx_withdrawal_requests_parent_id ON withdrawal_requests(parent_id);
CREATE INDEX idx_withdrawal_requests_status ON withdrawal_requests(status);
```

#### 8. `relationship_discoveries` (Track user relationship knowledge)
```sql
CREATE TABLE relationship_discoveries (
    id SERIAL PRIMARY KEY,
    child_id UUID NOT NULL REFERENCES children(id) ON DELETE CASCADE,
    source_learning_point_id TEXT NOT NULL, -- Neo4j ID
    target_learning_point_id TEXT NOT NULL, -- Neo4j ID
    relationship_type TEXT NOT NULL,
    discovered_at TIMESTAMP DEFAULT NOW(),
    bonus_awarded BOOLEAN DEFAULT FALSE,
    UNIQUE(child_id, source_learning_point_id, target_learning_point_id, relationship_type)
);

CREATE INDEX idx_relationship_discoveries_child_id ON relationship_discoveries(child_id);
CREATE INDEX idx_relationship_discoveries_source ON relationship_discoveries(source_learning_point_id);
```

---

## Implementation Tasks

### Task 1: Set Up Neo4j

1. **Choose deployment option**:
   - **Option A**: Neo4j Aura Free (cloud, easiest)
     - Sign up at https://neo4j.com/cloud/aura/
     - Create free database (50K nodes, 175K relationships)
     - Get connection URI and credentials
   - **Option B**: Docker (local dev, production)
     ```bash
     docker run \
       --name neo4j-learning-points \
       -p7474:7474 -p7687:7687 \
       -e NEO4J_AUTH=neo4j/password \
       neo4j:latest
     ```

2. **Create constraints**:
   ```cypher
   CREATE CONSTRAINT learning_point_id IF NOT EXISTS
   FOR (lp:LearningPoint) REQUIRE lp.id IS UNIQUE;
   
   CREATE CONSTRAINT learning_point_word IF NOT EXISTS
   FOR (lp:LearningPoint) REQUIRE lp.word IS UNIQUE;
   ```

3. **Test connection**:
   ```python
   from neo4j import GraphDatabase
   
   driver = GraphDatabase.driver(
       "neo4j://localhost:7687",
       auth=("neo4j", "password")
   )
   
   with driver.session() as session:
       result = session.run("RETURN 1 as test")
       print(result.single()["test"])  # Should print 1
   ```

### Task 2: Set Up PostgreSQL (Supabase)

1. Create Supabase project at https://supabase.com
2. Get connection string
3. Create migration files (see schema above)

### Task 3: Create Python Models

Create `src/models/` directory:

- `learning_point.py` - Pydantic model for LearningPoint
- `user.py` - Pydantic models for User, Child
- `progress.py` - Pydantic model for LearningProgress
- `verification.py` - Pydantic model for VerificationSchedule
- `points.py` - Pydantic models for PointsAccount, PointsTransaction
- `withdrawal.py` - Pydantic model for WithdrawalRequest

### Task 4: Create Database Connections

1. **Neo4j connection** (`src/database/neo4j_connection.py`):
   ```python
   from neo4j import GraphDatabase
   from typing import Optional
   
   class Neo4jConnection:
       def __init__(self, uri: str, user: str, password: str):
           self.driver = GraphDatabase.driver(uri, auth=(user, password))
       
       def close(self):
           self.driver.close()
       
       def get_session(self):
           return self.driver.session()
   ```

2. **PostgreSQL connection** (`src/database/postgres_connection.py`):
   ```python
   from sqlalchemy import create_engine
   from sqlalchemy.orm import sessionmaker
   
   class PostgresConnection:
       def __init__(self, connection_string: str):
           self.engine = create_engine(connection_string)
           self.SessionLocal = sessionmaker(bind=self.engine)
       
       def get_session(self):
           return self.SessionLocal()
   ```

### Task 5: Create CRUD Operations

**Neo4j CRUD** (`src/database/neo4j_crud/`):
- `learning_points.py` - CRUD for learning points
- `relationships.py` - Relationship queries

**PostgreSQL CRUD** (`src/database/postgres_crud/`):
- `users.py` - CRUD for users/children
- `progress.py` - CRUD for learning progress
- `verification.py` - CRUD for verification schedule
- `points.py` - CRUD for points accounts/transactions
- `withdrawals.py` - CRUD for withdrawal requests

### Task 6: Create Relationship Discovery Service

Create `src/services/relationship_discovery.py`:

```python
from src.database.neo4j_connection import Neo4jConnection
from src.database.postgres_crud.progress import get_user_known_components

def discover_relationships(child_id: str, learning_point_id: str):
    """
    Discover relationships for a newly learned word.
    Awards relationship discovery bonuses.
    """
    # Get user's known components from PostgreSQL
    known_components = get_user_known_components(child_id)
    
    # Query Neo4j for relationships
    with neo4j_conn.get_session() as session:
        result = session.run("""
            MATCH (source:LearningPoint {id: $id})-[r]-(target:LearningPoint)
            WHERE target.id IN $known_components
            RETURN target.id, type(r) as relationship_type
        """, id=learning_point_id, known_components=known_components)
        
        relationships = [record for record in result]
    
    # Award bonuses for discovered relationships
    for rel in relationships:
        award_relationship_bonus(child_id, learning_point_id, rel['target.id'], rel['relationship_type'])
    
    return relationships
```

### Task 7: Write Tests

Create `tests/test_database/`:
- `test_neo4j_schema.py` - Test Neo4j schema
- `test_neo4j_queries.py` - Test relationship queries
- `test_postgres_schema.py` - Test PostgreSQL schema
- `test_postgres_crud.py` - Test CRUD operations
- `test_relationship_discovery.py` - Test relationship discovery

---

## Success Criteria

- [ ] Neo4j instance set up and connected
- [ ] Neo4j constraints created
- [ ] PostgreSQL schema created with all tables
- [ ] All indexes created
- [ ] Pydantic models match schemas
- [ ] Basic CRUD operations working (both databases)
- [ ] Relationship discovery service working
- [ ] Tests passing (>80% coverage)

---

## Testing Requirements

### Unit Tests
- Test each CRUD operation (Neo4j and PostgreSQL)
- Test relationship queries
- Test relationship discovery logic

### Integration Tests
- Test full user flow (create parent → create child → learn word → discover relationships)
- Test points calculation with relationship bonuses
- Test verification scheduling

---

## Dependencies

**You have no blocking dependencies** - you can start immediately.

**You are a dependency for:**
- Phase 1 - Word List (needs Neo4j schema to populate)
- Phase 2 - User Auth (needs PostgreSQL users/children tables)
- Phase 2 - Learning Interface (needs Neo4j learning points)
- Phase 2 - MCQ System (needs Neo4j learning points)
- Phase 3 - All features (need all tables)

---

## Questions?

1. Check `docs/development/NEO4J_VS_POSTGRESQL_ANALYSIS.md` for why Neo4j
2. Check `docs/04-technical-architecture.md` for technical details
3. Check `docs/13-legal-analysis-taiwan.md` for legal requirements
4. Ask the master planning chat if still unclear

---

## Completion Report Format

When done, create a completion report:

```markdown
# Completion Report: Phase 1 - Database Schema (Neo4j + PostgreSQL)

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

