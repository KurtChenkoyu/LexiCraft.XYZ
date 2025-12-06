# NGSL Phrase List Integration - Future Tasks

**Status:** 📋 Planned for Post-MVP  
**Priority:** 🟡 Medium (Enhancement)  
**Estimated Time:** 1-2 days  
**Dependencies:** MVP core features complete

---

## Overview

This document outlines the tasks needed to integrate NGSL Phrase List as an enhancement to the current WordNet-based phrase extraction system.

**Current State:**
- ✅ WordNet lemmas provide 6,319 phrases
- ✅ 3,125 senses have phrase mappings
- ✅ System is functional and working

**Target State:**
- ✅ NGSL phrases merged with WordNet phrases
- ✅ Better coverage of exam-relevant collocations
- ✅ Backward compatible (no breaking changes)

---

## Prerequisites

- [ ] MVP core features complete (learning interface, MCQ generator, verification system)
- [ ] Current phrase system stable and tested
- [ ] Time allocated for enhancement work

---

## Task List

### Phase 1: Data Preparation

#### Task 1.1: Download NGSL Phrase List
**File:** `data/source/ngsl_phrases.csv` (or similar)

**Actions:**
1. Visit http://www.newgeneralservicelist.org/
2. Download NGSL Phrase List (if available as separate file)
3. If not available separately, check if phrases are in main NGSL dataset
4. Save to `data/source/ngsl_phrases.csv`

**Expected Format:**
```csv
anchor_word,phrase,type
run,run out of,phrasal_verb
run,run into,phrasal_verb
make,make up,phrasal_verb
```

**Estimated Time:** 30 minutes

---

#### Task 1.2: Parse and Validate NGSL Phrases
**File:** `backend/scripts/parse_ngsl_phrases.py` (new)

**Actions:**
1. Create script to parse NGSL phrase file
2. Validate format and data quality
3. Index phrases by anchor word
4. Check for duplicates with existing WordNet phrases
5. Generate statistics report

**Code Structure:**
```python
def parse_ngsl_phrases(file_path: str) -> dict:
    """
    Parse NGSL phrase list and return dict: {anchor_word: [phrases]}
    """
    pass

def validate_phrases(phrases: dict) -> dict:
    """
    Validate phrase data quality.
    Returns statistics and issues.
    """
    pass
```

**Estimated Time:** 1-2 hours

---

### Phase 2: Integration

#### Task 2.1: Create NGSL Phrase Loader
**File:** `backend/scripts/load_ngsl_phrases.py` (new)

**Actions:**
1. Create script to load NGSL phrases into Neo4j
2. Link phrases to anchor words
3. Optionally link to senses (if sense mapping available)
4. Handle duplicates (merge with existing WordNet phrases)
5. Add metadata to distinguish NGSL vs WordNet phrases

**Code Structure:**
```python
def load_ngsl_phrases(
    conn: Neo4jConnection,
    phrases_by_word: dict,
    merge_with_wordnet: bool = True
):
    """
    Load NGSL phrases into Neo4j.
    
    Args:
        conn: Neo4j connection
        phrases_by_word: Dict mapping anchor words to phrase lists
        merge_with_wordnet: If True, merge with existing WordNet phrases
    """
    pass
```

**Estimated Time:** 2-3 hours

---

#### Task 2.2: Enhance Structure Miner
**File:** `backend/src/structure_miner.py` (modify)

**Actions:**
1. Add optional parameter for NGSL phrase dictionary
2. Merge WordNet phrases with NGSL phrases
3. Prioritize NGSL phrases when available (or merge both)
4. Update `skeleton_phrases` to include both sources
5. Add metadata to track phrase source

**Code Changes:**
```python
def get_skeletons(
    word_text: str, 
    limit: int = 3, 
    ngsl_phrases: dict = None  # NEW parameter
) -> list:
    """
    Enhanced to include NGSL phrases.
    """
    # ... existing WordNet extraction ...
    
    # Merge with NGSL phrases if available
    if ngsl_phrases and word_text.lower() in ngsl_phrases:
        ngsl_phrases_list = ngsl_phrases[word_text.lower()]
        # Merge with WordNet phrases, avoiding duplicates
        all_phrases = list(set(skeleton_phrases + ngsl_phrases_list))
        skeleton_phrases = all_phrases
    
    # ... rest of function ...
```

**Estimated Time:** 1-2 hours

---

#### Task 2.3: Update Phrase Schema (Optional)
**File:** Database schema update

**Actions:**
1. Add `source` property to `(:Phrase)` nodes
   - Values: "wordnet", "ngsl", "merged"
2. Add `ngsl_phrase` boolean flag
3. Update existing phrases to mark source

**Cypher:**
```cypher
// Add source property to existing phrases
MATCH (p:Phrase)
WHERE p.source IS NULL
SET p.source = "wordnet"

// Add source to new NGSL phrases
MATCH (p:Phrase)
WHERE p.ngsl_phrase = true
SET p.source = "ngsl"
```

**Estimated Time:** 30 minutes

---

### Phase 3: Testing & Validation

#### Task 3.1: Test Phrase Merging
**Actions:**
1. Test with sample words (10-20 words)
2. Verify NGSL phrases are loaded correctly
3. Verify duplicates are handled properly
4. Check phrase-to-sense mappings
5. Validate data quality

**Test Cases:**
- Word with only WordNet phrases
- Word with only NGSL phrases
- Word with both (should merge)
- Word with duplicate phrases (should deduplicate)

**Estimated Time:** 1-2 hours

---

#### Task 3.2: Validate Content Generation
**Actions:**
1. Test Level 2 content generation with merged phrases
2. Verify phrases appear in prompts correctly
3. Check example quality improvement
4. Compare before/after phrase coverage

**Estimated Time:** 1 hour

---

#### Task 3.3: Performance Testing
**Actions:**
1. Test query performance with additional phrases
2. Check Neo4j query times
3. Verify no performance degradation
4. Optimize if needed

**Estimated Time:** 30 minutes

---

### Phase 4: Documentation & Deployment

#### Task 4.1: Update Documentation
**Files:**
- `backend/docs/EXTERNAL_RESOURCES_AND_APIS.md`
- `backend/docs/NGSL_PHRASE_LIST_IMPLEMENTATION.md`
- `backend/README.md` (if applicable)

**Actions:**
1. Update status from "Planned" to "Implemented"
2. Document integration process
3. Add usage examples
4. Update architecture diagrams

**Estimated Time:** 1 hour

---

#### Task 4.2: Create Migration Script
**File:** `backend/scripts/migrate_ngsl_phrases.py` (new)

**Actions:**
1. Create script to run full integration
2. Include rollback capability
3. Add progress tracking
4. Generate integration report

**Estimated Time:** 1-2 hours

---

## Implementation Strategy

### Option A: Incremental (Recommended)

1. **Week 1:** Data preparation (Tasks 1.1, 1.2)
2. **Week 2:** Integration (Tasks 2.1, 2.2, 2.3)
3. **Week 3:** Testing (Tasks 3.1, 3.2, 3.3)
4. **Week 4:** Documentation & deployment (Tasks 4.1, 4.2)

**Total Time:** ~2-3 days spread over 4 weeks

### Option B: Sprint (Fast)

Complete all tasks in 1-2 days:
- Day 1: Data prep + Integration
- Day 2: Testing + Documentation

**Risk:** Higher chance of issues, less time for validation

---

## Success Criteria

- [ ] NGSL phrases loaded into Neo4j
- [ ] Phrases merged with WordNet phrases (no duplicates)
- [ ] All existing functionality still works
- [ ] Phrase coverage improved (more senses have phrases)
- [ ] Content generation uses merged phrases
- [ ] Documentation updated
- [ ] No performance degradation

---

## Rollback Plan

If issues arise:

1. **Quick Rollback:**
   ```cypher
   // Remove NGSL phrases
   MATCH (p:Phrase)
   WHERE p.source = "ngsl" OR p.ngsl_phrase = true
   DETACH DELETE p
   ```

2. **Full Rollback:**
   - Restore from backup
   - Revert code changes
   - Remove NGSL phrase file

---

## Notes

- **Backward Compatibility:** Must maintain existing WordNet phrase functionality
- **Data Quality:** Validate NGSL phrases before loading
- **Performance:** Monitor query times after integration
- **Testing:** Test thoroughly before production deployment

---

## Related Documents

- `backend/docs/NGSL_PHRASE_LIST_IMPLEMENTATION.md` - Current implementation details
- `backend/docs/EXTERNAL_RESOURCES_AND_APIS.md` - External resources overview
- `backend/src/structure_miner.py` - Current phrase extraction
- `backend/src/agent.py` - Phrase mapping and storage

---

## Questions to Resolve

- [ ] Is NGSL phrase list available as separate download?
- [ ] What format is the NGSL phrase list in?
- [ ] How many phrases are in NGSL list?
- [ ] Do NGSL phrases include sense mappings?
- [ ] Should we prioritize NGSL over WordNet or merge equally?

---

**Last Updated:** December 2024  
**Status:** 📋 Planned for Post-MVP

