# Relationship Model Improvements

## Problem Statement

The current `RELATED_TO` relationships are **thin and ill-defined**:
- All WordNet lemmas in the same synset are treated as synonyms (but they're not always true synonyms)
- Relationships are at Word level, not Sense level (mixing different meanings)
- No quality scoring or relationship strength
- No distinction between true synonyms vs. related concepts

## Solution: Sense-Specific Relationships with Quality Scoring

### New Schema

**Sense-to-Sense Relationships** (Primary):
```cypher
(:Sense)-[:SYNONYM_OF {
    strength: 1.0,
    quality_score: 0.95,
    source: "wordnet"
}]->(:Sense)

(:Sense)-[:CLOSE_SYNONYM {
    strength: 0.85,
    quality_score: 0.82,
    source: "wordnet"
}]->(:Sense)

(:Sense)-[:RELATED_TO {
    strength: 0.70,
    quality_score: 0.68,
    source: "wordnet"
}]->(:Sense)
```

**Word-to-Word Relationships** (Aggregated, for backward compatibility):
```cypher
(:Word)-[:RELATED_TO {
    avg_quality: 0.75,
    relationship_count: 3,
    types: ["SYNONYM_OF", "CLOSE_SYNONYM", "RELATED_TO"]
}]->(:Word)
```

### Relationship Types

1. **SYNONYM_OF** - True synonyms (same WordNet synset)
   - Strength: 1.0
   - Example: "happy" ↔ "joyful" (same synset)

2. **CLOSE_SYNONYM** - Very similar (path similarity >= 0.8)
   - Strength: 0.8-0.99
   - Example: "happy" ↔ "cheerful" (very similar meanings)

3. **RELATED_TO** - Related concepts (path similarity 0.6-0.8)
   - Strength: 0.6-0.79
   - Example: "happy" ↔ "content" (related but distinct)

### Quality Scoring

Relationships are scored (0.0-1.0) based on:
- **40%** Semantic similarity (WordNet path similarity)
- **30%** Same synset (true synonyms get bonus)
- **20%** Part of speech matching
- **10%** Frequency rank similarity (pedagogical appropriateness)

Only relationships with `quality_score >= 0.6` (configurable) are created.

## Benefits

1. **Semantically Meaningful**: Relationships are sense-specific, not word-level
2. **Quality Filtered**: Weak relationships are filtered out
3. **Type Distinction**: Can query for true synonyms vs. related words
4. **Backward Compatible**: Word-level aggregated relationships maintained

## Migration

### Step 1: Run New Relationship Miner

```bash
cd backend
source venv/bin/activate
python src/relationship_miner.py 0.6  # 0.6 = minimum quality threshold
```

This will:
- Create sense-specific relationships
- Filter by quality score
- Create aggregated word-level relationships

### Step 2: Update Queries

**Old Query** (Word-level):
```cypher
MATCH (w:Word {name: "happy"})-[:RELATED_TO]->(related:Word)
RETURN related.name
```

**New Query** (Sense-specific, better quality):
```cypher
// Get true synonyms only
MATCH (w:Word {name: "happy"})-[:HAS_SENSE]->(s:Sense)
MATCH (s)-[:SYNONYM_OF]->(related_sense:Sense)
MATCH (related_sense)<-[:HAS_SENSE]-(related:Word)
RETURN related.name, related_sense.definition_en
ORDER BY related_sense.usage_ratio DESC
```

**Or use aggregated Word-level** (backward compatible):
```cypher
MATCH (w:Word {name: "happy"})-[:RELATED_TO]->(related:Word)
WHERE related.avg_quality >= 0.7  // Filter by quality
RETURN related.name, related.avg_quality
ORDER BY related.avg_quality DESC
```

## Comparison

### Before (Current)
- 3,956 `RELATED_TO` relationships (all WordNet lemmas)
- Word-level only
- No quality filtering
- Mixes different senses

### After (Improved)
- ~2,000-2,500 relationships (quality filtered)
- Sense-specific relationships
- Quality scored (0.6-1.0)
- Type distinction (SYNONYM_OF, CLOSE_SYNONYM, RELATED_TO)

## Usage Examples

### Get True Synonyms Only
```cypher
MATCH (w:Word {name: "good"})-[:HAS_SENSE]->(s:Sense)
MATCH (s)-[:SYNONYM_OF]->(syn_sense:Sense)
MATCH (syn_sense)<-[:HAS_SENSE]-(syn_word:Word)
RETURN syn_word.name, syn_sense.definition_en
```

### Get High-Quality Related Words
```cypher
MATCH (w:Word {name: "good"})-[:RELATED_TO]->(related:Word)
WHERE related.avg_quality >= 0.75
RETURN related.name, related.avg_quality
ORDER BY related.avg_quality DESC
LIMIT 10
```

### Find Words Related to a Specific Sense
```cypher
MATCH (s:Sense {id: "good.a.01"})
MATCH (s)-[r:SYNONYM_OF|CLOSE_SYNONYM|RELATED_TO]->(related_sense:Sense)
WHERE r.quality_score >= 0.7
RETURN related_sense.id, r.relationship_type, r.quality_score
ORDER BY r.quality_score DESC
```

## Next Steps

1. ✅ Run relationship miner to create new relationships
2. ⏳ Update queries in `agent_stage2.py` to use sense-specific relationships
3. ⏳ Update connection-building algorithm to prioritize SYNONYM_OF
4. ⏳ Consider removing old low-quality relationships (optional)


