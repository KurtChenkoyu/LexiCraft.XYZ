# MCQ Generation V3 - High-Speed CSV Generation with 15-Distractor Pool

## Overview

The MCQ Assembler V3 generates fair, helpful MCQs with:
1. **Always provide context** (example sentence)
2. **Avoid polysemy traps** (distractors from different words only)
3. **15-distractor pool** (max variety, prevents pattern memorization)
4. **Waterfall filling strategy** (prioritized distractor sources, Tier 5 capped at 10)
5. **POS and frequency validation** (fair, learner-appropriate distractors)
6. **Fast CSV generation** (CPU-bound, 60,000+ MCQs/minute vs. 800/minute for database writes)

---

## What's New in V3

### 15-Distractor Pool Strategy

We now generate **15 distractors** per MCQ using a waterfall filling strategy (expanded from 8 to prevent pattern memorization). This enables:

- **4-option MCQs**: Select 3 from pool of 15 (2,730 possible combinations)
- **6-option MCQs**: Select 5 from pool of 15 (3,003 possible combinations)
- **Adaptive difficulty**: Pick harder/easier distractors based on user ability
- **Anti-memorization**: Users seeing the same question 3+ times get different distractors
- **Replacement pool**: Swap ineffective distractors without regenerating

### The 5-Tier Waterfall

```
Tier 1: CONFUSED_WITH (Best - 2 slots)
├── Different words commonly confused
├── Example: "affect" vs "effect"
├── POS relaxed (high pedagogical value)
└── Highest priority

Tier 2: OPPOSITE_TO (2 slots)
├── Different words with opposite meaning
├── Example: "deposit" vs "withdraw"
├── POS must match
└── Tests meaning boundaries

Tier 3: ORTHOGRAPHIC (2 slots)
├── Words with small edit distance (Levenshtein ≤ 2)
├── Example: "through" vs "thorough", "quiet" vs "quite"
├── Critical for EFL learners
└── Visual confusion trap

Tier 4: RELATED_TO (1 slot)
├── Synonyms or semantically similar words
├── Example: "start" vs "begin"
├── Use carefully - may be too similar
└── POS must match

Tier 5: BAND_SAMPLE (Fill remaining)
├── Random words from same frequency band (±500)
├── Example: Same difficulty level words
├── "Camouflage" to prevent guessing by elimination
└── POS must match
```

### Validation Filters

All distractors (except Tier 1) must pass:

1. **POS Lock**: Distractor POS must match target POS
   - Noun → Noun, Verb → Verb, etc.
   - Adjective variants (a, s) are interchangeable

2. **Frequency Band**: Distractor must be within ±2000 rank of target
   - Prevents obscure words as distractors
   - Keeps difficulty fair for learner level

---

## The Core Principles (Unchanged from V2)

### Polysemy Safety

Distractors ONLY come from **different words**, never from other senses of the same word.

```
Word: "break" (opportunity sense)

VALID distractors (different words):
✅ 錯過 (from "miss" - opposite)
✅ 煞車 (from "brake" - confused)
✅ 開始 (from "start" - similar)

EXCLUDED (same word, different sense):
❌ 休息 (from "break" rest sense) - UNFAIR!
```

### Context Required

Every MEANING MCQ includes the example sentence so the learner knows which sense we're testing.

---

## MCQ Types

### Type 1: MEANING (with Context)

```
┌─────────────────────────────────────────────────────────────────┐
│ Q: 在這個句子中，"break" 是什麼意思？                           │
│                                                                 │
│ 📖 "Getting that job was a real break for him."                 │
│                                                                 │
│ A) 機會；好運           [target]                  ✅ Tier 0     │
│ B) 錯過；失去           [confused: miss]             Tier 1     │
│ C) 煞車；制動           [confused: brake]            Tier 1     │
│ D) 拒絕；否認           [opposite: refuse]           Tier 2     │
│ E) 打破；透過           [orthographic: thorough]     Tier 3     │
│ F) 開始；啟動           [similar: start]             Tier 4     │
│                                                                 │
│ 💡 正確答案是「機會；好運」。                                   │
└─────────────────────────────────────────────────────────────────┘
```

For **4-option** display, system selects 3 distractors:
- High ability user → A, B, C, D (harder: tier 1-2)
- Low ability user → A, D, E, F (easier: tier 2-5)

### Type 2: USAGE (Sense-Specific)

Tests if learner can identify which sentence shows this specific meaning.

Current guardrails:
- Distractors come only from **related/confused/opposite** examples (different words), never other sentences of the **same sense**.
- If we cannot collect **3+** such distractors, we **skip generating** the USAGE MCQ to avoid “all options are plausible.”

### Type 3: DISCRIMINATION (Different Words)

Tests if learner can distinguish between genuinely different words (fill-in-the-blank).

---

## Storage Format

MCQs are stored with all 8 distractors in the options JSONB:

```json
{
  "options": [
    {"text": "機會", "is_correct": true, "source": "target", "tier": 0},
    {"text": "影響", "is_correct": false, "source": "confused", "tier": 1, "source_word": "affect"},
    {"text": "效果", "is_correct": false, "source": "confused", "tier": 1, "source_word": "effect"},
    {"text": "拒絕", "is_correct": false, "source": "opposite", "tier": 2, "source_word": "refuse"},
    {"text": "接受", "is_correct": false, "source": "opposite", "tier": 2, "source_word": "accept"},
    {"text": "期望", "is_correct": false, "source": "orthographic", "tier": 3, "source_word": "expect"},
    {"text": "相關", "is_correct": false, "source": "similar", "tier": 4, "source_word": "related"},
    {"text": "重要", "is_correct": false, "source": "band_sample", "tier": 5, "source_word": "important"},
    {"text": "決定", "is_correct": false, "source": "band_sample", "tier": 5, "source_word": "decide"}
  ]
}
```

---

## Selection at Serving Time

```python
from src.mcq_adaptive import select_options_from_pool

# For 4-option MCQ (standard)
options, correct_idx = select_options_from_pool(
    mcq.options, 
    distractor_count=3
)

# For 6-option MCQ (harder format)
options, correct_idx = select_options_from_pool(
    mcq.options, 
    distractor_count=5
)

# Adaptive based on user ability
options, correct_idx = select_options_from_pool(
    mcq.options, 
    distractor_count=3, 
    user_ability=0.85  # High ability → harder distractors
)
```

---

## Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                     MCQ GENERATION V3                           │
└─────────────────────────────────────────────────────────────────┘

1. INPUT: Sense ID (e.g., "accept.v.01")
   │
   ▼
2. FETCH SENSE DATA (from VocabularyStore V3)
   ├── vocabulary_store.get_sense(sense_id) → All data embedded
   ├── Target definition: "接受"
   ├── Context sentence: "She decided to accept the offer."
   ├── POS: "v" (verb)
   ├── Frequency rank: 1500
   ├── Connections: {related, opposite, confused} (embedded)
   └── Other senses: vocabulary_store.get_other_senses_of_word(sense_id)
   │
   ▼
3. WATERFALL DISTRACTOR FILLING
   │
   ├── Tier 1: CONFUSED_WITH (embedded in sense.connections.confused)
   │   ├── Source: vocabulary_store.get_confused_senses(sense_id)
   │   ├── Validate: POS relaxed, Rank ±2000
   │   └── Take up to 2
   │
   ├── Tier 2: OPPOSITE_TO (embedded in sense.connections.opposite)
   │   ├── Source: vocabulary_store.get_opposite_senses(sense_id)
   │   ├── Validate: POS strict, Rank ±2000
   │   └── Take up to 2
   │
   ├── Tier 3: ORTHOGRAPHIC (Levenshtein ≤ 2)
   │   ├── Source: vocabulary_store.get_senses_by_rank_range() + Levenshtein filter
   │   ├── Filter: Edit distance ≤ 2
   │   └── Take up to 2
   │
   ├── Tier 4: RELATED_TO (embedded in sense.connections.related)
   │   ├── Source: vocabulary_store.get_related_senses(sense_id)
   │   ├── Validate: POS strict, Rank ±2000
   │   └── Take up to 1
   │
   └── Tier 5: BAND_SAMPLE (fallback)
       ├── Source: vocabulary_store.get_random_senses_in_band(band, pos)
       ├── Validate: POS strict
       └── Fill remaining slots (up to 8 total)
   │
   ▼
4. GENERATE MCQ
   ├── 1 correct answer (tier 0)
   ├── Up to 8 distractors (tiers 1-5)
   ├── Minimum 4 distractors required
   └── Store tier metadata for selection
   │
   ▼
5. OUTPUT: 9-option pool (1 correct + 8 distractors)
```

---

## Minimum Requirements

An MCQ is only generated if we can collect **at least 4 distractors**. This ensures graceful degradation:

- **8 distractors**: Full pool - all formats supported
- **5-7 distractors**: Good coverage - 6-option may have less variety
- **4 distractors**: Minimum - 4-option MCQs only
- **<4 distractors**: MCQ not generated - flagged for review

---

## Testing

```bash
# Test waterfall strategy
python3 -m src.mcq_assembler --word accept --store

# Check tier distribution
python3 -m src.mcq_assembler --sense accept.v.01

# Full MCQ output with all 8 distractors
python3 -m scripts.test_mcq_assembler --word break --full
```

---

## Philosophy Recap

> **"Help, not confuse"**

- ✅ **Context**: Always show the sentence so learner knows WHICH meaning
- ✅ **Fair distractors**: From different words, not polysemy traps
- ✅ **POS consistency**: Verb distractors for verb targets
- ✅ **Frequency fairness**: No obscure words as distractors
- ✅ **Orthographic traps**: Catch spelling confusion (EFL focus)
- ✅ **20-30 distractor pool**: Expanded for multiple MCQs with unique subsets
- ❌ **Never**: Use other senses of same word as "wrong" answers
- ❌ **Never**: Use words outside learner's difficulty band

---

## Enhanced MCQ Generation (December 2025)

### Multiple MCQs Per Sense (Tiered by Usage)

The MCQ Assembler has been enhanced to generate **10-25 MCQs per sense** based on usage frequency:

```
Tiered by Usage Ratio:
├── PRIMARY (>50% usage): 15-20 MEANING MCQs + 3 USAGE + 3 DISCRIMINATION = ~21-26 MCQs
├── COMMON (20-50% usage): 8-12 MEANING MCQs + 3 USAGE + 3 DISCRIMINATION = ~14-18 MCQs
└── RARE (<20% usage): 5-8 MEANING MCQs + 2 USAGE + 2 DISCRIMINATION = ~9-12 MCQs
```

**Rationale:** Primary senses are encountered constantly, requiring more unique MCQs to prevent pattern memorization.

### Enhanced Distractor Pool

Distractor pool expanded from 8 to **20-30** distractors using the same waterfall strategy:

```
Tier allocation (enhanced):
├── Tier 1: CONFUSED_WITH (up to 5)
├── Tier 2: OPPOSITE_TO (up to 5)
├── Tier 3: Orthographic (up to 5)
├── Tier 4: RELATED_TO (up to 5)
└── Tier 5: Band Sample (fill to 25)
```

### Unique Distractor Subsets

Each MCQ selects a **unique subset of 8 distractors** from the full pool:

```python
# Example: Sense has 25 distractors in pool
# MCQ 1 (example_index=0): Selects distractors at positions 0,1,2...
# MCQ 2 (example_index=1): Selects distractors at positions 1,2,3...
# ...
# This prevents pattern memorization across MCQs
```

### Prerequisites

To achieve 8-15 MCQs per sense:

1. **Level 2 Enrichment Required**: Run enhanced Level 2 enrichment to generate 5-8 contextual examples per sense
2. **Confused Relationships**: Senses with multiple confused words get multiple DISCRIMINATION MCQs

### Expected Results

| Metric | Before Enhancement | After V3 (Current) |
|--------|-------------------|----------------------------|
| MCQs per sense (primary) | 1-3 | 21-26 |
| MCQs per sense (common) | 1-3 | 14-18 |
| MCQs per sense (rare) | 1-3 | 9-12 |
| Total MCQs | ~13,000-15,000 | ~161,000 (10,470 senses) |
| Distractor pool | 8 | 15 (max 10 Tier 5) |
| Distractor variety | Same per sense | Unique per MCQ |
| Generation speed | ~800 MCQs/min (database) | ~60,000 MCQs/min (CSV) |

---

## High-Speed CSV Generation Workflow

### The Problem

Database writes are **network-bound**: ~99% of generation time is spent waiting for SSL handshakes and transaction acknowledgments to Supabase. At 800 MCQs/minute, full regeneration takes 6-10 hours.

### The Solution: Offline CSV Generation

Decouple generation (CPU-fast) from storage (network-slow) using the ETL pattern:

1. **Generate:** Write MCQs to local CSV files (~2-3 minutes for 161k MCQs)
2. **Import:** Bulk load to PostgreSQL via `COPY` command (~5-10 minutes)

**Total time:** 10-15 minutes vs. 6-10 hours (40-60x speedup)

### Usage

```bash
# Generate to CSV (bypasses database)
python3 scripts/generate_all_mcqs.py --workers 5 --batch-size 200 --output-csv mcq_csvs

# Combine worker CSVs
cd mcq_csvs && cat mcqs_worker_*.csv > all_mcqs.csv

# Bulk import to PostgreSQL
psql $DATABASE_URL -c "\COPY mcq_pool(...) FROM 'all_mcqs.csv' WITH (FORMAT CSV);"
```

### CSV Format

Each row contains 9 columns matching PostgreSQL schema:

1. `sense_id` - Sense identifier
2. `word` - Target word
3. `mcq_type` - `meaning`, `usage`, or `discrimination`
4. `question` - Question text
5. `context` - Example sentence
6. `options` - JSON array of options (all fields quoted)
7. `correct_index` - Index of correct option
8. `explanation` - Post-answer explanation
9. `metadata` - JSON object with distractor sources

**Note:** `id`, `created_at`, `updated_at` are auto-generated by PostgreSQL.

### Quality Checks

**Active checks (implemented):**
- ✅ Polysemy filtering (no same-word distractors)
- ✅ POS validation (distractors match target part-of-speech)
- ✅ Frequency band (distractors within ±2000 rank)
- ✅ Definition similarity (SequenceMatcher 75% threshold)

**Deferred checks (post-processing):**
- ⏭️ Semantic similarity (requires embeddings, can filter CSV before import)
- ⏭️ User feedback integration (flag low-quality MCQs via `is_active = False`)

CSV format allows flexible quality pipelines - add semantic checks later without regenerating.

### Performance Metrics (Actual Results)

| Metric | Database Mode | CSV Mode |
|--------|--------------|---------|
| **Time** | 6-10 hours | 2.3 minutes |
| **Rate** | 800 MCQs/min | 60,000+ MCQs/min |
| **Bottleneck** | Network (SSL) | CPU |
| **Concurrency** | Limited by connections | 5 workers, no blocking |
| **Resumability** | Complex (savepoints) | Simple (re-run) |

**Real run:** 10,470 senses → 161,597 MCQs in 137.5 seconds (2.3 min)

