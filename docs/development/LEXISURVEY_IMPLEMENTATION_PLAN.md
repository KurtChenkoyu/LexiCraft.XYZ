# LexiSurvey Implementation Plan

**Feature**: LexiSurvey • 字塊勘測  
**Status**: Planning Phase  
**Priority**: High (MVP Feature)  
**Estimated Timeline**: 3-4 weeks

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Implementation Phases](#2-implementation-phases)
3. [Technical Tasks](#3-technical-tasks)
4. [Integration Checklist](#4-integration-checklist)
5. [Testing Strategy](#5-testing-strategy)
6. [Dependencies & Blockers](#6-dependencies--blockers)

---

## 0. Engine Integration (Pre-Implementation)

### 0.1 Engine Provided

The LexiSurvey engine (Version 7.1) is **already implemented** and provided. Integration requires:

1. **Schema Mapping**: Adapt engine queries to current Neo4j schema
2. **Missing Relationships**: Create `CONFUSED_WITH` relationships
3. **Optional Enhancements**: Add embeddings and `usage_ratio` properties

**See**: [`LEXISURVEY_ENGINE_INTEGRATION.md`](./LEXISURVEY_ENGINE_INTEGRATION.md) for detailed integration steps.

### 0.2 Modified Implementation Plan

Since the engine is provided, Phase 1 tasks are modified:

**Original Task 1.2**: "Extend ValuationEngine → LexiSurveyEngine"  
**Modified**: "Integrate provided ValuationEngine with schema adapter"

**Original Task 1.3**: "Create PostgreSQL Schema"  
**Unchanged**: Still need to create survey tables

---

## 1. Prerequisites

### 1.1 Database Requirements

#### Neo4j
- [x] `(:Word)` nodes with `frequency_rank` property ✅ (Exists)
- [x] `(:Sense)` nodes with `definition_zh` property ✅ (Exists)
- [x] `[:HAS_SENSE]` relationships ✅ (Exists)
- [ ] `[:CONFUSED_WITH]` relationships ❌ (Need to create)
- [ ] Vector embeddings for similarity checking ⚠️ (Optional, can use Gemini on-the-fly)

#### PostgreSQL
- [x] `users` table ✅ (Exists)
- [x] `children` table ✅ (Exists)
- [ ] `survey_sessions` table ❌ (Need to create)
- [ ] `survey_results` table ❌ (Need to create)
- [ ] `survey_answers` table ❌ (Need to create)

### 1.2 Code Dependencies

- [x] `RankMap` class in `valuation_engine.py` ✅ (Can reuse)
- [x] `Neo4jConnection` class ✅ (Exists)
- [ ] FastAPI setup ⚠️ (Check if exists)
- [ ] Pydantic models for data validation

---

## 2. Implementation Phases

### Phase 1: Backend Foundation (Week 1)

#### Task 1.1: Create CONFUSED_WITH Relationships
**File**: `backend/src/survey/adversary_builder.py`

**Description**: Build adversarial relationships for trap generation.

**Approach**:
1. Use existing `OPPOSITE_TO` and `RELATED_TO` as seed data
2. Use Gemini to identify Taiwan-specific false friends
3. Store as `[:CONFUSED_WITH]` relationships with `reason` property

**Example**:
```python
# Pseudo-code
def build_confused_with_relationships(conn):
    # 1. Get high-frequency words (rank < 2000)
    # 2. For each word, use Gemini to identify common confusions
    # 3. Create CONFUSED_WITH relationships
    # 4. Validate with vector similarity (if embeddings exist)
```

**Dependencies**: Gemini API key, Neo4j connection

**Estimated Time**: 2-3 days

---

#### Task 1.2: Integrate ValuationEngine with Schema Adapter
**File**: `backend/src/survey/lexisurvey_engine.py`

**Description**: Create adapter layer and extend engine for current schema.

**Components**:
1. `SchemaAdapter` class (maps abstract `:Block` → concrete `:Word`, `global_rank` → `frequency_rank`)
2. `LexiSurveyEngine` class that extends `ValuationEngine` (uses adapter, no schema changes)
3. Override `_generate_question_payload` to use adapter pattern
4. Adapt all Cypher queries using adapter (no database migration)

**Key Decision**: `:Word` is a concrete subclass of abstract `:Block` concept. Schema Adapter Pattern is the ONLY approach - no migration needed.

**Key Algorithm**: Engine already implements 3-phase funnel - just need schema mapping.

**Dependencies**: Task 1.1 (CONFUSED_WITH relationships)

**Estimated Time**: 2-3 days

---

#### Task 1.3: Create PostgreSQL Schema
**File**: `backend/migrations/002_survey_schema.sql`

**Description**: Add survey-related tables to PostgreSQL.

**Tables**:
- `survey_sessions`
- `survey_results`
- `survey_answers`

**Dependencies**: PostgreSQL connection, migration system

**Estimated Time**: 1 day

---

### Phase 2: API Layer (Week 2)

#### Task 2.1: FastAPI Endpoints
**File**: `backend/src/api/survey.py`

**Endpoints**:
1. `POST /api/v1/survey/start` - Initialize survey session
2. `POST /api/v1/survey/next` - Get next question / submit answer
3. `GET /api/v1/survey/{session_id}/status` - Get current status
4. `GET /api/v1/survey/{session_id}/results` - Get final results

**Dependencies**: Phase 1 tasks complete

**Estimated Time**: 2-3 days

---

#### Task 2.2: Session Management
**File**: `backend/src/survey/session_manager.py`

**Description**: Handle survey state persistence.

**Options**:
- **Option A**: Redis (fast, ephemeral)
- **Option B**: PostgreSQL (persistent, slower)
- **Option C**: In-memory (development only)

**Recommendation**: Start with PostgreSQL, migrate to Redis if needed.

**Estimated Time**: 1-2 days

---

### Phase 3: Frontend (Week 3)

#### Task 3.1: CEFR Calibration Modal
**File**: `landing-page/components/survey/CEFRModal.tsx`

**Features**:
- Radio buttons for CEFR levels (A1-C2)
- "Skip" button (defaults to Rank 2000)
- Sends selection to `/api/v1/survey/start`

**Estimated Time**: 1 day

---

#### Task 3.2: Survey Interface
**File**: `landing-page/components/survey/SurveyInterface.tsx`

**Features**:
- Minimalist design (text + checkboxes)
- 6-option multi-select
- Progress bar (no immediate feedback)
- 12-second timer per question
- Calls `/api/v1/survey/next` on submit

**Estimated Time**: 2-3 days

---

#### Task 3.3: Results Dashboard
**File**: `landing-page/components/survey/ResultsDashboard.tsx`

**Features**:
- Tri-metric display (Volume, Reach, Density)
- Heatmap visualization (8,000 blocks)
- Taiwan exam benchmarks (CAP @ 1200, GSAT @ 4500)
- Color coding: Green (owned), Yellow (frontier), Grey (unexplored)

**Dependencies**: Heatmap library (e.g., D3.js, Recharts)

**Estimated Time**: 3-4 days

---

### Phase 4: Testing & Polish (Week 4)

#### Task 4.1: Unit Tests
**Files**: `backend/tests/test_lexisurvey_engine.py`

**Coverage**:
- 3-phase funnel algorithm
- Tri-metric calculations
- Question generation logic
- Schema adapter functionality

**Estimated Time**: 2 days

---

#### Task 4.2: Integration Tests
**Files**: `backend/tests/test_survey_api.py`

**Coverage**:
- End-to-end survey flow
- Session persistence
- Results accuracy

**Estimated Time**: 2 days

---

#### Task 4.3: Performance Optimization
**Tasks**:
- Query optimization (Neo4j)
- Caching (question generation)
- API response time (< 200ms)

**Estimated Time**: 1-2 days

---

## 3. Technical Tasks

### 3.1 Question Generation Matrix

**Current State**: Engine already implements 6-option multi-select generation.

**Required**: Use Schema Adapter Pattern to map abstract `:Block` → concrete `:Word` in queries. No schema changes needed.

**Implementation**: See `LEXISURVEY_ENGINE_INTEGRATION.md` Section 3.

**Dependencies**: CONFUSED_WITH relationships, Neo4j query optimization

---

### 3.2 Vector Similarity Validation

**Problem**: Need to ensure trap definitions are distinct from target.

**Options**:
1. **On-the-fly**: Use Gemini to generate embeddings and calculate similarity
2. **Pre-computed**: Store embeddings in Neo4j, calculate during generation
3. **Skip**: Use heuristic (e.g., different word families)

**Recommendation**: Start with Option 3 (heuristic), add Option 1 if needed.

---

### 3.3 Tri-Metric Calculation

**Volume (Est. Reserves)**:
- Area under probability curve
- Sum of confidence-weighted word counts

**Reach (Horizon)**:
- Highest rank where reliability > 50%
- Last correct answer in fine-tuning phase

**Density (Solidity)**:
- Consistency within owned zone
- Ratio of correct answers in low-bound range

**Implementation**: Engine already implements this. See `_calculate_final_metrics` method.

---

## 4. Integration Checklist

### Backend
- [ ] Create `backend/src/survey/` directory
- [ ] Implement `adversary_builder.py`
- [ ] Implement `schema_adapter.py`
- [ ] Implement `lexisurvey_engine.py`
- [ ] Implement `session_manager.py`
- [ ] Create API endpoints in `backend/src/api/survey.py`
- [ ] Add PostgreSQL migration `002_survey_schema.sql`
- [ ] Add unit tests
- [ ] Add integration tests

### Frontend
- [ ] Create `landing-page/components/survey/` directory
- [ ] Implement `CEFRModal.tsx`
- [ ] Implement `SurveyInterface.tsx`
- [ ] Implement `ResultsDashboard.tsx`
- [ ] Implement `VocabularyHeatmap.tsx`
- [ ] Add survey route/page
- [ ] Add API client functions

### Documentation
- [x] Create `docs/17-lexisurvey-specification.md` ✅
- [x] Create `docs/development/LEXISURVEY_ENGINE_INTEGRATION.md` ✅
- [x] Create `docs/development/LEXISURVEY_IMPLEMENTATION_PLAN.md` ✅
- [ ] Update `README.md` to reference LexiSurvey
- [ ] Update `docs/03-implementation-roadmap.md` to include LexiSurvey

---

## 5. Testing Strategy

### 5.1 Unit Tests

**LexiSurveyEngine**:
- Test 3-phase funnel algorithm with mock data
- Test question generation (6 options, correct distribution)
- Test tri-metric calculations
- Test schema adapter functionality

**MetricsCalculator**:
- Test Volume calculation
- Test Reach calculation
- Test Density calculation

### 5.2 Integration Tests

**Survey Flow**:
1. Start survey with CEFR calibration
2. Complete 15 questions
3. Verify results accuracy
4. Check session persistence

**API Endpoints**:
- Test `/start` endpoint
- Test `/next` endpoint (all phases)
- Test error handling

### 5.3 User Acceptance Testing

**Scenarios**:
1. Beginner user (A1-A2) completes survey
2. Intermediate user (B1-B2) completes survey
3. Advanced user (C1-C2) completes survey
4. User skips CEFR calibration
5. User completes survey in < 3 minutes

---

## 6. Dependencies & Blockers

### Critical Dependencies

1. **CONFUSED_WITH Relationships**
   - **Blocker**: Cannot generate high-quality traps without these
   - **Workaround**: Use `RELATED_TO` as proxy (less accurate)
   - **Solution**: Build relationship miner (Task 1.1)

2. **Vector Embeddings**
   - **Blocker**: Trap validation requires similarity checking
   - **Workaround**: Use heuristic (different word families)
   - **Solution**: Use Gemini on-the-fly or pre-compute

3. **FastAPI Setup**
   - **Blocker**: Need to verify if FastAPI exists
   - **Solution**: Check `backend/src/api/` or create new

### Non-Critical Dependencies

1. **Heatmap Visualization Library**
   - Can use D3.js, Recharts, or custom SVG
   - Not a blocker, can use simple bar chart initially

2. **Session Storage**
   - Can start with PostgreSQL, migrate to Redis later
   - Not a blocker

---

## 7. Risk Mitigation

### Risk 1: Question Generation Too Slow
**Mitigation**: Cache question generation, pre-generate for common ranks

### Risk 2: Tri-Metric Calculations Inaccurate
**Mitigation**: Validate against known vocabulary sizes, adjust formulas

### Risk 3: Survey Takes Too Long (> 3 minutes)
**Mitigation**: Optimize API response times, reduce question count if needed

---

## 8. Success Metrics

### Technical Metrics
- Survey completion time: < 3 minutes ✅
- API response time: < 200ms ✅
- Question generation: < 100ms ✅

### User Experience Metrics
- Survey completion rate: > 80%
- User satisfaction: > 4/5 stars
- Results accuracy: Validated against known vocabulary sizes

---

## 9. Next Steps

1. **Review and approve this plan** with team
2. **Set up development environment**
3. **Begin Phase 1: Backend Foundation**
   - Start with Task 1.1 (CONFUSED_WITH relationships)
   - Then Task 1.2 (Schema adapter and engine integration)
   - Finally Task 1.3 (PostgreSQL schema)

---

**Related Documentation**:
- [`17-lexisurvey-specification.md`](../17-lexisurvey-specification.md) - Full feature specification
- [`LEXISURVEY_ENGINE_INTEGRATION.md`](./LEXISURVEY_ENGINE_INTEGRATION.md) - Engine integration guide

