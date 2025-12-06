# LexiSurvey Engine Integration Guide

**Engine Version**: 7.1  
**Status**: Ready for Integration  
**Date**: 2025-12-03

---

## Table of Contents

1. [Engine Overview](#1-engine-overview)
2. [Schema Mapping](#2-schema-mapping)
3. [Integration Steps](#3-integration-steps)
4. [Required Schema Changes](#4-required-schema-changes)
5. [API Integration](#5-api-integration)
6. [Testing Strategy](#6-testing-strategy)
7. [Migration Checklist](#7-migration-checklist)
8. [Known Issues & Workarounds](#8-known-issues--workarounds)
9. [Performance Considerations](#9-performance-considerations)
10. [Next Steps](#10-next-steps)

---

## 1. Engine Overview

The LexiSurvey ValuationEngine implements:

- **3-Phase Funnel Algorithm**: Coarse sweep (Q1-Q5), Fine tuning (Q6-Q12), Verification (Q13-Q15)
- **Adaptive Binary Search**: ±1500 steps (Phase 1), ±200 steps (Phase 2), ±100 steps (Phase 3)
- **Tri-Metric Calculation**: Volume (Reserves), Reach (Horizon), Density (Solidity)
- **Discriminator Logic**: Cosine similarity validation for trap options (rejects if similarity > 0.6)
- **Multi-Select Questions**: 6-option format with variable correct answers (1-5 targets)

### Key Components

```python
# Core Classes
- ValuationEngine: Main controller
- SurveyState: Session state management
- QuestionPayload: Question data structure
- SurveyResult: API response format
- TriMetricReport: Final results
```

---

## 2. Schema Mapping

### Key Decision: Schema Adapter Pattern (No Migration)

**:Word nodes are defined as a concrete subclass of the abstract :Block concept.**

- **Conceptual Model**: `:Block` is the abstract concept (semantic territory blocks)
- **Implementation**: `:Word` is the concrete Neo4j node label (Core Blocks)
- **Strategy**: Use **Schema Adapter Pattern** to alias `:Block` → `:Word` in all queries
- **No Migration**: Database schema remains unchanged. All mapping happens in Python/Cypher query layer.

### Current Schema → Engine Expected Schema

| Engine Expects | Current Schema | Mapping Strategy |
|----------------|---------------|------------------|
| `:Block` (abstract) | `:Word` (concrete subclass) | **Schema Adapter Pattern** - Alias `:Block` to `:Word` in queries |
| `global_rank` | `frequency_rank` | **Schema Adapter Pattern** - Alias `global_rank` to `frequency_rank` in queries |
| `:CONFUSED_WITH` | ❌ Missing | **Need to create** (see Section 4) |
| `embedding` (on Block) | ❌ Missing | **Need to add** (optional, can use on-the-fly) |
| `embedding` (on Sense) | ❌ Missing | **Need to add** (optional, can use on-the-fly) |
| `usage_ratio` (on Sense) | ❌ Missing | **Need to add** or use default (1.0) |

### Query Mapping Example

**Engine Query:**
```cypher
MATCH (b:Block) 
WHERE b.global_rank >= $min_r AND b.global_rank <= $max_r
```

**Mapped Query (Current Schema):**
```cypher
MATCH (b:Word) 
WHERE b.frequency_rank >= $min_r AND b.frequency_rank <= $max_r
```

**Or with Alias (Recommended):**
```cypher
MATCH (b:Word) 
WHERE b.frequency_rank >= $min_r AND b.frequency_rank <= $max_r
WITH b, b.frequency_rank as global_rank
```

---

## 3. Integration Steps

### Step 1: Schema Adaptation Layer

Create a query adapter that maps engine queries to current schema.

**File**: `backend/src/survey/schema_adapter.py`

```python
class SchemaAdapter:
    """
    Schema Adapter Pattern: Maps abstract :Block concept to concrete :Word implementation.
    
    Key Decision: :Word is a concrete subclass of abstract :Block concept.
    No database migration needed - all mapping happens in query layer.
    
    Maps:
    - :Block (abstract) → :Word (concrete)
    - global_rank (abstract) → frequency_rank (concrete)
    """
    
    @staticmethod
    def adapt_block_query(query: str) -> str:
        """
        Adapts abstract :Block queries to concrete :Word schema.
        Replaces :Block with :Word, global_rank with frequency_rank.
        """
        query = query.replace(":Block", ":Word")
        query = query.replace("global_rank", "frequency_rank")
        return query
    
    @staticmethod
    def adapt_result(record: dict) -> dict:
        """Map result properties to engine-expected format"""
        if 'frequency_rank' in record:
            record['global_rank'] = record['frequency_rank']
        return record
```

### Step 2: Extend ValuationEngine

**File**: `backend/src/survey/lexisurvey_engine.py`

```python
from src.database.neo4j_connection import Neo4jConnection
from src.survey.schema_adapter import SchemaAdapter

class LexiSurveyEngine(ValuationEngine):
    """
    Extended engine that works with current schema.
    """
    
    def __init__(self, conn: Neo4jConnection):
        # Get connection details from Neo4jConnection
        uri = conn.uri
        auth = (conn.user, conn.password)
        super().__init__(uri, auth)
        self.adapter = SchemaAdapter()
        self.conn = conn  # Keep reference for session management
    
    def _generate_question_payload(self, rank: int, phase: int) -> QuestionPayload:
        """
        Override to use current schema and connection.
        """
        with self.conn.get_session() as session:
            # Adapt query for current schema
            query = """
                MATCH (b:Word) 
                WHERE b.frequency_rank >= $min_r AND b.frequency_rank <= $max_r
                WITH b, rand() as r ORDER BY r LIMIT 1
                RETURN b.name as word, b.frequency_rank as global_rank
            """
            
            row = session.run(query, min_r=rank-20, max_r=rank+20).single()
            
            if not row:
                word = "Estimate"
                target_embedding = None
            else:
                word = row["word"]
                target_embedding = None  # Will be generated on-the-fly if needed
            
            # Continue with adapted query for options...
```

### Step 3: Add Missing Properties

See Section 4 for required schema changes.

---

## 4. Required Schema Changes

### 4.1 Add CONFUSED_WITH Relationships

**Priority**: **HIGH** (Required for trap generation)

**File**: `backend/src/survey/adversary_builder.py`

```python
def build_confused_with_relationships(conn: Neo4jConnection):
    """
    Creates CONFUSED_WITH relationships for trap generation.
    
    Strategy:
    1. Use existing OPPOSITE_TO and RELATED_TO as seed
    2. Use Gemini to identify Taiwan-specific false friends
    3. Store with reason property
    """
    with conn.get_session() as session:
        # Option 1: Convert some RELATED_TO to CONFUSED_WITH
        # (Words that are commonly confused, not just related)
        
        # Option 2: Use Gemini to generate confusion pairs
        # For high-frequency words (rank < 2000)
        
        # Example query:
        query = """
        MATCH (w1:Word)-[:RELATED_TO]->(w2:Word)
        WHERE w1.frequency_rank < 2000 AND w2.frequency_rank < 2000
        // Add logic to identify commonly confused pairs
        MERGE (w1)-[:CONFUSED_WITH {reason: "Semantic", source: "WordNet"}]->(w2)
        """
```

**Estimated Time**: 2-3 days

---

### 4.2 Add Embeddings (Optional)

**Priority**: **MEDIUM** (Can use on-the-fly generation)

**Options**:

#### Option A: On-the-Fly Generation (Recommended for MVP)
- Use Gemini API to generate embeddings when needed
- No schema changes required
- Slower but flexible

#### Option B: Pre-compute and Store
- Generate embeddings for all Words and Senses
- Store as `embedding` property (List[float])
- Faster but requires storage space

**Implementation** (Option A):
```python
def _cosine_similarity(self, v1: List[float], v2: List[float]) -> float:
    """
    Calculate cosine similarity.
    If embeddings are None, use heuristic instead.
    """
    if not v1 or not v2:
        # Fallback: Use word frequency difference as proxy
        return 0.3  # Default low similarity
    
    # Real cosine similarity calculation
    dot_product = sum(a * b for a, b in zip(v1, v2))
    norm1 = math.sqrt(sum(a * a for a in v1))
    norm2 = math.sqrt(sum(a * a for a in v2))
    
    if norm1 == 0 or norm2 == 0:
        return 0.0
    
    return dot_product / (norm1 * norm2)
```

---

### 4.3 Add usage_ratio Property (Optional)

**Priority**: **LOW** (Can use default 1.0)

**Current**: Sense nodes don't have `usage_ratio`

**Options**:
1. **Default to 1.0**: All senses equally weighted
2. **Calculate from WordNet**: Use synset frequency
3. **Add during enrichment**: Gemini can estimate usage frequency

**Recommended**: Start with default 1.0, add later if needed.

---

## 5. API Integration

### 5.1 FastAPI Endpoints

**File**: `backend/src/api/survey.py`

```python
from fastapi import APIRouter, HTTPException
from src.survey.lexisurvey_engine import LexiSurveyEngine
from src.database.neo4j_connection import Neo4jConnection
from src.survey.models import SurveyState, AnswerSubmission, SurveyResult

router = APIRouter(prefix="/api/v1/survey", tags=["survey"])

# Initialize engine (singleton pattern recommended)
engine = None

def get_engine():
    global engine
    if engine is None:
        conn = Neo4jConnection()
        engine = LexiSurveyEngine(conn)
    return engine

@router.post("/start")
async def start_survey(cefr_level: Optional[str] = None):
    """
    Initialize survey session.
    """
    # Map CEFR to start rank
    start_rank_map = {
        "A1": 1000, "A2": 1000,
        "B1": 3500, "B2": 3500,
        "C1": 5500, "C2": 5500
    }
    start_rank = start_rank_map.get(cefr_level, 2000)  # Default: Market Median
    
    # Create session
    session_id = f"sess_{uuid.uuid4().hex[:12]}"
    state = SurveyState(
        session_id=session_id,
        current_rank=start_rank
    )
    
    # Store state (Redis or PostgreSQL)
    store_survey_state(state)
    
    # Get first question
    engine = get_engine()
    result = engine.process_step(state)
    
    return result.dict()

@router.post("/next")
async def next_question(
    session_id: str,
    previous_answer: AnswerSubmission
):
    """
    Process answer and get next question.
    """
    # Load state
    state = load_survey_state(session_id)
    if not state:
        raise HTTPException(404, "Session not found")
    
    # Process step
    engine = get_engine()
    result = engine.process_step(state, previous_answer)
    
    # Save updated state
    save_survey_state(state)
    
    return result.dict()
```

---

## 6. Testing Strategy

### 6.1 Unit Tests

**File**: `backend/tests/test_lexisurvey_engine.py`

```python
def test_3_phase_funnel():
    """Test that phases transition correctly"""
    engine = LexiSurveyEngine(mock_conn)
    state = SurveyState(session_id="test", current_rank=2000)
    
    # Phase 1: Q1-Q5
    for i in range(5):
        result = engine.process_step(state)
        assert result.debug_info["phase"] == 1
    
    # Phase 2: Q6-Q12
    for i in range(7):
        result = engine.process_step(state)
        assert result.debug_info["phase"] == 2
    
    # Phase 3: Q13-Q15
    for i in range(3):
        result = engine.process_step(state)
        assert result.debug_info["phase"] == 3

def test_tri_metrics_calculation():
    """Test tri-metric accuracy"""
    engine = LexiSurveyEngine(mock_conn)
    state = SurveyState(session_id="test", current_rank=2000)
    
    # Simulate survey completion
    # ... add mock answers ...
    
    result = engine.process_step(state)
    assert result.status == "complete"
    assert "volume_reserves" in result.metrics
    assert "reach_horizon" in result.metrics
    assert "density_solidity" in result.metrics
```

### 6.2 Integration Tests

**File**: `backend/tests/test_survey_api.py`

```python
def test_survey_flow():
    """Test end-to-end survey flow"""
    # Start survey
    response = client.post("/api/v1/survey/start", json={"cefr_level": "B1"})
    assert response.status_code == 200
    session_id = response.json()["session_id"]
    
    # Complete 15 questions
    for i in range(15):
        # Get question
        response = client.post("/api/v1/survey/next", json={
            "session_id": session_id,
            "previous_answer": {
                "question_id": f"q_{i}",
                "selected_option_ids": ["opt_target_123"],
                "time_taken": 5.0
            }
        })
        assert response.status_code == 200
    
    # Final result
    assert response.json()["status"] == "complete"
    assert "metrics" in response.json()
```

---

## 7. Migration Checklist

### Phase 1: Schema Preparation
- [ ] Create `CONFUSED_WITH` relationships (or use fallback)
- [ ] Add `usage_ratio` property to Sense nodes (or use default)
- [ ] Decide on embedding strategy (on-the-fly vs pre-compute)

### Phase 2: Engine Integration
- [ ] Create `SchemaAdapter` class (aliases `:Block` → `:Word`, `global_rank` → `frequency_rank`)
- [ ] Extend `ValuationEngine` → `LexiSurveyEngine` (uses adapter, no schema changes)
- [ ] Adapt all Cypher queries using adapter pattern (no database migration)
- [ ] Test question generation with real data

### Phase 3: API Layer
- [ ] Create FastAPI endpoints
- [ ] Implement session management (PostgreSQL or Redis)
- [ ] Add error handling
- [ ] Add logging

### Phase 4: Testing
- [ ] Unit tests for engine logic
- [ ] Integration tests for API
- [ ] End-to-end survey flow test
- [ ] Performance testing (< 200ms response time)

---

## 8. Known Issues & Workarounds

### Issue 1: Missing CONFUSED_WITH Relationships
**Workaround**: Use `RELATED_TO` relationships as proxy (less accurate but functional)

### Issue 2: Missing Embeddings
**Workaround**: Use heuristic similarity (word frequency difference) or generate on-the-fly with Gemini

### Issue 3: Missing usage_ratio
**Workaround**: Default all senses to `usage_ratio = 1.0`

### Issue 4: Schema Conceptual Mapping (Block vs Word)
**Solution**: `:Word` is defined as a concrete subclass of the abstract `:Block` concept. Use Schema Adapter Pattern to alias `:Block` → `:Word` in all queries. **No database migration needed or recommended.**

---

## 9. Performance Considerations

### Query Optimization
- Add index on `frequency_rank` if not exists ✅ (Already exists)
- Cache question generation for common ranks
- Use parameterized queries to leverage query plan cache

### Session Management
- **Development**: In-memory (simple)
- **Production**: Redis (fast) or PostgreSQL (persistent)

### Embedding Generation
- **On-the-fly**: ~100-200ms per question (Gemini API)
- **Pre-computed**: ~5-10ms per question (database lookup)
- **Recommendation**: Start with on-the-fly, migrate to pre-computed if needed

---

## 10. Next Steps

1. **Review this integration guide** with team
2. **Create CONFUSED_WITH relationships** (highest priority)
3. **Implement SchemaAdapter** and extend engine
4. **Build API endpoints** with session management
5. **Test with real data** from Neo4j
6. **Deploy and monitor** performance

---

**Related Documentation**:
- [`17-lexisurvey-specification.md`](../17-lexisurvey-specification.md) - Full feature specification
- [`LEXISURVEY_IMPLEMENTATION_PLAN.md`](./LEXISURVEY_IMPLEMENTATION_PLAN.md) - Implementation roadmap

