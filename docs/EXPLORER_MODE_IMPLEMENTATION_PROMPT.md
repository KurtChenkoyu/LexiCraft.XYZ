# Explorer Mode Implementation Prompt

Copy this prompt into a new chat to start implementing Explorer Mode:

---

```
You're building LexiCraft MVP - Phase 1: Explorer Mode with Smart Suggestions

CONTEXT:
LexiCraft is a vocabulary verification platform where kids earn money by verifying words they've encountered. Users typically encounter words elsewhere first (school, books, media), and we verify/solidify that knowledge. 
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
   - Connection-based suggestions (words connected to verified words)
   - Prerequisite suggestions (words ready to learn)
   - Level-appropriate suggestions (based on LexiSurvey)
   - Interest-based suggestions (if specified)
   - Bridge word suggestions (connect multiple verified words)
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
```

2. user_learning_mode table:
```sql
CREATE TABLE user_learning_mode (
    user_id UUID PRIMARY KEY REFERENCES users(id),
    mode TEXT DEFAULT 'guided',
    curriculum TEXT,
    interests TEXT[] DEFAULT '{}',
    entry_point TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

3. graph_structure table:
```sql
CREATE TABLE graph_structure (
    id SERIAL PRIMARY KEY,
    nodes JSONB,
    edges JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);
```

SUGGESTION ALGORITHM:

Priority Order:
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
- [ ] Populate learning_points table
- [ ] Add relationship data to connections JSONB
- [ ] Pre-compute 2-3 degree connections
- [ ] Build graph_structure table

Step 2: Suggestion Engine
- [ ] Implement connection-based suggestions
- [ ] Implement prerequisite suggestions
- [ ] Implement level-appropriate suggestions
- [ ] Implement interest-based suggestions
- [ ] Implement bridge word detection
- [ ] Combine and score suggestions

Step 3: API Endpoints
- [ ] GET /api/v1/words/explorer/suggestions
- [ ] GET /api/v1/graph/personalized
- [ ] GET /api/v1/words/search
- [ ] POST /api/v1/learning-mode

Step 4: Frontend Components
- [ ] Explorer Mode UI component
- [ ] Suggestion cards
- [ ] Search bar
- [ ] Graph visualization
- [ ] Mode toggle

Step 5: Integration
- [ ] Word selection flow
- [ ] Learning progress updates
- [ ] Relationship discovery
- [ ] Graph visualization updates

SUCCESS CRITERIA:
- [ ] Pre-built graph structure working
- [ ] Suggestion engine providing smart recommendations
- [ ] Explorer Mode UI functional
- [ ] Graph visualization showing personalized network
- [ ] Learners can search and choose words freely
- [ ] Relationship discovery bonuses working
- [ ] Mode switching working

READ THE FULL DOCS:
- docs/EXPLORER_MODE_IMPLEMENTATION.md - Complete implementation guide
- docs/connection-building-scope-algorithm.md - Algorithm details
- docs/10-mvp-validation-strategy-enhanced.md - MVP plan

Start with Step 1: Pre-Build Graph Structure. Report back when complete.
```


