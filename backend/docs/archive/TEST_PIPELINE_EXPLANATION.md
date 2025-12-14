# LexiSurvey Test Pipeline Explanation

## Overview

The test pipeline is a **3-stage verification system** that ensures the complete LexiSurvey integration works correctly from frontend → backend → database.

```
┌─────────────────────────────────────────────────────────────┐
│                    TEST PIPELINE                            │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
        ┌─────────────────────────────────────┐
        │  Stage 1: CONFUSED_WITH Verification│
        │  (Neo4j Relationship Check)           │
        └─────────────────────────────────────┘
                              │
                              ▼
        ┌─────────────────────────────────────┐
        │  Stage 2: Integration Tests          │
        │  (Frontend → Backend → Database)     │
        └─────────────────────────────────────┘
                              │
                              ▼
        ┌─────────────────────────────────────┐
        │  Stage 3: CONFUSED_WITH Usage Tests  │
        │  (Relationship Usage Verification)   │
        └─────────────────────────────────────┘
                              │
                              ▼
                    ✅ All Tests Pass
```

## Pipeline Execution Flow

### Entry Point: `run_integration_tests.sh`

The pipeline starts with a bash script that orchestrates all tests:

```bash
./run_integration_tests.sh
```

**What it does:**
1. ✅ Validates environment (checks for `requirements.txt`)
2. ✅ Activates virtual environment (if exists)
3. ✅ Installs test dependencies (`pytest`, `httpx`)
4. ✅ Runs all 3 test stages sequentially
5. ✅ Stops on first failure (`set -e`)
6. ✅ Provides colored output (green ✅ / red ❌)

---

## Stage 1: CONFUSED_WITH Verification

**Script**: `scripts/verify_confused_with.py`

**Purpose**: Verify that Neo4j has the required CONFUSED_WITH relationships for trap generation.

### What It Checks:

```
1. Connection Test
   └─> Can we connect to Neo4j? ✅

2. Relationship Count
   └─> How many CONFUSED_WITH relationships exist?
       Expected: > 0
       
3. Relationship Properties
   └─> Do relationships have required properties?
       - reason (Look-alike, Sound-alike, Semantic)
       - distance (Levenshtein distance)
       - source (adversary_builder_v7.1)
       
4. Sample Relationships
   └─> Display 10 sample relationships for inspection
   
5. Top Words
   └─> Which words have the most CONFUSED_WITH relationships?
   
6. Common Words Coverage
   └─> Do common words (rank < 2000) have relationships?
```

### Example Output:
```
==========================================
CONFUSED_WITH Relationships Verification
==========================================
✅ Connected to Neo4j

📊 Total CONFUSED_WITH relationships: 1234

📈 Relationships by reason:
   - Look-alike: 456
   - Sound-alike: 234
   - Semantic: 544

📋 Sample relationships:
   establish -[:CONFUSED_WITH {reason: 'Look-alike', distance: 2}]-> estimate
   ...

✅ Verification complete!
```

### Why This Stage Matters:
- **Without CONFUSED_WITH relationships**, the survey can't generate trap options
- **Trap options** are crucial for question quality
- **Early detection** prevents integration test failures later

---

## Stage 2: Integration Tests

**File**: `tests/test_survey_integration.py`

**Purpose**: Test the complete flow from API request → database persistence.

### Test Flow Diagram:

```
┌─────────────────────────────────────────────────────────────┐
│                    Integration Test Flow                     │
└─────────────────────────────────────────────────────────────┘

Test 1: test_start_survey_creates_session
───────────────────────────────────────────
Frontend Request
    │
    ▼
POST /api/v1/survey/start
    │
    ├─> Backend creates SurveyState
    ├─> Engine generates first question
    └─> Database writes:
        ├─> survey_sessions (new session)
        ├─> survey_history (empty history)
        └─> survey_questions (first question)
    │
    ▼
Verify:
✅ Response has session_id
✅ Session exists in PostgreSQL
✅ History record created
✅ Question stored correctly


Test 2: test_submit_answer_updates_session
────────────────────────────────────────────
Frontend Request
    │
    ▼
POST /api/v1/survey/next?session_id=...
    │
    ├─> Backend loads session from DB
    ├─> Engine grades answer
    ├─> Engine calculates next rank
    └─> Database updates:
        ├─> survey_sessions (current_rank, status)
        ├─> survey_history (append new answer)
        └─> survey_questions (store next question)
    │
    ▼
Verify:
✅ Session state updated
✅ History contains answer
✅ Next question generated


Test 3: test_survey_completes_after_minimum_questions
─────────────────────────────────────────────────────
Frontend Requests (15+ times)
    │
    ▼
Loop: POST /api/v1/survey/next
    │
    ├─> Each answer updates state
    ├─> After 15 questions: completion check
    └─> Engine calculates metrics:
        ├─> Volume (Est. Reserves)
        ├─> Reach (Horizon)
        └─> Density (Solidity)
    │
    ▼
Database writes:
    ├─> survey_results (final metrics)
    └─> survey_sessions (status = 'completed')
    │
    ▼
Verify:
✅ Survey completes after minimum questions
✅ Metrics calculated correctly
✅ Results saved to database
✅ Session status = 'completed'


Test 4: test_session_persistence_across_requests
─────────────────────────────────────────────────
Request 1: Start survey
    │
    └─> Creates session_id: "abc-123"
    │
Request 2: Submit answer (uses session_id)
    │
    └─> Backend loads session from DB
    └─> Updates history
    │
Request 3: Submit another answer
    │
    └─> Backend loads session again
    └─> History should contain BOTH answers
    │
    ▼
Verify:
✅ Session persists across requests
✅ History accumulates correctly
✅ State is maintained
```

### Test Infrastructure:

**Fixtures** (provided by pytest):
```python
@pytest.fixture
def client():
    """FastAPI TestClient - simulates HTTP requests"""
    return TestClient(app)

@pytest.fixture
def db_conn():
    """PostgreSQL connection for database verification"""
    conn = PostgresConnection()
    yield conn  # Provide connection
    conn.close()  # Cleanup after test
```

**Test Execution**:
- Each test is **independent** (fresh database state)
- Tests use **real database connections** (not mocks)
- Tests verify **actual database records** (not just API responses)

---

## Stage 3: CONFUSED_WITH Usage Tests

**File**: `tests/test_confused_with_relationships.py`

**Purpose**: Verify that CONFUSED_WITH relationships are actually used in question generation.

### What It Tests:

```
Test 1: test_confused_with_relationships_exist
──────────────────────────────────────────────
Query Neo4j:
  MATCH ()-[r:CONFUSED_WITH]->()
  RETURN count(r)
  
Verify: count > 0


Test 2: test_confused_with_has_properties
───────────────────────────────────────────
Query Neo4j:
  MATCH (source)-[r:CONFUSED_WITH]->(target)
  RETURN r.reason, r.distance, r.source
  
Verify:
✅ All relationships have 'reason'
✅ All relationships have 'distance'
✅ All relationships have 'source'
✅ Reason is one of: Look-alike, Sound-alike, Semantic


Test 3: test_confused_with_used_in_question_generation
───────────────────────────────────────────────────────
1. Create test SurveyState
2. Call engine._generate_question_payload()
3. Check generated options:
   └─> Are there trap options? (from CONFUSED_WITH)
   └─> Do options have correct types?
   
Verify:
✅ Question generated successfully
✅ Trap options present (if relationships exist)
✅ All option types present (target, trap, filler, unknown)


Test 4: test_confused_with_bidirectional
─────────────────────────────────────────
Query Neo4j:
  MATCH (w:Word)-[:CONFUSED_WITH]->(other:Word)
  WHERE w.name = "establish"
  RETURN other.name
  
Verify:
✅ Can query outgoing relationships
✅ Relationships are accessible


Test 5: test_confused_with_for_common_words
───────────────────────────────────────────
Query Neo4j:
  MATCH (w:Word)-[:CONFUSED_WITH]->(other:Word)
  WHERE w.frequency_rank < 2000
  RETURN count(DISTINCT w)
  
Verify:
✅ Common words have relationships
✅ High-frequency words are covered
```

### Why This Stage Matters:
- **Validates data quality**: Relationships exist AND are used
- **Catches integration issues**: Even if relationships exist, they might not be used correctly
- **Ensures question quality**: Trap options depend on these relationships

---

## Complete Pipeline Execution

### Example Run:

```bash
$ ./run_integration_tests.sh

==========================================
LexiSurvey Integration Tests
==========================================

Activating virtual environment...
Checking dependencies...

==========================================
1. Testing CONFUSED_WITH Relationships
==========================================
✅ Connected to Neo4j
📊 Total CONFUSED_WITH relationships: 1234
✅ Verification complete!
✅ CONFUSED_WITH verification passed

==========================================
2. Running Integration Tests
==========================================
test_start_survey_creates_session ... PASSED
test_submit_answer_updates_session ... PASSED
test_survey_completes_after_minimum_questions ... PASSED
test_session_persistence_across_requests ... PASSED
✅ Integration tests passed

==========================================
3. Testing CONFUSED_WITH Usage
==========================================
test_confused_with_relationships_exist ... PASSED
test_confused_with_has_properties ... PASSED
test_confused_with_used_in_question_generation ... PASSED
test_confused_with_bidirectional ... PASSED
test_confused_with_for_common_words ... PASSED
✅ CONFUSED_WITH tests passed

==========================================
✅ All tests passed!
==========================================
```

---

## Failure Scenarios

### Stage 1 Fails:
```
❌ CONFUSED_WITH verification failed
   → No relationships found
   → Solution: Run adversary_builder.py
```

### Stage 2 Fails:
```
❌ Integration tests failed
   → Database connection error
   → Solution: Check DATABASE_URL
   
   → Session not found
   → Solution: Check database migrations
   
   → API error
   → Solution: Check backend logs
```

### Stage 3 Fails:
```
❌ CONFUSED_WITH tests failed
   → Relationships exist but not used
   → Solution: Check engine._generate_options()
   
   → Missing properties
   → Solution: Re-run adversary_builder.py
```

---

## Key Design Decisions

### 1. **Sequential Execution**
- Tests run in order (Stage 1 → 2 → 3)
- Early failures stop the pipeline (`set -e`)
- **Why**: Stage 1 must pass for Stage 2 to work

### 2. **Real Database Connections**
- Tests use actual PostgreSQL and Neo4j connections
- No mocks or test databases
- **Why**: Verify real integration, not just code logic

### 3. **Independent Tests**
- Each test is self-contained
- Tests don't depend on each other
- **Why**: Easier debugging, can run tests individually

### 4. **Comprehensive Verification**
- Tests check API responses AND database state
- Tests verify both existence AND usage
- **Why**: Catch integration issues early

---

## Running Individual Stages

You can run stages independently:

```bash
# Stage 1 only
python scripts/verify_confused_with.py

# Stage 2 only
pytest tests/test_survey_integration.py -v

# Stage 3 only
pytest tests/test_confused_with_relationships.py -v

# Specific test
pytest tests/test_survey_integration.py::TestSurveyIntegration::test_start_survey_creates_session -v
```

---

## Integration with CI/CD

The pipeline can be integrated into CI/CD:

```yaml
# GitHub Actions example
- name: Run Integration Tests
  run: |
    cd backend
    ./run_integration_tests.sh
  env:
    DATABASE_URL: ${{ secrets.DATABASE_URL }}
    NEO4J_URI: ${{ secrets.NEO4J_URI }}
    NEO4J_USER: ${{ secrets.NEO4J_USER }}
    NEO4J_PASSWORD: ${{ secrets.NEO4J_PASSWORD }}
```

---

## Summary

The test pipeline is a **3-stage verification system** that:

1. ✅ **Verifies data exists** (CONFUSED_WITH relationships)
2. ✅ **Tests integration** (API → Database flow)
3. ✅ **Validates usage** (Relationships used correctly)

This ensures the complete LexiSurvey system works end-to-end before deployment.


