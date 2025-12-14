# Relationship Model Improvement Plan

## Current State Analysis

### Current Problems

1. **RELATED_TO relationships are thin and ill-defined**:
   - All WordNet lemmas in same synset treated as synonyms (but they're not always true synonyms)
   - Relationships at Word level, not Sense level (mixing different meanings)
   - No quality scoring or relationship strength
   - No distinction between true synonyms vs. related concepts
   - Example: "bank" (financial) might connect to "shore" (from river sense)

2. **Graph Connectivity Issues**:
   - Only 29.3% average reachability between words
   - Average 5.95 hops to reach other words
   - Many isolated words (0% reachable)
   - Impacts connection-building algorithm effectiveness

3. **Missing Relationship Types**:
   - Morphological relationships (prefixes/suffixes) - **designed but not implemented**
   - Hypernyms/hyponyms (conceptual hierarchies) - **not implemented**
   - Meronyms/holonyms (part-whole) - **not implemented**
   - Entailments (verb relationships) - **not implemented**
   - Derivationally related forms - **not implemented**

## Current Schema (V6.1)

**Nodes:**
- `(:Word)` - 3,500 nodes
- `(:Sense)` - 8,873 nodes

**Relationships:**
- `(:Word)-[:HAS_SENSE]->(:Sense)` - 8,873 relationships
- `(:Word)-[:OPPOSITE_TO]->(:Word)` - 489 relationships
- `(:Word)-[:RELATED_TO]->(:Word)` - 3,956 relationships (problematic)

## Improvement Plan

### Relationship Milestone 1: Fix RELATED_TO Relationships (Priority 1) ✅

**Status**: Code created (`relationship_miner.py`), needs to be run

**Changes**:
1. **Sense-specific relationships** (not word-level)
   - `(:Sense)-[:SYNONYM_OF]->(:Sense)` - True synonyms (same synset)
   - `(:Sense)-[:CLOSE_SYNONYM]->(:Sense)` - Very similar (similarity >= 0.8)
   - `(:Sense)-[:RELATED_TO]->(:Sense)` - Related concepts (similarity 0.6-0.8)

2. **Quality scoring** (0.0-1.0):
   - 40% semantic similarity (WordNet path similarity)
   - 30% same synset bonus
   - 20% part of speech matching
   - 10% frequency rank similarity
   - Only relationships with quality >= 0.6 are created

3. **Backward compatibility**:
   - Creates aggregated `(:Word)-[:RELATED_TO]->(:Word)` relationships
   - All existing queries continue to work
   - Adds quality metadata: `avg_quality`, `relationship_count`, `types`

**Files**:
- `backend/src/relationship_miner.py` - New improved miner
- `backend/RELATIONSHIP_MODEL_IMPROVEMENTS.md` - Documentation
- `backend/RELATIONSHIP_QUERY_EXAMPLES.md` - Query examples

**Action**: Run `python src/relationship_miner.py 0.6`

---

### Relationship Milestone 2: Add Morphological Relationships (Priority 2) ⏳

**Status**: Designed but not implemented

**What to Add**:
1. **Derivationally Related Forms** (WordNet):
   - Use `lemma.derivationally_related_forms()`
   - Find word families: "happy" → "happiness", "happily", "unhappy"

2. **Prefix/Suffix Detection**:
   - Detect common prefixes: "un-", "in-", "re-", "pre-", etc.
   - Detect common suffixes: "-ness", "-ly", "-tion", "-ed", "-ing", etc.
   - Create relationships: `(:Word)-[:HAS_PREFIX]->(:Word)` or `(:Word)-[:HAS_SUFFIX]->(:Word)`

3. **Schema**:
   ```cypher
   (:Word)-[:DERIVED_FROM]->(:Word)  // Word families
   (:Word)-[:HAS_PREFIX {prefix: "un-"}]->(:Word)  // Prefix relationships
   (:Word)-[:HAS_SUFFIX {suffix: "-ness"}]->(:Word)  // Suffix relationships
   ```

**Benefits**:
- Learn word families together
- Better graph connectivity
- Natural learning paths
- Already in connection-building algorithm design

**Action**: Create `morphological_miner.py` using WordNet's `derivationally_related_forms()`

---

### Relationship Milestone 3: Add Conceptual Hierarchies (Priority 3) ⏳

**Status**: Not implemented

**What to Add**:
1. **Hypernyms** (more general):
   - "dog" → "canine" → "animal" → "living_thing"
   - Schema: `(:Sense)-[:HYPERNYM_OF]->(:Sense)`

2. **Hyponyms** (more specific):
   - "animal" → "dog", "cat", "bird", "fish"
   - Schema: `(:Sense)-[:HYPONYM_OF]->(:Sense)`

3. **Benefits**:
   - Build conceptual hierarchies
   - Natural learning paths (general → specific)
   - Better connection-building algorithm

**Action**: Extend `relationship_miner.py` to include hypernyms/hyponyms

---

### Relationship Milestone 4: Add Part-Whole Relationships (Priority 4) ⏳

**Status**: Not implemented

**What to Add**:
1. **Meronyms** (parts):
   - "car" → "wheel", "engine", "door"
   - Schema: `(:Sense)-[:HAS_PART]->(:Sense)`

2. **Holonyms** (wholes):
   - "wheel" → "car", "bicycle"
   - Schema: `(:Sense)-[:PART_OF]->(:Sense)`

**Benefits**:
   - Learn vocabulary in groups
   - Useful for technical vocabulary
   - Better connection-building

**Action**: Extend `relationship_miner.py` to include meronyms/holonyms

---

### Relationship Milestone 5: Add Verb Relationships (Priority 5) ⏳

**Status**: Not implemented

**What to Add**:
1. **Entailments**:
   - "snore" entails "sleep"
   - "buy" entails "pay"
   - Schema: `(:Sense)-[:ENTAILS]->(:Sense)`

**Benefits**:
   - Understand verb relationships
   - Natural collocations
   - Advanced learning

**Action**: Extend `relationship_miner.py` to include entailments

---

## Implementation Order

### Step 1: Run Improved Relationship Miner (Immediate)
```bash
cd backend
source venv/bin/activate
python src/relationship_miner.py 0.6
```

**Expected Results**:
- ~2,000-2,500 quality-filtered relationships (down from 3,956)
- Sense-specific relationships
- Quality scores on all relationships
- Backward-compatible word-level relationships

### Step 2: Create Morphological Miner (Next)
- Create `backend/src/morphological_miner.py`
- Use WordNet's `derivationally_related_forms()`
- Detect prefix/suffix patterns
- Create DERIVED_FROM, HAS_PREFIX, HAS_SUFFIX relationships

### Step 3: Extend Relationship Miner (Future)
- Add hypernyms/hyponyms
- Add meronyms/holonyms
- Add entailments

### Step 4: Update Queries (Gradual)
- Update `agent_stage2.py` to use sense-specific relationships
- Update connection-building algorithm to prioritize new relationship types
- Add quality filters to existing queries

---

## Expected Improvements

### Graph Connectivity
- **Current**: 29.3% average reachability, 5.95 hops
- **After Milestone 1**: Better quality, but similar connectivity
- **After Milestone 2**: Significantly improved (morphological relationships add many connections)
- **After Milestones 3-5**: Much better connectivity (conceptual hierarchies, part-whole, verb relationships)

### Relationship Quality
- **Current**: All relationships equal, no filtering
- **After**: Quality-scored, filtered, type-distinguished

### Learning Path Quality
- **Current**: May suggest weakly related words
- **After**: Better suggestions based on relationship types and quality

---

## Files to Create/Modify

### New Files
1. `backend/src/relationship_miner.py` ✅ (already created)
2. `backend/src/morphological_miner.py` ⏳ (needs creation)
3. `backend/RELATIONSHIP_MODEL_IMPROVEMENTS.md` ✅ (already created)
4. `backend/RELATIONSHIP_QUERY_EXAMPLES.md` ✅ (already created)

### Files to Update
1. `backend/src/agent_stage2.py` - Use sense-specific relationships
2. `backend/src/main_factory.py` - Integrate new miners
3. Connection-building algorithm queries - Use new relationship types

---

## Testing Strategy

1. **Verify Relationship Quality**:
   - Sample check: Are relationships semantically meaningful?
   - Quality score distribution: Are most relationships above 0.7?

2. **Verify Graph Connectivity**:
   - Re-run `analyze_word_paths.py`
   - Check if reachability improved
   - Check if average hops decreased

3. **Verify Backward Compatibility**:
   - All existing queries still work
   - Word-level RELATED_TO still queryable

---

## Success Metrics

- ✅ Relationships are sense-specific (not mixing meanings)
- ✅ Quality scores on all relationships
- ✅ Relationship types distinguished (SYNONYM_OF, CLOSE_SYNONYM, RELATED_TO)
- ✅ Morphological relationships created
- ✅ Graph connectivity improved (target: >50% reachability)
- ✅ All existing queries still work (backward compatible)

---

## Notes

- WordNet is the primary data source (already integrated)
- All improvements use existing WordNet features
- No external APIs needed for core relationships
- Morphological relationships can use WordNet's `derivationally_related_forms()`
- Consider adding external APIs (Datamuse, etc.) later for validation/enhancement

