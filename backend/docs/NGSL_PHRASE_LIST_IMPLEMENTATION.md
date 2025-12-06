# NGSL Phrase List Implementation

**Status:** ⚠️ **Partially Implemented** - Uses WordNet lemmas instead of NGSL phrase list  
**Last Updated:** December 2024

---

## Overview

The documentation mentions using **NGSL Phrase List** for collocations and phrases, but the current implementation actually extracts phrases from **WordNet lemmas** rather than a separate NGSL phrase database. This document explains how phrases are currently implemented and how NGSL phrase list could be integrated.

---

## Current Implementation

### 1. Phrase Extraction (Structure Mining Phase)

**File:** `backend/src/structure_miner.py`

Phrases are extracted from **WordNet synset lemmas** during structure mining:

```python
def get_skeletons(word_text: str, limit: int = 3) -> list:
    """
    Fetches and filters synsets for a word.
    Returns a list of dicts: {sense_id, definition, pos, lemma_names, skeleton_phrases}
    """
    synsets = wn.synsets(word_text)
    
    skeletons = []
    for syn in synsets[:limit]:
        # Extract lemmas
        lemmas = [l.name().replace('_', ' ') for l in syn.lemmas()]
        
        # Identify phrases (multi-word lemmas)
        # These serve as "Skeleton Phrases" for the Agent to map
        skeleton_phrases = [lemma for lemma in lemmas 
                           if ' ' in lemma and word_text.lower() in lemma.lower()]
        
        skeletons.append({
            "id": sense_id,
            "definition": syn.definition(),
            "pos": syn.pos(),
            "lemmas": lemmas,
            "skeleton_phrases": skeleton_phrases  # ← Stored here
        })
    
    return skeletons
```

**How it works:**
1. Gets WordNet synsets for a word
2. Extracts all lemmas from each synset
3. Filters for multi-word lemmas (phrases) that contain the target word
4. Stores as `skeleton_phrases` on the Sense node

**Example:**
- Word: "run"
- WordNet lemmas: ["run", "running", "run out of", "run into"]
- `skeleton_phrases`: ["run out of", "run into"] (multi-word phrases)

---

### 2. Phrase Storage in Neo4j

**Schema:**
```cypher
(:Sense {
    skeleton_phrases: List[String]  // Temporary: from WordNet
})

(:Phrase {
    text: String                   // The phrase itself
})

(:Word)-[:HAS_SENSE]->(:Sense)
(:Phrase)-[:MAPS_TO_SENSE]->(:Sense)
(:Phrase)-[:ANCHORED_TO]->(:Word)
```

**Storage Process:**

1. **Temporary Storage** (Structure Mining):
   - `skeleton_phrases` stored as property on `(:Sense)` node
   - Source: WordNet lemmas

2. **Permanent Storage** (Content Generation):
   - `(:Phrase)` nodes created by the Agent
   - Linked to specific senses via `[:MAPS_TO_SENSE]`
   - Anchored to words via `[:ANCHORED_TO]`

**File:** `backend/src/agent.py`

```python
def update_graph(conn: Neo4jConnection, enriched_senses: list):
    # 3. Create Phrase Nodes (Maps To Sense)
    query_phrases = """
    UNWIND $data AS row
    MATCH (s:Sense {id: row.sense_id})<-[:HAS_SENSE]-(w:Word)
    WITH s, w, row
    UNWIND row.mapped_phrases AS phrase_text
    MERGE (p:Phrase {text: phrase_text})
    MERGE (p)-[:MAPS_TO_SENSE]->(s)
    MERGE (p)-[:ANCHORED_TO]->(w)
    """
    session.run(query_phrases, data=enriched_senses)
```

**What happens:**
1. Agent receives `skeleton_phrases` from Sense nodes
2. Agent maps phrases to correct senses (or suggests new collocations)
3. Creates `(:Phrase)` nodes in Neo4j
4. Links phrases to senses and anchor words

---

### 3. Phrase Usage in Content Generation

**File:** `backend/src/agent_stage2.py`

Phrases are fetched and used in Level 2 content generation:

```python
# Fetch phrases for a sense
query = """
MATCH (w:Word)-[:HAS_SENSE]->(s:Sense)
WHERE s.enriched = true 
  AND (s.stage2_enriched IS NULL OR s.stage2_enriched = false)
OPTIONAL MATCH (s)<-[:MAPS_TO_SENSE]-(p:Phrase)
WITH w, s, collect(DISTINCT p.text) as phrases
RETURN ...
"""

# Use in prompt
if phrases:
    context_sections.append(f"\nCommon Phrases for this sense:")
    context_sections.append(f"  {', '.join(phrases[:5])}")
    context_sections.append("  → Consider using these phrases in examples if natural")
```

**Purpose:**
- Provides context to Gemini API for generating natural examples
- Ensures examples use common collocations
- Improves example quality and authenticity

---

## Current Data Sources

### ✅ WordNet (Currently Used)

**Source:** NLTK WordNet corpus  
**Type:** Semantic database  
**What we extract:**
- Multi-word lemmas (phrases)
- Example: "run out of", "make up", "break down"

**Limitations:**
- Limited to phrases in WordNet
- May miss common collocations not in WordNet
- Not specifically exam-focused

### ⚠️ NGSL Phrase List (Mentioned but Not Implemented)

**Source:** New General Service List - Phrase component  
**Type:** Academic phrase database  
**Status:** Mentioned in documentation but not actually used

**What it would provide:**
- Academically validated phrase list
- Common collocations indexed by anchor word
- Exam-relevant expressions
- Examples: "run out of" → anchored to "run", "make up" → anchored to "make"

**Why not implemented:**
- No actual NGSL phrase file found in codebase
- Current implementation uses WordNet lemmas instead
- May require separate download/integration

---

## NGSL Data Files

**Found in codebase:**
- `data/source/ngsl.csv` - Contains word frequency rankings only
  - Format: `word,ngsl_rank`
  - Example: `bank,1`, `money,2`, `interest,3`
  - **Does NOT contain phrases**

**Missing:**
- NGSL Phrase List file (not found in codebase)
- Would need to be downloaded from NGSL website

---

## Implementation Flow

### Current Flow (WordNet-based)

```
1. Structure Mining (structure_miner.py)
   └─> Extract WordNet synsets
       └─> Get lemmas
           └─> Filter multi-word lemmas → skeleton_phrases
               └─> Store on Sense node

2. Content Generation (agent.py)
   └─> Read skeleton_phrases from Sense
       └─> Agent maps phrases to senses
           └─> Create (:Phrase) nodes
               └─> Link via [:MAPS_TO_SENSE] and [:ANCHORED_TO]

3. Level 2 Content (agent_stage2.py)
   └─> Fetch phrases from Neo4j
       └─> Include in prompt context
           └─> Generate natural examples using phrases
```

### Proposed Flow (NGSL-based)

```
1. Data Preparation
   └─> Download NGSL Phrase List
       └─> Parse phrase list
           └─> Index by anchor word

2. Structure Mining (enhanced)
   └─> Extract WordNet synsets (as before)
       └─> ALSO: Look up NGSL phrases for anchor word
           └─> Merge WordNet + NGSL phrases
               └─> Store on Sense node

3. Content Generation (same as current)
   └─> Agent maps phrases to senses
       └─> Create (:Phrase) nodes
```

---

## How to Integrate NGSL Phrase List

### Step 1: Download NGSL Phrase List

**Source:** http://www.newgeneralservicelist.org/  
**Expected format:** CSV or text file with phrases and anchor words

### Step 2: Create Phrase Loader Script

**File:** `backend/scripts/load_ngsl_phrases.py`

```python
def load_ngsl_phrases(ngsl_phrase_file: str, conn: Neo4jConnection):
    """
    Load NGSL phrases into Neo4j.
    Creates (:Phrase) nodes and links to anchor words.
    """
    with conn.get_session() as session:
        # Parse NGSL phrase file
        phrases_by_word = parse_ngsl_phrases(ngsl_phrase_file)
        
        # For each anchor word
        for word, phrases in phrases_by_word.items():
            # Find Word node
            # Create Phrase nodes
            # Link to appropriate senses
            pass
```

### Step 3: Enhance Structure Miner

**File:** `backend/src/structure_miner.py`

```python
def get_skeletons(word_text: str, limit: int = 3, ngsl_phrases: dict = None) -> list:
    """
    Enhanced to include NGSL phrases.
    """
    # ... existing WordNet extraction ...
    
    # Add NGSL phrases if available
    if ngsl_phrases and word_text in ngsl_phrases:
        for phrase in ngsl_phrases[word_text]:
            # Add to skeleton_phrases
            pass
```

### Step 4: Update Documentation

- Clarify that NGSL phrase list is optional enhancement
- Document WordNet as primary source
- Explain how to integrate NGSL phrases

---

## Current Status Summary

| Component | Status | Source |
|-----------|--------|--------|
| **Phrase Extraction** | ✅ Implemented | WordNet lemmas |
| **Phrase Storage** | ✅ Implemented | Neo4j (:Phrase) nodes |
| **Phrase Mapping** | ✅ Implemented | Agent maps to senses |
| **Phrase Usage** | ✅ Implemented | Level 2 content generation |
| **NGSL Phrase List** | ❌ Not Implemented | Mentioned in docs only |
| **NGSL Word List** | ✅ Used | `data/source/ngsl.csv` (rankings only) |

---

## Recommendations

### ✅ **RECOMMENDED: Option 3 - Hybrid Approach (Deferred to Post-MVP)**

**Decision:** Keep current WordNet-based implementation, plan NGSL integration for after MVP completion.

**Rationale:**
1. **Current system is functional** - 6,319 phrases, 3,125 senses covered
2. **Higher priorities** - Learning interface, MCQ generator, verification system are more critical
3. **Low risk** - Current approach works; NGSL can be added incrementally
4. **Better ROI** - Focus development on core features first

**Implementation Plan:**
- **Phase 1 (Now):** Keep WordNet phrases, focus on MVP features
- **Phase 2 (Post-MVP):** Integrate NGSL phrases as enhancement
- **Strategy:** Merge WordNet + NGSL, backward compatible

**See:** `backend/docs/NGSL_PHRASE_INTEGRATION_TASKS.md` for detailed task list

---

### Option 1: Keep Current Implementation (WordNet-based)

**Pros:**
- Already working
- No additional data files needed
- Integrated with WordNet structure

**Cons:**
- Limited to WordNet phrases
- May miss exam-relevant collocations
- Not specifically validated for learning

### Option 2: Integrate NGSL Phrase List (Future)

**Pros:**
- Academically validated
- Exam-relevant expressions
- Better coverage of common collocations

**Cons:**
- Requires downloading NGSL phrase file
- Need to merge with WordNet phrases
- Additional maintenance
- Lower priority than core MVP features

---

## Related Files

- `backend/src/structure_miner.py` - Phrase extraction
- `backend/src/agent.py` - Phrase mapping and storage
- `backend/src/agent_stage2.py` - Phrase usage in content generation
- `data/source/ngsl.csv` - NGSL word rankings (not phrases)
- `docs/development/LEARNING_POINT_CLOUD_CONSTRUCTION_PLAN.md` - Documentation mentioning NGSL phrases

---

## Conclusion

The current implementation uses **WordNet lemmas** for phrase extraction, not a separate NGSL phrase list. The NGSL phrase list is mentioned in documentation but not actually integrated. The system works well with WordNet phrases, but integrating NGSL phrases would provide additional exam-relevant collocations.

