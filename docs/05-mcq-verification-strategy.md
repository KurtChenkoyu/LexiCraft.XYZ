# MCQ Verification Strategy: 6-Option Model

## Overview

Using **6-option Multiple Choice Questions (MCQ)** for verification provides:
- ✅ **Easier to start**: Simpler than open-ended questions
- ✅ **Less argument**: Clear right/wrong answers
- ✅ **Scalable**: Automated scoring
- ✅ **Consistent**: Standardized assessment

**Key Question**: How many times must a learner get an answer right to show solid understanding (not just guessing)?

## Statistical Analysis

### Guessing Probability

With **6 options**, the probability of guessing correctly:
- **1 attempt**: 1/6 = **16.67%** chance
- **2 attempts**: (1/6)² = **2.78%** chance (both correct by luck)
- **3 attempts**: (1/6)³ = **0.46%** chance (all three by luck)
- **4 attempts**: (1/6)⁴ = **0.077%** chance (all four by luck)
- **5 attempts**: (1/6)⁵ = **0.013%** chance (all five by luck)

### Confidence Levels

To be **95% confident** they're not guessing:
- Need probability of guessing < 5%
- **3 correct answers**: 0.46% chance of guessing = **99.54% confidence**
- **2 correct answers**: 2.78% chance of guessing = **97.22% confidence**

To be **99% confident** they're not guessing:
- Need probability of guessing < 1%
- **3 correct answers**: 0.46% chance = **exceeds 99% confidence**

## Recommended Verification Strategy

### Minimum Requirement: 3 Correct Answers

**Rationale**:
- **Statistical confidence**: 99.54% confidence they're not guessing
- **Practical balance**: Not too easy, not too hard
- **Spaced repetition**: Can be spread over time

### Verification Schedule

#### Option 1: Sequential (Same Session)
```
Attempt 1: Correct → Continue
Attempt 2: Correct → Continue
Attempt 3: Correct → VERIFIED
If any wrong: Reset, provide feedback
```

**Pros**: Fast verification
**Cons**: Can memorize pattern, less retention

#### Option 2: Spaced Repetition (Recommended)
```
Day 1: Learn component
Day 3: Test 1 → Must pass
Day 7: Test 2 → Must pass
Day 14: Test 3 → Must pass → VERIFIED
Day 60: Long-term retention check → Permanent unlock
If any fail: Reschedule, additional support
```

**Pros**: Ensures retention, prevents cramming, validates long-term learning
**Cons**: Takes longer (14+ days minimum)

**See**: `06-spaced-repetition-strategy.md` for detailed spacing intervals and adaptive scheduling

#### Option 3: Hybrid (Best of Both)
```
Day 1: Learn component
  → Immediate test (3 questions, must get 2/3 right)
Day 3: Retention test → Must pass
Day 7: Retention test → Must pass
Day 14: Final test → Must pass → VERIFIED
```

**Pros**: Immediate feedback + retention verification
**Cons**: More complex to implement

## Detailed Verification Rules

### Initial Learning (Day 1)

**Immediate Assessment**:
- **3 MCQ questions** about the component
- **Must get 2/3 correct** (66.7% threshold)
- **Purpose**: Initial understanding check
- **If pass**: Schedule spaced repetition
- **If fail**: Provide feedback, retry after review

**Rationale for 2/3**:
- With 6 options, getting 2/3 right by guessing: ~7.4% chance
- Still allows for one mistake (learning curve)
- Provides immediate feedback

### Spaced Repetition (Day 3, 7, 14)

**Retention Tests**:
- **1 MCQ question** per test
- **Must pass all 3 tests** (3/3 correct)
- **Purpose**: Verify retention over time
- **If any fail**: Reschedule, provide additional support

**Rationale**:
- 3 correct answers over time = 99.54% confidence
- Spaced repetition ensures long-term retention
- Prevents cramming and memorization

### Final Verification (Day 14+)

**Comprehensive Test**:
- **3 MCQ questions** (different contexts/variations)
- **Must get 3/3 correct** (100% threshold)
- **Purpose**: Final verification before money unlock
- **If pass**: Component verified, money unlocked
- **If fail**: Additional support, extended timeline

## Question Design Strategy

### 6-Option Structure

**Option Distribution**:
- **1 correct answer** (100% correct)
- **1 close answer** (80% correct - common mistake)
- **1 partial answer** (60% correct - partial understanding)
- **1 related answer** (40% correct - related concept)
- **1 distractor** (20% correct - plausible but wrong)
- **1 "I don't know"** (0% correct - honest uncertainty)

### Example: "Beat Around the Bush"

**Question**: "What does 'beat around the bush' mean?"

**Options**:
- A) To avoid being direct (100% - correct)
- B) To be honest and clear (80% - opposite, common mistake)
- C) To talk about nature (60% - literal interpretation)
- D) To make a decision quickly (40% - related but wrong)
- E) To beat someone (20% - distractor)
- F) I don't know (0% - honest)

**Scoring**:
- A = 1.0 (correct)
- B = 0.8 (close, partial credit)
- C = 0.6 (partial understanding)
- D = 0.4 (related concept)
- E = 0.2 (wrong)
- F = 0.0 (no understanding)

### Context Variations

**Test 1 (Day 3)**: Basic meaning
- "What does 'beat around the bush' mean?"

**Test 2 (Day 7)**: Usage in context
- "Which sentence uses 'beat around the bush' correctly?"
  - A) "He beat around the bush and told the truth"
  - B) "Stop beating around the bush and be direct"
  - C) "She beat around the bush in the garden"
  - D) "They beat around the bush to make a decision"
  - E) "I beat around the bush every morning"
  - F) I don't know

**Test 3 (Day 14)**: Relationship understanding
- "What is the opposite of 'beat around the bush'?"
  - A) Be direct
  - B) Be indirect
  - C) Be honest
  - D) Be clear
  - E) Be vague
  - F) I don't know

## Verification Thresholds

### Minimum Thresholds by Tier

**Tier 1 (Basic)**: 3 correct answers
- Day 3: 1/1 correct
- Day 7: 1/1 correct
- Day 14: 1/1 correct
- **Total**: 3/3 = 100% pass rate

**Tier 2 (Multiple Meanings)**: 4 correct answers
- Day 3: 2/2 correct (both meanings)
- Day 7: 1/1 correct (retention)
- Day 14: 1/1 correct (final)
- **Total**: 4/4 = 100% pass rate

**Tier 3 (Phrases)**: 4 correct answers
- Day 3: 2/2 correct (phrase + usage)
- Day 7: 1/1 correct (retention)
- Day 14: 1/1 correct (final)
- **Total**: 4/4 = 100% pass rate

**Tier 4 (Idioms)**: 5 correct answers
- Day 3: 2/2 correct (meaning + usage)
- Day 7: 1/1 correct (retention)
- Day 14: 2/2 correct (relationship + final)
- **Total**: 5/5 = 100% pass rate

### Partial Credit System

**Option**: Allow partial credit for close answers
- **Correct (A)**: 1.0 point
- **Close (B)**: 0.8 point
- **Partial (C)**: 0.6 point
- **Related (D)**: 0.4 point
- **Wrong (E, F)**: 0.0 point

**Threshold**: 0.8 average across all tests
- **3 tests**: Need 2.4/3.0 total points
- **Allows**: 1 close answer (0.8) + 2 correct (1.0 each) = 2.8/3.0 ✅

## Statistical Confidence Levels

### Confidence by Number of Correct Answers

| Correct Answers | Guessing Probability | Confidence Level | Recommendation |
|----------------|----------------------|------------------|----------------|
| 1 | 16.67% | 83.33% | ❌ Too low |
| 2 | 2.78% | 97.22% | ⚠️ Acceptable |
| 3 | 0.46% | 99.54% | ✅ **Recommended** |
| 4 | 0.077% | 99.92% | ✅ Very confident |
| 5 | 0.013% | 99.99% | ✅ Extremely confident |

### Recommended: 3 Correct Answers

**Why 3 is optimal**:
- **99.54% confidence** they're not guessing
- **Practical**: Not too many tests, not too few
- **Balanced**: Ensures understanding without being punitive
- **Spaced**: Can be spread over 14 days (retention)

## Implementation Rules

### Verification Flow

```
1. Learn component (Day 1)
   ↓
2. Immediate test: 3 questions, need 2/3 correct
   ↓
3. If pass: Schedule spaced repetition
   ↓
4. Day 3: Test 1 → Must pass (1/1)
   ↓
5. Day 7: Test 2 → Must pass (1/1)
   ↓
6. Day 14: Test 3 → Must pass (1/1)
   ↓
7. If all pass: VERIFIED (3/3 = 100%)
   ↓
8. Money unlocked (70% immediate, 10% after retention)
```

### Failure Handling

**Immediate test failure** (Day 1):
- Provide feedback
- Show correct answer
- Retry after 1 day

**Spaced repetition failure** (Day 3, 7, 14):
- Reschedule test after 3 days
- Provide additional learning materials
- Track failure count (max 3 retries)

**Multiple failures**:
- Flag for human review
- Provide personalized support
- Consider adjusting difficulty

## Question Generation Strategy

### From Learning Point Cloud

**Query Learning Point Cloud**:
```cypher
MATCH (target:LearningPoint {id: $component_id})-[*1..2]-(related:LearningPoint)
RETURN related
ORDER BY related.frequency_rank
LIMIT 10
```

**Generate Options**:
1. **Correct answer**: Target component
2. **Close answer**: Common mistake (from error patterns)
3. **Partial answer**: Related component (1-degree relationship)
4. **Related answer**: Related component (2-degree relationship)
5. **Distractor**: Unrelated but plausible
6. **"I don't know"**: Always included

### Context Variations

**Test 1**: Basic meaning
- "What does X mean?"

**Test 2**: Usage in context
- "Which sentence uses X correctly?"

**Test 3**: Relationship understanding
- "How is X related to Y?"
- "What is the opposite of X?"

## Quality Assurance

### Question Quality
- **Clear wording**: No ambiguous questions
- **Plausible distractors**: All options seem reasonable
- **Context-appropriate**: Questions match learning context
- **Difficulty-appropriate**: Matches tier level

### Scoring Accuracy
- **Automated scoring**: Consistent, no bias
- **Partial credit**: Fair assessment of understanding
- **Feedback**: Explain why answers are correct/incorrect

### Statistical Monitoring
- **Track pass rates**: Monitor by tier, component type
- **Identify patterns**: Common mistakes, difficult concepts
- **Adjust difficulty**: Based on actual performance
- **Improve questions**: Based on user feedback

## Recommendations

### Minimum Standard
- **3 correct answers** over spaced repetition (Day 3, 7, 14)
- **99.54% confidence** they're not guessing
- **100% pass rate** required (no partial failures)

### Enhanced Standard (Optional)
- **4 correct answers** for higher tiers (Tier 4+)
- **Partial credit** for close answers (0.8 threshold)
- **Context variations** in each test

### Quality Assurance
- **Question review**: Human review of generated questions
- **Statistical monitoring**: Track pass rates, adjust difficulty
- **User feedback**: Improve questions based on feedback

## Verification Bundle Pre-Caching

### Strategy

MCQs are pre-cached for the user's entire block inventory when they visit the Mine page. This enables instant MCQ loading without API calls during verification.

### Flow

1. User visits Mine → Starter pack loads from `vocabulary.json`
2. Background: Fetch verification bundles for all inventory blocks (`POST /api/v1/mcq/bundles`)
3. Store in IndexedDB (`localStore.verificationBundles`)
4. User forges/verifies any word → MCQs load instantly from cache (~10ms)
5. Answer feedback is immediate (correct_index available locally)
6. Server submission happens in background for gamification

### Bundle Structure

Each bundle contains:
- `senseId`: The sense identifier
- `word`: The vocabulary word
- `mcqs`: Array of MCQ objects with `correct_index` for instant feedback
- `cachedAt`: Timestamp for cache freshness

### Storage

~2.5KB per sense. 500 senses = 1.25MB (minimal for IndexedDB).

### Key Files

- `services/bundleCacheService.ts` - Pre-cache logic
- `lib/local-store.ts` - IndexedDB storage (verificationBundles store)
- `components/features/mcq/MCQSession.tsx` - Cache-first loading
- `components/features/mcq/MCQCard.tsx` - Instant feedback using cached correct_index

## Next Steps

1. ~~Implement MCQ generation from Learning Point Cloud~~ ✅
2. ~~Build verification scheduler (spaced repetition)~~ ✅
3. ~~Create scoring system (with partial credit option)~~ ✅
4. ~~Implement verification bundle pre-caching~~ ✅
5. **Monitor and adjust** based on results

See `verification-rules.md` for complete verification requirements.

