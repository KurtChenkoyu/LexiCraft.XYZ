# Relationship Population Script

**Status:** ✅ Complete  
**File:** `backend/scripts/populate_relationships.py`

---

## Overview

The relationship population script creates semantic relationships between learning points using WordNet data:
- **Synonyms** → `RELATED_TO` relationships
- **Antonyms** → `OPPOSITE_OF` relationships

---

## Usage

### Basic Usage
```bash
cd backend
source venv/bin/activate

# Create all relationships (synonyms + antonyms)
python3 scripts/populate_relationships.py

# Create only synonyms
python3 scripts/populate_relationships.py --type synonyms

# Create only antonyms
python3 scripts/populate_relationships.py --type antonyms

# Test with limited learning points
python3 scripts/populate_relationships.py --word-limit 100

# Limit relationships per learning point
python3 scripts/populate_relationships.py --limit 5
```

### Arguments
- `--type`: `synonyms`, `antonyms`, or `all` (default: `all`)
- `--limit`: Maximum relationships per learning point (default: all)
- `--word-limit`: Maximum learning points to process (for testing)

---

## How It Works

1. **Load Learning Points**: Retrieves all learning points from Neo4j
2. **Extract Synset**: Gets WordNet synset ID from learning point metadata
3. **Find Synonyms/Antonyms**: Uses WordNet to find related words
4. **Match Learning Points**: Finds learning points in database for each synonym/antonym
5. **Create Relationships**: Creates `RELATED_TO` or `OPPOSITE_OF` relationships

---

## Relationship Types

### RELATED_TO (Synonyms)
- **Type**: `RELATED_TO`
- **Properties**: `{source: "wordnet", type: "synonym"}`
- **Direction**: Unidirectional (can be queried bidirectionally)

### OPPOSITE_OF (Antonyms)
- **Type**: `OPPOSITE_OF`
- **Properties**: `{source: "wordnet", type: "antonym"}`
- **Direction**: Unidirectional

---

## Example

For the word "good" (adjective):
- **Synset**: `good.a.01`
- **Synonyms**: "good", "nice"
- **Antonyms**: "bad", "evil"

If "nice" and "bad" exist in the database:
- Creates: `good_a1` → `RELATED_TO` → `nice_a1`
- Creates: `good_a1` → `OPPOSITE_OF` → `bad_a1`

---

## Notes

1. **Requires Populated Learning Points**: Run `populate_learning_points.py` first
2. **Matches Only Existing Words**: Only creates relationships if both words exist in database
3. **Skips Duplicates**: Automatically skips if relationship already exists
4. **Metadata Required**: Learning points must have `synset_id` in metadata

---

## Verification Queries

After population, verify relationships in Neo4j:

```cypher
// Count all relationships
MATCH ()-[r]->()
RETURN type(r) as rel_type, count(r) as count
ORDER BY count DESC

// Get relationships for a specific word
MATCH (lp:LearningPoint {word: "good"})-[r]-(related:LearningPoint)
RETURN lp.word, type(r), related.word
LIMIT 20

// Count relationships by type
MATCH ()-[r:RELATED_TO]->()
RETURN count(r) as synonym_count

MATCH ()-[r:OPPOSITE_OF]->()
RETURN count(r) as antonym_count
```

---

## Expected Results

With ~5,000 learning points:
- **Synonym relationships**: ~10,000-20,000 (many words share synonyms)
- **Antonym relationships**: ~2,000-5,000 (fewer words have clear antonyms)

**Note**: Actual counts depend on:
- How many words have synonyms/antonyms in WordNet
- How many synonyms/antonyms are also in the word list
- WordNet coverage for the specific words

---

## Troubleshooting

### No Relationships Created
- **Check**: Are learning points populated? Run `populate_learning_points.py` first
- **Check**: Do learning points have `synset_id` in metadata?
- **Check**: Are synonyms/antonyms in the word list? (WordNet might have synonyms not in our list)

### Low Relationship Count
- **Normal**: Not all words have synonyms/antonyms in WordNet
- **Normal**: Synonyms might not be in the word list
- **Solution**: Run with full population for better coverage

### Performance
- **Large datasets**: Use `--word-limit` for testing
- **Incremental**: Can run multiple times (skips duplicates)

---

## Future Enhancements

1. **Morphological Relationships**: Prefix/suffix patterns
2. **Collocation Relationships**: Common word pairs from corpus
3. **Prerequisite Relationships**: Based on CEFR levels and frequency
4. **Part-of Relationships**: Words that are part of phrases/idioms
5. **Hypernym/Hyponym**: WordNet hierarchical relationships

---

## Files

- **Script**: `backend/scripts/populate_relationships.py`
- **CRUD Functions**: `backend/src/database/neo4j_crud/relationships.py`
- **Relationship Types**: `backend/src/models/learning_point.py` (RelationshipType class)

---

**Ready to use after learning points are populated!** 🚀


