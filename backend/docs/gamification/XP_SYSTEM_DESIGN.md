# XP System Design - Complete Specification

**Last Updated:** December 20th, 2025  
**Status:** ✅ Implemented (with pending updates)  
**Version:** 2.0 - Frequency-Aligned Dual Economy

---

## Executive Summary

LexiCraft uses a **dual XP system** that separates **effort rewards** (participation, engagement) from **mastery rewards** (verified learning). This design follows educational best practices (Khan Academy model) and ensures that:

1. **Effort is rewarded** - Users get XP for trying, not just succeeding
2. **Mastery is valued** - Verified words earn tier-based XP based on frequency/utility
3. **Frequency-aligned** - Common words (high utility) aren't undervalued compared to rare idioms
4. **Anti-gaming** - Prevents "idiom hunting" for leaderboard manipulation

---

## The Dual XP System

### Principle: Effort vs. Mastery Separation

Following Khan Academy's model, we separate:
- **Effort Points** (Energy Points) - For participation, attempts, engagement
- **Mastery Points** - For verified/completed learning

This ensures struggling learners are rewarded for effort, while successful learners are rewarded for mastery.

---

## XP Sources & Amounts

### 1. Effort-Based XP (Participation Rewards)

| Action | XP Amount | When Awarded | Status |
|--------|-----------|--------------|--------|
| **Correct answer in verification** | 10 XP | Every correct MCQ answer | ✅ Implemented |
| **Word enters "in progress"** | 5 XP | When word status changes to `pending`, `hollow`, or `learning` | ⏳ To Implement |
| **Review session started** | 5 XP | When user starts a review session | ⏳ Future Enhancement |

**Rationale:**
- Rewards engagement, not just success
- Encourages struggling learners to keep trying
- Builds growth mindset (effort matters)

---

### 2. Mastery-Based XP (Tier-Based Rewards)

| Tier | Type | Base XP | Frequency | Complexity | When Awarded |
|------|------|---------|-----------|------------|--------------|
| **1** | Basic Block | **100 XP** | High (A1-A2) | Low | When word reaches `verified`/`mastered`/`solid` |
| **2** | Multi-Block | **120 XP** | High | Low-Medium | When word with multiple meanings is verified |
| **5** | Pattern Block | **150 XP** | Mid | Medium | When morphological pattern is verified |
| **3** | Phrase Block | **200 XP** | Mid (B1) | Medium-High | When collocation/phrase is verified |
| **6** | Register Block | **200 XP** | Mid | Medium | When formal/informal variant is verified |
| **7** | Context Block | **250 XP** | Low (C1) | High | When context-specific meaning is verified |
| **4** | Idiom Block | **300 XP** | Low (C2) | Very High | When idiomatic expression is verified |

**Frequency-Aligned Design Logic:**
- **High frequency words** (Tier 1-2): Foundation of language. Most utility. Base rewards.
- **Mid frequency** (Tier 3, 5-6): Common but specialized. Moderate rewards.
- **Low frequency** (Tier 4, 7): Advanced/abstract. Higher rewards but not "jackpot" (max 3x base).

**Why This Works:**
1. **Fairness**: Learning "cat" (100 XP) vs. "raining cats and dogs" (300 XP) feels proportional (1 word vs. 3-4 words)
2. **Anti-Gaming**: Prevents users from "hunting idioms" just to spike leaderboard rank
3. **Sustainability**: Gap between Level 1 and Level 50 won't be broken by a few lucky idiom finds
4. **Utility-Aligned**: Rewards reflect actual language utility, not just difficulty

---

### 3. Activity-Based XP

| Action | XP Amount | When Awarded | Status |
|--------|-----------|--------------|--------|
| **Streak day** | 5 XP | Daily streak maintained | ⏳ To Implement |
| **Daily review completed** | 20 XP | Complete daily review session | ⏳ To Implement |
| **Achievement unlocked** | 25-500 XP | Achievement milestone reached | ✅ Implemented |
| **Goal completed** | 50 XP | Learning goal achieved | ✅ Implemented |

---

## XP Award Flow

### Word Learning Journey

```
1. User starts verification
   └─> No XP (just starting)

2. User answers MCQ correctly
   └─> +10 XP (Effort: correct answer)

3. Word status changes to "pending"/"hollow"/"learning"
   └─> +5 XP (Effort: word in progress)
   
4. Word status changes to "verified"/"mastered"/"solid"
   └─> +Tier XP (Mastery: 100-300 XP based on tier)
```

**Total XP for a Basic Word (Tier 1):**
- Correct answer: 10 XP
- In progress: 5 XP
- Verified: 100 XP
- **Total: 115 XP**

**Total XP for an Idiom (Tier 4):**
- Correct answer: 10 XP
- In progress: 5 XP
- Verified: 300 XP
- **Total: 315 XP**

---

## Implementation Status

### ✅ Implemented

1. **Verification Step XP** (`BASE_XP_CORRECT = 10`)
   - Location: `backend/src/api/mcq.py`
   - Awards 10 XP per correct answer
   - Includes speed trap (no XP if < 1500ms)

2. **Word Learned XP** (`BASE_XP_WORD_LEARNED = 15`)
   - Location: `backend/src/api/words.py`
   - Awards 15 XP when word verification starts
   - Note: This may overlap with verification step XP - needs review

3. **Tier-Based Mastery XP** (`TIER_BASE_XP`)
   - Location: `backend/src/services/levels.py`
   - Awards tier-based XP when word is verified
   - **Current values need updating** (see below)

4. **Achievement & Goal XP**
   - Fully implemented and working

### ⏳ To Implement

1. **Word In Progress XP** (5 XP)
   - When word status changes to `pending`, `hollow`, or `learning`
   - Location: `backend/src/api/words.py` (start_verification) or progress update logic

2. **Streak XP** (5 XP/day)
   - Daily streak maintenance
   - Location: `backend/src/services/learning_velocity.py`

3. **Review Session XP** (20 XP)
   - Complete daily review session
   - Location: Review completion endpoints

### 🔄 Needs Update

1. **TIER_BASE_XP Values**
   - Current: Tier 4 (Idiom) = 1000 XP (10x base) - **Too high**
   - Proposed: Tier 4 (Idiom) = 300 XP (3x base) - **Frequency-aligned**
   - See "Tier Value Updates" section below

---

## Tier Value Updates

### Current Values (Outdated)

```python
TIER_BASE_XP = {
    1: 100,   # Basic Block
    2: 250,   # Multi-Block
    3: 500,   # Phrase Block
    4: 1000,  # Idiom Block ← TOO HIGH (10x base)
    5: 300,   # Pattern Block
    6: 400,   # Register Block
    7: 750,   # Context Block
}
```

**Problems:**
- Tier 4 (Idiom) at 1000 XP is 10x base - creates "jackpot" effect
- Tier 5 (Pattern) at 300 XP is lower than Tier 3 (500 XP) - breaks progression
- Not aligned with frequency/utility

### Proposed Values (Frequency-Aligned)

```python
TIER_BASE_XP = {
    1: 100,   # Basic Block (High Freq - Baseline)
    2: 120,   # Multi-Block (High Freq - Variant)
    3: 200,   # Phrase Block (Mid Freq - Combinatorial)
    4: 300,   # Idiom Block (Low Freq - Abstract) ← REDUCED from 1000
    5: 150,   # Pattern Block (Mid Freq - Structural)
    6: 200,   # Register Block (Mid Freq - Social)
    7: 250,   # Context Block (Low Freq - Nuance)
}
```

**Benefits:**
- Smooth progression: 100 → 120 → 150 → 200 → 200 → 250 → 300
- Frequency-aligned: High utility words aren't undervalued
- Anti-gaming: No "idiom hunting" for leaderboard manipulation
- Sustainable: Balanced level progression

---

## Connection Bonuses

In addition to base tier XP, words can earn **connection bonuses**:

| Connection Type | Bonus XP | Example |
|----------------|----------|---------|
| Related word | +10 XP | "break" related to "fracture" |
| Opposite word | +10 XP | "break" opposite to "repair" |
| Part of phrase | +20 XP | "break" in "break the ice" |
| Part of idiom | +30 XP | "break" in "break a leg" |
| Morphological | +10 XP | "break" → "breakable" |
| Register variant | +10 XP | "break" (informal) vs. "fracture" (formal) |

**Total XP Formula:**
```
Total XP = Base Tier XP + Sum(Connection Bonuses)
```

**Example:**
- "break" (Tier 2: Multi-Block) = 120 base XP
- 5 related words = +50 XP
- 2 phrases = +40 XP
- **Total: 210 XP**

---

## Level Progression

**Formula:** `100 + (N-1) × 50` XP per level

| Level | XP Needed | Cumulative XP |
|-------|-----------|---------------|
| 1 | 100 | 0-99 |
| 2 | 150 | 100-249 |
| 3 | 200 | 250-449 |
| 10 | 550 | 2,250-2,799 |
| 20 | 1,050 | 9,500-10,549 |

**With New Tier Values:**
- Level 1: ~1 Basic word (100 XP)
- Level 2: ~2 Basic words (200 XP)
- Level 10: ~20-25 Basic words (2,000-2,500 XP)
- Level 20: ~50-60 Basic words (5,000-6,000 XP)

---

## Design Principles

### 1. Frequency = Utility
High-frequency words (Tier 1-2) are the foundation of language. They deserve solid rewards, not just "starter" rewards.

### 2. Effort Matters
Struggling learners should be rewarded for trying, not just succeeding. This builds growth mindset.

### 3. Anti-Gaming
No "jackpot" rewards that encourage exploitation. Smooth progression prevents leaderboard manipulation.

### 4. Sustainable Economy
XP values should create balanced progression. Users shouldn't hit walls or get stuck.

### 5. Educational Alignment
XP should reflect learning value, not just difficulty. A common word is more valuable than a rare idiom.

---

## Migration Notes

### Backfill Impact

When updating `TIER_BASE_XP` values:
1. **Historical XP** - Already calculated with old values (acceptable for beta)
2. **Future XP** - Will use new values automatically
3. **No recalculation needed** - Historical data stays as-is

### Backfill Script Update

The backfill script (`backend/scripts/backfill_xp_to_learners.py`) uses `LevelService.TIER_BASE_XP` directly, so:
- ✅ New values will be used automatically
- ✅ No script changes needed
- ⚠️ Historical backfilled data used old values (acceptable)

---

## References

- **Khan Academy Model**: Separates "mastery points" from "energy points"
- **Educational Best Practices**: Effort-based rewards for growth mindset
- **Frequency Analysis**: CEFR levels and corpus frequency data
- **Gaming Industry**: Balanced progression curves, anti-exploitation

---

## Next Steps

1. ✅ **Update `TIER_BASE_XP` values** in `backend/src/services/levels.py`
2. ⏳ **Implement "Word In Progress" XP** (5 XP when status changes)
3. ⏳ **Review `BASE_XP_WORD_LEARNED`** - May overlap with verification step XP
4. ⏳ **Update documentation** in other gamification docs
5. ⏳ **Test XP calculations** with new tier values

---

**Document Version:** 2.0  
**Last Updated:** December 20th, 2025  
**Next Review:** After tier value updates

