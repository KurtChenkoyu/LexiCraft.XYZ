# Learning Point Cloud Construction Plan

**Purpose:** This document explains how we plan to construct the Learning Point Cloud (Neo4j knowledge graph) for second opinion review.

**Status:** 🚧 Planning Phase

**Version:** 2.0 (The "Graph Factory" Architecture)

---

## Overview

The Learning Point Cloud is a **pre-populated knowledge graph** (Neo4j) that serves as the source of truth for all learning relationships. It contains vocabulary words, phrases, grammar patterns, and morphological components with their relationships, organized by frequency and learning difficulty.

**Key Principle:** The Learning Point Cloud is PRE-POPULATED with ALL relationships. Agents query it to discover what to check—they don't create relationships.

### Architecture Philosophy: The "Graph Factory" ⭐ NEW

Moving from "on-demand generation" to **"pre-built knowledge"**:

1. **Pedagogical Accuracy**: Uses a "Double Skeleton" (WordNet + NGSL Phrases) to ensure content is academically sound and exam-relevant
2. **Verification Depth**: Incorporates an "Adversarial Layer" to map common mistakes and confusion points (e.g., Rise vs. Raise), enabling high-quality distractor generation
3. **Enterprise Performance**: Implements database-level optimizations (Indexing, Vector Search, Label Promotion) to ensure sub-10ms query times for mobile users

---

## Tech Stack ⭐ UPDATED

### Core Technologies

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Language** | Python 3.9+ | Pipeline processing |
| **AI Agent** | Gemini 2.5 Flash | Content enrichment, translation |
| **Database** | Neo4j AuraDB (Free Tier) or Dockerized Neo4j | Graph storage |
| **Data Models** | Pydantic | Strict JSON validation |
| **Libraries** | `pandas`, `google-generativeai`, `neo4j`, `tqdm`, `nltk`, `numpy` | Various utilities |

### Python Dependencies (`requirements.txt`)
```
pandas>=2.0.0
google-generativeai>=0.3.0
neo4j>=5.0.0
python-dotenv>=1.0.0
pydantic>=2.0.0
tqdm>=4.65.0
nltk>=3.8.0
numpy>=1.24.0
```

### Environment Variables (`.env`)
```
GEMINI_API_KEY=your_gemini_api_key
NEO4J_URI=neo4j+s://xxxxx.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_password
```

---

## Data Sources

### The "Double Skeleton" Approach ⭐ NEW

We use two foundational data sources to ensure **pedagogical accuracy**:

1. **WordNet** - Open-source semantic structure (avoids OED copyright, reduces AI hallucinations)
2. **NGSL Phrase List** - Exam-relevant phrases and collocations

This combination provides:
- Academic rigor from WordNet
- Practical exam relevance from NGSL
- Structured foundation before AI enrichment

---

### 1. Taiwan MOE 7000 Word List ⭐ NEW (Primary)

**Source:** Taiwan Ministry of Education official vocabulary list

**Why This Matters:**
- **THE** authoritative list for Taiwan exams (學測, 指考, 會考)
- Organized by difficulty levels (1-6)
- Parents and students recognize these benchmarks

**What we'll use:**
- 7,000 core vocabulary words
- Official MOE difficulty levels (1-6)
- Maps directly to Taiwan curriculum

**How we'll use it:**
- Master vocabulary list for Taiwan market
- Official difficulty rankings
- "Did they learn what school taught?" validation

**MVP Status:** ✅ Essential for Taiwan market positioning

---

### 2. NGSL Frequency List ⭐ NEW (Ranking)

**Source:** New General Service List (NGSL) - academic frequency research

**What we'll use:**
- Global frequency rankings (objective authority)
- ~2,800 high-frequency words covering 90%+ of English text
- Academic research-backed rankings

**Purpose:**
- Frequency rankings (objective authority)
- Prioritization for learning order
- Cross-reference with Taiwan MOE list

**How we'll use it:**
- Merge with Taiwan MOE list
- Rank words by frequency within MOE levels
- Prioritize common patterns first (80/20 principle)

**MVP Status:** ✅ Use for MVP - Academically validated

---

### 3. NGSL Phrase List ⭐ NEW (Collocations)

**Source:** New General Service List - Phrase component

**What we'll use:**
- Academically validated phrase list
- Common collocations indexed by anchor word
- Exam-relevant expressions

**Purpose:**
- Skeleton for phrase/collocation relationships
- Anchor phrases to their key words
- Map phrases to specific word senses

**Example:**
- "run out of" → Anchored to "run"
- "make up" → Anchored to "make"

**MVP Status:** ✅ Use for MVP - Essential for phrase relationships

---

### 4. N-gram Frequency Data (Historical Corpus) ⭐ MVP

**Source:** Google Books Ngram or similar corpus datasets

**What we'll use:**
- **Top 100K words:** ~10-20 MB (1-grams)
- **Top 1M bigrams:** ~100-200 MB (2-grams)
- **Practical subset:** 50-200 MB optimized for our needs

**Purpose:**
- Frequency rankings (objective authority)
- Collocation patterns (words that appear together)
- Genre-specific insights
- Time trends

**Limitations we're aware of:**
- Recency gap (most corpora end 2019-2020)
- Genre bias (books ≠ conversation)
- Context missing (frequency doesn't show meaning)
- Register mismatch (formal vs. conversational)

**How we'll use it:**
- Extract word frequency rankings
- Identify common collocations (bigrams, trigrams)
- Prioritize common patterns first (80/20 principle)
- Store frequency_rank as node attribute

**MVP Status:** ✅ Use for MVP - Fast, reliable, no API setup needed

---

### 2. YouTube Captions (Modern Corpus) ⚠️ PHASE 2 (NOT MVP)

**Source:** YouTube video captions (2024/2025 content)

**The Insight:**
When a user sends a 2-hour YouTube video to parse, GLAAS does the same thing as parsing corpus data—just without frequency understanding initially. When we process thousands of videos, frequency data emerges.

**Why NOT for MVP:**
- **Too complex:** Requires API setup, authentication, quota management
- **Too time-consuming:** 6-11 days development vs. 1-2 hours for existing corpus
- **Not essential:** Existing corpus data (Google 10K, COCA) sufficient for MVP validation
- **MVP goal:** Validate concept, not build perfect system

**Implementation Strategy (Phase 2):**

**Phase 2: Batch Processing**
- Parse thousands of YouTube videos
- Aggregate learning points
- Build frequency data
- Create Learning Point Cloud updates

**Phase 3: Continuous Updates**
- New videos added regularly
- Update frequency data
- Keep Learning Point Cloud current

**Benefits (Phase 2+):**
- **Recency:** 2024/2025 content (solves 2019 gap)
- **Authentic:** Real spoken English
- **Diverse:** Multiple registers (lectures, vlogs, tutorials)
- **Scalable:** Millions of videos available
- **Continuous:** Can update regularly
- **Practical:** Patterns learners actually encounter

**Register Tagging:**
- Use video categories for register tagging
- Simple 3-category model: "all", "formal", "informal"
- Tag patterns, not complex analysis

**MVP Status:** ❌ Skip for MVP - Add in Phase 2 after validation

---

### 3. Dictionary/Thesaurus Data (Relationships) ⭐ MVP

**Sources:**
- WordNet (semantic relationships: synonyms, hypernyms)
- COBUILD (collocations)
- Oxford/Cambridge APIs (definitions, some collocations)
- EVP (CEFR difficulty levels)

**What we'll extract:**
- Synonyms → `RELATED_TO` relationships
- Antonyms → `OPPOSITE_OF` relationships
- Collocations → `COLLOCATES_WITH` relationships
- CEFR levels → difficulty attributes on nodes
- Definitions → stored as node attributes

**MVP Status:** ✅ Use for MVP - Essential for relationships

---

## Graph Structure (Neo4j Schema V2) ⭐ UPDATED

### Schema Design Principles

The schema is optimized for:
1. **Query Speed** - Label promotion, proper indexing
2. **Learning Paths** ("Happy Paths") - Positive connections for learning
3. **Trap Paths** ("Adversarial Layer") - Confusion points for distractor generation

---

### Nodes

#### Word Node (Primary)
```cypher
(:Word {
  name: String,                  // The word itself (unique)
  ngsl_rank: Integer,            // NGSL frequency rank (if available)
  corpus_rank: Integer,          // N-gram/corpus rank (fallback)
  frequency_rank: Integer,       // Final normalized rank (used for queries)
  learning_priority: Integer,     // MOE-adjusted priority (lower = higher priority)
  is_moe_word: Boolean,          // Is this word in MOE 7000 list?
  moe_level: Integer,            // Taiwan MOE level (1-6)
  cefr: String,                  // "A1" | "A2" | "B1" | "B2" | "C1" | "C2"
  embedding: List<Float>         // Vector embedding for similarity search
})
```

**Frequency & Priority Fields:**
- `ngsl_rank`: Raw NGSL rank (1-2,800) if word exists in NGSL
- `corpus_rank`: Raw corpus rank (fallback for words not in NGSL)
- `frequency_rank`: Final normalized rank (1-100,000 scale, lower = more frequent)
- `learning_priority`: MOE-adjusted priority for Taiwan market
  - Formula: `learning_priority = frequency_rank * 0.8` (if `is_moe_word = true`)
  - Formula: `learning_priority = frequency_rank` (if `is_moe_word = false`)
  - Used for learning path prioritization (ensures MOE exam words appear earlier)

**Label Promotion (Performance)** ⭐ NEW:
- Words with `moe_level = 1` also get label `:Level1`
- Words with `moe_level = 2` also get label `:Level2`
- (Repeat for levels 1-6)
- **Why:** Filtering by Label is faster than filtering by Property

#### Sense Node (Polysemy Support)
```cypher
(:Sense {
  id: String,                    // WordNet synset ID
  def: String,                   // English definition (simplified)
  zh: String,                    // Traditional Chinese translation
  example: String,               // Modern example sentence
  pos: String                    // Part of speech
})
```

#### Phrase Node
```cypher
(:Phrase {
  text: String,                  // The phrase itself
  type: String                   // "collocation" | "idiom" | "phrasal_verb"
})
```

#### Root Node (Morphological)
```cypher
(:Root {
  text: String,                  // The root/prefix/suffix
  meaning: String                // What it means
})
```

#### Context Node
```cypher
(:Context {
  tag: String                    // "Business" | "Medical" | "Academic" | "Daily"
})
```

#### Question Node (Pre-generated MCQs)
```cypher
(:Question {
  text: String,                  // Question text
  options: List<String>,         // 6 answer options
  answer: Integer                // Correct answer index
})
```

---

### Relationships

#### Learning Relationships ("Happy Paths")
```cypher
// Word to Sense (Polysemy)
(:Word)-[:HAS_SENSE]->(:Sense)

// Phrase to Word (Anchor)
(:Phrase)-[:ANCHORED_TO]->(:Word)

// Phrase to Sense (Meaning)
(:Phrase)-[:MAPS_TO_SENSE]->(:Sense)

// Morphological
(:Word)-[:DERIVED_FROM]->(:Root)

// Context
(:Word)-[:USED_IN]->(:Context)
(:Sense)-[:USED_IN]->(:Context)
```

#### Collocation Relationships (Split by POS for Speed) ⭐ NEW
```cypher
// Typed collocations for faster queries
(:Sense)-[:COLLOCATES_NOUN]->(:Word)
(:Sense)-[:COLLOCATES_VERB]->(:Word)
(:Sense)-[:COLLOCATES_ADJ]->(:Word)
(:Sense)-[:COLLOCATES_ADV]->(:Word)
```

**Why Split by POS:**
- Faster queries (only traverse relevant relationship type)
- Better distractor generation (can find nouns that collocate)

#### Semantic Relationships
```cypher
(:Word)-[:RELATED_TO]->(:Word)      // Synonyms, similar concepts
(:Word)-[:OPPOSITE_TO]->(:Word)     // Antonyms
```

#### Adversarial Relationships ("Trap Layer") ⭐ NEW
```cypher
// Confusion mapping for distractor generation
(:Word)-[:CONFUSED_WITH {reason: "Sound"}]->(:Word)     // affect/effect
(:Word)-[:CONFUSED_WITH {reason: "Spelling"}]->(:Word)  // desert/dessert
(:Word)-[:CONFUSED_WITH {reason: "L1"}]->(:Word)        // False friends (Chinese)
(:Word)-[:CONFUSED_WITH {reason: "Usage"}]->(:Word)     // rise/raise
```

**Why This Matters:**
- High-quality MCQ distractors come from REAL confusion points
- Not random words, but words students ACTUALLY confuse
- Maps common errors for Taiwan students specifically

#### Prerequisite Relationships
```cypher
(:Word)-[:PREREQUISITE_OF]->(:Word)
(:Word)-[:PREREQUISITE_OF]->(:Phrase)
```

---

### Multi-hop Support
- 1-degree: Direct connections
- 2-degree: Through one intermediate node
- 3-degree: Through two intermediate nodes
- N-degree: Any depth traversal

---

## Construction Process: The "Graph Factory" Pipeline ⭐ UPDATED

### Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    GRAPH FACTORY PIPELINE                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Phase 0: Data Preparation                                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │ Taiwan MOE  │  │    NGSL     │  │    NGSL     │             │
│  │  7000 List  │  │  Frequency  │  │   Phrases   │             │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘             │
│         │                │                │                     │
│         └────────────────┼────────────────┘                     │
│                          ▼                                      │
│                 ┌────────────────┐                              │
│                 │ master_vocab   │                              │
│                 │ master_phrases │                              │
│                 └───────┬────────┘                              │
│                         │                                       │
├─────────────────────────┼───────────────────────────────────────┤
│                         ▼                                       │
│  Phase 1: Structure Extraction (WordNet Skeleton)               │
│  ┌──────────────────────────────────────────┐                   │
│  │  For each word:                          │                   │
│  │  - Fetch WordNet synsets                 │                   │
│  │  - Filter top 3-5 by lemma frequency     │                   │
│  │  - Create "Sense Skeletons"              │                   │
│  └──────────────────────┬───────────────────┘                   │
│                         │                                       │
├─────────────────────────┼───────────────────────────────────────┤
│                         ▼                                       │
│  Phase 2: Content Enrichment (Gemini Agent)                     │
│  ┌──────────────────────────────────────────┐                   │
│  │  AI as "Local Teacher":                  │                   │
│  │  - Simplify definitions                  │                   │
│  │  - Translate to Traditional Chinese      │                   │
│  │  - Create modern example sentences       │                   │
│  │  - Map NGSL phrases to senses            │                   │
│  │  - Generate MCQ per sense                │                   │
│  └──────────────────────┬───────────────────┘                   │
│                         │                                       │
├─────────────────────────┼───────────────────────────────────────┤
│                         ▼                                       │
│  Phase 3: Adversarial Layer (Trap Generator) ⭐ NEW             │
│  ┌──────────────────────────────────────────┐                   │
│  │  For each word, identify:                │                   │
│  │  - Look-alikes (Adapt/Adopt)             │                   │
│  │  - False friends (Chinese speakers)      │                   │
│  │  - Antonyms (Direct opposites)           │                   │
│  │  - Usage confusion (Rise/Raise)          │                   │
│  └──────────────────────┬───────────────────┘                   │
│                         │                                       │
├─────────────────────────┼───────────────────────────────────────┤
│                         ▼                                       │
│  Phase 4: Graph Injection (Neo4j Loader)                        │
│  ┌──────────────────────────────────────────┐                   │
│  │  - MERGE all nodes (idempotent)          │                   │
│  │  - Create "ghost nodes" for unprocessed  │                   │
│  │  - Link phrases to BOTH Word + Sense     │                   │
│  │  - Add adversarial relationships         │                   │
│  └──────────────────────┬───────────────────┘                   │
│                         │                                       │
├─────────────────────────┼───────────────────────────────────────┤
│                         ▼                                       │
│  Phase 5: Performance Engineering ⭐ NEW                        │
│  ┌──────────────────────────────────────────┐                   │
│  │  - Create indexes & constraints          │                   │
│  │  - Label promotion (Level1, Level2...)   │                   │
│  │  - Generate vector embeddings            │                   │
│  │  - Create vector index for similarity    │                   │
│  └──────────────────────────────────────────┘                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

### Phase 0: Data Preparation (The Foundation)

**Purpose:** Create curated lists before any AI processing

**File:** `src/data_prep.py`

**Cursor Prompt:**
```
Create a script src/data_prep.py.

Load the 'Taiwan MOE 7000 Word List' (CSV).
Load the 'NGSL Frequency List' (CSV).
Load the 'NGSL Phrase List' (CSV).

Merge Logic: Create a master_vocab.csv containing words present in MOE, 
ranked by NGSL frequency.

Create a master_phrases.csv containing phrases, indexed by their anchor word 
(e.g., 'run out of' -> 'run').
```

**Output Files:**
- `data/master_vocab.csv` - Words from MOE, ranked by NGSL frequency
- `data/master_phrases.csv` - Phrases indexed by anchor word

---

### Phase 0.5: Frequency Normalization & MOE Override ⭐ NEW

**Purpose:** Standardize frequency across sources and apply MOE priority boost for Taiwan market

**File:** `src/frequency_normalizer.py`

**Cursor Prompt:**
```
Create src/frequency_normalizer.py.

Function normalize_frequency(word, ngsl_rank, corpus_rank, moe_level, is_moe_word):
1. Priority: NGSL rank > Corpus rank > Default (50000)
2. Normalize corpus rank to NGSL scale (1-100,000)
   - If corpus has 100K words, map percentile to NGSL scale
   - Example: Corpus rank 5000 (top 5%) → NGSL scale ~1400
3. Calculate frequency_rank:
   - If ngsl_rank exists: frequency_rank = ngsl_rank
   - Else if corpus_rank exists: frequency_rank = normalize_corpus_rank(corpus_rank)
   - Else: frequency_rank = 50000 (low frequency default)
4. Calculate learning_priority (MOE Override):
   - If is_moe_word = true: learning_priority = frequency_rank * 0.8
   - Else: learning_priority = frequency_rank
5. Return: {frequency_rank, learning_priority, ngsl_rank, corpus_rank, is_moe_word}
```

**MOE Override Formula:**
```python
def calculate_learning_priority(frequency_rank, is_moe_word):
    """
    MOE words get 20% priority boost (rank becomes smaller = higher priority)
    This ensures Taiwan exam words appear earlier in learning paths,
    even if they're less frequent globally.
    """
    if is_moe_word:
        return int(frequency_rank * 0.8)  # Boost priority
    return frequency_rank
```

**Example:**
- Word: "insolvency"
- NGSL rank: 8000 (less frequent globally)
- MOE level: 3 (必考 - required for Taiwan exams)
- `is_moe_word = true`
- Result: 
  - `frequency_rank = 8000`
  - `learning_priority = 6400` (boosted by 20%)
- Effect: Even though "insolvency" is less frequent globally, it appears earlier in learning paths for Taiwan students because it's on the MOE exam list.

**Why This Matters:**
- Taiwan MOE 7000 is the "Bible" for Taiwan exams
- Some words are less frequent globally but critical for Taiwan curriculum
- MOE Override ensures exam-relevant words get priority in learning paths

---

### Phase 1: Structure Extraction (The Skeleton)

**Purpose:** Use open-source WordNet for structure (avoids copyright, reduces hallucinations)

**File:** `src/structure_miner.py`

**Cursor Prompt:**
```
Create src/structure_miner.py using nltk.

Function get_skeletons(word):
- Fetch WordNet synsets.
- Filter: Keep only top 3-5 synsets based on lemma frequency.
- Filter: Ensure the lemma name matches the target word.
- Return a list of 'Sense Skeletons' (ID + Raw Definition).
```

**Why WordNet:**
- Free and open-source
- Academically validated
- Provides sense disambiguation
- Avoids OED copyright issues
- Reduces AI hallucinations (structured source)

---

### Phase 2: Content Enrichment (The Gemini Agent)

**Purpose:** AI acts as the "Local Teacher" for Taiwan market

**File:** `src/agent.py`

**Cursor Prompt:**
```
Create src/agent.py. Use gemini-2.5-flash.

Use pydantic to define WordNode and SenseData models.

System Prompt:
'You are an expert EFL curriculum developer for Taiwan.
Input: Target Word, WordNet Senses, Skeleton Phrases.
Tasks:
1. Filter: Select only senses relevant to a CEFR B1/B2 learner.
2. Enrich: Rewrite definitions to be simple. 
   Provide Traditional Chinese translations. 
   Write modern example sentences.
3. Map Phrases: Assign provided Skeleton Phrases to the correct Sense.
4. Quiz: Generate 1 MCQ per sense to verify recognition.'

Return strict JSON.
```

**Pydantic Models (`models.py`):**
```python
from pydantic import BaseModel
from typing import List, Optional

class SenseData(BaseModel):
    id: str
    definition: str
    zh_translation: str
    example: str
    pos: str
    context: str

class WordAnalysis(BaseModel):
    word: str
    cefr: str
    moe_level: int
    definitions: List[SenseData]
    collocations: List[str]
    idioms: List[str]
    related_concepts: List[str]
    morphology: dict
```

---

### Phase 3: The Adversary (Trap Generator) ⭐ NEW

**Purpose:** Map confusion points for high-quality distractor generation

**File:** `src/adversary.py`

**Cursor Prompt:**
```
Create src/adversary.py.

System Prompt:
'You are a tricky English examiner specializing in Taiwan EFL.

Input: Target Word.

Task: Identify 3 types of confusion:
1. Look-alikes (e.g., Adapt/Adopt, Affect/Effect)
2. False Friends (Confusing for Chinese speakers)
3. Antonyms (Direct opposites)
4. Usage Confusion (e.g., Rise/Raise, Lay/Lie)

Return JSON with:
- target_word
- confused_words: [{word, reason, explanation}]
'
```

**Why This Matters:**
- High-quality MCQ distractors come from REAL confusion points
- "affect" vs "effect" is a better distractor than random word
- Maps common errors for Taiwan students specifically
- Enables 99.54% verification confidence

**Example Output:**
```json
{
  "target_word": "affect",
  "confused_words": [
    {"word": "effect", "reason": "Sound", "explanation": "Sound similar, different POS"},
    {"word": "impact", "reason": "Usage", "explanation": "Similar meaning, different register"}
  ]
}
```

---

### Phase 4: Graph Injection (The Loader)

**Purpose:** Load data into Neo4j with idempotent operations

**File:** `src/db_loader.py`

**Cursor Prompt:**
```
Create src/db_loader.py.

Write Cypher queries to load the data structure defined in our Schema.

Critical:
- Use MERGE for all nodes (idempotent - won't duplicate).
- When linking Phrases, create relationships to BOTH the Word (Anchor) 
  and the Sense (Meaning).
- Load Adversarial data as :CONFUSED_WITH relationships.
- If 'Bank' connects to 'Money', and 'Money' hasn't been analyzed yet, 
  create a 'ghost node' for Money. When the script eventually processes 
  'Money', it should fill in the details of that existing ghost node.
```

**Ghost Node Strategy:**
```cypher
// When processing "Bank", create ghost node for "Money" if not exists
MERGE (money:Word {name: "money"})
// Later, when processing "Money", fill in details
MATCH (money:Word {name: "money"})
SET money.frequency_rank = 500, 
    money.learning_priority = 400,  // If MOE word: 500 * 0.8
    money.moe_level = 1, 
    money.is_moe_word = true, ...
```

**Why Ghost Nodes:**
- Creates highly interconnected graph (not isolated star patterns)
- Relationships exist even before target word is processed
- Enables multi-hop queries from day one

---

### Frequency-Based Query Examples ⭐ NEW

**Query Logic (Correct - Use Properties, Not Relationships):**

```cypher
// Find neighbors of 'Bank', sorted by learning priority
// This ensures students see "Money" (priority 50) before "Insolvency" (priority 6400)
MATCH (bank:Word {name: "bank"})-[:RELATED_TO|COLLOCATES_WITH]-(neighbor:Word)
RETURN neighbor.name, neighbor.learning_priority, neighbor.frequency_rank
ORDER BY neighbor.learning_priority ASC
LIMIT 10
```

**Result:** Returns words in learning order - easy to hard, with MOE exam words prioritized.

**Query Logic (WRONG - Don't do this):**

```cypher
// ❌ DO NOT create frequency edges
MATCH (w:Word)-[:FREQUENCY_RANK]->(other:Word)
// This would make "the" (rank 1) connect to millions of words!
// This creates dense nodes and crashes the database.
```

**Why:** Frequency is a property, not a relationship. Use WHERE/ORDER BY instead.

**Learning Path Query:**
```cypher
// Get learning path: Start with easy words, progress to harder ones
MATCH (start:Word {name: "bank"})-[:RELATED_TO]-(next:Word)
WHERE next.learning_priority > start.learning_priority
  AND next.learning_priority < start.learning_priority + 1000
RETURN next
ORDER BY next.learning_priority ASC
LIMIT 5
```

---

### Phase 5: Performance Engineering ⭐ NEW

**Purpose:** Optimize for sub-10ms queries on mobile

**File:** `src/optimize_db.py`

**Cursor Prompt:**
```
Create src/optimize_db.py. This script runs AFTER data loading.

Task 1: Indexing
- Create constraints on unique IDs (Word.name, Sense.id).
- Create Fulltext indexes on definitions and Chinese text.

Task 2: Label Promotion (Speed Hack)
- Iterate through all Words.
- If w.moe_level = 1, execute SET w:Level1. (Repeat for levels 1-6).
- Reason: Filtering by Label is faster than filtering by Property.

Task 3: Vector Embeddings
- Connect to Gemini text-embedding-004.
- For each Word, generate a vector embedding.
- Save it to w.embedding.
- Create a Neo4j Vector Index for fast 'Related Word' discovery.

Task 4: Frequency Index ⭐ NEW
- Create index on frequency_rank and learning_priority.
- Enables fast queries: "Get top 10 most common words related to Bank"
- Example: CREATE INDEX word_frequency_idx FOR (w:Word) ON (w.frequency_rank, w.learning_priority)
```

**Performance Optimizations:**

1. **Indexing:**
   ```cypher
   CREATE CONSTRAINT word_name IF NOT EXISTS 
   FOR (w:Word) REQUIRE w.name IS UNIQUE;
   
   CREATE FULLTEXT INDEX definition_index IF NOT EXISTS 
   FOR (s:Sense) ON EACH [s.def, s.zh];
   ```

2. **Label Promotion:**
   ```cypher
   // Much faster to query MATCH (w:Level1) than 
   // MATCH (w:Word) WHERE w.moe_level = 1
   MATCH (w:Word) WHERE w.moe_level = 1 SET w:Level1;
   MATCH (w:Word) WHERE w.moe_level = 2 SET w:Level2;
   // ... repeat for all levels
   ```

3. **Vector Index:**
   ```cypher
   CREATE VECTOR INDEX word_embedding IF NOT EXISTS
   FOR (w:Word) ON w.embedding
   OPTIONS {indexConfig: {
     `vector.dimensions`: 768,
     `vector.similarity_function`: 'cosine'
   }};
   ```

4. **Frequency Index:** ⭐ NEW
   ```cypher
   CREATE INDEX word_frequency_idx IF NOT EXISTS
   FOR (w:Word) ON (w.frequency_rank, w.learning_priority);
   
   // This enables fast queries like:
   // "Get top 10 most common words related to Bank"
   // ORDER BY learning_priority ASC
   ```

---

### Phase 6: The Factory (Orchestrator)

**Purpose:** Tie everything together with error handling

**File:** `src/main_factory.py`

**Cursor Prompt:**
```
Create src/main_factory.py.

1. Load master_vocab.csv.
2. Loop through words (use tqdm for progress bar).
3. Pipeline: structure_miner -> agent -> adversary -> db_loader.
4. Batch Processing: Run 50 words, then commit, to manage memory.
5. Log errors to logs/failed.csv.
6. Skip words that already exist in Neo4j (save API costs).
```

**Error Handling:**
- Retry mechanism with exponential backoff for API calls
- Log failed words to `logs/failed.csv` for later retry
- Checkpoint progress every 50 words

---

### Legacy: Extract Learning Points from Corpus

**From N-grams (MVP):**
1. Parse n-gram datasets (top 100K words, top 1M bigrams)
2. Extract unique words and phrases
3. Calculate frequency rankings
4. Create initial node set

**From YouTube Captions (Phase 2):**
1. Extract captions from videos
2. Tokenize and identify learning points
3. Aggregate across videos to build frequency
4. Add to node set (merge with n-gram data)

**Output:** Set of learning point nodes with frequency_rank

---

### Step 2: Extract Relationships

**Morphological Relationships:**
- **Method:** Pattern matching + dictionary lookup
- **Process:**
  - Identify prefixes/suffixes (e.g., "in-", "-ed", "-ing")
  - Match words containing these components
  - Create `MORPHOLOGICAL` edges
  - Example: "indirect" → `MORPHOLOGICAL` → "in-" prefix

**Collocation Relationships:**
- **Method:** N-gram analysis (bigrams, trigrams) - MVP
- **Method (Phase 2):** YouTube caption analysis for modern collocations
- **Process:**
  - Extract common word pairs from corpus
  - Calculate co-occurrence frequency
  - Create `COLLOCATES_WITH` edges for high-frequency pairs
  - Example: "make" ↔ `COLLOCATES_WITH` ↔ "decision"

**Semantic Relationships:**
- **Method:** Dictionary/thesaurus APIs (WordNet, Oxford, Cambridge)
- **Process:**
  - Query synonyms → `RELATED_TO` edges
  - Query antonyms → `OPPOSITE_OF` edges
  - Query hypernyms/hyponyms → `RELATED_TO` edges
  - Example: "direct" ↔ `OPPOSITE_OF` ↔ "indirect"

**Part-of Relationships:**
- **Method:** Pattern matching + phrase analysis
- **Process:**
  - Identify phrases/idioms
  - Extract component words
  - Create `PART_OF` edges
  - Example: "beat" → `PART_OF` → "beat around the bush"

**Prerequisite Relationships:**
- **Method:** CEFR levels + learning_priority + morphological analysis
- **Process:**
  - Lower CEFR level → prerequisite of higher level
  - Higher learning_priority (lower rank number) → prerequisite of lower learning_priority
  - Component words → prerequisite of phrases
  - Example: "direct" → `PREREQUISITE_OF` → "indirect" (if "direct" is A1, "indirect" is A2)
- **Note:** Uses `learning_priority` (not just `frequency_rank`) to ensure MOE exam words are prioritized correctly

**Register Variants:**
- **Method (MVP):** Dictionary lookup
- **Method (Phase 2):** Dictionary lookup + YouTube video category analysis
- **Process:**
  - Identify formal/informal variants from dictionaries
  - Use YouTube video categories to tag register (Phase 2)
  - Create `REGISTER_VARIANT` edges
  - Example: "bush" → `REGISTER_VARIANT` → "shrub" (formal)

**Frequency-Based Prioritization (NOT Relationships):** ⭐ CRITICAL
- **Method:** Use node property `frequency_rank` and `learning_priority`
- **Critical:** DO NOT create frequency edges - this would create dense nodes
- **Process:**
  - Frequency is stored as node property only
  - Use Cypher WHERE clauses for filtering: `WHERE w.frequency_rank < 1000`
  - Use ORDER BY for sorting: `ORDER BY w.learning_priority ASC`
  - Example: "Find neighbors of 'Bank', return ORDER BY neighbor.learning_priority ASC"
- **Why:** Creating edges from "the" (rank 1) to all other words would crash the database
- **Correct Query Pattern:**
  ```cypher
  MATCH (bank:Word {name: "bank"})-[:RELATED_TO|COLLOCATES_WITH]-(neighbor:Word)
  RETURN neighbor
  ORDER BY neighbor.learning_priority ASC
  LIMIT 10
  ```

---

### Step 3: Add Metadata

**Difficulty Levels (CEFR):**
- Source: EVP (English Vocabulary Profile) or similar
- Map words to A1-C2 levels
- Store as `difficulty` attribute

**Definitions:**
- Source: Dictionary APIs (Oxford, Cambridge, etc.)
- Store as `definition` attribute

**Examples:**
- Source (MVP): Corpus data (n-grams)
- Source (Phase 2): Corpus data + YouTube captions
- Extract example sentences where word/phrase appears
- Store as `examples` array

**Context Tags:**
- Source: Manual tagging + pattern matching
- Examples: "idiomatic", "literal", "technical", "academic"
- Store as `contexts` array

---

### Step 4: Populate Neo4j Graph

**Process:**
1. Create nodes for all learning points
2. Create edges for all relationships
3. Index on `id`, `type`, `frequency_rank`, `difficulty`
4. Verify graph integrity (no orphaned nodes, valid relationships)

**Cypher Example:**
```cypher
// Create a learning point node
CREATE (lp:LearningPoint {
  id: "beat_around_the_bush",
  type: "idiom",
  content: "beat around the bush",
  frequency_rank: 5000,
  difficulty: "B2",
  register: "all",
  definition: "To avoid talking about something directly",
  examples: ["Stop beating around the bush and tell me what happened."],
  contexts: ["idiomatic"]
})

// Create relationships
MATCH (lp:LearningPoint {id: "beat_around_the_bush"})
MATCH (beat:LearningPoint {id: "beat"})
MATCH (bush:LearningPoint {id: "bush"})
MATCH (direct:LearningPoint {id: "direct"})
MATCH (indirect:LearningPoint {id: "indirect"})

CREATE (lp)-[:PART_OF]->(beat)
CREATE (lp)-[:PART_OF]->(bush)
CREATE (lp)-[:RELATED_TO]->(direct)
CREATE (lp)-[:RELATED_TO]->(indirect)
```

---

## Grammar Pattern Extraction

### Simplified Approach (80/20 Principle)

**Focus:** Core 5 tenses (80-90% of English usage)
1. Simple Present
2. Simple Past
3. Present Continuous
4. Future (going to/will)
5. Present Perfect

### Pattern Extraction Process

**From Corpus (MVP):**
1. Extract verb patterns from n-grams
2. Identify common patterns (e.g., "have been [verb]-ing")
3. Calculate frequency
4. Tag register from dictionaries

**From YouTube Captions (Phase 2):**
1. Extract verb patterns from YouTube captions
2. Identify common patterns
3. Calculate frequency
4. Tag register from video categories

**Pattern Structure:**
```cypher
(:GrammarPattern {
  id: "have_been_ing",
  pattern_formula: "have been [verb]-ing",
  frequency_rank: 500,
  difficulty: "intermediate",
  register: "all",
  prerequisites: ["have", "be", "-ing"],
  related_patterns: ["have done"],
  examples: ["I have been working here for 5 years."]
})
```

**Relationships:**
- Component words → `PREREQUISITE_OF` → grammar pattern
- Related patterns → `RELATED_TO` → grammar pattern

---

## Quality Assurance

### Validation Steps

1. **Node Completeness:**
   - All high-frequency words included (top 10K-50K)
   - All common phrases/collocations included
   - Morphological components (prefixes/suffixes) included

2. **Relationship Completeness:**
   - Morphological relationships for all prefix/suffix words
   - Collocation relationships for common pairs
   - Semantic relationships from dictionaries
   - Prerequisite relationships based on CEFR/frequency
   - **Adversarial relationships** for distractor generation ⭐ NEW

3. **Data Quality:**
   - Frequency rankings consistent across sources
   - **MOE override applied correctly** (learning_priority = frequency_rank * 0.8 for MOE words) ⭐ NEW
   - CEFR levels accurate
   - Definitions present for all words
   - Examples present for common patterns
   - **Traditional Chinese translations verified** ⭐ NEW

4. **Graph Integrity:**
   - No orphaned nodes
   - All relationships valid (source and target exist)
   - No circular prerequisites
   - **Frequency stored as properties only** (NO frequency edges created) ⭐ NEW
   - **Ghost nodes filled in** (no empty placeholders) ⭐ NEW

5. **Performance Validation:** ⭐ NEW
   - Sub-10ms query times for single word lookups
   - Sub-50ms for multi-hop traversals
   - Vector similarity search working
   - Label promotion indexes active

### Verification Checklist (Before Full Run)

**Run the script for 50 words first.** Don't process 8,000 immediately.

1. **Check Neo4j Bloom (Visualizer):**
   - Are "Bank" (Finance) and "Bank" (River) separated correctly?
   - Are confusion pairs linked (affect ↔ effect)?
   - Are phrases anchored to correct words?

2. **Check Polysemy Handling:**
   - "Bank" should have multiple `:Sense` nodes
   - Each sense should map to correct context
   - Phrases should link to specific sense, not just word

3. **Check Adversarial Layer:**
   - Common confusion pairs exist (rise/raise, affect/effect)
   - False friends for Chinese speakers identified
   - Antonyms properly linked

---

## Cost & Execution Strategy ⭐ NEW

### API Cost Estimates

| Component | Tokens/Word | Words | Total Tokens | Cost |
|-----------|-------------|-------|--------------|------|
| Gemini 2.5 Flash (Content) | ~500 | 8,000 | ~4M | ~$1.50 |
| Gemini 2.5 Flash (Adversary) | ~200 | 8,000 | ~1.6M | ~$0.50 |
| Gemini Embeddings | ~10 | 8,000 | ~80K | ~$0.10 |
| **Total** | | | ~5.7M | **~$2-3 USD** |

**Budget:** Under $5 USD for the entire 8,000-word dataset

### Execution Order

1. **Phase 0:** Run `data_prep.py` to get merged CSVs
2. **Phase 1-4:** Run `main_factory.py` on **small sample first** (50 words: "Bank", "Run", "Effect", etc.)
3. **Verify in Neo4j:**
   - Does "Bank" have confusion links (to "Bench" or "Bang")?
   - Are phrase links correct?
   - Are senses properly separated?
4. **Phase 5:** Run `optimize_db.py` to generate indexes and embeddings
5. **Full Scale:** Run on all 8,000 words (overnight batch job)

### Resource Requirements

| Resource | Requirement | Notes |
|----------|-------------|-------|
| **Neo4j** | AuraDB Free Tier (50K nodes) | Sufficient for MVP |
| **Gemini API** | Standard tier | ~$5 budget |
| **Compute** | Any laptop | Python scripts, not heavy compute |
| **Time** | 4-8 hours | For full 8,000 word processing |

---

## Phase Breakdown

### Phase 1: MVP (Current) ⭐

**Timeline:** 2-4 weeks

**Data Sources:**
- ✅ Taiwan MOE 7000 (primary word list) ⭐ NEW
- ✅ NGSL Frequency List (rankings) ⭐ NEW
- ✅ NGSL Phrase List (collocations) ⭐ NEW
- ✅ Google 10K (frequency backup)
- ✅ COCA (collocations backup)
- ✅ EVP (CEFR levels)
- ✅ WordNet (relationships + structure skeleton) ⭐ UPDATED
- ✅ Oxford/Cambridge APIs (definitions)
- ❌ YouTube Captions (skip for MVP)

**Scope:**
- Tier 1-2 only (~5,000 learning points)
- Basic relationships (morphological, collocations, semantic)
- **Adversarial Layer** (confusion mapping) ⭐ NEW
- Frequency from existing corpus
- Register from dictionaries only
- **Traditional Chinese translations** ⭐ NEW

**Pipeline Components:**
- ✅ Data Preparation (`data_prep.py`)
- ✅ Structure Extraction (`structure_miner.py`)
- ✅ Content Enrichment (`agent.py`)
- ✅ Adversary Generation (`adversary.py`)
- ✅ Graph Injection (`db_loader.py`)
- ✅ Performance Optimization (`optimize_db.py`)
- ✅ Orchestrator (`main_factory.py`)

**Why This Works:**
- Fast to implement (1-2 hours vs. 6-11 days)
- No API complexity
- Sufficient for MVP validation
- Can expand later
- **Low cost** (~$2-3 USD total) ⭐ NEW

---

### Phase 2: Expansion (After MVP Validation)

**Timeline:** 4-8 weeks

**Add:**
- ✅ YouTube Caption Processing
- ✅ Modern frequency data (2024/2025)
- ✅ Register tagging from video categories
- ✅ Tier 3-7 (phrases, idioms, advanced contexts)
- ✅ Expand to ~13,700 learning points

**YouTube Implementation:**
- YouTube Data API setup
- Caption extraction pipeline
- Batch processing (thousands of videos)
- Frequency aggregation
- Register tagging from categories

---

### Phase 3: Continuous Updates (Ongoing)

**Timeline:** Ongoing

**Process:**
- Regular YouTube caption processing
- Periodic updates from dictionaries
- Version control for graph changes
- Keep frequency data current

---

## Open Questions / Areas for Second Opinion

### 1. Relationship Extraction Methods ✅ RESOLVED

**Resolution:** Use "Double Skeleton" approach:
- **WordNet** for semantic structure (open source, validated)
- **NGSL Phrase List** for collocations (academically validated)
- **Gemini Agent** for enrichment (translations, examples)
- **Adversary Agent** for confusion mapping (distractors)

**Validation:** LLMs (Gemini) used for enrichment, not extraction. Structure comes from authoritative sources.

---

### 2. Prerequisite Relationship Logic

**Question:** How should we determine prerequisites?

**Current Plan:**
- Lower CEFR level → prerequisite of higher level
- More frequent → prerequisite of less frequent
- Component words → prerequisite of phrases
- **Taiwan MOE level alignment** ⭐ NEW

**Concerns:**
- Is CEFR level alone sufficient?
- Should we consider semantic complexity?
- How to handle cases where prerequisites aren't clear?

---

### 3. Scale and Performance ✅ RESOLVED

**Resolution:** Use performance engineering:
- **Label Promotion** - `:Level1`, `:Level2` labels for fast filtering
- **Vector Index** - Embeddings for similarity search
- **Proper Indexing** - Constraints and fulltext indexes
- **Neo4j AuraDB** - Cloud-hosted, free tier sufficient for MVP

**Expected Performance:**
- Sub-10ms single word queries
- Sub-50ms multi-hop traversals
- 50K nodes free tier is sufficient

---

### 4. Data Source Integration ✅ RESOLVED

**Resolution:** Clear priority order:
1. **Taiwan MOE 7000** - Primary word list (authoritative for Taiwan)
2. **NGSL Frequency** - Ranking within MOE levels
3. **NGSL Phrases** - Skeleton for collocations
4. **WordNet** - Semantic structure
5. **Gemini** - Enrichment only (not authoritative)

**Conflict Resolution:**
- MOE level takes precedence over CEFR
- NGSL frequency for ranking
- WordNet for polysemy structure

---

### 5. Relationship Validation

**Question:** How to ensure relationship quality?

**Current Plan:**
- **50-word pilot** before full run ⭐ NEW
- Manual review of high-frequency relationships
- Automated checks for graph integrity
- Validation against known dictionaries
- Check polysemy separation in Neo4j Bloom

**Concerns:**
- How to handle edge cases?
- How to measure relationship accuracy?

---

### 6. Continuous Updates

**Question:** How to keep the graph current?

**Current Plan:**
- MVP: Static corpus data (sufficient for validation)
- Phase 2: Regular YouTube caption processing
- Periodic updates from dictionaries
- Version control for graph changes

**Concerns:**
- How often to update?
- How to handle deprecated relationships?
- How to version the graph?

---

### 7. Adversarial Layer Coverage ⭐ NEW

**Question:** How comprehensive should confusion mapping be?

**Current Plan:**
- Gemini-generated confusion pairs
- Focus on Taiwan-specific false friends
- Include sound-alikes, look-alikes, usage confusion

**Concerns:**
- Should we manually curate confusion pairs for high-frequency words?
- How to validate confusion pairs are actually confusing?
- Should we collect confusion data from actual user errors?

---

## Example: Complete Construction Flow

### For "beat around the bush" idiom:

**Step 1: Extract from Corpus (MVP)**
- Found in n-grams (frequency_rank: 5000)
- Tagged as idiom, register: "all" (from dictionary)

**Step 1: Extract from Corpus (Phase 2)**
- Found in YouTube captions (frequency: medium)
- Found in n-grams (frequency_rank: 5000)
- Tagged as idiom, register: "all" (from video categories)

**Step 2: Extract Relationships**
- `PART_OF`: "beat", "around", "bush" (component words)
- `RELATED_TO`: "direct", "indirect" (semantic from dictionary)
- `MORPHOLOGICAL`: "indirect" → "in-" prefix (pattern matching)
- `OPPOSITE_OF`: "direct" ↔ "indirect" (dictionary)

**Step 3: Add Metadata**
- CEFR level: B2 (from EVP)
- Definition: "To avoid talking about something directly" (dictionary)
- Examples: ["Stop beating around the bush..."] (from corpus)

**Step 4: Create Neo4j Nodes and Edges**
```cypher
// Create idiom node
CREATE (idiom:LearningPoint {
  id: "beat_around_the_bush",
  type: "idiom",
  content: "beat around the bush",
  frequency_rank: 5000,
  difficulty: "B2",
  register: "all",
  definition: "To avoid talking about something directly",
  examples: ["Stop beating around the bush and tell me what happened."]
})

// Create component word nodes (if not exist)
CREATE (beat:LearningPoint {id: "beat", type: "word", ...})
CREATE (bush:LearningPoint {id: "bush", type: "word", ...})
CREATE (direct:LearningPoint {id: "direct", type: "word", ...})
CREATE (indirect:LearningPoint {id: "indirect", type: "word", ...})
CREATE (in_prefix:LearningPoint {id: "in-", type: "prefix", ...})

// Create relationships
CREATE (idiom)-[:PART_OF]->(beat)
CREATE (idiom)-[:PART_OF]->(bush)
CREATE (idiom)-[:RELATED_TO]->(direct)
CREATE (idiom)-[:RELATED_TO]->(indirect)
CREATE (indirect)-[:MORPHOLOGICAL {type: "prefix"}]->(in_prefix)
CREATE (direct)-[:OPPOSITE_OF]->(indirect)
```

---

## Technology Stack

**MVP:**
- **Graph Database:** Neo4j AuraDB (Free Tier) or Neo4j Community Edition
- **Hosting:** Neo4j AuraDB (cloud-hosted) or self-hosted
- **Data Processing:** Python scripts ("Graph Factory" pipeline)
- **AI Agent:** Gemini 2.5 Flash (content enrichment, adversary generation)
- **APIs:** Dictionary APIs (Oxford, Cambridge), WordNet, EVP
- **Data Sources:** Taiwan MOE 7000, NGSL, Google 10K, COCA, EVP

**Phase 2:**
- **Add:** YouTube Data API for caption extraction
- **Add:** YouTube processing pipeline
- **Add:** Register tagging from video categories

---

## Frontend Integration ⭐ NEW

### The Lightweight API Layer

**Important:** You cannot connect to Neo4j directly from the browser (exposes credentials). You need a middle layer.

**File:** `api/get-graph-data.py` (Serverless function)

**Cursor Prompt:**
```
Create a folder 'api'. I need a simple serverless function (Python FastAPI).

Create an endpoint /get-graph-data?word={word}.

It should:
1. Connect to Neo4j.
2. Run a Cypher query to fetch the central word, its neighbors 
   (collocations, related, confused_with), and relationships.
3. Return the JSON structure expected by the frontend visualization.
```

**Example Response:**
```json
{
  "word": "bank",
  "senses": [
    {
      "id": "bank.n.01",
      "definition": "A financial institution",
      "zh": "銀行",
      "collocations": ["account", "loan", "deposit"],
      "confused_with": ["bench", "bang"]
    },
    {
      "id": "bank.n.02", 
      "definition": "The side of a river",
      "zh": "河岸",
      "collocations": ["river", "stream"],
      "confused_with": []
    }
  ],
  "phrases": ["bank account", "bank on"],
  "relationships": [
    {"type": "CONFUSED_WITH", "target": "bench", "reason": "Sound"}
  ]
}
```

### Frontend Visualization Update

**Cursor Prompt:**
```
Open the visualization component.

Modify the data fetching function.
Instead of calling Gemini API directly, fetch data from the new API endpoint 
(/api/get-graph-data).

Keep the visualization logic exactly the same.
```

**Visualization States:**
- **Unlearned:** Dim, disconnected dots
- **Learning:** Partially connected, pulsing
- **Mastered:** Glowing, fully interconnected

---

## Timeline (Estimated)

**Phase 1: MVP (Tier 1-2 only)**
- Extract top 3,000-4,000 words (Tier 1-2)
- Create ~5,000 learning points
- Extract basic relationships (morphological, collocations, semantic)
- Use existing corpus data (Google 10K, COCA, EVP)
- **Time:** 2-4 weeks ✅ Fits MVP timeline

**Phase 2: Full Learning Point Cloud + YouTube**
- Add YouTube caption processing
- Add Tier 3-7 (phrases, idioms, advanced contexts)
- Expand to ~13,700 learning points
- Add all relationship types
- Modern frequency data (2024/2025)
- **Time:** 4-8 weeks (after MVP validation)

**Phase 3: Continuous Updates**
- Set up YouTube caption processing pipeline
- Regular updates from dictionaries
- Version control and quality assurance
- **Time:** Ongoing

---

## Success Criteria

1. **Completeness:** All Taiwan MOE 7000 words included (Phase 1: Tier 1-2)
2. **Relationship Quality:** Accurate, validated relationships from WordNet + NGSL
3. **Performance:** Sub-10ms single word queries, sub-50ms multi-hop traversals ⭐ UPDATED
4. **Accuracy:** Relationships match authoritative sources
5. **Currency:** Graph reflects modern English usage (2024/2025) - Phase 2+
6. **Adversarial Coverage:** Confusion pairs mapped for high-quality distractors ⭐ NEW
7. **Taiwan Localization:** Traditional Chinese translations, MOE level alignment ⭐ NEW
8. **Cost Efficiency:** Under $5 USD total API cost ⭐ NEW

---

## References

- Main Architecture Document: `docs/02-learning-point-integration.md`
- Technical Architecture: `docs/04-technical-architecture.md`
- MVP Strategy: `docs/10-mvp-validation-strategy.md`
- Key Decisions: `docs/15-key-decisions-summary.md`

