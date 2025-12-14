# MCQ Bulk Generation Checklist

**Purpose:** Verify all prerequisites before generating MCQs for all 10,470 senses.

**Date:** December 2025

---

## ✅ System Architecture

### MCQ Generation Method
- **Status:** ✅ **Rule-Based (No AI Prompts)**
- **Note:** MCQs are assembled from existing vocabulary data using hardcoded templates
- **No prompts to update** - questions are generated via code logic

### Question Templates (Hardcoded)
- ✅ **MEANING MCQ:** `'在這個句子中，"{word}" 是什麼意思？'`
- ✅ **USAGE MCQ:** `'哪一個句子中的 "{word}" 表示「{def_display}」？'`
- ✅ **DISCRIMINATION MCQ:** `'請選擇正確的詞填入空格：'`
- **Status:** Templates are appropriate and up-to-date

---

## ✅ Data Requirements

### 1. VocabularyStore (Primary Data Source)
- **File:** `backend/data/vocabulary.json`
- **Version:** V3.0 ✅
- **Total Senses:** 10,470 ✅
- **Required Fields Per Sense:**
  - ✅ `definition_zh` - Required for all MCQs
  - ✅ `definition_en` - Fallback if `definition_zh` missing
  - ✅ `example_en` - Required for MEANING MCQ
  - ✅ `pos` - Required for distractor validation
  - ✅ `frequency_rank` - Required for frequency band matching
  - ✅ `connections.confused` - Required for DISCRIMINATION MCQ (4,535 senses have this)
  - ✅ `connections.opposite` - Used for Tier 2 distractors
  - ✅ `connections.related` - Used for Tier 4 distractors
  - ✅ `other_senses` - Embedded for polysemy checking

**Verification Complete:**
- ✅ **9,990 senses (95.4%)** have `definition_zh`
- ✅ **10,470 senses (100.0%)** have `example_en` (required for MEANING MCQ)
- ✅ **4,535 senses (43.3%)** have `connections.confused` (required for DISCRIMINATION MCQ)
- ✅ **1,473 senses (14.1%)** have `connections.opposite` (Tier 2 distractors)
- ✅ **9,319 senses (89.0%)** have `connections.related` (Tier 4 distractors)

### 2. Database Schema
- **Table:** `mcq_pool` ✅ (Migration 012)
- **Table:** `mcq_statistics` ✅ (Migration 012)
- **Table:** `mcq_attempts` ✅ (Migration 012)
- **Status:** Schema is ready

### 3. PostgreSQL Connection
- **File:** `backend/src/database/postgres_connection.py` ✅
- **Environment:** `DATABASE_URL` required
- **Status:** Connection manager exists

---

## ✅ Code Components

### 1. MCQ Assembler
- **File:** `backend/src/mcq_assembler.py` ✅
- **Version:** V3 (VocabularyStore-based)
- **Features:**
  - ✅ 8-distractor pool with waterfall strategy
  - ✅ Polysemy-safe (excludes same-word distractors)
  - ✅ POS and frequency validation
  - ✅ Three MCQ types (MEANING, USAGE, DISCRIMINATION)
- **Status:** Complete

### 2. Storage Functions
- **File:** `backend/src/mcq_assembler.py::store_mcqs_to_postgres()` ✅
- **File:** `backend/src/database/postgres_crud/mcq_stats.py::create_mcq()` ✅
- **Status:** Storage functions exist

### 3. Batch Generation
- **Function:** `MCQAssembler.assemble_mcqs_batch(limit)` ✅
- **Current Limit:** Default 10 (needs modification for bulk)
- **Status:** Function exists but needs bulk script

---

## ⚠️ Prerequisites to Verify

### 1. Vocabulary Data Coverage
**Action Required:** Run data quality check

```python
# Check how many senses can generate MCQs
- Senses with definition_zh: ? / 10,470
- Senses with example_en: ? / 10,470 (required for MEANING)
- Senses with connections.confused: 4,535 / 10,470 (for DISCRIMINATION)
```

**Actual Coverage (Verified):**
- **MEANING MCQ:** **100%** (10,470 senses - all have `example_en`)
- **USAGE MCQ:** ~30-40% (requires 4+ example sentences - needs verification)
- **DISCRIMINATION MCQ:** **43.3%** (4,535 senses with confused relationships)

### 2. Database Connection
**Action Required:** Verify `DATABASE_URL` is set

```bash
# Check environment variable
echo $DATABASE_URL
```

### 3. Bulk Generation Script
**Action Required:** Create script to process all senses

**Requirements:**
- Process all 10,470 senses
- Batch processing (e.g., 100 at a time)
- Progress tracking
- Error handling
- Resume capability (checkpoint)
- Skip already-generated MCQs

---

## 📋 Pre-Generation Verification Steps

### Step 1: Check Vocabulary Data Quality ✅ COMPLETE
**Results:**
- Total senses: 10,470
- With definition_zh: 9,990 (95.4%)
- With example_en: 10,470 (100.0%)
- With confused connections: 4,535 (43.3%)

### Step 2: Test MCQ Generation (Small Sample) ✅ COMPLETE
**Test Results:**
- Tested 5 senses
- Generated 8 MCQs (5 MEANING, 3 DISCRIMINATION)
- ✅ Generation working correctly

### Step 3: Verify Database Storage
```sql
-- Check if MCQs were stored
SELECT COUNT(*) FROM mcq_pool;
SELECT mcq_type, COUNT(*) FROM mcq_pool GROUP BY mcq_type;
```

### Step 4: Check Existing MCQs
```sql
-- Check how many MCQs already exist
SELECT 
    COUNT(DISTINCT sense_id) as senses_with_mcqs,
    COUNT(*) as total_mcqs
FROM mcq_pool
WHERE is_active = true;
```

---

## 🚀 Bulk Generation Plan

### Script Requirements
1. **Input:** All sense IDs from VocabularyStore
2. **Processing:**
   - Generate MCQs for each sense (8-15 per sense after enhanced enrichment)
   - Store to PostgreSQL
   - Track progress
3. **Output:**
   - Progress log
   - Summary statistics
   - Error report

### Estimated Output (After Enhanced Level 2 Enrichment)
- **Total Senses:** 10,470
- **Expected MCQs:**
  - MEANING: ~52,350-83,760 MCQs (5-8 per sense)
  - USAGE: ~10,470-31,410 MCQs (1-3 per sense)
  - DISCRIMINATION: ~9,070-13,605 MCQs (2-3 per sense)
- **Total:** ~104,700-157,050 MCQs (10-15 per sense average)

### Performance Estimate
- **Time per sense:** ~0.2-0.8 seconds (more MCQs per sense)
- **Total time:** ~30-60 minutes (with 10 workers)
- **With batching:** Parallelized for faster processing

---

## ✅ Summary

### Ready to Proceed?
- ✅ MCQ generation code is complete (enhanced for 8-15 MCQs per sense)
- ✅ Database schema is ready
- ✅ Storage functions exist
- ✅ Question templates are appropriate (no prompts to update)
- ✅ **Vocabulary data coverage verified** (100% for MEANING, 43.3% for DISCRIMINATION)
- ✅ **Bulk generation script created** (`backend/scripts/generate_all_mcqs.py`)
- ✅ **Script tested** (100 senses test successful)
- ✅ **Enhanced MCQ assembler** generates multiple MCQs per type
- ✅ **Distractor pool expanded** to 20-30 with unique subsets per MCQ
- 🟡 **Pending:** Run enhanced Level 2 enrichment for 5-8 examples per sense

### Next Steps
1. ✅ MCQ assembler enhanced for multiple MCQs per sense
2. ✅ Level 2 enrichment prompt updated for 5-8 examples
3. 🔄 Run enhanced Level 2 enrichment for all senses
4. 🔄 Regenerate all MCQs with enhanced assembler
5. 🔄 Verify 10-15 MCQs per sense average

---

**Note:** MCQ generation is **rule-based**, not AI-generated. The enhanced assembler generates 8-15 MCQs per sense by:
- Creating one MEANING MCQ per contextual example (5-8 examples = 5-8 MCQs)
- Creating multiple USAGE MCQs with different correct answers
- Creating multiple DISCRIMINATION MCQs (one per confused word relationship)
- Using different distractor subsets per MCQ to prevent pattern memorization

