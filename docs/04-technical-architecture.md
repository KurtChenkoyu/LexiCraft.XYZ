# Technical Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (React/Next.js)                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ Parent       │  │ Child        │  │ Admin        │     │
│  │ Dashboard    │  │ Learning UI  │  │ Dashboard    │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              Backend API (Python/FastAPI)                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ Learning     │  │ Verification │  │ Financial    │     │
│  │ API          │  │ API          │  │ API          │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
         │              │              │
         ▼              ▼              ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ Learning     │  │ User        │  │ Escrow       │
│ Point Cloud  │  │ Knowledge   │  │ Accounts     │
│ (Neo4j)      │  │ (PostgreSQL)│  │ (Bank API)   │
└──────────────┘  └──────────────┘  └──────────────┘
```

## Core Components

### 1. Learning Point Cloud (Neo4j)

**Purpose**: Pre-populated knowledge graph of all learning relationships

**Structure**:
```cypher
(:LearningPoint {
  id: String,
  type: "word" | "phrase" | "idiom" | "prefix" | "suffix",
  content: String,
  frequency_rank: Integer,
  difficulty: "A1" | "A2" | "B1" | "B2" | "C1" | "C2",
  register: "formal" | "informal" | "both",
  contexts: [String]
})

(:LearningPoint)-[:PREREQUISITE_OF]->(:LearningPoint)
(:LearningPoint)-[:COLLOCATES_WITH]->(:LearningPoint)
(:LearningPoint)-[:RELATED_TO]->(:LearningPoint)
(:LearningPoint)-[:PART_OF]->(:LearningPoint)
(:LearningPoint)-[:OPPOSITE_OF]->(:LearningPoint)
(:LearningPoint)-[:MORPHOLOGICAL {type: "prefix"|"suffix"}]->(:LearningPoint)
(:LearningPoint)-[:REGISTER_VARIANT]->(:LearningPoint)
(:LearningPoint)-[:FREQUENCY_RANK]->(:LearningPoint)
```

**Key Queries**:
```cypher
// Find all components related to a learning point
MATCH path = (target:LearningPoint {id: $id})-[*1..3]-(component:LearningPoint)
RETURN component.id, length(path) as degrees, relationships(path)
ORDER BY degrees, component.frequency_rank

// Find prerequisites
MATCH (prereq:LearningPoint)-[:PREREQUISITE_OF]->(target:LearningPoint {id: $id})
RETURN prereq

// Find collocations
MATCH (word:LearningPoint {id: $id})-[:COLLOCATES_WITH]-(colloc:LearningPoint)
RETURN colloc
```

### 2. User Knowledge State (PostgreSQL)

**Purpose**: Track user accounts, learning progress, points, and verification schedules

**Schema**:
```sql
-- 1. Users (Parents)
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

-- 2. Children
CREATE TABLE children (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    parent_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    age INTEGER,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 3. Learning Progress
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

-- 4. Verification Schedule
CREATE TABLE verification_schedule (
    id SERIAL PRIMARY KEY,
    child_id UUID NOT NULL REFERENCES children(id) ON DELETE CASCADE,
    learning_progress_id INTEGER NOT NULL REFERENCES learning_progress(id) ON DELETE CASCADE,
    test_day INTEGER NOT NULL, -- 1, 3, or 7
    scheduled_date DATE NOT NULL,
    completed BOOLEAN DEFAULT FALSE,
    completed_at TIMESTAMP,
    passed BOOLEAN,
    score DECIMAL(5, 2),
    questions JSONB,
    answers JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 5. Points Accounts
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

-- 6. Points Transactions
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

-- 7. Withdrawal Requests
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

-- 8. Relationship Discoveries
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
```

**Key Design Decisions**:
- **UUID for users/children**: Better security and distribution
- **Child-centric tracking**: All progress tracked per child (not per user)
- **Learning progress links to Neo4j**: `learning_point_id` references Neo4j LearningPoint nodes
- **Points system**: Separate accounts and transactions for audit trail
- **Relationship discoveries**: Tracks bonus awards for relationship discovery
- **Verification schedule**: Uses JSONB for flexible question/answer storage

### 3. Verification Engine

**Components**:
- Spaced repetition scheduler
- Multi-modal assessment generator
- Behavioral analytics processor
- AI-powered contextual tester
- Retention tracker

**Verification Flow**:
```
1. User learns component
   ↓
2. Schedule verification (Day 3, 7, 14)
   ↓
3. Generate assessment (4 test types)
   ↓
4. User completes assessment
   ↓
5. Score and evaluate
   ↓
6. If passed: Update knowledge state, unlock money
   ↓
7. If failed: Reschedule, provide feedback
   ↓
8. Schedule retention check (Day 60)
```

**Assessment Types**:
1. **Recognition**: Multiple choice
2. **Recall**: Fill-in-the-blank
3. **Usage**: Sentence completion
4. **Comprehension**: Short answer (AI-graded)

### 4. Earning Calculation Engine

**Tier Definitions**:
```python
TIER_RATES = {
    1: 1.00,   # Basic recognition
    2: 2.50,   # Multiple meanings
    3: 5.00,   # Phrase mastery
    4: 10.00,  # Idiom mastery
    5: 3.00,   # Morphological relationships
    6: 4.00,   # Register mastery
    7: 7.50    # Advanced context
}

BONUS_TYPES = {
    "relationship_discovery": 1.50,
    "pattern_recognition": 2.00,
    "phrase_completion": 3.00,
    "idiom_unlock": 7.00,
    "context_mastery": 2.00,
    "pattern_mastery": 5.00
}
```

**Calculation Logic**:
```python
def calculate_earning(learning_point_id, tier, bonuses=[]):
    base_amount = TIER_RATES[tier]
    bonus_amount = sum(BONUS_TYPES[b] for b in bonuses)
    return base_amount + bonus_amount
```

### 5. Financial Infrastructure

**Escrow Management**:
- Third-party escrow service integration
- Automated unlock triggers
- Transfer processing
- Dispute resolution workflow

**Payment Processing**:
- Stripe for parent deposits
- Plaid for bank account linking
- Automated transfer to child accounts
- Transaction history tracking

## API Design

### Learning Point Cloud API

```python
# Get learning point details
GET /api/learning-points/{id}
Response: {
    "id": "beat_around_the_bush",
    "type": "idiom",
    "content": "beat around the bush",
    "relationships": [...],
    "frequency_rank": 1234,
    "difficulty": "B2"
}

# Find related components
GET /api/learning-points/{id}/related?degrees=3
Response: {
    "components": [
        {"id": "beat", "degrees": 1, "relationship": "PART_OF"},
        {"id": "indirect", "degrees": 2, "relationship": "RELATED_TO"}
    ]
}

# Query prerequisites
GET /api/learning-points/{id}/prerequisites
Response: {
    "prerequisites": ["direct", "in-"]
}
```

### User Knowledge API

```python
# Get child learning progress
GET /api/children/{child_id}/progress
Response: {
    "learning": [...],
    "pending": [...],
    "verified": [...],
    "failed": [...]
}

# Create learning progress entry
POST /api/children/{child_id}/progress
Body: {
    "learning_point_id": "beat_around_the_bush",
    "tier": 1,
    "status": "learning"
}

# Get points account
GET /api/children/{child_id}/points
Response: {
    "total_earned": 1250,
    "available_points": 1000,
    "locked_points": 200,
    "withdrawn_points": 50,
    "deficit_points": 0
}

# Get points transactions
GET /api/children/{child_id}/transactions
Response: {
    "transactions": [
        {
            "id": 1,
            "transaction_type": "earned",
            "points": 100,
            "tier": 1,
            "created_at": "2025-01-01T00:00:00Z"
        }
    ]
}
```

### Verification API

```python
# Generate assessment
POST /api/verification/assessments
Body: {
    "child_id": "...",
    "learning_point_id": "beat",
    "verification_type": "initial"
}
Response: {
    "assessment_id": "...",
    "questions": [...]
}

# Submit assessment
POST /api/verification/assessments/{id}/submit
Body: {
    "answers": [...]
}
Response: {
    "passed": true,
    "score": 0.95,
    "unlocked_amount": 1.00
}
```

### Financial API

```python
# Deposit (parent)
POST /api/financial/deposit
Body: {
    "user_id": "...",
    "amount": 10000.00,
    "payment_method": "..."
}

# Get unlock status
GET /api/financial/children/{child_id}/unlocks
Response: {
    "total_earned": 2500,
    "available_points": 1500,
    "locked_points": 800,
    "withdrawn_points": 200
}

# Create withdrawal request
POST /api/financial/withdrawals
Body: {
    "child_id": "...",
    "parent_id": "...",
    "points_amount": 500,
    "amount_ntd": 500.00,
    "bank_account": "..."
}
```
```

## Technology Stack

### Backend
- **Framework**: FastAPI (Python)
- **Database**: Neo4j (Learning Point Cloud), PostgreSQL (user data)
- **Cache**: Redis
- **Queue**: Celery + Redis
- **AI/ML**: OpenAI API, custom models

### Frontend
- **Framework**: Next.js (React)
- **State Management**: Zustand/Redux
- **UI Library**: Tailwind CSS, shadcn/ui
- **Charts**: Recharts/D3.js

### Infrastructure (MVP)
- **Hosting**: Vercel (free tier)
- **Neo4j**: Neo4j Aura Free (50K nodes, 175K relationships)
- **PostgreSQL**: Supabase (free tier, 500MB)
- **CDN**: Vercel Edge (included)
- **Monitoring**: PostHog (free tier)
- **Logging**: Vercel logs (included)

**Deployment**: Cloud-based (SaaS) - Internet required. See `docs/development/DEPLOYMENT_ARCHITECTURE.md` for details.

**Distraction Mitigation**: See `docs/development/DISTRACTION_MITIGATION.md` for strategies.

### Payments
- **Escrow**: Third-party service (TBD)
- **Payments**: Stripe
- **Banking**: Plaid

## Security & Compliance

### Data Security
- Encryption at rest and in transit
- Secure API authentication (JWT)
- Role-based access control
- Regular security audits

### Compliance
- COPPA compliance (children's data)
- FERPA compliance (if school partnerships)
- Financial regulations (escrow, money transmission)
- GDPR compliance (if international)

### Privacy
- Minimal data collection
- Parental consent for children
- Data retention policies
- Right to deletion

## Scalability Considerations

### Database
- Neo4j: Shared instance, read replicas
- PostgreSQL: Read replicas, connection pooling
- Redis: Cluster mode for caching

### API
- Horizontal scaling (multiple instances)
- Load balancing
- Rate limiting
- Caching strategies

### Processing
- Async task processing (Celery)
- Background jobs for verification
- Batch processing for analytics

## Next Steps

1. Set up development environment
2. Initialize databases
3. Implement Learning Point Cloud API
4. Build user knowledge tracking
5. Create verification engine

See `05-api-specifications.md` for detailed API documentation.

