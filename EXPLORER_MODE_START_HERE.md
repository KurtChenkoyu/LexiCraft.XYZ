# 🚀 Explorer Mode Implementation - Start Here

## Copy This Prompt Into a New Chat:

---

```
You're building LexiCraft MVP - Phase 1: Explorer Mode with Smart Suggestions

CONTEXT:
LexiCraft is a vocabulary learning platform where kids earn money by learning words. 
We're implementing Explorer Mode - a learning mode where learners build their own 
vocabulary network with intelligent suggestions.

KEY INSIGHT:
- Pre-build graph structure in PostgreSQL (all words + relationships)
- Each learner sees personalized graph based on their progress
- System provides smart suggestions, but learner has full freedom
- Graph visualization shows their personal "city" growing organically

WHAT'S ALREADY BUILT ✅:
1. Database schema (PostgreSQL with learning_points, learning_progress tables)
2. Auth system (Supabase)
3. LexiSurvey (vocabulary assessment)
4. Basic parent/child dashboard structure

WHAT NEEDS TO BE BUILT ❌:

1. Pre-Build Graph Structure
   - Populate learning_points table with 3,000-4,000 words
   - Add relationship data (prerequisites, collocations, morphological, etc.)
   - Pre-compute 2-3 degree connections
   - Store in connections JSONB field
   - Build graph_structure table for visualization

2. Explorer Mode Suggestion Engine
   - Connection-based suggestions (words connected to learned words)
   - Prerequisite suggestions (words ready to learn)
   - Level-appropriate suggestions (based on LexiSurvey)
   - Interest-based suggestions (if specified)
   - Bridge word suggestions (connect multiple learned words)
   - Scoring and prioritization system

3. Explorer Mode UI Components
   - Suggestion cards (word, reason, connection info, priority)
   - Search functionality (search any word)
   - Graph visualization (D3.js or vis-network)
   - Mode toggle (Guided/Explorer)
   - Interactive graph (click, hover, drag, zoom)

4. API Endpoints
   - GET /api/v1/words/explorer/suggestions
   - GET /api/v1/graph/personalized
   - GET /api/v1/words/search
   - POST /api/v1/learning-mode (set mode)

5. Integration
   - Word selection flow (check mode, show suggestions or auto-select)
   - Learning progress tracking
   - Relationship discovery bonuses
   - Graph visualization updates

TECHNICAL STACK:
- Backend: FastAPI (Python)
- Database: PostgreSQL (Supabase)
- Frontend: Next.js 14 (App Router) + TypeScript
- Visualization: D3.js or vis-network
- Styling: Tailwind CSS

KEY FILES TO REFERENCE:
- docs/10-mvp-validation-strategy-enhanced.md - Full MVP plan
- docs/connection-building-scope-algorithm.md - Algorithm details
- docs/EXPLORER_MODE_IMPLEMENTATION.md - Implementation guide
- backend/migrations/007_unified_user_model.sql - Database schema
- backend/src/database/models.py - SQLAlchemy models

DATABASE SCHEMA NEEDED:

1. learning_points table (with connections JSONB):
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
    connections JSONB DEFAULT '{}'
);

CREATE INDEX idx_learning_points_connections ON learning_points USING GIN (connections);
CREATE INDEX idx_learning_points_curricula ON learning_points USING GIN (curricula);
CREATE INDEX idx_learning_points_topics ON learning_points USING GIN (topics);
```

2. user_learning_mode table:
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

3. graph_structure table:
```sql
CREATE TABLE graph_structure (
    id SERIAL PRIMARY KEY,
    version INTEGER DEFAULT 1,
    nodes JSONB,
    edges JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);
```

SUGGESTION ALGORITHM:

Priority Order (Scoring):
1. Prerequisites Met (+100 points)
2. Bridge Words (+60 per connection)
3. Direct Relationships (+50 each)
4. Interest Matches (+40)
5. Phrase Components (+40)
6. Morphological Patterns (+30)
7. Level-Appropriate (+20)
8. 2-Degree Connections (+20 each)

IMPLEMENTATION ORDER:

Step 1: Pre-Build Graph Structure
- [ ] Create learning_points table migration
- [ ] Populate with 3,000-4,000 words (Tier 1-2)
- [ ] Add relationship data to connections JSONB
- [ ] Pre-compute 2-3 degree connections
- [ ] Build graph_structure table
- [ ] Create indexes for fast queries

Step 2: Suggestion Engine (Backend)
- [ ] Implement connection-based suggestions
- [ ] Implement prerequisite suggestions
- [ ] Implement level-appropriate suggestions
- [ ] Implement interest-based suggestions
- [ ] Implement bridge word detection
- [ ] Combine and score suggestions
- [ ] Create API endpoint: GET /api/v1/words/explorer/suggestions

Step 3: Graph Visualization API
- [ ] Create API endpoint: GET /api/v1/graph/personalized
- [ ] Filter graph by learned words
- [ ] Add personalization (colors, sizes, highlights)
- [ ] Return nodes and edges for visualization

Step 4: Search Functionality
- [ ] Create API endpoint: GET /api/v1/words/search
- [ ] Search words by name
- [ ] Show connection info if connected to learned words
- [ ] Return suggestion score if applicable

Step 5: Frontend Components
- [ ] Explorer Mode UI component
- [ ] Suggestion cards with priority indicators
- [ ] Search bar component
- [ ] Graph visualization (D3.js or vis-network)
- [ ] Mode toggle component
- [ ] Integration with word selection flow

Step 6: Integration & Testing
- [ ] Word selection flow (check mode)
- [ ] Learning progress updates
- [ ] Relationship discovery bonuses
- [ ] Graph visualization updates
- [ ] Mode switching
- [ ] Write tests

SUCCESS CRITERIA:
- [ ] Pre-built graph structure working
- [ ] Suggestion engine providing smart recommendations
- [ ] Explorer Mode UI functional
- [ ] Graph visualization showing personalized network
- [ ] Learners can search and choose words freely
- [ ] Relationship discovery bonuses working
- [ ] Mode switching working
- [ ] Tests passing

READ THE FULL DOCS:
- docs/EXPLORER_MODE_IMPLEMENTATION.md - Complete implementation guide
- docs/connection-building-scope-algorithm.md - Algorithm details
- docs/10-mvp-validation-strategy-enhanced.md - MVP plan
- docs/NEO4J_BUSINESS_ANALYSIS.md - Why pre-build instead of Neo4j

Start with Step 1: Pre-Build Graph Structure. Report back when complete.
```

---

## Quick Reference

**Key Decisions Made:**
1. ✅ Pre-build graph structure in PostgreSQL (not real-time Neo4j)
2. ✅ Support both Guided Mode and Explorer Mode
3. ✅ Smart suggestions in Explorer Mode (not just free-for-all)
4. ✅ Personalized graph visualization (same structure, different views)
5. ✅ Tagged graph for different curricula/levels

**Files Created:**
- `docs/EXPLORER_MODE_IMPLEMENTATION.md` - Full implementation guide
- `docs/EXPLORER_MODE_IMPLEMENTATION_PROMPT.md` - Detailed prompt
- `docs/EXPLORER_MODE_SUMMARY.md` - Summary of decisions
- `EXPLORER_MODE_START_HERE.md` - This file (copy prompt from above)

**Next Step:**
Copy the prompt above into a new chat and start implementing!


