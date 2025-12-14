# Relationship Query Examples

## Backward Compatibility: Word-Level RELATED_TO

**Yes, you can still query `(:Word)-[:RELATED_TO]->(:Word)` exactly as before!**

The new relationship miner creates **aggregated Word-level relationships** for backward compatibility. All existing queries will continue to work.

### Basic Query (Same as Before)
```cypher
MATCH (w:Word {name: "happy"})-[:RELATED_TO]->(related:Word)
RETURN related.name
```

### Enhanced Query (With Quality Filtering)
```cypher
MATCH (w:Word {name: "happy"})-[:RELATED_TO]->(related:Word)
WHERE related.avg_quality >= 0.7  // Optional: filter by quality
RETURN related.name, related.avg_quality
ORDER BY related.avg_quality DESC
```

### Query with Relationship Details
```cypher
MATCH (w:Word {name: "happy"})-[r:RELATED_TO]->(related:Word)
RETURN 
    related.name,
    r.avg_quality,
    r.relationship_count,
    r.types
ORDER BY r.avg_quality DESC
```

## New: Sense-Specific Queries (Better Quality)

### Get True Synonyms Only
```cypher
MATCH (w:Word {name: "happy"})-[:HAS_SENSE]->(s:Sense)
MATCH (s)-[:SYNONYM_OF]->(syn_sense:Sense)
MATCH (syn_sense)<-[:HAS_SENSE]-(syn_word:Word)
RETURN syn_word.name, syn_sense.definition_en
ORDER BY syn_sense.usage_ratio DESC
```

### Get High-Quality Related Words (All Types)
```cypher
MATCH (w:Word {name: "happy"})-[:HAS_SENSE]->(s:Sense)
MATCH (s)-[r:SYNONYM_OF|CLOSE_SYNONYM|RELATED_TO]->(related_sense:Sense)
WHERE r.quality_score >= 0.7
MATCH (related_sense)<-[:HAS_SENSE]-(related_word:Word)
RETURN 
    related_word.name,
    type(r) as relationship_type,
    r.quality_score,
    related_sense.definition_en
ORDER BY r.quality_score DESC
```

### Get Related Words for Specific Sense
```cypher
MATCH (s:Sense {id: "happy.a.01"})
MATCH (s)-[r:SYNONYM_OF|CLOSE_SYNONYM|RELATED_TO]->(related_sense:Sense)
MATCH (related_sense)<-[:HAS_SENSE]-(related_word:Word)
RETURN 
    related_word.name,
    type(r) as relationship_type,
    r.quality_score
ORDER BY r.quality_score DESC
```

## Comparison: Old vs New

### Old Query (Still Works!)
```cypher
// Gets all related words (no quality filtering)
MATCH (w:Word {name: "good"})-[:RELATED_TO]->(related:Word)
RETURN related.name
```

### New Query (Better Quality)
```cypher
// Gets only high-quality relationships
MATCH (w:Word {name: "good"})-[r:RELATED_TO]->(related:Word)
WHERE r.avg_quality >= 0.75
RETURN related.name, r.avg_quality
ORDER BY r.avg_quality DESC
```

### Best Query (Sense-Specific)
```cypher
// Gets true synonyms for the most common sense
MATCH (w:Word {name: "good"})-[:HAS_SENSE]->(s:Sense)
WITH s ORDER BY s.usage_ratio DESC LIMIT 1
MATCH (s)-[:SYNONYM_OF]->(syn_sense:Sense)
MATCH (syn_sense)<-[:HAS_SENSE]-(syn_word:Word)
RETURN syn_word.name, syn_sense.definition_en
```

## What Gets Created

After running the new relationship miner:

1. **Sense-to-Sense relationships** (new, high quality):
   - `(:Sense)-[:SYNONYM_OF]->(:Sense)`
   - `(:Sense)-[:CLOSE_SYNONYM]->(:Sense)`
   - `(:Sense)-[:RELATED_TO]->(:Sense)`

2. **Word-to-Word relationships** (aggregated, backward compatible):
   - `(:Word)-[:RELATED_TO {avg_quality, relationship_count, types}]->(:Word)`

## Migration Path

### Phase 1: Run New Miner (No Breaking Changes)
```bash
python src/relationship_miner.py 0.6
```
- Creates new sense-specific relationships
- Creates aggregated word-level relationships
- **All existing queries still work!**

### Phase 2: Gradually Update Queries (Optional)
- Update queries to use sense-specific relationships for better quality
- Add quality filters to existing queries
- No rush - backward compatibility maintained

### Phase 3: Remove Old Relationships (Optional, Future)
- Only if you want to clean up
- Can keep both - they serve different purposes

## Summary

✅ **Yes, you can still query `(:Word)-[:RELATED_TO]->(:Word)` exactly as before**

✅ **Plus you get:**
- Quality scores on relationships
- Sense-specific relationships (better quality)
- Relationship type distinction (SYNONYM_OF, CLOSE_SYNONYM, RELATED_TO)

✅ **No breaking changes** - all existing code continues to work


