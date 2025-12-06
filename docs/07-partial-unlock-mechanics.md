# Partial Unlock Mechanics: Points & Deficit System

## Overview

**Problem**: 14+ day verification feels too long for kids
**Solution**: Partial unlock with early withdrawal + deficit penalty if verification fails

**Key Innovation**: Kids can withdraw points early, but face deficit if they don't complete verification

## Core Mechanics

### Terminology Change
- **Dollars ($)** → **Points (pts)**
- **Money** → **Points**
- **Cash out** → **Withdraw points**
- **Investment** → **Point deposit**

### Partial Unlock System

**Traditional Model** (too slow):
```
Day 1: Learn → 0 points unlocked
Day 14: Verify → 100 points unlocked
```

**Partial Unlock Model** (faster gratification):
```
Day 1: Learn → 30 points unlocked (can withdraw)
Day 3: Test 1 pass → +20 points unlocked (can withdraw)
Day 7: Test 2 pass → +20 points unlocked (can withdraw)
Day 14: Test 3 pass → +30 points unlocked (can withdraw)
Total: 100 points
```

**If Day 14 fails**:
- Already withdrawn: 70 points
- Deficit: -30 points (must earn back)
- Component: Unverified, must re-learn

## Point System

### Earning Rates (Points Instead of Dollars)

**Tier 1: Basic Recognition**
- **Rate**: 10 points per word
- **Partial unlock**: 3 pts (Day 1), 2 pts (Day 3), 2 pts (Day 7), 3 pts (Day 14)

**Tier 2: Multiple Meanings**
- **Rate**: 25 points per word
- **Partial unlock**: 8 pts (Day 1), 5 pts (Day 3), 5 pts (Day 7), 7 pts (Day 14)

**Tier 3: Phrase Mastery**
- **Rate**: 50 points per phrase
- **Partial unlock**: 15 pts (Day 1), 10 pts (Day 3), 10 pts (Day 7), 15 pts (Day 14)

**Tier 4: Idiom Mastery**
- **Rate**: 100 points per idiom
- **Partial unlock**: 30 pts (Day 1), 20 pts (Day 3), 20 pts (Day 7), 30 pts (Day 14)

**Tier 5: Morphological**
- **Rate**: 30 points per relationship
- **Partial unlock**: 9 pts (Day 1), 6 pts (Day 3), 6 pts (Day 7), 9 pts (Day 14)

**Tier 6: Register**
- **Rate**: 40 points per variant
- **Partial unlock**: 12 pts (Day 1), 8 pts (Day 3), 8 pts (Day 7), 12 pts (Day 14)

**Tier 7: Advanced Context**
- **Rate**: 75 points per context
- **Partial unlock**: 23 pts (Day 1), 15 pts (Day 3), 15 pts (Day 7), 22 pts (Day 14)

## Partial Unlock Schedule

### Day 1: Immediate Unlock (30%)

**After learning**:
- **Unlock**: 30% of total points
- **Can withdraw**: Yes, immediately
- **Risk**: If verification fails, deficit = -30%

**Example**: "beat around the bush" (100 points)
- **Day 1 unlock**: 30 points (can withdraw)
- **Remaining**: 70 points (locked until verification)

### Day 3: First Retention Test (20%)

**After passing Day 3 test**:
- **Unlock**: Additional 20% of total points
- **Can withdraw**: Yes, immediately
- **Risk**: If final verification fails, deficit = -50% (30% + 20%)

**Example**: "beat around the bush"
- **Day 3 unlock**: +20 points (total: 50 points unlocked)
- **Remaining**: 50 points (locked until verification)

### Day 7: Second Retention Test (20%)

**After passing Day 7 test**:
- **Unlock**: Additional 20% of total points
- **Can withdraw**: Yes, immediately
- **Risk**: If final verification fails, deficit = -70% (30% + 20% + 20%)

**Example**: "beat around the bush"
- **Day 7 unlock**: +20 points (total: 70 points unlocked)
- **Remaining**: 30 points (locked until verification)

### Day 14: Final Verification (30%)

**After passing Day 14 test**:
- **Unlock**: Final 30% of total points
- **Can withdraw**: Yes, immediately
- **Status**: Fully verified, no deficit risk
- **Long-term**: Day 60 retention check still applies

**Example**: "beat around the bush"
- **Day 14 unlock**: +30 points (total: 100 points unlocked)
- **Status**: VERIFIED ✅

## Deficit System

### How Deficit Works

**Scenario**: Child withdraws points early, then fails verification

**Example**: "beat around the bush" (100 points)
- **Day 1**: Withdraw 30 points
- **Day 3**: Withdraw 20 points
- **Day 7**: Withdraw 20 points
- **Day 14**: **FAILS** test
- **Total withdrawn**: 70 points
- **Deficit**: -30 points (must earn back)

### Deficit Mechanics

**Deficit Calculation**:
```
deficit = total_withdrawn - verified_amount
```

**Deficit Handling**:
1. **Track deficit**: Negative balance in account
2. **Must earn back**: Can't withdraw more until deficit cleared
3. **Component status**: Unverified, must re-learn
4. **Re-verification**: Must complete full cycle again
5. **Deficit cleared**: When component re-verified

### Deficit Examples

**Example 1: Partial Failure**
- Component: "bank" (25 points)
- Withdrawn: 8 points (Day 1) + 5 points (Day 3) = 13 points
- Day 14: **FAILS**
- Deficit: -13 points
- Must re-learn and re-verify to clear deficit

**Example 2: Early Withdrawal, Late Failure**
- Component: "make a decision" (50 points)
- Withdrawn: 15 points (Day 1) + 10 points (Day 3) + 10 points (Day 7) = 35 points
- Day 14: **FAILS**
- Deficit: -35 points
- Must re-learn and re-verify to clear deficit

**Example 3: No Deficit (Success)**
- Component: "beat around the bush" (100 points)
- Withdrawn: 30 + 20 + 20 + 30 = 100 points
- Day 14: **PASSES**
- Deficit: 0 points ✅
- Status: Fully verified

## Point Account System

### Account Structure

**Available Points**: Can withdraw immediately
**Locked Points**: Unlocked but not yet verified (at risk)
**Deficit Points**: Negative balance (must earn back)
**Total Balance**: Available - Deficit

### Account Example

**Initial**: Parent deposits 10,000 points

**Day 1**: Learn "beat around the bush"
- Available: 30 points (unlocked)
- Locked: 70 points (pending verification)
- Deficit: 0 points
- **Total**: 30 points available

**Day 1 (after withdrawal)**: Child withdraws 30 points
- Available: 0 points
- Locked: 70 points
- Deficit: 0 points
- **Total**: 0 points available

**Day 3**: Pass test, unlock 20 points
- Available: 20 points (unlocked)
- Locked: 50 points
- Deficit: 0 points
- **Total**: 20 points available

**Day 3 (after withdrawal)**: Child withdraws 20 points
- Available: 0 points
- Locked: 50 points
- Deficit: 0 points
- **Total**: 0 points available

**Day 14**: **FAILS** test
- Available: 0 points
- Locked: 0 points (failed, must re-learn)
- Deficit: -50 points (30 + 20 withdrawn)
- **Total**: -50 points (deficit)

**Re-verification**: Must earn back 50 points + complete verification

## Withdrawal Rules

### Withdrawal Limits

**Per Component**:
- Can withdraw up to unlocked amount
- Cannot withdraw locked points
- Cannot withdraw if deficit exists (must clear first)

**Per Day**:
- No daily limit (can withdraw all available)
- Can withdraw multiple times per day
- Withdrawal is instant

### Withdrawal Process

1. **Check available points**: Must have positive balance
2. **Check deficit**: Cannot withdraw if deficit > 0 (must clear first)
3. **Process withdrawal**: Instant transfer to child account
4. **Update balance**: Deduct from available points
5. **Track deficit risk**: If verification fails, deficit = withdrawn amount

## Deficit Recovery

### How to Clear Deficit

**Option 1: Re-verify Failed Component**
- Re-learn component
- Complete full verification cycle
- Earn back points
- Clear deficit

**Option 2: Earn New Points**
- Learn new components
- Earn points from new learning
- New points offset deficit
- Can withdraw once deficit cleared

### Deficit Priority

**When earning new points**:
1. **First**: Clear deficit (negative balance)
2. **Then**: Add to available points (positive balance)

**Example**:
- Deficit: -50 points
- Earn: 30 points (new component)
- Result: Deficit = -20 points, Available = 0 points
- Cannot withdraw until deficit cleared

## Gamification: Risk vs. Reward

### Conservative Strategy

**Withdraw only after Day 14**:
- **Risk**: Low (fully verified)
- **Reward**: 100% of points
- **Timeline**: 14 days
- **Deficit risk**: None

### Aggressive Strategy

**Withdraw immediately (Day 1)**:
- **Risk**: High (30% deficit if fails)
- **Reward**: Immediate gratification
- **Timeline**: Instant
- **Deficit risk**: 30% if fails

### Balanced Strategy

**Withdraw progressively**:
- **Risk**: Medium (increases with each withdrawal)
- **Reward**: Progressive gratification
- **Timeline**: Day 1, 3, 7, 14
- **Deficit risk**: Increases with each withdrawal

## Parent Controls

### Withdrawal Approval

**Option 1: Automatic** (recommended for engagement)
- Child can withdraw immediately
- No parent approval needed
- Deficit risk creates natural accountability

**Option 2: Parent Approval**
- Child requests withdrawal
- Parent approves/rejects
- More control, less engagement

### Deficit Notifications

**Parent receives**:
- Notification when deficit occurs
- Explanation of deficit (which component failed)
- Options to help child re-learn
- Progress on deficit recovery

## Implementation

### Database Schema

```sql
CREATE TABLE point_accounts (
    user_id VARCHAR(255) PRIMARY KEY,
    total_deposited DECIMAL(10,2) NOT NULL,
    available_points DECIMAL(10,2) DEFAULT 0,
    locked_points DECIMAL(10,2) DEFAULT 0,
    deficit_points DECIMAL(10,2) DEFAULT 0,
    total_withdrawn DECIMAL(10,2) DEFAULT 0
);

CREATE TABLE component_unlocks (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    component_id VARCHAR(255) NOT NULL,
    tier INTEGER NOT NULL,
    total_points DECIMAL(10,2) NOT NULL,
    unlocked_day1 DECIMAL(10,2) DEFAULT 0,
    unlocked_day3 DECIMAL(10,2) DEFAULT 0,
    unlocked_day7 DECIMAL(10,2) DEFAULT 0,
    unlocked_day14 DECIMAL(10,2) DEFAULT 0,
    withdrawn_day1 DECIMAL(10,2) DEFAULT 0,
    withdrawn_day3 DECIMAL(10,2) DEFAULT 0,
    withdrawn_day7 DECIMAL(10,2) DEFAULT 0,
    withdrawn_day14 DECIMAL(10,2) DEFAULT 0,
    verified BOOLEAN DEFAULT FALSE,
    deficit DECIMAL(10,2) DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES point_accounts(user_id)
);
```

### Point Calculation

```python
def calculate_unlock(component_id, tier, day):
    total_points = TIER_POINTS[tier]
    
    if day == 1:
        return total_points * 0.30  # 30%
    elif day == 3:
        return total_points * 0.20  # 20%
    elif day == 7:
        return total_points * 0.20  # 20%
    elif day == 14:
        return total_points * 0.30  # 30%
    
def calculate_deficit(component_id, withdrawn, verified):
    if verified:
        return 0
    else:
        return -withdrawn  # Negative balance
```

## Benefits

### For Kids
- ✅ **Immediate gratification**: Can withdraw points Day 1
- ✅ **Progressive rewards**: Points unlock over time
- ✅ **Engagement**: Faster feedback loop
- ✅ **Learning**: Deficit creates accountability

### For Parents
- ✅ **Flexibility**: Child can withdraw when needed
- ✅ **Accountability**: Deficit ensures completion
- ✅ **Transparency**: Clear tracking of points and deficit
- ✅ **Control**: Can monitor withdrawals and deficit

### For Platform
- ✅ **Engagement**: Faster gratification increases retention
- ✅ **Integrity**: Deficit maintains verification requirement
- ✅ **Revenue**: Points system allows for flexible pricing
- ✅ **Gamification**: Risk/reward creates engagement

## Key Takeaways

1. **Partial unlock**: 30% Day 1, 20% Day 3, 20% Day 7, 30% Day 14
2. **Early withdrawal**: Kids can withdraw immediately
3. **Deficit penalty**: If verification fails, deficit = withdrawn amount
4. **Points system**: Use points instead of dollars for flexibility
5. **Risk/reward**: Conservative vs. aggressive withdrawal strategies
6. **Deficit recovery**: Must re-verify or earn new points to clear
7. **Parent controls**: Optional approval, deficit notifications

## Next Steps

1. Update all documentation to use "points" terminology
2. Implement partial unlock calculation
3. Build deficit tracking system
4. Create withdrawal interface
5. Add deficit recovery mechanics

See `05-mcq-verification-strategy.md` for verification details.
See `06-spaced-repetition-strategy.md` for timing details.

