# Data Quality Issues Report

**Generated:** 2025-01-XX  
**Status:** 1,320 words with mismatched sense IDs (1,928 total mismatched senses)

---

## Summary

Many words in the database have **wrong definitions** because they're using shared WordNet senses that don't match the word's primary meaning. This happens when:

1. WordNet shares senses between related words (e.g., "brave" shares a sense with "weather" meaning "to endure")
2. The enrichment process enriched the wrong/shared sense instead of the word's primary sense
3. The sense_id doesn't match the word name pattern (e.g., `weather.v.01` for "brave" instead of `brave.n.01`)

---

## Issues Found

### 1. Mismatched Sense IDs ⚠️

**Problem:** Words are using sense IDs that don't match their name pattern.

**Examples:**
- **brave**: Using `weather.v.01` (to endure/weather) instead of `brave.n.01` or `brave.a.01` (courageous)
- **bread**: Using `boodle.n.01` (slang for money) instead of `bread.n.01` (food)
- **creature**: Using `animal.n.01` instead of `creature.n.01`
- **bother**: Using `fuss.n.02` instead of `bother.n.01` or `bother.v.01`

**Impact:** High - Users see wrong definitions in surveys

**Affected Words:** 1,320 words (out of ~8,000 total)

---

## How to Fix

### Option 1: Fix Individual Words (Recommended for Testing)

```bash
# Check a specific word
cd backend
python3 scripts/fix_data_quality.py --word brave

# Fix a specific word (dry run first)
python3 scripts/fix_data_quality.py --word brave --dry-run

# Actually fix it
python3 scripts/fix_data_quality.py --word brave --force
```

### Option 2: Check All Problematic Words

```bash
# List all words with issues
python3 scripts/fix_data_quality.py --check-all
```

### Option 3: Batch Fix (Future Enhancement)

The script currently supports fixing one word at a time. For batch fixing, you would need to:

1. Get list of problematic words
2. Loop through and fix each one
3. Monitor API rate limits

---

## What the Fix Script Does

1. **Checks current state**: Shows what senses the word currently has
2. **Fetches fresh skeletons**: Gets WordNet data for the word
3. **Filters to matching senses**: Only uses senses where `sense_id` starts with the word name
4. **Re-enriches**: Calls Gemini API to get correct Chinese definitions
5. **Updates database**: Saves the corrected definitions

---

## Priority Words to Fix

Based on survey usage, these words should be fixed first:

1. **brave** (rank 7817) - Wrong: "to endure" → Should be: "courageous"
2. **bread** (rank 3936) - Wrong: "money slang" → Should be: "food"
3. **creature** (rank 7861) - Wrong: generic "animal" → Should be: "living being"
4. **bother** (rank 7948) - Check if definition is correct
5. **possess** (rank 7633) - Check if definition is correct

---

## Root Cause

The issue occurs because:

1. **WordNet structure**: WordNet groups related words under shared synsets
2. **Enrichment process**: The agent enriched the first available sense, which might be a shared one
3. **No validation**: There was no check to ensure sense_id matches word name

---

## Prevention

The survey engine now has a fix (in `lexisurvey_engine.py` line 546-555) that prioritizes senses where `sense_id` starts with the word name. However, this doesn't fix existing bad data - it just prefers correct senses when they exist.

---

## Next Steps

1. **Immediate**: Fix high-priority words manually using the script
2. **Short-term**: Create a batch fix script for common problematic words
3. **Long-term**: Re-run enrichment for all words with mismatched senses (requires API credits)

---

## Script Usage Examples

```bash
# Check what's wrong with "brave"
python3 scripts/fix_data_quality.py --word brave

# See what would be fixed (dry run)
python3 scripts/fix_data_quality.py --word brave --dry-run

# Actually fix it (requires --force to re-enrich already-enriched senses)
python3 scripts/fix_data_quality.py --word brave --force

# Check all problematic words
python3 scripts/fix_data_quality.py --check-all
```

