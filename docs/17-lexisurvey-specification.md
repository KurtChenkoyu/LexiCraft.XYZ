# LexiSurvey • 字塊勘測 (Master Specification)

**Version:** 7.1 (Final)  
**Date:** 2025-12-03  
**Status:** Ready for Development  
**Module ID:** MOD_SURVEY_V1

---

## Table of Contents

1. [Product Definition](#1-product-definition)
2. [Algorithmic Core](#2-algorithmic-core)
3. [Technical Implementation](#3-technical-implementation)
4. [Integration Points](#4-integration-points)
5. [Related Documentation](#5-related-documentation)
6. [Engine Implementation](#6-engine-implementation)

---

## 1. Product Definition (The "What")

### 1.1 Core Philosophy

**LexiSurvey is not a "test"; it is a Block Survey of the user's semantic territory.**

- **Goal**: To establish the user's **Current State (Locus)** and **Asset Horizon (Reach)** within the 8,000-block Vector Space.
- **Method**: Rough Estimation (粗算). It trades granular precision for speed (< 3 minutes) to generate a "Confidence Interval" of ownership.
- **Measurement**: Checks **Recognition** (Passive/Illiquid Assets) via Definitions. It does not check active usage (that is reserved for the future LexiMine module).

### 1.2 The User Journey

#### Phase 0: Pre-Survey Calibration (Optional)

**Goal**: Avoid "Cold Start Shock" by setting an appropriate `start_rank`.

**Interaction**: A functional configuration modal.

**User Choice:**
- **"Skip"** (Default): Starts at Rank 2,000 (Market Median).
- **"Configure"**: User selects an International Proficiency Level (CEFR).

**Mapping Logic:**
- **A1-A2** (Beginner): Start Beam @ Rank 1,000.
- **B1-B2** (Intermediate): Start Beam @ Rank 3,500.
- **C1-C2** (Advanced): Start Beam @ Rank 5,500.

#### Phase 1: The Survey (Triangulation)

**Goal**: Locate the user's "Signal" in the Vector Space.

**Visual**: Minimalist. Pure data collection. Focus on text and options.

**Input**: 6-Option Multi-Select (Variable Correct Answers: 1-5).

**Feedback**: Progress bar only. No immediate "Correct/Wrong" animations to maintain flow.

#### Phase 2: The Result Dashboard (The Asset Report)

**Goal**: Visualize the "State" and motivate action.

**Visual**: "The Heatmap" overlaying the 8,000 blocks.
- **Solid Zone (Green)**: Owned Assets.
- **Fading Zone (Yellow)**: The "Rough Estimate" Frontier.
- **Dark Zone (Grey)**: Unexplored.

**Benchmarking**: Explicitly marks Taiwan Exam Checkpoints:
- **CAP** @ Rank 1,200
- **GSAT** @ Rank 4,500

---

## 2. Algorithmic Core (The "How")

### 2.1 The 15-Question Protocol

We use a **Three-Phase Funnel** to spend the "Question Budget" (Target: 15, Max: 20).

#### Phase 1: Coarse Sweep (Q1–Q5)
- **Aggressive Binary Search** (±1,500 steps) to find the broad sector.
- **Purpose**: Quickly identify the general vocabulary range.

#### Phase 2: Fine Tuning (Q6–Q12)
- **Oscillating Search** (±200 steps) to define the "Horizon" (Drop-off point).
- **Purpose**: Refine the boundary where user knowledge drops off.

#### Phase 3: Verification (Q13–Q15)
- **The "Double-Check Protocol"**.
- **Trigger**: If user made a massive Rank Jump (> 1,500) in Phase 1.
- **Action**: Serve a "Pivot Question" (different word, same Rank) to confirm it wasn't a lucky guess.

### 2.2 The Scoring Model (Tri-Metric Report)

We do not output a single score. We generate a **Financial Asset Report**:

| Metric | English Label | Chinese Label | Definition | User Value |
|--------|--------------|---------------|------------|------------|
| **A. Volume** | Est. Reserves | 資產總量 | Area under the probability curve. | "I own ~2,400 words." (Vanity) |
| **B. Reach** | Horizon | 有效邊界 | Highest Rank where reliability > 50%. | "I can survive Level 4 text." (Capability) |
| **C. Density** | Solidity | 資產密度 | Consistency within the owned zone. | "My foundation is 90% solid." (Quality) |

### 2.3 The "Discriminator" (Fairness Engine)

**Problem**: Synonyms (e.g., Effect vs Affect) can be validly ambiguous if we pick the wrong definition.

**Solution**: Vector_Judge.

**Logic**: When selecting a Trap Definition, calculate `CosineSimilarity(Target, Trap)`.

**Rule**: Only accept Traps where `Similarity < 0.6`. (Ensure the definitions are distinct).

---

## 3. Technical Implementation (The "Build")

### 3.1 Data Architecture (Neo4j)

#### Node Labels

```cypher
:Word (Properties: name, frequency_rank, embedding)
:Sense (Properties: def_zh, usage_ratio, embedding)
```

**Note**: Engine uses abstract `:Block` concept, but current schema implements `:Word` as the concrete subclass. The Schema Adapter Pattern maps `:Block` → `:Word` and `global_rank` → `frequency_rank` in queries. **No database migration needed.**

#### Relationships

```cypher
(:Word)-[:HAS_SENSE {ratio: 0.9}]->(:Sense)
(:Word)-[:CONFUSED_WITH]->(:Word)  # The Adversarial Graph
```

**Note**: `CONFUSED_WITH` relationships need to be created. See Implementation Plan.

#### Cypher Query: Fetching the Challenge Payload

```cypher
// 1. Fetch Target (True Senses)
MATCH (t:Word {name: $target_word})-[:HAS_SENSE]->(s:Sense)
RETURN s.definition_zh as text, true as is_correct, 
       s.usage_ratio as weight, 'target' as type

UNION

// 2. Fetch Validated Traps (Adversarial)
MATCH (t:Word {name: $target_word})-[:CONFUSED_WITH]->(trap:Word)
MATCH (trap)-[:HAS_SENSE]->(ts:Sense)
// Pre-calculated vector distance check should happen in Python 
// or be stored on the relationship
RETURN ts.definition_zh as text, false as is_correct, 
       -1.0 as weight, 'trap' as type
LIMIT 3

UNION

// 3. Fetch Fillers (Random Noise)
MATCH (f:Word) 
WHERE f.frequency_rank >= ($rank - 50) 
  AND f.frequency_rank <= ($rank + 50) 
  AND f.name <> $target_word
WITH f, rand() as r ORDER BY r LIMIT 2
MATCH (f)-[:HAS_SENSE]->(fs:Sense)
RETURN fs.definition_zh as text, false as is_correct, 
       -0.5 as weight, 'filler' as type
LIMIT 2
```

### 3.2 Python Backend (ValuationEngine)

#### Data Models

```python
from pydantic import BaseModel
from typing import List, Optional, Dict

class SurveyState(BaseModel):
    session_id: str
    current_rank: int
    low_bound: int = 1
    high_bound: int = 8000
    history: List[Dict]  # Stores (rank, correct, time_taken)
    phase: int = 1  # 1=Coarse, 2=Fine, 3=Verification
    confidence: float = 0.0
    pivot_triggered: bool = False

class QuestionPayload(BaseModel):
    question_id: str
    word: str
    rank: int
    options: List[Dict]  # 6 options with {id, text, type, is_correct}
    time_limit: int = 12  # Seconds per question suggested

class TriMetricReport(BaseModel):
    volume: int  # Est. Reserves (資產總量)
    reach: int   # Horizon (有效邊界)
    density: float  # Solidity (資產密度) 0.0-1.0
```

#### Core Engine Interface

```python
class ValuationEngine:
    def __init__(self, db_uri: str, db_auth: Tuple[str, str]):
        """Initialize Neo4j Driver and Configuration."""
        
    def process_step(self, state: SurveyState, previous_answer: Optional[AnswerSubmission] = None) -> SurveyResult:
        """
        CORE CONTROLLER:
        1. Grades previous answer (updates History).
        2. Checks if survey is complete (Tri-Metric Report).
        3. Calculates Next Rank (Adaptive Frequency Sweep).
        4. Fetches Question Data (Neo4j).
        """
```

### 3.3 API Contract

#### Endpoint: `POST /api/v1/survey/start`

**Request:**
```json
{
  "cefr_level": "B1"  // Optional: "A1" | "A2" | "B1" | "B2" | "C1" | "C2"
}
```

**Response:**
```json
{
  "session_id": "sess_12345",
  "status": "continue",
  "payload": {
    "question_id": "q_3500",
    "word": "Establish",
    "rank": 3500,
    "options": [
      {"id": "opt_a", "text": "建立", "type": "target", "is_correct": true},
      {"id": "opt_b", "text": "估計", "type": "trap", "is_correct": false},
      {"id": "opt_c", "text": "完成", "type": "target", "is_correct": true},
      {"id": "opt_d", "text": "開始", "type": "filler", "is_correct": false},
      {"id": "opt_e", "text": "結束", "type": "filler", "is_correct": false},
      {"id": "opt_f", "text": "我不知道", "type": "unknown", "is_correct": false}
    ],
    "time_limit": 12
  },
  "debug_info": {
    "current_confidence": 0.0,
    "phase": 1
  }
}
```

#### Endpoint: `POST /api/v1/survey/next`

**Request:**
```json
{
  "session_id": "sess_12345",
  "previous_answer": {
    "question_id": "q_3500",
    "selected_option_ids": ["opt_a", "opt_c"],
    "time_taken": 4.5
  }
}
```

**Response:**
```json
{
  "status": "continue",  // or "complete"
  "payload": {
    "word": "Establish",
    "rank": 3500,
    "options": [...]
  },
  "debug_info": {
    "current_confidence": 0.45,
    "phase": 1
  }
}
```

#### Endpoint: `POST /api/v1/survey/complete` (Final Response)

**Response:**
```json
{
  "status": "complete",
  "session_id": "sess_12345",
  "metrics": {
    "volume_reserves": 2400,
    "reach_horizon": 4200,
    "density_solidity": 0.87
  },
  "asset_report": {
    "owned_zone": {
      "start": 1,
      "end": 2400,
      "confidence": 0.95
    },
    "frontier_zone": {
      "start": 2400,
      "end": 4200,
      "confidence": 0.50
    },
    "unexplored_zone": {
      "start": 4200,
      "end": 8000
    },
    "benchmarks": {
      "cap": {"rank": 1200, "status": "passed"},
      "gsat": {"rank": 4500, "status": "not_reached"}
    }
  }
}
```

---

## 4. Integration Points

### 4.1 With Existing Systems

#### ValuationEngine (`backend/src/valuation_engine.py`)
- **Reuse**: `RankMap` class for rank-to-word lookups
- **Extend**: Create `LexiSurveyEngine` that inherits or wraps `ValuationEngine`
- **Location**: `backend/src/survey/lexisurvey_engine.py`

#### Neo4j Schema
- **Current**: `(:Word)` nodes with `frequency_rank` property
- **Required**: `CONFUSED_WITH` relationships (need to be created)
- **Action**: Build adversary relationship miner (see Implementation Plan)

#### Question Generation (`backend/src/agent.py`)
- **Current**: Generates 4-option single-select questions
- **Required**: 6-option multi-select with Traditional Chinese definitions
- **Action**: Extend or create new question generator for survey format

### 4.2 With User Knowledge State (PostgreSQL)

#### Storage Requirements

```sql
-- Survey Session Tracking
CREATE TABLE survey_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    child_id UUID REFERENCES children(id),
    session_id TEXT UNIQUE NOT NULL,
    cefr_level TEXT,
    start_rank INTEGER,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Survey Results
CREATE TABLE survey_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id TEXT REFERENCES survey_sessions(session_id),
    volume INTEGER,
    reach INTEGER,
    density FLOAT,
    asset_report JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Survey Question History
CREATE TABLE survey_answers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id TEXT REFERENCES survey_sessions(session_id),
    question_id TEXT,
    word TEXT,
    rank INTEGER,
    selected_options TEXT[],
    correct_options TEXT[],
    is_correct BOOLEAN,
    time_taken FLOAT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### 4.3 With Frontend

#### Components Required
1. **CEFR Calibration Modal** (`components/survey/CEFRModal.tsx`)
2. **Survey Interface** (`components/survey/SurveyInterface.tsx`)
3. **Results Dashboard** (`components/survey/ResultsDashboard.tsx`)
4. **Heatmap Visualization** (`components/survey/VocabularyHeatmap.tsx`)

---

## 5. Related Documentation

### Core Feature Docs
- [`05-mcq-verification-strategy.md`](./05-mcq-verification-strategy.md) - MCQ format and statistical analysis
- [`06-spaced-repetition-strategy.md`](./06-spaced-repetition-strategy.md) - Verification scheduling (different from survey)

### Technical Docs
- [`04-technical-architecture.md`](./04-technical-architecture.md) - System architecture overview
- [`development/LEARNING_POINT_CLOUD_CONSTRUCTION_PLAN.md`](./development/LEARNING_POINT_CLOUD_CONSTRUCTION_PLAN.md) - Neo4j schema details

### Implementation
- [`development/LEXISURVEY_IMPLEMENTATION_PLAN.md`](./development/LEXISURVEY_IMPLEMENTATION_PLAN.md) - Detailed implementation steps
- [`development/LEXISURVEY_ENGINE_INTEGRATION.md`](./development/LEXISURVEY_ENGINE_INTEGRATION.md) - Engine integration guide

---

## 6. Engine Implementation

### 6.1 Provided Engine

The LexiSurvey feature uses a pre-built `ValuationEngine` (Version 7.1) that implements:

- **3-Phase Funnel Algorithm**: Adaptive binary search with phase-specific step sizes
- **Tri-Metric Calculation**: Volume, Reach, and Density metrics
- **Discriminator Logic**: Cosine similarity validation for trap options
- **Multi-Select Questions**: 6-option format with variable correct answers

**Engine Location**: See [`development/LEXISURVEY_ENGINE_INTEGRATION.md`](./development/LEXISURVEY_ENGINE_INTEGRATION.md)

### 6.2 Schema Compatibility

**Key Decision**: `:Word` is defined as a concrete subclass of the abstract `:Block` concept.

The engine uses abstract concepts:
- `:Block` (abstract) → `:Word` (concrete implementation)
- `global_rank` (abstract) → `frequency_rank` (concrete property)

**Integration Strategy**: **Schema Adapter Pattern** - All queries use adapter to alias abstract concepts to concrete schema. No database migration needed or recommended.

Additional requirements:
- `:CONFUSED_WITH` relationships (need to be created)
- `embedding` properties (optional, can be generated on-the-fly)

See integration guide for adapter implementation details.

---

## 7. Success Criteria

### Functional Requirements
- [ ] Survey completes in < 3 minutes (15 questions, 12s each = 3min)
- [ ] CEFR calibration sets appropriate start rank
- [ ] 3-phase funnel correctly identifies vocabulary range
- [ ] Tri-metric report accurately reflects user knowledge
- [ ] Heatmap visualization displays owned/frontier/unexplored zones

### Technical Requirements
- [ ] API endpoints respond in < 200ms
- [ ] Question generation uses validated traps (similarity < 0.6)
- [ ] Survey state persists across sessions
- [ ] Results stored in PostgreSQL for analytics

### User Experience
- [ ] Minimalist interface (no distractions)
- [ ] Progress bar shows completion status
- [ ] Results dashboard motivates continued learning
- [ ] Taiwan exam benchmarks clearly marked

---

**Next Steps**: See [`development/LEXISURVEY_IMPLEMENTATION_PLAN.md`](./development/LEXISURVEY_IMPLEMENTATION_PLAN.md) for detailed implementation roadmap.

