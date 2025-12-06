# Next Steps: Schema Integration (Task 3)

**Status**: 🟡 Partially Complete  
**Priority**: High (Required to complete Phase 1)  
**Estimated Time**: 1-2 hours

---

## Current Status

### ✅ Completed (Tasks 1 & 2)
- **Neo4j Setup**: Complete with all CRUD operations
- **PostgreSQL Setup**: Complete with all 8 tables and CRUD operations
- **Pydantic Models**: Created for both databases
- **Database Connections**: Working for both Neo4j and PostgreSQL
- **Documentation**: Technical architecture updated

### ⚠️ Missing (Task 3)
- **Unified Relationship Discovery Service**: Needs to be created
- **Integration Tests**: Need to be written
- **Schema Decisions Documentation**: Needs to be created

---

## What Needs to Be Done

### 1. Create Unified Relationship Discovery Service

**File**: `backend/src/services/relationship_discovery.py`

**Purpose**: Integrate Neo4j relationship queries with PostgreSQL relationship discovery tracking

**Requirements**:
- Query Neo4j for relationships when a child learns a new word
- Get child's known learning points from PostgreSQL
- Discover relationships between new word and known words
- Create relationship discovery entries in PostgreSQL
- Award bonus points for discoveries

**Reference**: See `docs/development/handoffs/HANDOFF_PHASE1_DATABASE_NEO4J.md` Task 6

### 2. Write Integration Tests

**Files**: `backend/tests/test_integration_*.py`

**Requirements**:
- Test full flow: create child → learn word → discover relationships → award bonuses
- Test relationship discovery service end-to-end
- Test points calculation with relationship bonuses
- Test verification scheduling
- Target: >80% coverage

### 3. Document Schema Decisions

**File**: `backend/docs/SCHEMA_DECISIONS.md` (or similar)

**Requirements**:
- Document why hybrid approach (Neo4j + PostgreSQL)
- Document schema alignment decisions
- Document relationship discovery flow
- Document any trade-offs or limitations

---

## Implementation Prompt

Use this prompt to complete Task 3:

```
You are completing Phase 1 - Schema Integration for the LexiCraft MVP.

CONTEXT:
- Neo4j setup is complete (backend/src/database/neo4j_*)
- PostgreSQL setup is complete (backend/src/database/postgres_*)
- Both databases have CRUD operations working
- Pydantic models exist for both databases

TASKS:
1. Create unified relationship discovery service:
   - File: backend/src/services/relationship_discovery.py
   - Function: discover_relationships_for_child(child_id, learning_point_id)
   - Should:
     * Get child's known learning points from PostgreSQL (learning_progress table)
     * Query Neo4j for relationships between new word and known words
     * Create relationship_discoveries entries in PostgreSQL
     * Return discovered relationships
   - Use existing CRUD functions from both databases

2. Write integration tests:
   - Test relationship discovery service end-to-end
   - Test full user flow (create parent → create child → learn word → discover relationships)
   - Test points calculation with relationship bonuses
   - Target: >80% coverage

3. Document schema decisions:
   - Why hybrid approach (Neo4j + PostgreSQL)
   - How schemas align (learning_point_id references)
   - Relationship discovery flow
   - Any trade-offs or limitations

READ:
- docs/development/handoffs/HANDOFF_PHASE1_DATABASE_NEO4J.md (Task 6)
- backend/src/database/neo4j_crud/relationships.py (discover_relationships function)
- backend/src/database/postgres_crud/progress.py (get_user_known_components function)
- backend/src/database/postgres_crud/relationships.py (create_relationship_discovery function)

SUCCESS CRITERIA:
- [ ] Relationship discovery service created and working
- [ ] Integration tests written and passing (>80% coverage)
- [ ] Schema decisions documented
- [ ] All code follows existing patterns and style

REPORT BACK:
- Completion report with files created
- Test results and coverage
- Schema decisions documented
```

---

## Files That Should Be Created

```
backend/
├── src/
│   └── services/
│       ├── __init__.py
│       └── relationship_discovery.py  ← NEW
├── tests/
│   ├── test_integration_relationship_discovery.py  ← NEW
│   └── test_integration_full_flow.py  ← NEW
└── docs/
    └── SCHEMA_DECISIONS.md  ← NEW
```

---

## Dependencies

**Uses**:
- `backend/src/database/neo4j_crud/relationships.py` - `discover_relationships()`
- `backend/src/database/postgres_crud/progress.py` - `get_user_known_components()`
- `backend/src/database/postgres_crud/relationships.py` - `create_relationship_discovery()`
- `backend/src/database/postgres_crud/points.py` - Points transaction functions

**Enables**:
- Phase 2: Learning Interface (can use relationship discovery)
- Phase 2: Points System (can award relationship bonuses)
- Phase 2: MCQ System (can use relationship data)

---

## After Completion

Once Task 3 is complete:
1. ✅ Update `SCHEMA_COORDINATION_STATUS.md` to mark Task 3 complete
2. ✅ Create final completion report for Master Planning Chat
3. ✅ Mark Phase 1 - Database Schema as complete
4. ✅ Ready for Phase 2 development

---

**Last Updated**: January 2025  
**Status**: Ready for Implementation


