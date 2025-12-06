# External Resources and APIs for Further Development

**Purpose:** Comprehensive guide to external resources, APIs, and data sources that can be utilized for vocabulary learning application development.

**Last Updated:** December 2024

---

## Table of Contents

1. [Semantic & Relationship Resources](#semantic--relationship-resources)
2. [Dictionary & Thesaurus APIs](#dictionary--thesaurus-apis)
3. [Frequency & Corpus Data](#frequency--corpus-data)
4. [CEFR & Difficulty Level Resources](#cefr--difficulty-level-resources)
5. [Phrase & Collocation Resources](#phrase--collocation-resources)
6. [Pronunciation & Audio Resources](#pronunciation--audio-resources)
7. [Implementation Status](#implementation-status)

---

## Semantic & Relationship Resources

### 1. WordNet (NLTK) ✅ Currently Used

**Source:** Natural Language Toolkit (NLTK) - WordNet corpus  
**Type:** Open-source semantic database  
**Status:** ✅ **Active** - Core relationship mining

**What we use:**
- Semantic relationships (synonyms, antonyms, hypernyms, hyponyms)
- Part-of-speech tagging
- Sense definitions
- Example sentences
- Morphological relationships (derivationally related forms)

**Implementation:**
- `backend/src/structure_miner.py` - Extracts WordNet synsets
- `backend/src/relationship_miner.py` - Creates sense-specific relationships
- `backend/src/morphological_miner.py` - Finds word families

**Key Features:**
- Open-source (no copyright issues)
- Reduces AI hallucinations (structured source)
- Academic rigor
- Free to use

**Documentation:**
- NLTK WordNet: https://www.nltk.org/howto/wordnet.html
- WordNet Database: https://wordnet.princeton.edu/

---

## Dictionary & Thesaurus APIs

### 1. Oxford Dictionary API ⚠️ Mentioned but Not Implemented

**Source:** Oxford University Press  
**Type:** Commercial API  
**Status:** ⚠️ **Planned** - Mentioned in documentation but not implemented

**Potential Uses:**
- Definitions
- Collocations
- Example sentences
- CEFR levels

**Limitations:**
- Requires API key
- Commercial (may have costs)
- Rate limits

**Documentation:**
- Oxford API: https://developer.oxforddictionaries.com/

---

### 2. Cambridge Dictionary API ⚠️ Mentioned but Not Implemented

**Source:** Cambridge University Press  
**Type:** Commercial API  
**Status:** ⚠️ **Planned** - Mentioned in documentation but not implemented

**Potential Uses:**
- Definitions
- Example sentences
- CEFR levels
- Collocations

**Limitations:**
- Requires API key
- Commercial (may have costs)
- Rate limits

**Documentation:**
- Cambridge API: https://dictionary.cambridge.org/api

---

### 3. COBUILD ⚠️ Mentioned but Not Implemented

**Source:** Collins COBUILD  
**Type:** Dictionary/Corpus data  
**Status:** ⚠️ **Planned** - Mentioned for collocations

**Potential Uses:**
- Collocations
- Usage patterns
- Example sentences

**Note:** May require licensing or API access

---

## Frequency & Corpus Data

### 1. NGSL Frequency List ✅ Currently Used

**Source:** New General Service List (NGSL)  
**Type:** Academic frequency research  
**Status:** ✅ **Active** - Used for frequency rankings

**What we use:**
- Global frequency rankings (~2,800 high-frequency words)
- Covers 90%+ of English text
- Academic research-backed rankings

**Implementation:**
- Used in word ranking and prioritization
- Cross-referenced with Taiwan MOE list

**Documentation:**
- NGSL: http://www.newgeneralservicelist.org/

---

### 2. Google Books N-gram Data ⚠️ Mentioned but Not Implemented

**Source:** Google Books Ngram Viewer  
**Type:** Historical corpus dataset  
**Status:** ⚠️ **Planned** - Mentioned for MVP

**Potential Uses:**
- Frequency rankings (top 100K words)
- Collocation patterns (bigrams, trigrams)
- Genre-specific insights
- Time trends

**Limitations:**
- Recency gap (most corpora end 2019-2020)
- Genre bias (books ≠ conversation)
- Large file sizes (50-200 MB)

**Documentation:**
- Google Books Ngram: https://books.google.com/ngrams

---

### 3. COCA (Corpus of Contemporary American English) ⚠️ Mentioned but Not Implemented

**Source:** Brigham Young University  
**Type:** Academic corpus  
**Status:** ⚠️ **Planned** - Mentioned in documentation

**Potential Uses:**
- Frequency data
- Collocation patterns
- Register-specific usage

**Limitations:**
- Requires registration
- May have access restrictions

**Documentation:**
- COCA: https://www.wordfrequency.info/

---

### 4. BNC (British National Corpus) ⚠️ Mentioned but Not Implemented

**Source:** British National Corpus  
**Type:** Academic corpus  
**Status:** ⚠️ **Planned** - Mentioned in documentation

**Potential Uses:**
- Frequency rankings
- British English patterns
- Register analysis

**Documentation:**
- BNC: http://www.natcorp.ox.ac.uk/

---

## CEFR & Difficulty Level Resources

### 1. English Vocabulary Profile (EVP) ⚠️ Mentioned but Not Implemented

**Source:** Cambridge University Press / English Profile  
**Type:** CEFR-aligned vocabulary database  
**Status:** ⚠️ **Planned** - Mentioned for CEFR difficulty levels

**Potential Uses:**
- CEFR difficulty levels (A1-C2)
- Word difficulty mapping
- Curriculum alignment

**Limitations:**
- Requires registration
- May require API access or download

**Documentation:**
- EVP: https://www.englishprofile.org/wordlists

---

### 2. Taiwan MOE 7000 Word List ✅ Currently Used

**Source:** Taiwan Ministry of Education  
**Type:** Official curriculum vocabulary  
**Status:** ✅ **Active** - Primary word list source

**What we use:**
- 7,000 core vocabulary words
- Official MOE difficulty levels (1-6)
- Maps directly to Taiwan curriculum

**Implementation:**
- Master vocabulary list for Taiwan market
- Official difficulty rankings
- Exam vocabulary validation

**Why This Matters:**
- Authoritative list for Taiwan exams (學測, 指考, 會考)
- Parents and students recognize these benchmarks

---

## Phrase & Collocation Resources

### 1. NGSL Phrase List ⚠️ Planned Enhancement

**Source:** New General Service List - Phrase component  
**Type:** Academic phrase database  
**Status:** ⚠️ **Planned** - Currently using WordNet lemmas instead

**Current Implementation:**
- **WordNet lemmas** are used as primary source for phrases
- Extracted from WordNet synset lemmas (multi-word expressions)
- 6,319 phrase nodes currently in Neo4j
- 3,125 senses have phrase mappings

**What NGSL would provide (future):**
- Academically validated phrase list
- Common collocations indexed by anchor word
- Exam-relevant expressions
- Better coverage of exam-specific collocations

**Examples:**
- "run out of" → Anchored to "run"
- "make up" → Anchored to "make"

**Note:** See `backend/docs/NGSL_PHRASE_LIST_IMPLEMENTATION.md` for detailed implementation status and integration plan.

---

## Pronunciation & Audio Resources

### 1. YouGlish API ⚠️ Mentioned but Not Implemented

**Source:** YouGlish  
**Type:** Video-based pronunciation examples  
**Status:** ⚠️ **Planned** - Mentioned in Oxford3000_Vocab repository

**Potential Uses:**
- Pronunciation examples
- Real-world usage videos
- Contextual examples

**Note:** Found in `scripts/Oxford3000_Vocab-main/README.md` - used in Anki deck integration

**Documentation:**
- YouGlish: https://youglish.com/

---

## Modern Corpus Resources (Future)

### 1. YouTube Captions ⚠️ Phase 2 (Not MVP)

**Source:** YouTube video captions (2024/2025 content)  
**Type:** Modern corpus data  
**Status:** ⚠️ **Phase 2** - Planned for future development

**Potential Benefits:**
- Recency (2024/2025 content - solves 2019 gap)
- Authentic (real spoken English)
- Diverse (multiple registers: lectures, vlogs, tutorials)
- Scalable (millions of videos available)
- Continuous (can update regularly)

**Why NOT for MVP:**
- Too complex (requires API setup, authentication, quota management)
- Too time-consuming (6-11 days development vs. 1-2 hours for existing corpus)
- Not essential (existing corpus data sufficient for MVP validation)

**Implementation Strategy (Phase 2):**
1. Batch Processing: Parse thousands of YouTube videos
2. Aggregate learning points
3. Build frequency data
4. Create Learning Point Cloud updates

**Register Tagging:**
- Use video categories for register tagging
- Simple 3-category model: "all", "formal", "informal"

---

## Implementation Status

### ✅ Currently Implemented

1. **WordNet (NLTK)** - Core semantic relationships + phrase extraction
2. **NGSL Frequency List** - Word rankings
3. **WordNet Phrases** - Multi-word lemmas as phrases (6,319 phrases)
4. **Taiwan MOE 7000** - Primary word list
5. **Gemini API** - Content generation

### ⚠️ Mentioned but Not Implemented

1. **NGSL Phrase List** - Exam-relevant collocations (using WordNet instead)
2. **Oxford Dictionary API** - Definitions, collocations
3. **Cambridge Dictionary API** - Definitions, CEFR levels
4. **COBUILD** - Collocations
5. **EVP** - CEFR difficulty levels
6. **Google Books N-gram** - Frequency data
7. **COCA** - Corpus frequency
8. **BNC** - British corpus
9. **YouGlish API** - Pronunciation examples

### 🔮 Future/Phase 2

1. **YouTube Captions** - Modern corpus data
2. **Additional Dictionary APIs** - As needed
3. **Real-time frequency updates** - Continuous learning

---

## Recommendations for Further Development

### High Priority (Immediate Value)

1. **EVP Integration** - CEFR difficulty levels
   - Would improve difficulty assessment
   - Better curriculum alignment
   - Requires registration/API access

2. **Oxford/Cambridge API** - Enhanced definitions
   - Better quality definitions
   - More example sentences
   - Requires API keys and may have costs

### Medium Priority (Enhancement)

3. **COCA/BNC Integration** - Frequency data
   - More accurate frequency rankings
   - Register-specific patterns
   - May require registration

4. **YouGlish Integration** - Pronunciation
   - Real-world usage examples
   - Video-based learning
   - Free to use

### Low Priority (Future)

5. **YouTube Captions** - Modern corpus
   - Phase 2 implementation
   - Requires significant development
   - High value but complex

---

## Integration Examples

### WordNet Integration (Current)

```python
import nltk
from nltk.corpus import wordnet as wn

# Get synsets for a word
synsets = wn.synsets('bank')
if synsets:
    syn = synsets[0]
    definition = syn.definition()
    examples = syn.examples()
    pos = syn.pos()
    
    # Get relationships
    hypernyms = syn.hypernyms()
    hyponyms = syn.hyponyms()
    antonyms = [lemma.antonyms() for lemma in syn.lemmas()]
```

### NGSL Integration (Current)

```python
# NGSL frequency list used for ranking
# Integrated in word list compilation
# Cross-referenced with Taiwan MOE levels
```

---

## Notes

- **WordNet is the primary resource** for semantic relationships AND phrases (currently implemented)
- **NGSL Frequency List and Taiwan MOE** are primary sources for word lists and rankings
- **NGSL Phrase List** is mentioned in docs but not implemented - using WordNet lemmas instead
- **Dictionary APIs** (Oxford, Cambridge) are mentioned but not yet integrated
- **Modern corpus data** (YouTube) is planned for Phase 2
- **CEFR resources** (EVP) would be valuable but require registration/API access

## Current Phrase Implementation

**Status:** ✅ Working with WordNet lemmas
- 6,319 phrase nodes in Neo4j
- 3,125 senses have phrase mappings
- Extracted from WordNet multi-word lemmas
- Used in Level 2 content generation

**Future Enhancement:** NGSL Phrase List integration (post-MVP)
- See `backend/docs/NGSL_PHRASE_LIST_IMPLEMENTATION.md` for details

---

## Related Documentation

- `docs/development/LEARNING_POINT_CLOUD_CONSTRUCTION_PLAN.md` - Main data sources document
- `backend/RELATIONSHIP_IMPROVEMENT_PLAN.md` - Relationship mining using WordNet
- `docs/10-mvp-validation-strategy-enhanced.md` - MVP data sources
- `scripts/PHASE1_COMPLETION_REPORT.md` - Word list compilation sources

