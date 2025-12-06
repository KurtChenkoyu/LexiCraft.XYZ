# Word Discovery/Selection Flow - Investigation Report

**Date:** 2024  
**Status:** Investigation Complete  
**Purpose:** Document current word selection/discovery mechanisms and identify gaps for Explorer Mode implementation

---

## Executive Summary

This document investigates how users currently discover and select words for verification in LexiCraft. The investigation reveals:

1. **Current State**: Word selection is **manual** - users must provide a `learning_point_id` to start verification
2. **Explorer Mode**: Fully designed but **not yet implemented**
3. **Connection-Building Algorithm**: Fully specified but **not yet implemented**
4. **Word Lookup**: Basic Neo4j lookup exists, but **no API endpoint** exposed
5. **Word Suggestions**: **No suggestion engine exists**

---

## Key Questions Answered

### 1. How do users currently select words to verify?

**Answer:** Users manually provide a `learning_point_id` via the `/api/v1/words/start-verification` endpoint.

**Current Flow:**
```
User → Frontend → POST /api/v1/words/start-verification
  → { learning_point_id: "word_123", tier: 1, initial_difficulty: 0.5 }
  → Backend creates learning_progress entry
  → Backend creates verification_schedule entry
  → User can now take verification tests
```

**Limitations:**
- ❌ No automatic word selection
- ❌ No word suggestions
- ❌ No search functionality exposed via API
- ❌ No connection-based recommendations
- ❌ User must know the `learning_point_id` beforehand

**Files:**
- `backend/src/api/words.py` - Contains the only word-related API endpoint

---

### 2. What word suggestion mechanisms exist?

**Answer:** **None currently implemented.** However, comprehensive designs exist:

#### Designed (Not Implemented):

**A. Connection-Building Scope Algorithm**
- **Location:** `docs/connection-building-scope-algorithm.md`
- **Status:** Fully specified, not implemented
- **Strategy:** 60% connection-based, 40% adaptive level-based
- **Priority Scoring:**
  1. Prerequisites Met (+100 points)
  2. Direct Relationships (+50 each)
  3. Phrase Components (+40)
  4. Morphological Patterns (+30)
  5. 2-Degree Connections (+20 each)

**B. Explorer Mode Suggestions**
- **Location:** `docs/EXPLORER_MODE_IMPLEMENTATION.md`
- **Status:** Fully designed, not implemented
- **Suggestion Types:**
  1. Connection-Based (Primary)
  2. Prerequisite Suggestions (Highest Priority)
  3. Level-Appropriate (From LexiSurvey)
  4. Interest-Based (If specified)
  5. Bridge Words (Connect multiple learned words)

**C. Guided Mode Auto-Selection**
- **Location:** `docs/connection-building-scope-algorithm.md`
- **Status:** Designed, not implemented
- **Behavior:** Algorithm automatically selects words based on curriculum and connections

---

### 3. How does Explorer Mode work?

**Answer:** Explorer Mode is **fully designed but not implemented**. Here's how it's intended to work:

#### Design Overview:

**Core Concept:** Learners build their own vocabulary network with intelligent suggestions from the system.

**Key Features:**
1. **Smart Suggestions System**
   - System provides intelligent suggestions
   - Learner has full freedom to choose
   - Can search any word in database

2. **Suggestion Priority:**
   - Prerequisites Met (Highest)
   - Bridge Words (Discovery bonus available)
   - Connection-Based (High)
   - Interest-Based (High)
   - Level-Appropriate (Medium)

3. **Graph Visualization**
   - Pre-built graph structure (PostgreSQL JSONB)
   - Personalized visualization based on verified words
   - Shows connections between verified words
   - Highlights suggested words

**Planned API Endpoints (Not Implemented):**
- `GET /api/v1/words/explorer/suggestions` - Get word suggestions
- `GET /api/v1/graph/personalized` - Get personalized graph data
- `GET /api/v1/words/search` - Search words
- `POST /api/v1/learning-mode` - Set learning mode (guided/explorer)

**Database Schema (Not Implemented):**
- `learning_points` table with `connections` JSONB field
- `user_learning_mode` table
- `graph_structure` table

**Documentation:**
- `EXPLORER_MODE_START_HERE.md` - Quick start guide
- `docs/EXPLORER_MODE_IMPLEMENTATION.md` - Full implementation guide
- `docs/EXPLORER_MODE_SUMMARY.md` - Summary of decisions

---

### 4. What APIs exist for word discovery?

**Answer:** **Very limited.** Only one word-related API exists:

#### Existing APIs:

**1. POST /api/v1/words/start-verification**
- **File:** `backend/src/api/words.py`
- **Purpose:** Start verification for a word
- **Input:** `learning_point_id` (user must provide)
- **Output:** Creates learning_progress and verification_schedule entries
- **Limitation:** Requires user to know the learning_point_id

#### Missing APIs (Designed but Not Implemented):

**1. GET /api/v1/words/explorer/suggestions**
- **Purpose:** Get intelligent word suggestions for Explorer Mode
- **Status:** Designed in `docs/EXPLORER_MODE_IMPLEMENTATION.md`
- **Expected Response:**
  ```json
  {
    "suggestions": [
      {
        "word_id": "indirect",
        "word": "indirect",
        "source": "direct",
        "relationship": "MORPHOLOGICAL",
        "reason": "Shares pattern with 'direct'",
        "priority": "high",
        "score": 50
      }
    ],
    "search_enabled": true,
    "mode": "explorer",
    "total_available": 5000,
    "learned_count": 15
  }
  ```

**2. GET /api/v1/words/search**
- **Purpose:** Search words by name
- **Status:** Designed but not implemented
- **Expected Query:** `?q={query}&user_id={user_id}`
- **Expected Response:** Word details + connection info if connected to learned words

**3. GET /api/v1/graph/personalized**
- **Purpose:** Get personalized graph data for visualization
- **Status:** Designed but not implemented
- **Expected Response:** Nodes and edges filtered by user's learned words

**4. POST /api/v1/learning-mode**
- **Purpose:** Set user's learning mode (guided/explorer)
- **Status:** Designed but not implemented

#### Backend Services (Not Exposed as APIs):

**1. Neo4j Learning Points CRUD**
- **File:** `backend/src/database/neo4j_crud/learning_points.py`
- **Functions:**
  - `get_learning_point(learning_point_id)` - Get by ID
  - `get_learning_point_by_word(word)` - Get by word name
  - `list_learning_points(limit, offset, tier, difficulty, type)` - List with filters
- **Status:** Exists but not exposed via API
- **Note:** Uses Neo4j, but Explorer Mode design calls for PostgreSQL + JSONB

---

## Connection-Building Algorithm

### Overview

The **Connection-Building Scope Algorithm** is the intelligent word selection system designed to choose words based on relationships to already verified words.

**Status:** Fully specified, **not implemented**

**Key Documents:**
- `docs/connection-building-scope-algorithm.md` - Complete technical specification
- `docs/10-mvp-validation-strategy-enhanced.md` - Algorithm overview

### Algorithm Design

**Core Principle:** Select words that connect to words already verified/encountered, building semantic networks.

**Strategy Mix:**
- **60% Connection-Based:** Words connected to verified words
- **40% Adaptive Level-Based:** Words at user's vocabulary level (from LexiSurvey)

**Priority Order:**
1. Prerequisites Met (+100 points)
2. Direct Relationships (+50 each)
3. Phrase Components (+40)
4. Morphological Patterns (+30)
5. 2-Degree Connections (+20 each)

### Learning Modes

**1. Guided Mode** (Not Implemented):
- Algorithm selects words automatically
- Curriculum-focused (Taiwan MOE, CEFR, etc.)
- Learner can override/search if needed

**2. Explorer Mode** (Not Implemented):
- Algorithm suggests words intelligently
- Learner chooses which to learn
- Full freedom to search any word
- Smart suggestions based on connections, prerequisites, interests

---

## Database Schema Status

### Current State

**PostgreSQL Models:**
- `learning_progress` - Tracks user progress on learning points
- `verification_schedule` - Spaced repetition scheduling
- **Note:** No `learning_points` table in PostgreSQL (uses Neo4j)

**Neo4j:**
- `LearningPoint` nodes exist
- Word data stored in Neo4j
- Relationships exist in Neo4j

### Required for Explorer Mode (Not Implemented)

**1. learning_points Table (PostgreSQL)**
```sql
CREATE TABLE learning_points (
    id TEXT PRIMARY KEY,
    word TEXT NOT NULL,
    type TEXT DEFAULT 'word',
    tier INTEGER NOT NULL,
    definition TEXT,
    example TEXT,
    frequency_rank INTEGER,
    difficulty INTEGER,
    curricula TEXT[] DEFAULT '{}',
    topics TEXT[] DEFAULT '{}',
    connections JSONB DEFAULT '{}'  -- Pre-built relationships
);
```

**2. user_learning_mode Table**
```sql
CREATE TABLE user_learning_mode (
    user_id UUID PRIMARY KEY REFERENCES users(id),
    mode TEXT DEFAULT 'guided',  -- 'guided' or 'explorer'
    curriculum TEXT,
    interests TEXT[] DEFAULT '{}',
    entry_point TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

**3. graph_structure Table**
```sql
CREATE TABLE graph_structure (
    id SERIAL PRIMARY KEY,
    version INTEGER DEFAULT 1,
    nodes JSONB,
    edges JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## Word Lookup/Dictionary Feature

### Current State

**Backend Functionality:**
- ✅ Neo4j lookup exists: `get_learning_point_by_word(word)`
- ❌ No API endpoint exposed
- ❌ No search functionality
- ❌ No dictionary UI

**Files:**
- `backend/src/database/neo4j_crud/learning_points.py` - Contains lookup functions

### Missing Features

1. **Word Search API**
   - Search by word name (partial match)
   - Search by definition
   - Filter by tier, difficulty, curriculum

2. **Dictionary API**
   - Get word details (definition, examples, pronunciation)
   - Show connections to learned words
   - Show suggestion score if applicable

3. **Frontend Dictionary UI**
   - Search bar
   - Word details display
   - Connection visualization

---

## Missing APIs and Features

### Critical Missing APIs

1. **GET /api/v1/words/explorer/suggestions**
   - **Priority:** High
   - **Purpose:** Get intelligent word suggestions
   - **Status:** Designed, not implemented

2. **GET /api/v1/words/search**
   - **Priority:** High
   - **Purpose:** Search words by name
   - **Status:** Designed, not implemented

3. **GET /api/v1/graph/personalized**
   - **Priority:** Medium
   - **Purpose:** Get graph data for visualization
   - **Status:** Designed, not implemented

4. **POST /api/v1/learning-mode**
   - **Priority:** Medium
   - **Purpose:** Set user's learning mode
   - **Status:** Designed, not implemented

5. **GET /api/v1/words/lookup**
   - **Priority:** Medium
   - **Purpose:** Lookup word by name (dictionary feature)
   - **Status:** Backend function exists, not exposed

### Missing Backend Services

1. **Word Suggestion Engine**
   - Connection-based suggestions
   - Prerequisite checking
   - Bridge word detection
   - Interest matching
   - Level appropriateness

2. **Connection-Building Algorithm Implementation**
   - Word scoring function
   - Connection query logic
   - Prerequisite validation

3. **Graph Personalization Service**
   - Filter graph by learned words
   - Add personalization metadata
   - Generate visualization data

### Missing Database Infrastructure

1. **PostgreSQL learning_points Table**
   - Pre-built graph structure
   - Connections JSONB field
   - Curriculum/topic tags

2. **user_learning_mode Table**
   - Store learning mode preference
   - Store interests
   - Store entry point

3. **graph_structure Table**
   - Pre-built nodes and edges
   - For visualization

---

## Implementation Recommendations

### Phase 1: Foundation (Critical)

1. **Create PostgreSQL learning_points Table**
   - Migrate word data from Neo4j (or sync)
   - Add connections JSONB field
   - Populate with 3,000-4,000 words

2. **Implement Word Search API**
   - `GET /api/v1/words/search`
   - Basic search by word name
   - Return word details

3. **Expose Word Lookup**
   - `GET /api/v1/words/lookup?word={word}`
   - Use existing Neo4j function
   - Return word details

### Phase 2: Suggestion Engine (High Priority)

1. **Implement Connection-Building Algorithm**
   - Word scoring function
   - Connection queries
   - Prerequisite checking

2. **Create Explorer Suggestions API**
   - `GET /api/v1/words/explorer/suggestions`
   - Implement all suggestion types
   - Return scored suggestions

3. **Create Learning Mode API**
   - `POST /api/v1/learning-mode`
   - Store user preference
   - Create user_learning_mode table

### Phase 3: Graph Visualization (Medium Priority)

1. **Create Graph Personalization API**
   - `GET /api/v1/graph/personalized`
   - Filter by learned words
   - Return nodes and edges

2. **Build Graph Structure Table**
   - Pre-compute graph structure
   - Store nodes and edges

3. **Frontend Graph Visualization**
   - D3.js or vis-network
   - Interactive exploration

---

## Current Word Selection Flow

### As-Is Flow

```
1. User encounters word elsewhere (school, books, media)
2. User wants to verify knowledge
3. User must know learning_point_id
4. Frontend calls: POST /api/v1/words/start-verification
   {
     "learning_point_id": "word_123",
     "tier": 1,
     "initial_difficulty": 0.5
   }
5. Backend creates learning_progress entry
6. Backend creates verification_schedule entry
7. User can now take verification tests
```

### Problems

- ❌ User must know learning_point_id (not user-friendly)
- ❌ No word discovery mechanism
- ❌ No suggestions
- ❌ No search functionality
- ❌ No connection-based recommendations

---

## Explorer Mode Flow (Designed, Not Implemented)

### To-Be Flow

```
1. User opens Explorer Mode
2. System checks user's learning mode (guided/explorer)
3. If Explorer Mode:
   a. System gets learned words
   b. System generates suggestions:
      - Connection-based
      - Prerequisites met
      - Level-appropriate
      - Interest-based
      - Bridge words
   c. System displays suggestions with priority
   d. User can:
      - Choose from suggestions
      - Search any word
      - View graph visualization
4. User selects word
5. Frontend calls: POST /api/v1/words/start-verification
6. Backend creates learning_progress entry
7. Backend creates verification_schedule entry
8. User can now take verification tests
```

### Benefits

- ✅ Intelligent suggestions
- ✅ Full user freedom
- ✅ Search functionality
- ✅ Connection visualization
- ✅ Personalized learning path

---

## Files Reference

### Documentation
- `EXPLORER_MODE_START_HERE.md` - Quick start guide
- `docs/EXPLORER_MODE_IMPLEMENTATION.md` - Full implementation guide
- `docs/EXPLORER_MODE_SUMMARY.md` - Summary of decisions
- `docs/connection-building-scope-algorithm.md` - Algorithm specification
- `docs/10-mvp-validation-strategy-enhanced.md` - MVP plan with algorithm

### Backend Code
- `backend/src/api/words.py` - Only word-related API endpoint
- `backend/src/database/neo4j_crud/learning_points.py` - Neo4j CRUD operations
- `backend/src/database/models.py` - PostgreSQL models (no learning_points table)

### Related Systems
- `backend/src/api/survey.py` - LexiSurvey (vocabulary assessment)
- `backend/src/api/verification.py` - Verification scheduling
- `backend/src/api/mcq.py` - MCQ generation and testing

---

## Summary

### What Exists
- ✅ Basic word verification API (`/api/v1/words/start-verification`)
- ✅ Neo4j word lookup functions (not exposed as API)
- ✅ Comprehensive Explorer Mode design
- ✅ Complete Connection-Building Algorithm specification
- ✅ Database schema designs

### What's Missing
- ❌ Word suggestion engine
- ❌ Word search API
- ❌ Explorer Mode API endpoints
- ❌ Connection-Building Algorithm implementation
- ❌ PostgreSQL learning_points table
- ❌ Graph personalization service
- ❌ Learning mode management

### Next Steps
1. Implement PostgreSQL learning_points table
2. Create word search API
3. Implement suggestion engine
4. Create Explorer Mode API endpoints
5. Build frontend Explorer Mode UI

---

**Investigation Complete** ✅

