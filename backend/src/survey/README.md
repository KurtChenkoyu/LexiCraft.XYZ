# LexiSurvey Survey Module

## Adversary Builder

The `adversary_builder.py` script implements the "Hunter" logic (V7.1) to create `CONFUSED_WITH` relationships in Neo4j.

### Usage

```bash
# Basic usage (processes words with rank <= 4000)
python -m src.survey.adversary_builder

# Custom max rank
python -m src.survey.adversary_builder 2000

# Dry run (see what would be created without writing)
python -m src.survey.adversary_builder 4000 --dry-run
```

### Hunter Filters

1. **Filter A (Morphology)**: Levenshtein Distance <= 2
   - Finds look-alike words (e.g., adapt/adopt, affect/effect)
   
2. **Filter B (Phonetic)**: Sound-alike detection (optional)
   - Requires `Fuzzy` library
   - Finds words that sound similar
   
3. **Filter C (Semantic)**: Existing RELATED_TO relationships
   - Flags semantically related words as potential traps
   - Examples: words that are synonyms but commonly confused

### Output

Creates `[:CONFUSED_WITH]` relationships with properties:
- `reason`: "Look-alike", "Sound-alike", or "Semantic"
- `distance`: Levenshtein distance between words
- `source`: "adversary_builder_v7.1"

### Dependencies

- `python-Levenshtein`: Required for distance calculation
- `Fuzzy`: Optional, for phonetic matching

Install with:
```bash
pip install python-Levenshtein Fuzzy
```

