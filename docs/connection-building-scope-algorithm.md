# Connection-Building Scope Algorithm: Technical Specification

## Overview

The **Connection-Building Scope** algorithm is the intelligent word selection system that chooses the next verification block based on relationships and connections to words already verified/encountered. This creates semantic networks rather than random word lists, improving retention and verification effectiveness. Note: Users typically encounter words elsewhere first (school, books, media), and we verify/solidify that knowledge.

---

## Problem Statement

### Current Approach (Simple Sequential)
```
Day 1: Learn words 1-20 (rank 1-20)
Day 2: Learn words 21-40 (rank 21-40)
Day 3: Learn words 41-60 (rank 41-60)
```

**Problems**:
- No connection between words
- No prerequisite enforcement
- Misses relationship discovery bonuses
- Lower retention (isolated words)
- Less engaging (no "aha!" moments)

### Enhanced Approach (Connection-Building)
```
Day 1: Learn "direct" (rank 500)
Day 2: Learn "indirect" (related to "direct") + "redirect" (morphological)
Day 3: Learn "make" + "decision" (collocation pair)
Day 4: Learn "make a decision" (phrase completion)
```

**Benefits**:
- Words reinforce each other
- Prerequisites make learning easier
- More relationship discovery bonuses
- Higher retention (semantic networks)
- More engaging (see connections)

---

## Algorithm Design

### Core Principle

**Select words that connect to words already verified/encountered, building semantic networks.**

### Learning Modes ⭐ NEW

**1. Guided Mode** (Follow Curriculum):
- Algorithm selects words automatically
- Curriculum-focused (Taiwan MOE, CEFR, etc.)
- Learner can override/search if needed
- Best for: Structured learning, exam prep

**2. Explorer Mode** (Build Your Own City) ⭐ NEW:
- Algorithm suggests words intelligently
- Learner chooses which to learn
- Full freedom to search any word
- Smart suggestions based on connections, prerequisites, interests
- Best for: Self-directed learning, interest-driven exploration

### Strategy Mix

- **60% Connection-Based**: Words connected to verified/encountered words
- **40% Adaptive Level-Based**: Words at child's vocabulary level

### Priority Order (Connection-Based)

1. **Prerequisites Met** (Score: +100)
   - Words whose prerequisites are already learned
   - Example: "indirect" requires "direct"
   - Query: Find words where all prerequisites are in learned set

2. **Direct Relationships** (Score: +50 each)
   - `RELATED_TO`: Synonyms, related concepts
   - `COLLOCATES_WITH`: Words often used together
   - `OPPOSITE_OF`: Antonyms
   - Example: "make" → "decision" (collocation)

3. **Phrase Components** (Score: +40)
   - Words that complete phrases already started
   - Example: "beat" + "around" → "bush" (for "beat around the bush")
   - Query: Find words that are part of phrases with learned components

4. **Morphological Patterns** (Score: +30)
   - Words sharing prefixes/suffixes
   - Example: "direct" → "indirect", "redirect", "direction"
   - Query: Find words with same morphological patterns

5. **2-Degree Connections** (Score: +20 each)
   - Words connected through one intermediate word
   - Example: "direct" → "indirect" → "indirectly"
   - Query: Find words connected via one intermediate learned word

### Scoring Function

```python
def score_word_connection(
    word: LearningPoint,
    learned_words: List[str],
    relationships: Dict[str, List[str]],
    user_level: int
) -> float:
    """
    Score word based on connection strength to learned words.
    
    Args:
        word: The word being scored
        learned_words: List of learned word IDs
        relationships: Dictionary of relationship types to word IDs
        user_level: User's vocabulary level (from LexiSurvey)
    
    Returns:
        Score (higher = better priority)
    """
    score = 0.0
    
    # 1. Prerequisites Met (+100)
    if all_prerequisites_met(word, learned_words):
        score += 100.0
    
    # 2. Direct Relationships (+50 each)
    direct_rels = count_direct_relationships(word, learned_words, relationships)
    score += direct_rels * 50.0
    
    # 3. Phrase Components (+40)
    if is_phrase_component(word, learned_words):
        score += 40.0
    
    # 4. Morphological Patterns (+30)
    if shares_morphological_pattern(word, learned_words):
        score += 30.0
    
    # 5. 2-Degree Connections (+20 each)
    two_degree = count_2degree_connections(word, learned_words, relationships)
    score += two_degree * 20.0
    
    # 6. Frequency Bonus (+10 if high frequency)
    if word.frequency_rank < 1000:
        score += 10.0
    
    # 7. Difficulty Penalty (-10 if too hard)
    if word.difficulty > user_level + 1:
        score -= 10.0
    
    return score
```

---

## Implementation

### Database Schema (PostgreSQL)

```sql
CREATE TABLE learning_points (
    id SERIAL PRIMARY KEY,
    word TEXT NOT NULL,
    type TEXT DEFAULT 'word',
    tier INTEGER NOT NULL,
    definition TEXT,
    example TEXT,
    frequency_rank INTEGER,
    difficulty INTEGER,  -- CEFR level (1-6 for A1-C2)
    metadata JSONB DEFAULT '{}'  -- Relationships
);

-- Metadata structure:
{
  "prerequisites": ["word_id_1", "word_id_2"],
  "related_words": ["word_id_3"],
  "collocations": ["word_id_4"],
  "morphological_patterns": ["prefix_in", "suffix_ly"],
  "opposites": ["word_id_5"],
  "phrase_components": ["word_id_6", "word_id_7"]
}

-- Indexes for fast queries
CREATE INDEX idx_learning_points_metadata ON learning_points USING GIN (metadata);
CREATE INDEX idx_learning_points_frequency ON learning_points(frequency_rank);
CREATE INDEX idx_learning_points_difficulty ON learning_points(difficulty);
```

### Query Examples

#### 1. Find Prerequisites Met

```sql
-- Find words where all prerequisites are learned
SELECT lp.*
FROM learning_points lp
WHERE NOT EXISTS (
    SELECT 1
    FROM jsonb_array_elements_text(lp.metadata->'prerequisites') AS prereq_id
    WHERE prereq_id NOT IN (
        SELECT learning_point_id::text
        FROM learning_progress
        WHERE user_id = $user_id
        AND status IN ('verified', 'learning')
    )
)
AND lp.id NOT IN (
    SELECT learning_point_id::text
    FROM learning_progress
    WHERE user_id = $user_id
)
ORDER BY lp.frequency_rank
LIMIT 20;
```

#### 2. Find Direct Relationships

```sql
-- Find words related to learned words
SELECT DISTINCT lp.*
FROM learning_points lp
WHERE lp.metadata->'related_words' ?| (
    SELECT array_agg(learning_point_id::text)
    FROM learning_progress
    WHERE user_id = $user_id
    AND status IN ('verified', 'learning')
)
OR lp.metadata->'collocations' ?| (
    SELECT array_agg(learning_point_id::text)
    FROM learning_progress
    WHERE user_id = $user_id
    AND status IN ('verified', 'learning')
)
AND lp.id NOT IN (
    SELECT learning_point_id::text
    FROM learning_progress
    WHERE user_id = $user_id
)
ORDER BY lp.frequency_rank
LIMIT 20;
```

#### 3. Find Phrase Components

```sql
-- Find words that complete phrases with learned components
SELECT lp.*
FROM learning_points lp
WHERE lp.type = 'word'
AND lp.metadata->'phrase_components' ?| (
    SELECT array_agg(learning_point_id::text)
    FROM learning_progress
    WHERE user_id = $user_id
    AND status IN ('verified', 'learning')
)
AND lp.id NOT IN (
    SELECT learning_point_id::text
    FROM learning_progress
    WHERE user_id = $user_id
)
ORDER BY lp.frequency_rank
LIMIT 20;
```

### Python Implementation

```python
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text

def select_daily_words(
    session: Session,
    user_id: str,
    daily_limit: int = 20,
    vocab_level: Optional[int] = None
) -> List[Dict]:
    """
    Select daily words using connection-building scope strategy.
    
    Args:
        session: Database session
        user_id: User ID
        daily_limit: Maximum words per day (default: 20)
        vocab_level: User's vocabulary level (from LexiSurvey)
    
    Returns:
        List of word dictionaries with connection context
    """
    # Get learned words
    learned_words = get_learned_words(session, user_id)
    
    # Get vocabulary level if not provided
    if vocab_level is None:
        vocab_level = get_user_vocab_level(session, user_id)
    
    # Strategy 1: Connection-Based Selection (60%)
    connection_limit = int(daily_limit * 0.6)
    connection_words = select_connection_words(
        session, learned_words, connection_limit
    )
    
    # Strategy 2: Adaptive Level-Based Selection (40%)
    level_limit = daily_limit - len(connection_words)
    level_words = select_adaptive_words(
        session, vocab_level, learned_words, level_limit
    )
    
    # Merge and prioritize
    all_words = connection_words + level_words
    
    # Score and sort
    scored_words = [
        {
            **word,
            'connection_score': score_word_connection(
                word, learned_words, get_relationships(session, word['id']), vocab_level
            ),
            'connection_type': get_connection_type(word, learned_words)
        }
        for word in all_words
    ]
    
    # Sort by score (highest first)
    scored_words.sort(key=lambda x: x['connection_score'], reverse=True)
    
    # Return top N words
    return scored_words[:daily_limit]


def select_connection_words(
    session: Session,
    learned_words: List[str],
    limit: int
) -> List[Dict]:
    """Select words based on connections to learned words."""
    
    if not learned_words:
        # No learned words yet - return high-frequency words
        return select_high_frequency_words(session, limit)
    
    # Query for connection words
    query = text("""
        WITH learned_ids AS (
            SELECT learning_point_id::text as id
            FROM learning_progress
            WHERE user_id = :user_id
            AND status IN ('verified', 'learning')
        ),
        connection_candidates AS (
            -- Prerequisites met
            SELECT lp.*, 100 as priority
            FROM learning_points lp
            WHERE NOT EXISTS (
                SELECT 1
                FROM jsonb_array_elements_text(lp.metadata->'prerequisites') AS prereq_id
                WHERE prereq_id NOT IN (SELECT id FROM learned_ids)
            )
            AND lp.id NOT IN (SELECT id FROM learned_ids)
            
            UNION ALL
            
            -- Direct relationships
            SELECT lp.*, 50 as priority
            FROM learning_points lp
            WHERE (
                lp.metadata->'related_words' ?| (SELECT array_agg(id) FROM learned_ids)
                OR lp.metadata->'collocations' ?| (SELECT array_agg(id) FROM learned_ids)
                OR lp.metadata->'opposites' ?| (SELECT array_agg(id) FROM learned_ids)
            )
            AND lp.id NOT IN (SELECT id FROM learned_ids)
            
            UNION ALL
            
            -- Phrase components
            SELECT lp.*, 40 as priority
            FROM learning_points lp
            WHERE lp.metadata->'phrase_components' ?| (SELECT array_agg(id) FROM learned_ids)
            AND lp.id NOT IN (SELECT id FROM learned_ids)
            
            UNION ALL
            
            -- Morphological patterns
            SELECT lp.*, 30 as priority
            FROM learning_points lp
            WHERE lp.metadata->'morphological_patterns' ?| (
                SELECT DISTINCT jsonb_array_elements_text(lp2.metadata->'morphological_patterns')
                FROM learning_points lp2
                WHERE lp2.id IN (SELECT id FROM learned_ids)
            )
            AND lp.id NOT IN (SELECT id FROM learned_ids)
        )
        SELECT DISTINCT ON (id) *
        FROM connection_candidates
        ORDER BY id, priority DESC, frequency_rank
        LIMIT :limit
    """)
    
    result = session.execute(query, {'user_id': user_id, 'limit': limit})
    return [dict(row) for row in result]


def select_adaptive_words(
    session: Session,
    vocab_level: int,
    learned_words: List[str],
    limit: int
) -> List[Dict]:
    """Select words at appropriate difficulty level."""
    
    # Select words at user's level ± 1
    query = text("""
        SELECT lp.*
        FROM learning_points lp
        WHERE lp.difficulty BETWEEN :min_level AND :max_level
        AND lp.id NOT IN (
            SELECT learning_point_id::text
            FROM learning_progress
            WHERE user_id = :user_id
        )
        ORDER BY lp.frequency_rank
        LIMIT :limit
    """)
    
    result = session.execute(query, {
        'user_id': user_id,
        'min_level': max(1, vocab_level - 1),
        'max_level': min(6, vocab_level + 1),
        'limit': limit
    })
    
    return [dict(row) for row in result]


def all_prerequisites_met(
    word: Dict,
    learned_words: List[str]
) -> bool:
    """Check if all prerequisites for a word are learned."""
    prerequisites = word.get('metadata', {}).get('prerequisites', [])
    if not prerequisites:
        return True  # No prerequisites = always met
    
    return all(prereq_id in learned_words for prereq_id in prerequisites)


def get_connection_type(
    word: Dict,
    learned_words: List[str]
) -> str:
    """Get the type of connection this word has to learned words."""
    metadata = word.get('metadata', {})
    
    if all_prerequisites_met(word, learned_words) and metadata.get('prerequisites'):
        return 'prerequisite_met'
    
    if any(rel_id in learned_words for rel_id in metadata.get('related_words', [])):
        return 'related'
    
    if any(coll_id in learned_words for coll_id in metadata.get('collocations', [])):
        return 'collocation'
    
    if any(opp_id in learned_words for opp_id in metadata.get('opposites', [])):
        return 'opposite'
    
    if any(comp_id in learned_words for comp_id in metadata.get('phrase_components', [])):
        return 'phrase_component'
    
    return 'level_based'
```

---

## Example Flow

### Day 1: Initial Learning
```
Child learns: "direct" (rank 500, difficulty 2)
```

### Day 2: Connection-Based Selection
```
Algorithm finds:
1. "indirect" (prerequisite: "direct", RELATED_TO) - Score: 150
2. "redirect" (morphological pattern: "direct") - Score: 80
3. "direction" (morphological pattern: "direct") - Score: 80
4. "straight" (OPPOSITE_OF "direct") - Score: 60

Selected: "indirect", "redirect", "direction", "straight" + 16 level-based words
```

### Day 3: After Learning "indirect" and "make"
```
Algorithm finds:
1. "decision" (COLLOCATES_WITH "make") - Score: 60
2. "indirectly" (morphological from "indirect") - Score: 50
3. "make a decision" (phrase with "make" + "decision") - Score: 40

Selected: "decision", "indirectly", "make a decision" + 17 level-based words
```

### Result
- Child builds semantic network
- Words reinforce each other
- More relationship discovery bonuses
- Higher retention
- More engaging learning

---

## Relationship Discovery Integration

### When Child Learns New Word

```python
def on_word_learned(
    session: Session,
    user_id: str,
    word_id: str
):
    """Check for relationship discoveries when word is learned."""
    
    # Get learned words
    learned_words = get_learned_words(session, user_id)
    
    # Find relationships to learned words
    word = get_word(session, word_id)
    relationships = find_relationships(word, learned_words)
    
    # Award bonus points for discoveries
    for rel in relationships:
        if not relationship_discovered(session, user_id, word_id, rel['target_id']):
            award_relationship_bonus(
                session, user_id, word_id, rel['target_id'], rel['type']
            )
```

### Relationship Discovery Query

```python
def find_relationships(
    word: Dict,
    learned_words: List[str]
) -> List[Dict]:
    """Find relationships between word and learned words."""
    metadata = word.get('metadata', {})
    relationships = []
    
    # Check related words
    for rel_id in metadata.get('related_words', []):
        if rel_id in learned_words:
            relationships.append({
                'target_id': rel_id,
                'type': 'RELATED_TO'
            })
    
    # Check collocations
    for coll_id in metadata.get('collocations', []):
        if coll_id in learned_words:
            relationships.append({
                'target_id': coll_id,
                'type': 'COLLOCATES_WITH'
            })
    
    # Check opposites
    for opp_id in metadata.get('opposites', []):
        if opp_id in learned_words:
            relationships.append({
                'target_id': opp_id,
                'type': 'OPPOSITE_OF'
            })
    
    return relationships
```

---

## Performance Considerations

### Query Optimization

1. **Use GIN indexes** on JSONB metadata columns
2. **Cache learned words** in memory (refresh daily)
3. **Batch queries** for multiple words
4. **Limit result sets** early (LIMIT in subqueries)

### Scalability

- **MVP**: PostgreSQL + JSONB (sufficient for 5,000 words)
- **Phase 2**: Consider Neo4j for complex multi-hop queries
- **Caching**: Cache relationship data for frequently accessed words

---

## Testing Strategy

### Unit Tests

1. Test `score_word_connection()` with various scenarios
2. Test `all_prerequisites_met()` with different prerequisite sets
3. Test `select_connection_words()` with empty learned set
4. Test relationship discovery detection

### Integration Tests

1. Test full word selection flow
2. Test relationship discovery bonus awarding
3. Test daily limit enforcement
4. Test prerequisite enforcement

### Performance Tests

1. Query time for 100 learned words
2. Query time for 1,000 learned words
3. Memory usage with large learned sets

---

## Explorer Mode: Smart Suggestions + Full Freedom ⭐ NEW

### Overview

**Explorer Mode** allows learners to build their own learning path while still receiving intelligent suggestions. The system provides smart recommendations, but the learner has full freedom to choose.

### Suggestion Types

**1. Connection-Based Suggestions** (Primary):
- Words directly connected to learned words
- Shows relationship type and source word
- Priority: High

**2. Prerequisite Suggestions**:
- Words where all prerequisites are met
- Shows "Ready to learn!" indicator
- Priority: Highest

**3. Level-Appropriate Suggestions**:
- Words at learner's vocabulary level (from LexiSurvey)
- Prevents frustration (too hard) or boredom (too easy)
- Priority: Medium

**4. Interest-Based Suggestions**:
- Words matching learner's interests
- Adapts based on learning choices
- Priority: High

**5. Bridge Word Suggestions** (Discovery):
- Words that connect multiple learned words
- Example: "function" connects "algorithm" + "physics"
- Priority: Highest (discovery bonus available)

### Implementation

```python
def get_explorer_suggestions(user_id, learned_words, limit=50):
    """
    Get comprehensive suggestions for Explorer Mode.
    Combines all suggestion types, learner chooses.
    """
    # Get all suggestion types
    connection_suggestions = get_connection_suggestions(learned_words)
    prerequisite_suggestions = get_prerequisite_suggestions(learned_words)
    level_suggestions = get_level_suggestions(user_id, learned_words)
    interest_suggestions = get_interest_suggestions(user_id, learned_words)
    bridge_suggestions = get_bridge_word_suggestions(learned_words)
    
    # Combine and deduplicate
    all_suggestions = combine_suggestions([
        connection_suggestions,
        prerequisite_suggestions,
        level_suggestions,
        interest_suggestions,
        bridge_suggestions
    ])
    
    # Sort by score
    sorted_suggestions = sorted(all_suggestions, 
                               key=lambda x: x['score'], 
                               reverse=True)
    
    return {
        'suggestions': sorted_suggestions[:limit],
        'search_enabled': True,  # Can search any word
        'mode': 'explorer',
        'total_available': len(get_all_words())
    }
```

### UI Features

- **Search Bar**: Search any word in database
- **Suggestion Cards**: Show word, reason, connection info
- **Priority Indicators**: ⭐ (highest), 🔗 (high), 🔬 (interest)
- **Action Buttons**: [Learn] [Skip] [See Connections]
- **Mode Toggle**: Switch between Guided/Explorer

### Benefits

- **Intelligent Guidance**: Smart suggestions based on connections
- **Full Freedom**: Learner chooses their path
- **Discovery**: Find unexpected connections
- **Personalization**: Each learner builds unique network
- **Engagement**: More engaging than prescribed paths

---

## Future Enhancements (Phase 2)

1. **Neo4j Integration**: Multi-hop relationship queries
2. **Machine Learning**: Learn optimal connection weights from user data
3. **Adaptive Scoring**: Adjust connection scores based on success rates
4. **Visual Connection Map**: Interactive graph visualization
5. **Learning Path Recommendations**: Suggest optimal learning sequences
6. **Advanced Explorer Features**: Interest learning, topic clustering

---

## Summary

The **Connection-Building Scope** algorithm:

1. **Selects words connected to learned words** (60% connection-based)
2. **Enforces prerequisites** (can't skip ahead)
3. **Prioritizes by connection strength** (scoring function)
4. **Balances with adaptive level-based selection** (40%)
5. **Integrates with relationship discovery bonuses**

**Result**: Children build semantic networks, learn more effectively, and earn more relationship bonuses.

