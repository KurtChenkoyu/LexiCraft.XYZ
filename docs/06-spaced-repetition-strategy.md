# Spaced Repetition Strategy: Deep Dive

## Overview

Spaced repetition is **critical** for the earning model because:
- ✅ **Prevents cramming**: Can't rush through to unlock money
- ✅ **Ensures retention**: Long-term learning, not just memorization
- ✅ **Validates understanding**: Multiple tests over time = genuine learning
- ✅ **Maintains integrity**: Time requirement prevents gaming

## The Forgetting Curve

### Research-Based Intervals

**Hermann Ebbinghaus Forgetting Curve**:
- **Day 1**: 100% retention
- **Day 2**: ~50% retention (without review)
- **Day 7**: ~20% retention (without review)
- **Day 30**: ~10% retention (without review)

**Optimal Review Intervals** (to maintain 80%+ retention):
- **First review**: 1-2 days (Day 1-2)
- **Second review**: 4-7 days (Day 3-7)
- **Third review**: 14-21 days (Day 7-21)
- **Fourth review**: 30-60 days (Day 30-60)
- **Long-term**: 90+ days (Day 90+)

## Spaced Repetition Algorithms

### SM2 Algorithm (SuperMemo 2)

**Core Principle**: Adjust intervals based on performance
- **Ease Factor (EF)**: Starts at 2.5, adjusts based on performance
- **Interval**: Multiplies by EF after each successful review
- **Performance-based**: Harder items reviewed more frequently

**Example**:
```
Initial: EF = 2.5, Interval = 1 day
Pass: EF = 2.6, Interval = 2.5 days
Pass: EF = 2.7, Interval = 6.75 days
Fail: EF = 2.5, Interval = 1 day (reset)
```

### Anki Algorithm

**Similar to SM2** but with:
- **Graduating interval**: 1 day → 4 days → 10 days
- **Easy bonus**: Can skip ahead if marked "easy"
- **Lapse handling**: Reset to shorter interval on failure

### Our Model: Fixed + Adaptive Hybrid

**Fixed Schedule** (for verification):
- **Day 1**: Learn + immediate test
- **Day 3**: First retention test
- **Day 7**: Second retention test
- **Day 14**: Final verification test
- **Day 60**: Long-term retention check

**Adaptive Component** (for learning optimization):
- Adjust difficulty based on performance
- Extend intervals for strong performers
- Shorten intervals for struggling learners
- Track ease factor for future recommendations

## Optimal Intervals by Tier

### Tier 1: Basic Recognition (7-day cycle)

**Schedule**:
- **Day 1**: Learn + immediate test (3 questions, 2/3 correct)
- **Day 3**: Retention test 1 (1 question, must pass)
- **Day 7**: Retention test 2 (1 question, must pass) → **VERIFIED**

**Rationale**:
- Basic words are easier to remember
- Shorter cycle maintains engagement
- 7 days sufficient for basic recognition

**Long-term**: Day 30, Day 90 retention checks

### Tier 2: Multiple Meanings (14-day cycle)

**Schedule**:
- **Day 1**: Learn + immediate test (3 questions, 2/3 correct)
- **Day 3**: Retention test 1 (1 question, must pass)
- **Day 7**: Retention test 2 (1 question, must pass)
- **Day 14**: Final test (1 question, must pass) → **VERIFIED**

**Rationale**:
- Multiple meanings require more time
- 14 days allows for context differentiation
- Tests both meanings over time

**Long-term**: Day 30, Day 60, Day 90 retention checks

### Tier 3: Phrase Mastery (21-day cycle)

**Schedule**:
- **Day 1**: Learn + immediate test (3 questions, 2/3 correct)
- **Day 3**: Retention test 1 (1 question, must pass)
- **Day 7**: Retention test 2 (1 question, must pass)
- **Day 14**: Retention test 3 (1 question, must pass)
- **Day 21**: Final test (1 question, must pass) → **VERIFIED**

**Rationale**:
- Phrases require understanding of collocations
- 21 days ensures proper usage patterns
- Tests phrase completion over time

**Long-term**: Day 30, Day 60, Day 90 retention checks

### Tier 4: Idiom Mastery (30-day cycle)

**Schedule**:
- **Day 1**: Learn + immediate test (3 questions, 2/3 correct)
- **Day 3**: Retention test 1 (1 question, must pass)
- **Day 7**: Retention test 2 (1 question, must pass)
- **Day 14**: Retention test 3 (1 question, must pass)
- **Day 21**: Retention test 4 (1 question, must pass)
- **Day 30**: Final test (1 question, must pass) → **VERIFIED**

**Rationale**:
- Idioms require figurative understanding
- 30 days ensures deep comprehension
- Tests meaning, usage, and relationships

**Long-term**: Day 60, Day 90, Day 180 retention checks

### Tier 5-7: Advanced (14-30 day cycles)

**Similar to Tier 2-4** based on complexity:
- **Tier 5** (Morphological): 14-day cycle
- **Tier 6** (Register): 21-day cycle
- **Tier 7** (Advanced Context): 30-day cycle

## Integration with MCQ Model

### Day 1: Immediate Test (3 questions)

**Purpose**: Initial understanding check
- **Format**: 3 MCQ questions (6 options each)
- **Threshold**: 2/3 correct (66.7%)
- **Rationale**: Allows for one mistake, provides immediate feedback
- **If pass**: Schedule spaced repetition
- **If fail**: Provide feedback, retry after 1 day

**Question Types**:
1. Basic meaning
2. Usage in context
3. Relationship understanding

### Day 3: First Retention Test

**Purpose**: Early retention check (before forgetting curve drops)
- **Format**: 1 MCQ question (6 options)
- **Threshold**: 1/1 correct (100%)
- **Rationale**: Tests if information was encoded
- **Question Type**: Basic meaning (same as Day 1, question 1)
- **If pass**: Continue to Day 7
- **If fail**: Reschedule after 2 days, provide additional support

### Day 7: Second Retention Test

**Purpose**: Mid-term retention (after initial forgetting)
- **Format**: 1 MCQ question (6 options)
- **Threshold**: 1/1 correct (100%)
- **Rationale**: Tests retention after forgetting curve drop
- **Question Type**: Usage in context (same as Day 1, question 2)
- **If pass**: Continue to Day 14
- **If fail**: Reschedule after 3 days, provide additional support

### Day 14: Final Verification Test

**Purpose**: Long-term retention verification
- **Format**: 1 MCQ question (6 options)
- **Threshold**: 1/1 correct (100%)
- **Rationale**: Final verification before money unlock
- **Question Type**: Relationship understanding (same as Day 1, question 3)
- **If pass**: **VERIFIED** → Money unlocked (70%)
- **If fail**: Reschedule after 5 days, provide additional support

### Day 60: Long-Term Retention Check

**Purpose**: Permanent retention verification
- **Format**: 1 MCQ question (6 options)
- **Threshold**: 1/1 correct (100%)
- **Rationale**: Ensures long-term retention
- **Question Type**: Random from previous tests
- **If pass**: Permanent unlock (remaining 10% unlocked)
- **If fail**: Component becomes "unverified", money recalled

## Adaptive Scheduling

### Performance-Based Adjustments

**Strong Performance** (3/3 correct, high confidence):
- **Extend intervals**: Day 3 → Day 4, Day 7 → Day 9
- **Reduce frequency**: Fewer retention checks needed
- **Track ease factor**: Higher EF for future recommendations

**Struggling Performance** (Failures, low confidence):
- **Shorten intervals**: Day 3 → Day 2, Day 7 → Day 5
- **Increase frequency**: More retention checks
- **Track ease factor**: Lower EF, review more often
- **Additional support**: Provide extra learning materials

### Ease Factor Tracking

**Initial EF**: 2.5 (default)
**After successful review**: EF + 0.1 (up to 2.6)
**After difficult review**: EF - 0.1 (down to 2.4)
**After failure**: EF - 0.2 (down to 2.3)

**Use for**:
- Predicting future difficulty
- Adjusting intervals
- Identifying struggling components
- Providing personalized support

## Failure Handling

### Single Failure

**Scenario**: Fail Day 3 test
**Action**:
- Reschedule test after 2 days (Day 5)
- Provide additional learning materials
- Show correct answer with explanation
- Track failure count

**Impact**: Delays verification by 2 days

### Multiple Failures

**Scenario**: Fail Day 3, Day 5, Day 7 tests
**Action**:
- Flag for human review
- Provide personalized support
- Consider adjusting difficulty
- Extended timeline (up to 30 days)
- Track failure pattern

**Impact**: Significant delay, may require intervention

### Retention Failure

**Scenario**: Fail Day 60 retention check
**Action**:
- Component becomes "unverified"
- Money recalled (if not yet transferred)
- Schedule re-learning
- Provide additional support
- Track retention issues

**Impact**: Money recalled, must re-verify

## Question Variation Strategy

### Same Question, Different Contexts

**Day 1, Question 1**: "What does 'bank' mean in 'I went to the bank'?"
**Day 3**: "In 'I deposited money at the bank,' what does 'bank' mean?"
**Day 7**: "What does 'bank' mean when talking about money?"
**Day 14**: "Which sentence uses 'bank' correctly in a financial context?"

**Rationale**: Tests same concept, different contexts prevent memorization

### Progressive Difficulty

**Day 1**: Basic meaning question
**Day 3**: Same basic meaning (retention)
**Day 7**: Usage in context (application)
**Day 14**: Relationship understanding (deep comprehension)

**Rationale**: Progressive difficulty ensures deeper understanding

### Random Selection

**Day 60**: Random question from previous tests
**Rationale**: Prevents pattern memorization, tests genuine retention

## Long-Term Retention Strategy

### Ongoing Verification

**Monthly Re-Tests**:
- **10% random selection**: Of all verified components
- **Purpose**: Maintain retention over time
- **Threshold**: 80%+ retention rate
- **If fail**: Component unverified, money recalled

**Schedule**:
- **Month 1**: 10% random re-test
- **Month 2**: 10% random re-test
- **Month 3**: 10% random re-test
- **Ongoing**: Continuous random re-testing

### Retention Tracking

**Metrics**:
- **Retention rate**: % of components still known after X days
- **Forgetting curve**: Track retention over time
- **Failure patterns**: Identify difficult components
- **Success patterns**: Identify easy components

**Use for**:
- Adjusting intervals
- Identifying struggling learners
- Improving question quality
- Optimizing verification schedule

## Integration with Learning Point Cloud

### Prerequisite-Based Scheduling

**Example**: "indirect" requires "direct" + "in-" prefix
- **Learn "direct" first**: Day 1-14
- **Learn "in-" prefix**: Day 15-28
- **Learn "indirect"**: Day 29-42 (after prerequisites)

**Rationale**: Prerequisites must be verified before dependent components

### Relationship-Based Review

**Example**: "beat around the bush" related to "direct" and "indirect"
- **Review together**: Schedule related components on same day
- **Test relationships**: Questions about relationships
- **Bonus earning**: Relationship discovery bonuses

**Rationale**: Related components reinforce each other

### Frequency-Based Prioritization

**High frequency words**: Shorter intervals (more important)
**Low frequency words**: Longer intervals (less critical)

**Rationale**: Prioritize common words for faster learning

## Implementation Considerations

### Scheduling System

**Database Schema**:
```sql
CREATE TABLE verification_schedule (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    component_id VARCHAR(255) NOT NULL,
    tier INTEGER NOT NULL,
    scheduled_date DATE NOT NULL,
    test_type VARCHAR(50) NOT NULL,  -- "immediate", "retention", "final", "long_term"
    completed BOOLEAN DEFAULT FALSE,
    passed BOOLEAN,
    score FLOAT,
    ease_factor FLOAT DEFAULT 2.5,
    failure_count INTEGER DEFAULT 0,
    next_scheduled_date DATE
);
```

### Algorithm Implementation

**Fixed Schedule** (for verification):
```python
def schedule_verification(component_id, tier, learn_date):
    if tier == 1:
        return [
            learn_date + timedelta(days=1),  # Immediate
            learn_date + timedelta(days=3),   # Retention 1
            learn_date + timedelta(days=7),  # Retention 2
        ]
    elif tier == 2:
        return [
            learn_date + timedelta(days=1),   # Immediate
            learn_date + timedelta(days=3),   # Retention 1
            learn_date + timedelta(days=7),   # Retention 2
            learn_date + timedelta(days=14),  # Final
        ]
    # ... etc
```

**Adaptive Adjustment** (for optimization):
```python
def adjust_schedule(component_id, performance, ease_factor):
    if performance == "strong":
        ease_factor += 0.1
        # Extend intervals
    elif performance == "weak":
        ease_factor -= 0.1
        # Shorten intervals
    return ease_factor
```

## Recommendations

### Minimum Standard
- **3 tests over 14 days** (Day 3, 7, 14)
- **100% pass rate** required
- **Day 60 retention check** for permanent unlock

### Enhanced Standard (Optional)
- **Adaptive scheduling** based on performance
- **Question variation** to prevent memorization
- **Ongoing re-tests** (10% monthly)

### Quality Assurance
- **Track retention rates** by tier, component type
- **Monitor failure patterns** for struggling learners
- **Adjust intervals** based on data
- **Provide support** for multiple failures

## Key Takeaways

1. **Spaced repetition is essential**: Prevents cramming, ensures retention
2. **Optimal intervals**: Day 3, 7, 14 (minimum) based on research
3. **Tier-based cycles**: 7-30 days depending on complexity
4. **Adaptive scheduling**: Adjust based on performance
5. **Long-term verification**: Day 60+ retention checks
6. **Question variation**: Prevent memorization, test understanding
7. **Failure handling**: Reschedule, provide support, track patterns

## Next Steps

1. Implement scheduling system
2. Build adaptive algorithm
3. Create question variation logic
4. Set up retention tracking
5. Test with sample components

See `05-mcq-verification-strategy.md` for MCQ integration details.

