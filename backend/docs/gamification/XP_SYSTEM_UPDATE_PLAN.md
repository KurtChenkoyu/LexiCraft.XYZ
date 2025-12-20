# XP System Update Plan - Unified Implementation

**Created:** December 20th, 2025  
**Status:** 📋 Planning  
**Priority:** 🔴 HIGH

---

## Overview

This plan unifies three design decisions:
1. **Frequency-aligned tier values** (reduce Tier 4 from 1000 to 300 XP)
2. **Effort vs. mastery separation** (add XP for words in progress)
3. **Complete XP award flow** (document all XP sources)

---

## Part 1: Update Tier Base XP Values

### Current State
```python
# backend/src/services/levels.py
TIER_BASE_XP = {
    1: 100,   # Basic Block
    2: 250,   # Multi-Block
    3: 500,   # Phrase Block
    4: 1000,  # Idiom Block ← TOO HIGH
    5: 300,   # Pattern Block
    6: 400,   # Register Block
    7: 750,   # Context Block
}
```

### Target State
```python
# backend/src/services/levels.py
TIER_BASE_XP = {
    1: 100,   # Basic Block (High Freq - Baseline)
    2: 120,   # Multi-Block (High Freq - Variant)
    3: 200,   # Phrase Block (Mid Freq - Combinatorial)
    4: 300,   # Idiom Block (Low Freq - Abstract)
    5: 150,   # Pattern Block (Mid Freq - Structural)
    6: 200,   # Register Block (Mid Freq - Social)
    7: 250,   # Context Block (Low Freq - Nuance)
}
```

### Files to Update
1. `backend/src/services/levels.py` - Update `TIER_BASE_XP` dictionary
2. `backend/scripts/backfill_xp_to_learners.py` - Uses `LevelService.TIER_BASE_XP` (auto-updates)
3. `backend/scripts/recalculate_block_values.py` - Update if it has hardcoded values
4. `backend/scripts/enrich_comprehensive_senses.py` - Update if it has hardcoded values
5. `backend/scripts/extract_comprehensive_senses.py` - Update if it has hardcoded values

### Impact
- ✅ **Future XP calculations** will use new values automatically
- ⚠️ **Historical backfilled XP** used old values (acceptable for beta)
- ✅ **No database migration needed** - XP is recalculated on-the-fly

---

## Part 2: Add "Word In Progress" XP

### Current State
- Words enter "in progress" status (`pending`, `hollow`, `learning`)
- No XP awarded for this engagement

### Target State
- Award **5 XP** when word status changes to `pending`, `hollow`, or `learning`
- This rewards effort/participation, not just mastery

### Implementation

**Location:** `backend/src/api/words.py` - `start_verification()` endpoint

**Current Flow:**
```python
# Word verification starts
# → Creates/updates learning_progress with status='pending'
# → Awards BASE_XP_WORD_LEARNED (15 XP) - may overlap with verification step XP
```

**Target Flow:**
```python
# Word verification starts
# → Creates/updates learning_progress with status='pending'
# → Awards 5 XP for "word in progress" (effort reward)
# → Later: Awards 10 XP per correct answer (verification step)
# → Later: Awards tier-based XP when verified (mastery reward)
```

**Code Changes:**
```python
# In backend/src/api/words.py - start_verification()

# After creating/updating learning_progress with status='pending'/'hollow'/'learning'
# Award "word in progress" XP (effort reward)
if learner_id:
    try:
        level_service.add_xp(learner_id, 5, 'word_in_progress', learning_point_id)
    except Exception as e:
        logger.error(f"Failed to award word-in-progress XP: {e}")
```

**New Constant:**
```python
# In backend/src/services/levels.py
XP_REWARDS = {
    'word_learned': 10,
    'word_in_progress': 5,  # NEW: Effort reward
    'streak': 5,
    'achievement': 0,
    'review': 15,
    'goal': 50,
    'daily_review': 20
}
```

### Files to Update
1. `backend/src/services/levels.py` - Add `'word_in_progress': 5` to `XP_REWARDS`
2. `backend/src/api/words.py` - Add XP award when word enters "in progress" status
3. `backend/scripts/backfill_xp_to_learners.py` - Add logic to award 5 XP for words in progress

---

## Part 3: Review & Clean Up Existing XP Awards

### Current Overlaps

1. **`BASE_XP_WORD_LEARNED = 15`** in `words.py`
   - Awards 15 XP when word verification starts
   - May overlap with verification step XP (10 XP per correct answer)
   - **Action:** Review if this should be removed or adjusted

2. **Verification Step XP** (`BASE_XP_CORRECT = 10`)
   - Awards 10 XP per correct answer
   - ✅ This is correct (effort reward)

3. **Tier-Based Mastery XP**
   - Awards tier-based XP when word is verified
   - ✅ This is correct (mastery reward)

### Recommended Changes

**Option A: Keep `BASE_XP_WORD_LEARNED` but reduce to 5 XP**
- Rename to `BASE_XP_WORD_IN_PROGRESS = 5`
- Aligns with "word in progress" XP concept

**Option B: Remove `BASE_XP_WORD_LEARNED`**
- Replace with "word in progress" XP (5 XP)
- Verification step XP (10 XP) handles effort during quiz
- Tier-based XP handles mastery

**Recommendation:** Option B (remove `BASE_XP_WORD_LEARNED`, use "word in progress" XP instead)

---

## Part 4: Update Backfill Script

### Current State
- Backfill script only awards XP for `verified`/`mastered`/`solid` words
- No XP for words in progress

### Target State
- Award 5 XP for each word in progress (`pending`, `hollow`, `learning`)
- Award tier-based XP for verified words (using new tier values)

### Changes Needed

**File:** `backend/scripts/backfill_xp_to_learners.py`

**Current Logic:**
```python
# Only processes verified/mastered/solid words
AND lp.status IN ('verified', 'mastered', 'solid')
```

**Target Logic:**
```python
# Process ALL words (in progress + verified)
# Award 5 XP for in-progress words
# Award tier-based XP for verified words
```

**Implementation:**
```python
# For each learner:
# 1. Get all words in progress
progress_result = db.execute(
    text("""
        SELECT learning_point_id, tier, status
        FROM learning_progress
        WHERE learner_id = :learner_id
        AND status IN ('pending', 'hollow', 'learning')
    """),
    {'learner_id': learner_id}
)

# Award 5 XP for each word in progress
for row in progress_result.fetchall():
    xp_entries.append({
        'learner_id': learner_id,
        'user_id': user_id,
        'xp_amount': 5,  # Effort reward
        'source': 'word_in_progress',
        'source_id': row[0],
        'earned_at': row[3] or NOW()
    })

# 2. Get all verified words (existing logic)
# Award tier-based XP
```

---

## Implementation Checklist

### Phase 1: Update Tier Values (Immediate)

- [ ] Update `TIER_BASE_XP` in `backend/src/services/levels.py`
- [ ] Check and update hardcoded tier values in scripts:
  - [ ] `backend/scripts/recalculate_block_values.py`
  - [ ] `backend/scripts/enrich_comprehensive_senses.py`
  - [ ] `backend/scripts/extract_comprehensive_senses.py`
- [ ] Test tier-based XP calculations with new values
- [ ] Verify backfill script uses new values (should auto-update)

### Phase 2: Add Word In Progress XP

- [ ] Add `'word_in_progress': 5` to `XP_REWARDS` in `levels.py`
- [ ] Update `start_verification()` in `words.py` to award 5 XP
- [ ] Review and remove/adjust `BASE_XP_WORD_LEARNED` (15 XP)
- [ ] Update backfill script to award 5 XP for words in progress
- [ ] Test: Word enters "in progress" → Check 5 XP awarded

### Phase 3: Documentation & Testing

- [ ] Update `XP_ACHIEVEMENT_QUICK_REFERENCE.md` ✅ (Done)
- [ ] Update `XP_SYSTEM_DESIGN.md` ✅ (Done)
- [ ] Test complete XP flow:
  - [ ] Word in progress → 5 XP
  - [ ] Correct answer → 10 XP
  - [ ] Word verified → Tier-based XP (100-300)
- [ ] Verify leaderboard calculations with new values
- [ ] Test backfill script with new tier values

---

## Testing Plan

### Test Case 1: Basic Word (Tier 1)

1. Start verification for Tier 1 word
   - Expected: +5 XP (word in progress)
2. Answer MCQ correctly
   - Expected: +10 XP (correct answer)
3. Word becomes verified
   - Expected: +100 XP (Tier 1 mastery)
   - **Total: 115 XP**

### Test Case 2: Idiom (Tier 4)

1. Start verification for Tier 4 idiom
   - Expected: +5 XP (word in progress)
2. Answer MCQ correctly
   - Expected: +10 XP (correct answer)
3. Idiom becomes verified
   - Expected: +300 XP (Tier 4 mastery - NEW VALUE)
   - **Total: 315 XP** (vs. old 1015 XP)

### Test Case 3: Backfill Script

1. Run backfill script
   - Expected: Awards 5 XP for all words in progress
   - Expected: Awards tier-based XP (new values) for verified words
   - Expected: Total XP recalculated correctly

---

## Rollout Strategy

### Step 1: Update Tier Values (Low Risk)
- ✅ Code change only
- ✅ No database migration
- ✅ Future XP uses new values
- ⚠️ Historical XP stays as-is (acceptable)

### Step 2: Add Word In Progress XP (Medium Risk)
- ✅ New feature, doesn't break existing
- ⚠️ Requires backfill for historical data
- ✅ Can be tested incrementally

### Step 3: Clean Up Overlaps (Low Risk)
- ✅ Remove/adjust `BASE_XP_WORD_LEARNED`
- ✅ Consolidate XP award logic

---

## Success Metrics

### Tier Value Update
- ✅ Tier 4 XP reduced from 1000 to 300 (70% reduction)
- ✅ Smooth progression: 100 → 120 → 150 → 200 → 200 → 250 → 300
- ✅ No "idiom hunting" for leaderboard manipulation

### Word In Progress XP
- ✅ All words in progress have 5 XP awarded
- ✅ Backfill script processes all words (not just verified)
- ✅ XP history shows "word_in_progress" entries

### Overall System
- ✅ Dual XP system (effort + mastery) fully implemented
- ✅ Frequency-aligned tier values
- ✅ Complete XP award flow documented

---

## References

- **Design Document:** `XP_SYSTEM_DESIGN.md`
- **Quick Reference:** `XP_ACHIEVEMENT_QUICK_REFERENCE.md`
- **Analysis:** `XP_ACHIEVEMENT_SYSTEM_ANALYSIS.md`
- **Implementation:** `backend/src/services/levels.py`

---

**Next Steps:**
1. Review and approve this plan
2. Update tier values (Part 1)
3. Add word in progress XP (Part 2)
4. Test and verify

---

**Document Version:** 1.0  
**Created:** December 20th, 2025

