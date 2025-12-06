# Implementation Prompt: Word List Population

**Phase**: Phase 1 - Word List Population  
**Priority**: High (Required for Learning Interface)  
**Estimated Time**: 3-4 hours  
**Dependencies**: ✅ Database Schema Complete

---

## Your Mission

Populate the Neo4j Learning Point Cloud with the compiled word list (3,500 words). Create learning points in Neo4j with definitions, examples, and metadata using WordNet.

---

## Context

- ✅ Word list compilation complete (3,500 words in `scripts/combined_word_list_phase1.txt`)
- ✅ Neo4j schema ready (constraints, indexes, CRUD operations)
- ✅ Database connections working
- **Target**: ~5,000 learning points (Tier 1-2) from 3,500 words

---

## Tasks

### 1. Create Word List Population Script

**File**: `backend/scripts/populate_learning_points.py`

**Requirements**:
- Read word list from `scripts/combined_word_list_phase1.txt`
- Use WordNet (NLTK) for definitions and examples
- Create Tier 1 learning points (first meaning per word)
- Create Tier 2 learning points (additional meanings)
- Populate Neo4j using `create_learning_point()` function
- Handle errors gracefully (skip words without WordNet data)
- Show progress (words processed, learning points created)

**Key Properties to Populate**:
- `id`: snake_case version of word (e.g., "beat_around_the_bush")
- `word`: The word/phrase itself
- `type`: "word" (for now, phrases/idioms later)
- `tier`: 1 for first meaning, 2 for additional meanings
- `definition`: From WordNet synset.definition()
- `example`: From WordNet synset.examples()[0] if available
- `frequency_rank`: From word list rank (if available)
- `difficulty`: Default to "B1" (can enhance later)
- `register`: Default to "both"
- `contexts`: Empty list for now
- `metadata`: Store POS, synset_id, etc.

### 2. Create Relationship Population Script (Optional - Phase 1)

**File**: `backend/scripts/populate_relationships.py` (optional for MVP)

**Requirements**:
- Create basic relationships (synonyms, antonyms from WordNet)
- Create morphological relationships (prefix/suffix patterns)
- Use `create_relationship()` function from Neo4j CRUD
- Can be simplified for MVP (focus on word population first)

### 3. Test Population

**Requirements**:
- Test with small sample (10-20 words first)
- Verify learning points created correctly
- Verify constraints work (unique id, unique word)
- Check data quality (definitions, examples)
- Run full population
- Verify count matches expected (~5,000 learning points)

### 4. Create Population API Endpoint (Optional)

**File**: `backend/src/api/learning_points.py` (if FastAPI exists)

**Requirements**:
- `GET /api/learning-points` - List learning points (with filters)
- `GET /api/learning-points/{id}` - Get single learning point
- `GET /api/learning-points/{id}/related` - Get related learning points

---

## Implementation Details

### WordNet Integration

```python
import nltk
from nltk.corpus import wordnet as wn

# Download WordNet data if needed
try:
    nltk.data.find('corpora/wordnet')
except:
    nltk.download('wordnet')
    nltk.download('omw-1.4')

# Get synsets for a word
synsets = wn.synsets('beat')
if synsets:
    syn = synsets[0]  # First meaning (Tier 1)
    definition = syn.definition()
    examples = syn.examples()
    pos = syn.pos()  # 'n', 'v', 'a', 'r'
```

### Learning Point Creation

```python
from src.database.neo4j_connection import Neo4jConnection
from src.database.neo4j_crud.learning_points import create_learning_point

# Create learning point
learning_point = {
    'id': 'beat_v1',  # word_pos_tier
    'word': 'beat',
    'type': 'word',
    'tier': 1,
    'definition': syn.definition(),
    'example': syn.examples()[0] if syn.examples() else '',
    'frequency_rank': rank,
    'difficulty': 'B1',
    'register': 'both',
    'contexts': [],
    'metadata': {
        'pos': syn.pos(),
        'synset_id': syn.name()
    }
}

create_learning_point(conn, learning_point)
```

### ID Generation Strategy

For multiple meanings of the same word:
- Tier 1: `{word}_v1`, `{word}_n1`, `{word}_a1` (by POS)
- Tier 2: `{word}_v2`, `{word}_n2`, etc.

Or simpler:
- Tier 1: `{word}_1`, `{word}_2` (sequential)
- Tier 2: `{word}_1_t2`, `{word}_2_t2` (tier suffix)

---

## Success Criteria

- [ ] Population script created and working
- [ ] ~5,000 learning points created in Neo4j
- [ ] All learning points have definitions
- [ ] Examples populated where available
- [ ] Tier 1 and Tier 2 learning points created
- [ ] Data quality verified (no duplicates, valid definitions)
- [ ] Test script passes
- [ ] Ready for Learning Interface to query

---

## Files to Create

```
backend/
├── scripts/
│   ├── populate_learning_points.py  ← NEW
│   └── populate_relationships.py    ← NEW (optional)
└── tests/
    └── test_populate_learning_points.py  ← NEW
```

---

## Dependencies

**Uses**:
- `backend/src/database/neo4j_connection.py` - Connection
- `backend/src/database/neo4j_crud/learning_points.py` - CRUD operations
- `scripts/combined_word_list_phase1.txt` - Word list
- NLTK WordNet - Definitions and examples

**Enables**:
- Phase 2 - Learning Interface (can display words)
- Phase 2 - MCQ Generator (can generate questions)
- Phase 2 - Relationship Discovery (can discover relationships)

---

## Testing

1. **Small Sample Test**:
   ```bash
   # Test with 10 words first
   python scripts/populate_learning_points.py --limit 10
   ```

2. **Verify in Neo4j**:
   ```cypher
   MATCH (lp:LearningPoint)
   RETURN count(lp) as total
   
   MATCH (lp:LearningPoint {tier: 1})
   RETURN count(lp) as tier1_count
   
   MATCH (lp:LearningPoint {tier: 2})
   RETURN count(lp) as tier2_count
   ```

3. **Full Population**:
   ```bash
   python scripts/populate_learning_points.py
   ```

---

## Error Handling

- Skip words without WordNet data (log warning)
- Handle duplicate IDs gracefully (shouldn't happen with proper ID generation)
- Retry logic for connection failures
- Progress logging (every 100 words)

---

## Next Steps After Completion

1. Verify data quality in Neo4j browser
2. Test querying learning points from API
3. Create basic relationships (optional for MVP)
4. Ready for Learning Interface development

---

**READ**:
- `docs/development/handoffs/HANDOFF_PHASE1_WORDLIST.md` (Task 3: Populate Learning Points)
- `scripts/PHASE1_COMPLETION_REPORT.md` (Word list details)
- `backend/src/database/neo4j_crud/learning_points.py` (CRUD functions)

---

**Good luck! You're populating the Learning Point Cloud that powers the entire platform!** 🚀


