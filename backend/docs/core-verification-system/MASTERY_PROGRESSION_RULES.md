# Mastery Progression Rules

This document describes the exact rules and thresholds for mastery level progression in the spaced repetition system. Mastery levels indicate how well a user knows a word, and they are calculated differently for SM-2+ and FSRS algorithms.

## Table of Contents

- [Mastery Level Overview](#mastery-level-overview)
- [SM-2+ Mastery Calculation](#sm-2-mastery-calculation)
- [FSRS Mastery Calculation](#fsrs-mastery-calculation)
- [Algorithm Differences](#algorithm-differences)
- [Mastery Level Changes](#mastery-level-changes)
- [Mapping to learning_progress.status](#mapping-to-learning_progressstatus)
- [Examples](#examples)

---

## Mastery Level Overview

The system uses five mastery levels (plus a special "leech" status):

| Level | Description | Typical State |
|-------|-------------|---------------|
| `learning` | Just started learning, early stages | First few reviews |
| `familiar` | User has seen it a few times correctly | 3-4 consecutive correct |
| `known` | User knows it well, medium-term memory | 5+ consecutive correct, shorter intervals |
| `mastered` | Strong long-term memory | Long intervals (180+ days) |
| `permanent` | Very strong, near-permanent memory | Very long intervals (730+ days) |
| `leech` | Problematic word, repeatedly fails | Special status, overrides all levels |

**Note:** The `MasteryLevel` enum in `algorithm_interface.py` defines these as integers (0-4), but the actual implementation uses string values.

---

## SM-2+ Mastery Calculation

**Location:** `backend/src/spaced_repetition/algorithm_interface.py` (lines 252-270)

SM-2+ uses the base class `calculate_mastery_level()` method, which relies on:
- `consecutive_correct`: Number of consecutive correct reviews
- `current_interval`: Days until next review
- `is_leech`: Whether the card is marked as a leech

### SM-2+ Thresholds

```python
def calculate_mastery_level(self, state: CardState) -> str:
    if state.is_leech:
        return 'leech'
    
    if state.consecutive_correct < 3:
        return 'learning'
    elif state.consecutive_correct < 5:
        return 'familiar'
    elif state.current_interval < 180:
        return 'known'
    elif state.current_interval < 365 * 2:  # 730 days
        return 'mastered'
    else:
        return 'permanent'
```

### Exact Thresholds

| Mastery Level | Consecutive Correct | Current Interval | Notes |
|---------------|---------------------|------------------|-------|
| `learning` | < 3 | Any | Early learning stage |
| `familiar` | 3-4 | Any | User is getting familiar |
| `known` | ≥ 5 | < 180 days | Well-known, but not yet long-term |
| `mastered` | ≥ 5 | 180-729 days | Strong long-term memory |
| `permanent` | ≥ 5 | ≥ 730 days (2 years) | Near-permanent memory |
| `leech` | N/A | N/A | Overrides all (if `is_leech = True`) |

### Key Points

1. **Consecutive Correct is Primary**: The first gate is `consecutive_correct`. You need at least 3 consecutive correct to move beyond `learning`, and at least 5 to reach `known` or higher.

2. **Interval is Secondary**: Once you have 5+ consecutive correct, the interval determines whether you're `known`, `mastered`, or `permanent`.

3. **Resets on Failure**: If a review is incorrect (rating < `GOOD`), `consecutive_correct` resets to 0, which can drop mastery back to `learning`.

4. **Leech Override**: If `is_leech = True`, the mastery level is always `leech`, regardless of other factors.

---

## FSRS Mastery Calculation

**Location:** `backend/src/spaced_repetition/fsrs_service.py` (lines 323-343)

FSRS uses a custom `_calculate_fsrs_mastery()` method that relies on:
- `stability`: Memory stability in days (FSRS-specific metric)
- `is_leech`: Whether the card is marked as a leech

### FSRS Thresholds

```python
def _calculate_fsrs_mastery(self, state: CardState) -> str:
    if state.is_leech:
        return 'leech'
    
    stability = state.stability or 0
    
    if stability < 5:  # Less than 5 days stability
        return 'learning'
    elif stability < 30:  # Less than 1 month
        return 'familiar'
    elif stability < 180:  # Less than 6 months
        return 'known'
    elif stability < 730:  # Less than 2 years
        return 'mastered'
    else:
        return 'permanent'
```

### Exact Thresholds

| Mastery Level | Stability (days) | Description |
|---------------|-------------------|-------------|
| `learning` | < 5 | Very short-term memory |
| `familiar` | 5-29 | Short-term memory (< 1 month) |
| `known` | 30-179 | Medium-term memory (< 6 months) |
| `mastered` | 180-729 | Long-term memory (< 2 years) |
| `permanent` | ≥ 730 | Very long-term memory (≥ 2 years) |
| `leech` | N/A | Overrides all (if `is_leech = True`) |

### Key Points

1. **Stability is Primary**: FSRS uses `stability` (memory strength in days) as the sole metric for mastery progression. This is calculated by the FSRS algorithm based on review history.

2. **No Consecutive Correct Dependency**: Unlike SM-2+, FSRS doesn't explicitly track `consecutive_correct` for mastery (though it's still tracked for other purposes). The stability metric already incorporates review performance.

3. **Stability Increases with Success**: Each successful review increases stability. The rate of increase depends on:
   - Current stability
   - Word difficulty
   - Elapsed time since last review
   - Performance rating

4. **Stability Decreases with Failure**: Failed reviews reduce stability, which can cause mastery to drop.

5. **Leech Override**: Same as SM-2+, `is_leech = True` overrides to `leech`.

---

## Algorithm Differences

### Summary Table

| Aspect | SM-2+ | FSRS |
|--------|-------|------|
| **Primary Metric** | `consecutive_correct` + `current_interval` | `stability` (days) |
| **Calculation Method** | Base class `calculate_mastery_level()` | Custom `_calculate_fsrs_mastery()` |
| **Learning Threshold** | < 3 consecutive correct | < 5 days stability |
| **Familiar Threshold** | 3-4 consecutive correct | 5-29 days stability |
| **Known Threshold** | ≥ 5 consecutive correct AND < 180 days interval | 30-179 days stability |
| **Mastered Threshold** | ≥ 5 consecutive correct AND 180-729 days interval | 180-729 days stability |
| **Permanent Threshold** | ≥ 5 consecutive correct AND ≥ 730 days interval | ≥ 730 days stability |
| **Failure Impact** | Resets `consecutive_correct` to 0 | Reduces `stability` |
| **Progression Speed** | Can be faster (3-5 reviews to familiar/known) | More gradual (stability grows incrementally) |

### Key Differences

1. **Metric Used**:
   - **SM-2+**: Uses discrete counts (`consecutive_correct`) and intervals
   - **FSRS**: Uses continuous stability metric (learned from review history)

2. **Progression Logic**:
   - **SM-2+**: Two-stage check (consecutive correct first, then interval)
   - **FSRS**: Single-stage check (stability only)

3. **Failure Handling**:
   - **SM-2+**: Hard reset of `consecutive_correct` to 0 on failure
   - **FSRS**: Gradual reduction of stability (doesn't reset completely)

4. **Speed to Higher Levels**:
   - **SM-2+**: Can reach `known` in 5 consecutive correct reviews (if interval grows quickly)
   - **FSRS**: Stability grows more gradually, typically requiring more reviews to reach higher stability values

5. **Predictability**:
   - **SM-2+**: More predictable (explicit thresholds)
   - **FSRS**: Less predictable (stability depends on FSRS internal calculations)

---

## Mastery Level Changes

### When Mastery Level Changes

Mastery level is recalculated **after every review** in both algorithms:

1. **SM-2+** (`sm2_service.py`, line 173):
   ```python
   old_mastery = state.mastery_level
   new_state.mastery_level = self.calculate_mastery_level(new_state)
   mastery_changed = old_mastery != new_state.mastery_level
   ```

2. **FSRS** (`fsrs_service.py`, line 275):
   ```python
   old_mastery = state.mastery_level
   new_state.mastery_level = self._calculate_fsrs_mastery(new_state)
   mastery_changed = old_mastery != new_state.mastery_level
   ```

### What Triggers Changes

#### SM-2+ Triggers

1. **Consecutive Correct Changes**:
   - **Increases**: Each correct review (rating ≥ `GOOD`) increments `consecutive_correct`
   - **Decreases**: Any incorrect review (rating < `GOOD`) resets `consecutive_correct` to 0
   - **Impact**: Can cause transitions: `learning` ↔ `familiar` ↔ `known` ↔ `mastered` ↔ `permanent`

2. **Interval Growth**:
   - As intervals grow with successful reviews, mastery can progress from `known` → `mastered` → `permanent`
   - Interval growth depends on ease factor and previous interval

3. **Leech Detection**:
   - If leech conditions are met, mastery becomes `leech`
   - Leech conditions: consecutive failures, low ease factor, or poor overall performance

#### FSRS Triggers

1. **Stability Changes**:
   - **Increases**: Successful reviews increase stability (rate depends on current stability, difficulty, elapsed time)
   - **Decreases**: Failed reviews decrease stability
   - **Impact**: Stability changes directly map to mastery level changes

2. **Time-Based Decay**:
   - FSRS considers elapsed time since last review
   - Longer gaps may affect stability calculations

3. **Leech Detection**:
   - Same as SM-2+: if leech conditions are met, mastery becomes `leech`

### Mastery Progression Examples

#### SM-2+ Example

```
Review 1: GOOD → consecutive_correct = 1 → mastery = 'learning'
Review 2: GOOD → consecutive_correct = 2 → mastery = 'learning'
Review 3: GOOD → consecutive_correct = 3 → mastery = 'familiar'
Review 4: GOOD → consecutive_correct = 4 → mastery = 'familiar'
Review 5: GOOD → consecutive_correct = 5, interval = 7 → mastery = 'known'
Review 6: GOOD → consecutive_correct = 6, interval = 200 → mastery = 'mastered'
Review 7: AGAIN → consecutive_correct = 0 → mastery = 'learning' (reset!)
```

#### FSRS Example

```
Review 1: GOOD → stability = 2.5 → mastery = 'learning'
Review 2: GOOD → stability = 4.2 → mastery = 'learning'
Review 3: GOOD → stability = 8.1 → mastery = 'familiar'
Review 4: GOOD → stability = 25.3 → mastery = 'familiar'
Review 5: GOOD → stability = 45.7 → mastery = 'known'
Review 6: GOOD → stability = 120.4 → mastery = 'known'
Review 7: AGAIN → stability = 15.2 → mastery = 'familiar' (reduced, not reset)
```

---

## Mapping to learning_progress.status

**Location:** `backend/src/api/verification.py` (lines 298-308)

The `learning_progress.status` field is separate from mastery level but can be used to derive mastery in some contexts:

```python
# Derive mastery_level from status or tier
status = row[4] or 'learning'
tier = row[5] or 0
if status == 'mastered' or tier >= 5:
    mastery = 'mastered'
elif status == 'known' or tier >= 3:
    mastery = 'known'
elif tier >= 1:
    mastery = 'familiar'
else:
    mastery = 'learning'
```

### Status Values

The `learning_progress.status` field can have these values:
- `'learning'`: Word is being learned
- `'pending'`: Verification is pending
- `'verified'`: Verification completed
- `'failed'`: Verification failed

### Tier Values

The `learning_progress.tier` field is an integer (0-5) that indicates mastery level:
- `0`: Learning
- `1-2`: Familiar
- `3-4`: Known
- `5`: Mastered

### Relationship

**Important**: The mastery level stored in `verification_schedule.mastery_level` is the **source of truth** for spaced repetition. The `learning_progress.status` and `tier` fields are separate and may not always be in sync.

- **Mastery Level** (`verification_schedule.mastery_level`): Calculated by the algorithm after each review
- **Status** (`learning_progress.status`): Tracks verification workflow state
- **Tier** (`learning_progress.tier`): May be derived from mastery level or set independently

---

## Examples

### Example 1: SM-2+ Progression to Mastered

```python
# Initial state
card = CardState(
    consecutive_correct=0,
    current_interval=1,
    is_leech=False
)
# mastery = 'learning'

# After 3 correct reviews
card.consecutive_correct = 3
# mastery = 'familiar'

# After 5 correct reviews, interval grows
card.consecutive_correct = 5
card.current_interval = 100
# mastery = 'known'

# Interval continues growing
card.current_interval = 200
# mastery = 'mastered'

# Very long interval
card.current_interval = 800
# mastery = 'permanent'
```

### Example 2: FSRS Progression to Mastered

```python
# Initial state
card = CardState(
    stability=0.5,
    is_leech=False
)
# mastery = 'learning'

# Stability grows with successful reviews
card.stability = 8.0
# mastery = 'familiar'

card.stability = 50.0
# mastery = 'known'

card.stability = 200.0
# mastery = 'mastered'

card.stability = 800.0
# mastery = 'permanent'
```

### Example 3: Failure Impact (SM-2+)

```python
# User has mastered word
card = CardState(
    consecutive_correct=10,
    current_interval=300,
    is_leech=False
)
# mastery = 'mastered'

# User fails review
# consecutive_correct resets to 0
card.consecutive_correct = 0
# mastery = 'learning' (hard reset!)
```

### Example 4: Failure Impact (FSRS)

```python
# User has mastered word
card = CardState(
    stability=250.0,
    is_leech=False
)
# mastery = 'mastered'

# User fails review
# Stability reduces but doesn't reset completely
card.stability = 80.0
# mastery = 'known' (gradual reduction)
```

### Example 5: Leech Override

```python
# User has high mastery
card = CardState(
    consecutive_correct=10,
    current_interval=500,
    stability=600.0,
    is_leech=True
)
# mastery = 'leech' (overrides all other factors)
```

---

## Summary

### Quick Reference: SM-2+ Thresholds

| Level | Condition |
|-------|-----------|
| `learning` | `consecutive_correct < 3` |
| `familiar` | `3 ≤ consecutive_correct < 5` |
| `known` | `consecutive_correct ≥ 5` AND `current_interval < 180` |
| `mastered` | `consecutive_correct ≥ 5` AND `180 ≤ current_interval < 730` |
| `permanent` | `consecutive_correct ≥ 5` AND `current_interval ≥ 730` |
| `leech` | `is_leech = True` (overrides all) |

### Quick Reference: FSRS Thresholds

| Level | Condition |
|-------|-----------|
| `learning` | `stability < 5` |
| `familiar` | `5 ≤ stability < 30` |
| `known` | `30 ≤ stability < 180` |
| `mastered` | `180 ≤ stability < 730` |
| `permanent` | `stability ≥ 730` |
| `leech` | `is_leech = True` (overrides all) |

### Key Takeaways

1. **SM-2+** uses discrete thresholds based on consecutive correct counts and intervals
2. **FSRS** uses continuous stability metric based on learned memory strength
3. **Mastery is recalculated after every review**
4. **Failures reset SM-2+ consecutive count but only reduce FSRS stability**
5. **Leech status overrides all mastery levels**
6. **Mastery level is stored in `verification_schedule.mastery_level`** (separate from `learning_progress.status`)

---

## Related Documentation

- `backend/src/spaced_repetition/algorithm_interface.py` - Base interface and common mastery calculation
- `backend/src/spaced_repetition/sm2_service.py` - SM-2+ implementation
- `backend/src/spaced_repetition/fsrs_service.py` - FSRS implementation
- `backend/tests/spaced_repetition/test_sm2_service.py` - Test cases for mastery calculation
- `backend/docs/core-verification-system/WORD_VERIFICATION_SYSTEM.md` - Overall system documentation

