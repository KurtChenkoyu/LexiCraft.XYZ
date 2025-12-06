# Verification Rules Specification

## Core Principles

1. **Platform-Controlled**: Parents cannot override verification
2. **Multi-Layered**: Multiple verification mechanisms
3. **Time-Based**: Spaced repetition requirements
4. **Context-Aware**: Learning Point Cloud integration
5. **Quality-Focused**: Ensures genuine learning

## Verification Mechanisms

### 1. Spaced Repetition Verification

#### Requirements
- **Minimum cycle**: 7-30 days (based on tier)
- **Test schedule**: Day 3, Day 7, Day 14 (minimum)
- **All tests must pass**: Cannot skip steps
- **Retention check**: Day 60 (for permanent unlock)

#### Schedule by Tier (Research-Based Optimal Intervals)
- **Tier 1**: Day 1 (immediate), Day 3, Day 7 (7-day cycle)
- **Tier 2**: Day 1 (immediate), Day 3, Day 7, Day 14 (14-day cycle)
- **Tier 3**: Day 1 (immediate), Day 3, Day 7, Day 14, Day 21 (21-day cycle)
- **Tier 4**: Day 1 (immediate), Day 3, Day 7, Day 14, Day 21, Day 30 (30-day cycle)
- **Tier 5**: Day 1 (immediate), Day 3, Day 7, Day 14 (14-day cycle)
- **Tier 6**: Day 1 (immediate), Day 3, Day 7, Day 14, Day 21 (21-day cycle)
- **Tier 7**: Day 1 (immediate), Day 3, Day 7, Day 14, Day 21, Day 30 (30-day cycle)

**Long-term retention**: Day 60 for all tiers (permanent unlock)

**See**: `06-spaced-repetition-strategy.md` for detailed intervals, adaptive scheduling, and failure handling

#### Failure Handling
- **Test failure**: Reschedule after 3 days
- **Multiple failures**: Additional support, extended timeline
- **Retention failure**: Component becomes "unverified", money recalled

### 2. MCQ Assessment (6-Option Model)

#### Core Strategy
- **Format**: 6-option multiple choice questions
- **Rationale**: Easier to start, less argument, scalable
- **Statistical confidence**: 3 correct answers = 99.54% confidence (not guessing)

#### Question Structure
- **1 correct answer** (100% correct)
- **1 close answer** (80% correct - common mistake)
- **1 partial answer** (60% correct - partial understanding)
- **1 related answer** (40% correct - related concept)
- **1 distractor** (20% correct - plausible but wrong)
- **1 "I don't know"** (0% correct - honest uncertainty)

#### Verification Schedule
- **Day 1**: Immediate test (3 questions, need 2/3 correct)
- **Day 3**: Test 1 → Must pass (1/1 correct)
- **Day 7**: Test 2 → Must pass (1/1 correct)
- **Day 14**: Test 3 → Must pass (1/1 correct)
- **Total**: 3/3 correct = VERIFIED (99.54% confidence)

#### Scoring Options

**Option A: Strict (Recommended)**
- **Correct answer only**: 1.0 point
- **All others**: 0.0 points
- **Threshold**: 3/3 correct (100% pass rate)

**Option B: Partial Credit**
- **Correct (A)**: 1.0 point
- **Close (B)**: 0.8 point
- **Partial (C)**: 0.6 point
- **Related (D)**: 0.4 point
- **Wrong (E, F)**: 0.0 point
- **Threshold**: 0.8 average (2.4/3.0 total points)

#### Context Variations
- **Test 1 (Day 3)**: Basic meaning
- **Test 2 (Day 7)**: Usage in context
- **Test 3 (Day 14)**: Relationship understanding

See `05-mcq-verification-strategy.md` for detailed statistical analysis and recommendations.

### 3. Behavioral Analytics

#### Metrics Tracked
- **Time spent**: Minimum time per component (prevents rushing)
- **Error patterns**: Real learning shows specific patterns
- **Progression rate**: Natural limits (can't learn 100 words/day)
- **Interaction quality**: Mouse movements, typing patterns, hesitation

#### Detection Rules
- **Too fast**: < 30 seconds per word = suspicious
- **Too many**: > 50 words/day = suspicious
- **No errors**: Perfect scores with no mistakes = suspicious
- **Pattern detection**: Identical error patterns = gaming

#### Actions
- **Flag for review**: Suspicious patterns trigger human review
- **Additional testing**: Extra verification required
- **Penalty**: Reduced earning rate or extended timeline

### 4. Context-Dependent Testing (Learning Point Cloud)

#### Context Tests
- **Multiple meanings**: Test all meanings of word
- **Phrase usage**: Test word in collocations
- **Register appropriateness**: Test formal vs. informal
- **Frequency awareness**: Test if child knows usage frequency

#### Example: "Bank"
1. **Financial context**: "In 'I went to the bank,' what does 'bank' mean?"
2. **Geographic context**: "In 'the river bank,' what does 'bank' mean?"
3. **Usage test**: "Can you use 'bank' in both contexts correctly?"

#### Relationship Tests
- **Prerequisites**: Test if child knows prerequisite components
- **Related words**: Test understanding of relationships
- **Morphological**: Test prefix/suffix understanding
- **Opposites**: Test antonym knowledge

#### Example: "Indirect"
1. **Relationship**: "How is 'indirect' related to 'direct'?"
2. **Morphological**: "What prefix makes 'direct' into 'indirect'?"
3. **Usage**: "Use both 'direct' and 'indirect' in sentences"

### 5. Randomized Re-Testing

#### Ongoing Verification
- **Random selection**: 10% of "learned" words re-tested monthly
- **Retention requirement**: Must maintain 80%+ retention
- **Penalty**: If retention drops, component becomes "unverified"

#### Re-Test Schedule
- **Month 1**: 10% random re-test
- **Month 2**: 10% random re-test
- **Month 3**: 10% random re-test
- **Ongoing**: Continuous random re-testing

#### Failure Handling
- **Retention < 80%**: Component unverified, money recalled
- **Multiple failures**: Additional support, review learning path

## Verification Flow

### Initial Learning
```
1. User learns component
   ↓
2. Schedule verification (Day 3, 7, 14)
   ↓
3. Generate assessment (4 test types)
   ↓
4. User completes assessment
   ↓
5. Score and evaluate
   ↓
6. If passed: Update knowledge state, unlock 70% of money
   ↓
7. If failed: Reschedule, provide feedback
```

### Retention Check
```
1. Day 60: Schedule retention test
   ↓
2. Generate retention assessment
   ↓
3. User completes assessment
   ↓
4. If passed (80%+): Unlock remaining 10%, permanent unlock
   ↓
5. If failed: Component unverified, money recalled
```

### Random Re-Test
```
1. Monthly: Select 10% of learned components
   ↓
2. Generate re-test assessment
   ↓
3. User completes assessment
   ↓
4. If passed: Maintain verified status
   ↓
5. If failed: Component unverified, money recalled
```

## Verification Scoring

### Test Scoring
- **Recognition**: 1.0 if correct, 0.0 if incorrect
- **Recall**: 1.0 if correct, 0.0 if incorrect
- **Usage**: 0.0-1.0 (AI-graded, context-dependent)
- **Comprehension**: 0.0-1.0 (AI-graded, semantic understanding)

### Overall Scoring
```
overall_score = (recognition + recall + usage + comprehension) / 4
passing = overall_score >= 0.8 AND all_tests >= 0.8
```

### Retention Scoring
```
retention_score = current_test_score / original_test_score
passing = retention_score >= 0.8
```

## Verification Status

### Status Types
- **learning**: Currently learning, not yet verified
- **pending**: Verification scheduled, not yet completed
- **verified**: Passed all tests, money unlocked
- **unverified**: Failed tests, money not unlocked
- **recalled**: Previously verified, but retention failed

### Status Transitions
```
learning → pending → verified → (recalled if retention fails)
learning → pending → unverified → learning (retry)
```

## Appeals Process

### Parent Disputes
1. **Submit appeal**: Parent disputes verification result
2. **Human review**: Expert reviews assessment and results
3. **Additional testing**: Optional additional tests
4. **Resolution**: Fair resolution within 7 days
5. **Outcome**: Uphold, reverse, or modify verification

### Platform Errors
1. **Detection**: System detects potential error
2. **Automatic review**: AI flags for human review
3. **Correction**: Automatic correction if clear error
4. **Notification**: User notified of correction

## Quality Assurance

### Verification Accuracy
- **Target**: 95%+ accuracy
- **Monitoring**: Regular accuracy audits
- **Improvement**: Continuous model refinement

### Fraud Detection
- **Pattern analysis**: Detect gaming patterns
- **Behavioral flags**: Suspicious activity alerts
- **Human review**: Expert review of flagged cases

### User Experience
- **Clear feedback**: Explain why verification failed
- **Support**: Additional help for struggling learners
- **Fairness**: Transparent verification process

## Next Steps

See `earning-rules.md` for earning calculations.
See `database-schema.md` for data structures.

