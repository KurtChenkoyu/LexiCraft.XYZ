# Explorer Mode Implementation Guide

## Overview

**Explorer Mode** is a verification mode where learners build their own vocabulary network with intelligent suggestions from the system. Unlike Guided Mode (curriculum-focused), Explorer Mode gives learners full freedom to choose their verification path while still providing smart recommendations. Users typically encounter words elsewhere first (school, books, media), and we verify/solidify that knowledge.

---

## Key Features

### 1. Smart Suggestions System

The system provides intelligent suggestions based on:
- **Connection to verified words** (primary)
- **Prerequisites met** (highest priority)
- **Level appropriateness** (from LexiSurvey)
- **Interest matches** (if specified)
- **Bridge words** (connect multiple verified words)

### 2. Full Learner Freedom

- Search any word in database
- Choose from suggestions or ignore them
- Learn in any order
- Build custom learning paths
- Explore different branches

### 3. Graph Visualization

- Pre-built graph structure (PostgreSQL JSONB)
- Personalized visualization based on verified words
- Shows connections between verified words
- Highlights suggested words
- Interactive exploration

---

## Database Schema

### Learning Points Table (Pre-Built Graph)

```sql
CREATE TABLE learning_points (
    id TEXT PRIMARY KEY,
    word TEXT NOT NULL,
    type TEXT DEFAULT 'word',
    tier INTEGER NOT NULL,
    definition TEXT,
    example TEXT,
    frequency_rank INTEGER,
    difficulty INTEGER,  -- CEFR level (1-6 for A1-C2)
    
    -- Curriculum tags (for filtering, not restricting)
    curricula TEXT[] DEFAULT '{}',
    grade_levels INTEGER[] DEFAULT '{}',
    topics TEXT[] DEFAULT '{}',
    
    -- Pre-built connections (JSONB)
    connections JSONB DEFAULT '{}'
);

-- Connections structure:
{
  "prerequisites": ["word_id_1", "word_id_2"],
  "related_words": ["word_id_3", "word_id_4"],
  "collocations": ["word_id_5"],
  "morphological_patterns": ["prefix_in", "suffix_ly"],
  "opposites": ["word_id_6"],
  "phrase_components": ["word_id_7"],
  "2_degree": ["word_id_8"],  -- Pre-computed 2-hop connections
  "3_degree": ["word_id_9"]   -- Pre-computed 3-hop connections
}

-- Indexes
CREATE INDEX idx_learning_points_connections ON learning_points USING GIN (connections);
CREATE INDEX idx_learning_points_curricula ON learning_points USING GIN (curricula);
CREATE INDEX idx_learning_points_topics ON learning_points USING GIN (topics);
```

### User Learning Mode

```sql
CREATE TABLE user_learning_mode (
    user_id UUID PRIMARY KEY REFERENCES users(id),
    mode TEXT DEFAULT 'guided',  -- 'guided' or 'explorer'
    curriculum TEXT,  -- NULL if explorer mode
    interests TEXT[] DEFAULT '{}',
    entry_point TEXT,  -- First word learned
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### Graph Structure (For Visualization)

```sql
CREATE TABLE graph_structure (
    id SERIAL PRIMARY KEY,
    version INTEGER DEFAULT 1,
    nodes JSONB,  -- All words with properties
    edges JSONB,  -- All relationships
    created_at TIMESTAMP DEFAULT NOW()
);

-- Example structure:
{
  "nodes": [
    {"id": "direct", "word": "direct", "frequency_rank": 500, "difficulty": 2},
    {"id": "indirect", "word": "indirect", "frequency_rank": 1200, "difficulty": 3},
    ...
  ],
  "edges": [
    {"source": "direct", "target": "indirect", "type": "MORPHOLOGICAL", "weight": 50},
    ...
  ]
}
```

---

## API Endpoints

### 1. Get Explorer Suggestions

```python
GET /api/v1/words/explorer/suggestions?user_id={user_id}&limit=50

Response:
{
  "suggestions": [
    {
      "word_id": "indirect",
      "word": "indirect",
      "source": "direct",
      "relationship": "MORPHOLOGICAL",
      "reason": "Shares pattern with 'direct'",
      "priority": "high",
      "score": 50,
      "connection_info": {
        "type": "morphological",
        "source_word": "direct",
        "pattern": "in- prefix"
      }
    },
    ...
  ],
  "search_enabled": true,
  "mode": "explorer",
  "total_available": 5000,
  "learned_count": 15
}
```

### 2. Get Personalized Graph

```python
GET /api/v1/graph/personalized?user_id={user_id}

Response:
{
  "nodes": [
    {
      "id": "direct",
      "word": "direct",
      "learned": true,
      "status": "verified",
      "color": "green",
      "size": 30
    },
    {
      "id": "indirect",
      "word": "indirect",
      "learned": false,
      "suggested": true,
      "color": "yellow",
      "size": 15
    },
    ...
  ],
  "edges": [
    {
      "source": "direct",
      "target": "indirect",
      "type": "MORPHOLOGICAL",
      "highlighted": false,
      "opacity": 0.3
    },
    ...
  ]
}
```

### 3. Search Words

```python
GET /api/v1/words/search?q={query}&user_id={user_id}

Response:
{
  "results": [
    {
      "word_id": "quantum",
      "word": "quantum",
      "definition": "...",
      "difficulty": 4,
      "connected_to_learned": ["physics"],  -- If connected
      "suggestion_score": 30  -- If connected
    },
    ...
  ]
}
```

---

## Implementation Steps

### Step 1: Pre-Build Graph Structure

1. **Populate learning_points table**:
   - Import 3,000-4,000 words (Tier 1-2)
   - Add relationship data (prerequisites, collocations, morphological)
   - Tag with curriculum/level/topics

2. **Pre-compute connections**:
   - For each word, find all connected words
   - Store in `connections` JSONB field
   - Pre-compute 2-3 degree connections

3. **Build graph structure**:
   - Export nodes and edges
   - Store in `graph_structure` table
   - Use for visualization

### Step 2: Implement Suggestion Engine

1. **Connection-based suggestions**:
   - Query words connected to verified words
   - Score by relationship type
   - Sort by connection strength

2. **Prerequisite suggestions**:
   - Find words where prerequisites are met
   - Highest priority

3. **Level-appropriate suggestions**:
   - Use LexiSurvey results
   - Filter by difficulty level

4. **Interest-based suggestions**:
   - Match words to user interests
   - Adapt based on learning choices

5. **Bridge word suggestions**:
   - Find words connecting 2+ verified words
   - Discovery priority

### Step 3: Build Explorer Mode UI

1. **Suggestion cards**:
   - Show word, reason, connection info
   - Priority indicators
   - Action buttons

2. **Search functionality**:
   - Search any word
   - Show connection info if connected
   - Add to learning list

3. **Graph visualization**:
   - Use D3.js or vis-network
   - Show verified words (green)
   - Show suggested words (yellow)
   - Show connections
   - Interactive (click, hover, drag)

4. **Mode toggle**:
   - Switch between Guided/Explorer
   - Save preference

### Step 4: Integration

1. **Word selection flow**:
   - Check user's learning mode
   - If explorer: show suggestions
   - If guided: auto-select words

2. **Learning progress**:
   - Track verified words
   - Update graph visualization
   - Check for relationship discoveries

3. **Relationship discovery**:
   - When word learned, check connections
   - Award bonuses
   - Update suggestions

---

## Testing

### Unit Tests

1. Test suggestion scoring
2. Test connection queries
3. Test prerequisite checking
4. Test bridge word detection

### Integration Tests

1. Test full explorer flow
2. Test mode switching
3. Test graph visualization
4. Test relationship discovery

### User Testing

1. Test with real learners
2. Gather feedback on suggestions
3. Test graph visualization usability
4. Measure engagement metrics

---

## Success Metrics

- **Suggestion acceptance rate**: % of suggestions learner follows
- **Exploration rate**: % of learners using Explorer Mode
- **Discovery rate**: % of relationship discoveries
- **Engagement**: Time spent in Explorer Mode
- **Retention**: Words learned in Explorer Mode retention rate

---

## References

- `docs/10-mvp-validation-strategy-enhanced.md` - Full MVP plan
- `docs/connection-building-scope-algorithm.md` - Algorithm details
- `docs/NEO4J_BUSINESS_ANALYSIS.md` - Graph structure decisions


