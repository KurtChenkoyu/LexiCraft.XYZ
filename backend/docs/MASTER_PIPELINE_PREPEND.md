# Master Data Pipeline: From Taiwan MOE to Production MCQs

## Overview

This document describes the complete data pipeline from Taiwan's official curriculum to production-ready MCQs in PostgreSQL. Understanding this pipeline is critical for maintaining data quality and knowing when/how to regenerate content.

---

## Pipeline Architecture

```
Stage 0: Word List Preparation
Taiwan MOE 7000-word curriculum
    ↓
[CEFR mapping + Frequency ranking]
    ↓
master_vocab.csv (~10k words)

Stage 1: Level 1 Enrichment
master_vocab.csv
    ↓
[WordNet + Gemini AI: definitions, examples, translations]
    ↓
vocabulary.json V3.0 (core data, 10,470 senses)

Stage 2: Level 2 Enrichment
vocabulary.json (core)
    ↓
[Gemini AI: relationship examples, confused/opposite/similar connections]
    ↓
vocabulary.json V3.0 (enriched, ~43% with relationships)

Stage 3: MCQ Generation
vocabulary.json (enriched)
    ↓
[CPU-bound generation: 15-distractor pools, 3 MCQ types]
    ↓
mcq_csvs/*.csv (~15.7k MCQs, 2-3 min)

Stage 4: Quality Verification
CSV files
    ↓
[Sample 100, check for polysemy/ambiguity/JSON validity]
    ↓
Quality report (pass/fail)

Stage 5: PostgreSQL Import
Verified CSV
    ↓
[Bulk COPY in 5000-row batches]
    ↓
mcq_pool table (production database)
```

---

## Stage 0: Word List Preparation (Foundation)

**Purpose:** Create master vocabulary from Taiwan's official curriculum

**Input:**
- Taiwan MOE 7000-word vocabulary (`data/source/moe_7000.csv`)
- CEFR level mappings (`data/source/evp-cefr.json`)
- Frequency rankings (COCA/BNC)

**Output:** `data/processed/master_vocab.csv` (~10k words)

**Principles:**
- **Curriculum-aligned**: Taiwan Ministry of Education official list (not arbitrary WordNet filtering)
- **CEFR-mapped**: A1-C2 levels for progressive difficulty
- **Frequency-ranked**: Most common words prioritized
- **Pedagogically sound**: Proven vocabulary for Taiwan learners

**File Location:** Already exists (pre-processed)

**Unique Advantage:** Most vocabulary apps use random word lists; we use Taiwan's official curriculum aligned with the education system.

---

## Stage 1: Level 1 Enrichment (Core Data)

**Purpose:** Add definitions, translations, and contextual examples

**Input:** `data/processed/master_vocab.csv`

**Output:** `backend/data/vocabulary.json` V3.0 with core data (~10,470 senses)

**Principles:**
- **WordNet integration**: Get sense definitions from NLTK WordNet
- **AI-generated examples**: Taiwan-contextualized (60% universal, 40% Taiwan-specific)
- **Multiple examples per sense**: 16-17 contextual examples for variety
- **Chinese translations**: Direct translation + explanation with connection pathways

**Commands:**
```bash
cd backend
python3 scripts/enrich_vocabulary_v2.py --limit 10000
```

**Duration:** ~2-3 hours (API rate limits)
**Cost:** ~$50-100 (Gemini API)

**Current State:** ✅ Complete (10,470 senses enriched)

---

## Stage 2: Level 2 Enrichment (Relationships)

**Purpose:** Add confused/opposite/similar word relationships + examples

**Input:** `vocabulary.json` from Stage 1

**Output:** Updated `vocabulary.json` V3.0 with relationships

**Principles:**
- **Selective enrichment**: High-value senses only (not all 10k)
- **Relationship examples**: `examples_confused`, `examples_opposite`, `examples_similar` for USAGE MCQs
- **CONFUSED_WITH connections**: Enable DISCRIMINATION MCQs
- **AI-powered**: Gemini identifies semantically confusing pairs

**Commands:**
```bash
cd backend
# Run via agents (distributed processing)
python3 scripts/retry_failed_level2.py
python3 scripts/sync_level2_to_vocabulary.py
```

**Duration:** ~3-5 hours (API rate limits)
**Cost:** ~$100-200 (Gemini API)

**Current State:** ⚠️ Partial (43% of senses have CONFUSED_WITH; many have <3 relationship examples)

**Impact on MCQs:**
- Limited USAGE MCQs (need 3+ relationship examples)
- Limited DISCRIMINATION MCQs (need CONFUSED_WITH connections)
- Current output: 15.4 MCQs/sense instead of target 38/sense

---

## Stage 3: MCQ Generation (CSV)

**Purpose:** Generate 15-20 MCQs per sense with 15-distractor pools

**Input:** `backend/data/vocabulary.json`

**Output:** `backend/mcq_csvs/*.csv` files

**Principles:**
- **Polysemy-safe**: Distractors from different words only
- **POS-validated**: Match part-of-speech
- **Frequency-banded**: ±2000 rank tolerance
- **Tier-prioritized**: Confused > Opposite > Orthographic > Related > Band Sample
- **15-distractor pool**: Prevents pattern memorization (2,730 combinations for 4-option MCQs)

**Commands:**
```bash
cd backend
python3 scripts/generate_all_mcqs.py --workers 5 --batch-size 200 --output-csv mcq_csvs
```

**Duration:** ~2-3 minutes (CPU-bound, 60,000+ MCQs/minute)

**Current Output:**
- **Generated:** 15,773 valid MCQs
- **MEANING:** 14,256 (90.4%)
- **USAGE:** 1,185 (7.5%)
- **DISCRIMINATION:** 332 (2.1%)

**Quality Check Results:**
- ✅ Sample of 100 MCQs: 0% error rate
- ✅ No polysemy traps detected
- ✅ JSON structure valid
- ✅ No mock/placeholder data

**CSV Workflow Advantage:** Can regenerate in 10-15 minutes vs. 6-10 hours (database mode)

---

## Stage 4: Quality Verification

**Purpose:** Sample-check MCQ quality before production upload

**Input:** `mcq_csvs/all_mcqs_quoted.csv`

**Output:** Quality report (pass/fail)

**Process:**
1. Parse CSV to validate structure
2. Sample 100 MCQs (stratified by type)
3. Check for:
   - Duplicate questions
   - Polysemy traps (same-word distractors)
   - Ambiguous distractors
   - JSON validity
   - Mock/placeholder data

**Commands:**
```bash
cd backend/mcq_csvs
python3 << 'EOF'
import csv
import random
# ... (sampling and validation code)
EOF
```

**Pass Criteria:** <5% error rate

**Current State:** ✅ Passed (0% error rate on 100-MCQ sample)

---

## Stage 5: PostgreSQL Import

**Purpose:** Bulk load verified MCQs to production database

**Input:** `mcq_csvs/all_mcqs_quoted.csv`

**Output:** `mcq_pool` table populated

**Strategy:** Split into 5000-row batches (Supabase timeout workaround)

**Commands:**
```bash
cd backend/mcq_csvs
# Split into batches
split -l 5000 all_mcqs_quoted.csv batch_

# Import each batch
for batch in batch_*; do
  psql $DATABASE_URL -c "\COPY mcq_pool(sense_id, word, mcq_type, question, context, options, correct_index, explanation, metadata) FROM '$(pwd)/$batch' WITH (FORMAT CSV);"
done
```

**Duration:** ~10-15 minutes (network-bound, includes retries)

**Current State:** ⚠️ Partial (~99k imported, some batches timed out)

---

## Quality Gates

| Stage | Proceed If | Stop If |
|-------|-----------|---------|
| Stage 0 | MOE 7000 list valid | File missing/corrupt |
| Stage 1 | 8k+ senses enriched | <5k senses or definitions missing |
| Stage 2 | 40%+ have relationships | All relationships empty |
| Stage 3 | 10+ MCQs/sense avg | <5 MCQs/sense |
| Stage 4 | <5% bad MCQs in sample | >10% ambiguous/broken |
| Stage 5 | Batches imported successfully | Import failures persist |

---

## Regeneration Protocol

**When to regenerate:**
- Major vocabulary update (new words added)
- MCQ logic improvements (new distractor tiers)
- User feedback indicates systematic quality issues
- Level 2 enrichment completed (to unlock more USAGE/DISCRIMINATION MCQs)

**How to regenerate:**
```bash
# 1. Stop any running processes
pkill -f generate_all_mcqs

# 2. Backup current CSV
cd backend/mcq_csvs
mv all_mcqs_quoted.csv backup_$(date +%Y%m%d).csv

# 3. Truncate database (if replacing all)
psql $DATABASE_URL -c "TRUNCATE TABLE mcq_pool CASCADE;"

# 4. Re-run Stage 3
cd ..
python3 scripts/generate_all_mcqs.py --workers 5 --batch-size 200 --output-csv mcq_csvs

# 5. Verify quality (Stage 4)
# 6. Import to PostgreSQL (Stage 5)
```

**CSV Workflow Advantage:** Can regenerate in 10-15 minutes vs. 6-10 hours (database mode)

---

## Current State (Dec 2024)

- ✅ Stage 0 complete (MOE 7000 → master_vocab.csv)
- ✅ Stage 1 complete (Level 1 enrichment, 10,470 senses)
- ⚠️ Stage 2 partial (Level 2 enrichment, 43% with relationships)
- ✅ Stage 3 complete (15,773 MCQs in CSV, 2.3 min generation, 0% error rate)
- ✅ Stage 4 complete (quality verified, 0% error rate)
- ⏳ Stage 5 pending (import to PostgreSQL needed)

**Known Gaps:**
- Only 43% of senses have CONFUSED_WITH relationships
- Many senses have <3 relationship examples (need 3+ for USAGE MCQs)
- This limits output to 15.4 MCQs/sense instead of target 38/sense

**To Reach 400k MCQs:**
- Re-run Stage 2 with higher relationship targets
- Aim for 3+ examples per relationship type (confused/opposite/similar)
- This would unlock more USAGE & DISCRIMINATION MCQs

---

# MCQ Generation V3 - Detailed Technical Documentation

The following sections provide detailed technical information about the MCQ generation logic itself.

---


