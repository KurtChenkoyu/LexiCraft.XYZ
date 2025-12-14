# LexiSurvey Integration Testing Guide

This guide covers testing the complete LexiSurvey integration flow: frontend → backend → database.

## Overview

The integration tests verify:
1. **Frontend → Backend Flow**: API endpoints receive requests correctly
2. **Backend → Database Flow**: Survey sessions persist in PostgreSQL
3. **Neo4j Relationships**: CONFUSED_WITH relationships exist and are used
4. **End-to-End Flow**: Complete survey flow from start to completion

## Test Files

### 1. `tests/test_survey_integration.py`
Comprehensive integration tests for the survey flow:
- `test_start_survey_creates_session`: Verifies survey start creates DB session
- `test_submit_answer_updates_session`: Verifies answer submission updates state
- `test_survey_completes_after_minimum_questions`: Verifies completion flow
- `test_session_persistence_across_requests`: Verifies state persistence

### 2. `tests/test_confused_with_relationships.py`
Tests for Neo4j CONFUSED_WITH relationships:
- `test_confused_with_relationships_exist`: Verifies relationships exist
- `test_confused_with_has_properties`: Verifies relationship properties
- `test_confused_with_used_in_question_generation`: Verifies usage in questions
- `test_confused_with_bidirectional`: Verifies bidirectional queries
- `test_confused_with_for_common_words`: Verifies common words have relationships

### 3. `scripts/verify_confused_with.py`
Standalone verification script for CONFUSED_WITH relationships.

## Running Tests

### Prerequisites

1. **Environment Variables**: Set up `.env` file with:
   ```bash
   DATABASE_URL=postgresql://...
   NEO4J_URI=neo4j+s://...
   NEO4J_USER=neo4j
   NEO4J_PASSWORD=...
   ```

2. **Dependencies**: Install test dependencies:
   ```bash
   pip install pytest pytest-asyncio httpx
   ```

### Run All Tests

```bash
cd backend
./run_integration_tests.sh
```

This script runs:
1. CONFUSED_WITH relationship verification
2. Integration tests
3. CONFUSED_WITH usage tests

### Run Individual Test Suites

```bash
# Integration tests only
pytest tests/test_survey_integration.py -v

# CONFUSED_WITH tests only
pytest tests/test_confused_with_relationships.py -v

# Verify relationships script
python scripts/verify_confused_with.py
```

### Run Specific Tests

```bash
# Run a specific test
pytest tests/test_survey_integration.py::TestSurveyIntegration::test_start_survey_creates_session -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html
```

## Test Coverage

### Survey Integration Tests

✅ **Session Creation**
- Verifies POST `/api/v1/survey/start` creates session
- Verifies session stored in `survey_sessions` table
- Verifies history record created in `survey_history` table
- Verifies question stored in `survey_questions` table

✅ **Answer Submission**
- Verifies POST `/api/v1/survey/next` updates session
- Verifies history updated with answer
- Verifies session state persisted correctly

✅ **Survey Completion**
- Verifies survey completes after minimum questions
- Verifies metrics calculated correctly
- Verifies results saved to `survey_results` table
- Verifies session status updated to "completed"

✅ **State Persistence**
- Verifies session state persists across requests
- Verifies history accumulates correctly
- Verifies multiple answers stored in sequence

### CONFUSED_WITH Relationship Tests

✅ **Relationship Existence**
- Verifies relationships exist in Neo4j
- Verifies relationships have required properties (reason, distance, source)
- Verifies properties have correct types and values

✅ **Relationship Usage**
- Verifies relationships used in question generation
- Verifies trap options generated from CONFUSED_WITH
- Verifies bidirectional queries work

✅ **Data Quality**
- Verifies common words (rank < 2000) have relationships
- Verifies relationship properties are complete
- Verifies relationships are properly structured

## Expected Test Results

### Successful Test Run

```
==========================================
LexiSurvey Integration Tests
==========================================

==========================================
1. Testing CONFUSED_WITH Relationships
==========================================
✅ Connected to Neo4j
📊 Total CONFUSED_WITH relationships: 1234
✅ Verification complete!

==========================================
2. Running Integration Tests
==========================================
test_start_survey_creates_session ... PASSED
test_submit_answer_updates_session ... PASSED
test_survey_completes_after_minimum_questions ... PASSED
test_session_persistence_across_requests ... PASSED

==========================================
3. Testing CONFUSED_WITH Usage
==========================================
test_confused_with_relationships_exist ... PASSED
test_confused_with_has_properties ... PASSED
test_confused_with_used_in_question_generation ... PASSED
test_confused_with_bidirectional ... PASSED
test_confused_with_for_common_words ... PASSED

✅ All tests passed!
```

## Troubleshooting

### Database Connection Errors

**Error**: `Failed to connect to PostgreSQL`
- Verify `DATABASE_URL` is correct
- Check database is accessible
- Verify connection pooling settings

**Error**: `Failed to connect to Neo4j`
- Verify `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD` are correct
- Check Neo4j instance is running
- Verify network connectivity

### Missing CONFUSED_WITH Relationships

**Warning**: `No CONFUSED_WITH relationships found`
- Run `adversary_builder.py` to create relationships:
  ```bash
  python -m src.survey.adversary_builder --max-rank 4000
  ```
- Wait for relationships to be created
- Re-run verification script

### Test Failures

**Error**: `Session not found`
- Verify database migrations are applied
- Check `survey_sessions` table exists
- Verify UUID format is correct

**Error**: `No target options found`
- Verify Neo4j has word data
- Check word has Chinese definitions
- Verify word has senses with `definition_zh`

## Manual Testing

### Test Survey Flow Manually

1. **Start Survey**:
   ```bash
   curl -X POST http://localhost:8000/api/v1/survey/start \
     -H "Content-Type: application/json" \
     -d '{"cefr_level": "B1"}'
   ```

2. **Submit Answer**:
   ```bash
   curl -X POST "http://localhost:8000/api/v1/survey/next?session_id=YOUR_SESSION_ID" \
     -H "Content-Type: application/json" \
     -d '{
       "question_id": "q_2000_12345",
       "selected_option_ids": ["target_word_0"],
       "time_taken": 5.0
     }'
   ```

3. **Check Database**:
   ```sql
   SELECT * FROM survey_sessions WHERE id = 'YOUR_SESSION_ID';
   SELECT * FROM survey_history WHERE session_id = 'YOUR_SESSION_ID';
   ```

### Verify CONFUSED_WITH Relationships

```bash
python scripts/verify_confused_with.py
```

Or query Neo4j directly:
```cypher
MATCH (w:Word)-[r:CONFUSED_WITH]->(other:Word)
RETURN w.name, other.name, r.reason, r.distance
LIMIT 10
```

## Next Steps

After passing all tests:

1. **Deploy Backend**: Follow `DEPLOYMENT.md` guide
2. **Update Frontend**: Point frontend to deployed API URL
3. **Monitor**: Check logs and metrics in deployment platform
4. **Verify Production**: Test deployed endpoints

## Continuous Integration

To integrate into CI/CD:

```yaml
# Example GitHub Actions
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


