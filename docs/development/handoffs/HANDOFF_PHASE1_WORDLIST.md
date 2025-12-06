# Handoff: Phase 1 - Word List Compilation

**For:** Phase 1 - Word List Compilation  
**Feature:** Combined word list (CEFR + Taiwan + Corpus)  
**Priority:** High (Foundation - Required for learning interface)  
**Sprint:** MVP Week 1  
**Estimated Time:** 3-4 hours

---

## Your Mission

You are compiling the word list for the LexiCraft MVP. This combines multiple standards to create a comprehensive 3,000-4,000 word list.

**Key Decision**: Combine CEFR A1-B2 (40%) + Taiwan MOE (30%) + Corpus Frequency (30%)

---

## Context

This is part of **Week 1: Foundation** of the MVP build. The word list will be:
- Populated into the `learning_points` table
- Used by the learning interface
- Used by the MCQ generator

**Target**: 3,000-4,000 words → ~5,000 learning points (Tier 1-2 only for MVP)

---

## What You Need to Read

**1. MVP Strategy:**
- `docs/10-mvp-validation-strategy.md` - Word list strategy (Section: Learning Point System)

**2. Key Decisions:**
- `docs/15-key-decisions-summary.md` - Word list decision

---

## Word List Sources

### Source 1: CEFR A1-B2 (40% weight)

**Download:**
- **Google 10K**: https://github.com/first20hours/google-10000-english
  - Format: Plain text, one word per line
  - Time: 1 minute to download

- **Oxford 3000 CEFR**: Search GitHub "Oxford 3000 CSV"
  - Format: CSV with CEFR levels
  - Time: 5 minutes to find and download

- **English Vocabulary Profile (EVP)**: https://www.englishprofile.org/wordlists
  - Format: CSV/Excel (requires registration)
  - Time: 15 minutes (registration + download)
  - Most comprehensive CEFR-aligned list

**Target**: ~4,000 words from CEFR A1-B2 levels

### Source 2: Taiwan MOE Curriculum (30% weight)

**Sources:**
- Taiwan Ministry of Education English curriculum word lists
- Elementary (Grade 1-6): ~1,200 words
- Junior High (Grade 7-9): ~2,000 words (cumulative)

**Note**: May require manual compilation from curriculum documents or textbook word lists.

**Alternative**: Use Taiwan English textbook word lists (Kang Hsuan, Nan Yi, etc.)

**Target**: ~2,000-3,000 words from Taiwan curriculum

### Source 3: Corpus Frequency (30% weight)

**Download:**
- **Google 10K**: Same as above (already downloaded)
- **COCA**: https://www.wordfrequency.info/
  - Format: Excel/CSV (requires registration)
  - Time: 10 minutes
  - Top 60,000 words with frequency

**Target**: Top 3,000 words by frequency

---

## Implementation Tasks

### Task 1: Download Word Lists

1. Download Google 10K list
2. Download Oxford 3000 CEFR (if available)
3. Download COCA frequency list (if available)
4. Compile Taiwan curriculum words (if available)

### Task 2: Create Combination Script

Create `scripts/combine_word_lists.py`:

```python
#!/usr/bin/env python3
"""
Combine Word Lists: CEFR + Taiwan + Corpus Frequency
Target: 3,000-4,000 words for Phase 1
"""

import csv
import requests
from collections import defaultdict

def load_google_10k():
    """Load Google 10K word list"""
    url = "https://raw.githubusercontent.com/first20hours/google-10000-english/master/google-10000-english.txt"
    words = requests.get(url).text.strip().split('\n')
    return {word.lower(): i+1 for i, word in enumerate(words)}  # rank as score

def load_cefr_words(file_path):
    """Load CEFR words from CSV"""
    words = {}
    # Parse CSV and extract CEFR levels
    # Score by level (A1=4, A2=4, B1=3, B2=3)
    return words

def load_taiwan_curriculum(file_path):
    """Load Taiwan curriculum words"""
    words = {}
    # Parse and load
    return words

def combine_word_lists(cefr_words, taiwan_words, corpus_words, target_count=3500):
    """Combine with weighted scoring"""
    word_scores = defaultdict(float)
    
    # Weight: CEFR 40%, Taiwan 30%, Corpus 30%
    for word, score in cefr_words.items():
        word_scores[word] += score * 0.4
    
    for word, score in taiwan_words.items():
        word_scores[word] += score * 0.3
    
    # Corpus: inverse rank
    max_rank = max(corpus_words.values()) if corpus_words else 10000
    for word, rank in corpus_words.items():
        normalized_score = (max_rank - rank + 1) / max_rank
        word_scores[word] += normalized_score * 0.3
    
    # Sort by score
    sorted_words = sorted(word_scores.items(), key=lambda x: x[1], reverse=True)
    
    # Return top N words
    return [word for word, score in sorted_words[:target_count]]

# Main execution
if __name__ == "__main__":
    # Load sources
    corpus_words = load_google_10k()
    cefr_words = load_cefr_words('cefr_words.csv')  # If available
    taiwan_words = load_taiwan_curriculum('taiwan_words.txt')  # If available
    
    # Combine
    final_words = combine_word_lists(cefr_words, taiwan_words, corpus_words, target_count=3500)
    
    # Save
    with open('combined_word_list_phase1.txt', 'w') as f:
        f.write('\n'.join(final_words))
    
    print(f"Final word count: {len(final_words)}")
```

### Task 3: Populate Learning Points

Create `scripts/populate_learning_points.py`:

```python
#!/usr/bin/env python3
"""
Populate learning_points table from word list
Uses WordNet for definitions/examples
"""

import nltk
from nltk.corpus import wordnet as wn
from src.database.crud.learning_points import create_learning_point

# Download NLTK data
try:
    nltk.data.find('corpora/wordnet')
except:
    nltk.download('wordnet')
    nltk.download('omw-1.4')

def populate_word(word, tier=1):
    """Populate learning point for a word"""
    synsets = wn.synsets(word)
    
    if not synsets:
        return None
    
    # Tier 1: First meaning
    syn = synsets[0]
    learning_point = {
        'word': word,
        'type': 'word',
        'tier': tier,
        'definition': syn.definition(),
        'example': syn.examples()[0] if syn.examples() else None,
        'metadata': {
            'pos': syn.pos(),
            'synset_id': syn.name()
        }
    }
    
    create_learning_point(learning_point)
    
    # Tier 2: Additional meanings
    for syn in synsets[1:]:
        learning_point = {
            'word': word,
            'type': 'word',
            'tier': 2,
            'definition': syn.definition(),
            'example': syn.examples()[0] if syn.examples() else None,
            'metadata': {
                'pos': syn.pos(),
                'synset_id': syn.name()
            }
        }
        create_learning_point(learning_point)

# Load word list
with open('combined_word_list_phase1.txt', 'r') as f:
    words = [line.strip() for line in f if line.strip()]

# Populate
for word in words:
    populate_word(word, tier=1)

print(f"Populated {len(words)} words")
```

### Task 4: Create Word List API

Create `src/api/word_list.py`:

```python
from fastapi import APIRouter
from src.database.crud.learning_points import get_learning_points_by_tier

router = APIRouter()

@router.get("/api/words")
def get_word_list(tier: int = None, limit: int = 20):
    """Get word list for learning"""
    words = get_learning_points_by_tier(tier=tier, limit=limit)
    return {"words": words}
```

---

## Success Criteria

- [ ] 3,000-4,000 words compiled
- [ ] Weighted combination working
- [ ] Learning points populated in database
- [ ] ~5,000 learning points created (Tier 1-2)
- [ ] API endpoint returns word list
- [ ] Tests passing

---

## Testing Requirements

### Unit Tests
- Test word list combination logic
- Test WordNet integration
- Test database population

### Integration Tests
- Test API endpoint
- Test word list retrieval
- Test learning point creation

---

## Dependencies

**You depend on:**
- Phase 1 - Database Schema (needs `learning_points` table)

**You enable:**
- Phase 2 - Learning Interface (needs word list)
- Phase 2 - MCQ Generator (needs word list)

---

## Completion Report Format

When done, create a completion report:

```markdown
# Completion Report: Phase 1 - Word List Compilation

**Status:** ✅ Complete

## What was done:
- [List of what was implemented]

## Word counts:
- Total words: [count]
- Learning points (Tier 1): [count]
- Learning points (Tier 2): [count]
- Total learning points: [count]

## Sources used:
- [List of sources]

## Files created:
- [List of files]

## Testing:
- [Test results]

## Known issues:
- [Any issues]

## Next steps:
- [What Phase 2 needs from this]
```

---

**Good luck! You're creating the vocabulary foundation for the entire platform.**

