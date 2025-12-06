# Pipeline V2 Quality Review - Findings Summary

**Date**: 2025-12-07  
**Status**: Pipeline stopped for review  
**Progress**: 1,034 / 3,495 words (29.59%)  
**Senses Generated**: 2,929

---

## Executive Summary

The pipeline is generating vocabulary data successfully, but **Chinese translations have quality issues** (~8% problematic). The examples are good (Taiwan context), but the CC-CEDICT lookup algorithm is picking wrong translations.

---

## What's Working Well ✅

### 1. Examples (Excellent Quality)
- **Taiwan context**: Examples reference 學測, LINE, 捷運, 珍珠奶茶, 小七, 補習班
- **Natural sentences**: Conversational, relatable for B1/B2 students
- **Clear meaning**: Examples clearly demonstrate the word sense

**Example:**
```
Example EN: I'm super busy this month with midterms and my社團 performance.
Example ZH: 這個月我超忙，因為要期中考還有社團表演。
```

### 2. Sense Selection
- AI is selecting appropriate senses for B1/B2 learners
- Avoiding academic/obscure meanings
- Good balance of POS (nouns, verbs, adjectives)

### 3. Definition Simplification
- Definitions are simplified to B1/B2 level
- Clear and concise (15 words or less)
- Appropriate for learners

### 4. Pipeline Infrastructure
- Auto-restart working
- Checkpoint/resume working
- Status tracking working
- No crashes or errors

---

## Critical Issues Found ❌

### 1. Chinese Translation Quality (~8% problematic)

**Problem**: CC-CEDICT lookup is returning wrong translations.

**Examples of Bad Translations:**
- `"popular"` → `"愛玉冰"` (aiyu jelly) ❌ Should be: `"受歡迎的"` or `"流行的"`
- `"month"` → `"上浣"` (first 10 days of month) ❌ Should be: `"月"` or `"月份"`
- `"therefore"` → `"糠"` (chaff/spongy radish) ❌ Should be: `"所以"` or `"因此"`
- `"especially"` → `"省察"` (self-examination) ❌ Should be: `"尤其"` or `"特別"`
- `"cities"` → `"大安"` (Da'an district name) ❌ Should be: `"城市"`
- `"peak"` → `"友誼峰"` (Friendship Peak mountain) ❌ Should be: `"高峰"` or `"頂峰"`

**Root Cause**: CC-CEDICT is a **Chinese→English** dictionary, and we're reverse-indexing it. The scoring algorithm is flawed:

```python
# Current flawed scoring:
overlap = len(def_words & entry_words)  # Counts matching words
score = overlap / max(len(def_words), 1)
if word in entry['definition']:
    score += 0.5
```

**Why "therefore" → "糠" gets picked:**
- Definition: "as a consequence" → words: `{'a', 'as', 'consequence'}`
- Entry: "(of a radish etc) spongy (and **therefore** unappetising)"
- Overlap: `{'a'}` (just the stop word "a"!)
- Score: 1/3 + 0.5 = **0.83** (highest!)
- Correct matches like "所以" only get 0.5 (no overlap, just bonus)

**Issues with Current Algorithm:**
1. **Stop words inflate scores**: "a", "the", "of", "and" create false matches
2. **No priority for primary meanings**: Entries where word is main translation should rank higher
3. **Word overlap too simple**: "consequence" should match "therefore" semantically, not just literally

### 2. AI Validator Not Strict Enough

The translation validator is supposed to catch bad translations, but it's approving them:
- Status shows 94.5% validated, but many have wrong Chinese
- Validator prompt may not be strict enough
- May be approving CC-CEDICT translations without proper checking

---

## Statistics

### Current Progress
- **Words processed**: 1,034 / 3,495 (29.59%)
- **Senses created**: 2,929 (~2.8 per word)
- **Validation rate**: 94.5% (2,767 validated / 162 failed)
- **Problematic Chinese**: ~240 senses (~8%)
- **AI calls**: 8,868
- **Estimated cost**: $0.89 USD (~NT$28)

### Quality Breakdown
- ✅ **Examples**: Excellent (Taiwan context, natural)
- ✅ **Definitions**: Good (B1/B2 level, clear)
- ✅ **Sense selection**: Good (appropriate for learners)
- ❌ **Chinese translations**: **Needs improvement** (~8% wrong)

---

## Comparison: V1 vs V2 Prompts

### V1 Prompt (from `src/agent.py`)
**Strengths:**
- Two Chinese versions: `definition_zh_translation` + `definition_zh_explanation`
- Connection pathway instructions for idioms (literal → metaphorical → idiomatic)
- Detailed instructions about avoiding disconnection statements
- More pedagogical guidance
- Better handling of polysemy

**Example V1 output structure:**
```json
{
  "definition_zh_translation": "字面翻譯",
  "definition_zh_explanation": "意思說明（包含連接路徑）",
  "example_zh_translation": "字面翻譯",
  "example_zh_explanation": "意思說明（包含文化背景）"
}
```

### V2 Prompt (Current)
**Strengths:**
- Modular (separate steps: select → simplify → translate → validate)
- Uses CC-CEDICT as authority source
- Simpler, more focused

**Weaknesses:**
- Only one Chinese translation (no explanation)
- No connection pathway logic
- CC-CEDICT lookup is flawed
- Validator not strict enough

---

## Recommendations

### Immediate Fixes (Before Resuming)

1. **Fix CC-CEDICT Scoring Algorithm**
   - Ignore stop words in overlap calculation
   - Prioritize entries where word is PRIMARY meaning (not just mentioned)
   - Add semantic matching (e.g., "consequence" → "therefore")
   - Weight exact matches higher

2. **Strengthen AI Validator**
   - Make it more strict about checking if translation matches definition
   - Add explicit checks for single characters, place names, wrong meanings
   - Require validator to explain why it approves/rejects

3. **Consider V1 Approach for Chinese**
   - Add `definition_zh_explanation` field (like V1)
   - Use connection pathway logic for idioms
   - Two-step Chinese: literal + explanation

### Long-term Improvements

1. **Better CC-CEDICT Integration**
   - Use a proper English→Chinese dictionary if available
   - Or improve reverse-indexing with better scoring
   - Consider using multiple sources (CC-CEDICT + AI generation)

2. **Quality Assurance**
   - Add automated quality checks (flag single characters, place names, etc.)
   - Human review of top 500 words
   - Validation report with problematic entries

---

## Files Generated

- `backend/logs/checkpoint_samples.txt` - List of problematic Chinese definitions
- `backend/logs/checkpoint_samples_full.txt` - Full detailed samples for review
- `backend/logs/enrichment_checkpoint.json` - Current progress (2,929 senses)
- `backend/logs/pipeline_status.json` - Pipeline status

---

## Next Steps

1. ✅ **Review samples** in `logs/checkpoint_samples.txt`
2. ⏸️ **Fix CC-CEDICT scoring** algorithm
3. ⏸️ **Strengthen AI validator** prompt
4. ⏸️ **Test fixes** on small batch (50 words)
5. ⏸️ **Resume pipeline** with improved prompts

---

## Cost Estimate (If We Continue)

- **Current**: $0.89 USD for 1,034 words
- **Remaining**: ~2,461 words × $0.00086/word = **~$2.12 USD** (~NT$68)
- **Total for 3,500 words**: ~$3 USD (~NT$96)

Very affordable! But we should fix quality issues first.

