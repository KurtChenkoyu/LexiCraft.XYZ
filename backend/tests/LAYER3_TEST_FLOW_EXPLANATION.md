# Layer 3: Survey Simulation Test Flow

## Overview

Layer 3 tests the **complete survey experience** with **simulated users** who have **known vocabulary boundaries** (ground truth). This validates that the survey produces accurate metrics when given realistic answer patterns.

**Key Difference from Layer 2:**
- **Layer 2**: Tests algorithm logic in isolation (no database, no real questions)
- **Layer 3**: Tests full survey flow with simulated users answering questions

---

## The Test Flow

### Step 1: Create a Simulated User

A simulated user has a **known vocabulary boundary** - we know exactly what words they know.

```python
class SimulatedUser:
    def __init__(self, vocab_boundary: int, consistency: float = 0.95):
        """
        Args:
            vocab_boundary: User knows words up to this rank (e.g., 2000)
            consistency: Probability of correct answer within known range (0.95 = 95%)
        """
        self.vocab_boundary = vocab_boundary
        self.consistency = consistency
    
    def answer_question(self, word_rank: int) -> bool:
        """
        Simulate user answering a question.
        
        Logic:
        - If word_rank <= vocab_boundary: User knows it (usually correct)
        - If word_rank > vocab_boundary: User doesn't know it (usually wrong)
        - Small chance of mistakes/lucky guesses for realism
        """
        if word_rank <= self.vocab_boundary:
            # Known word - usually correct (95% chance)
            return random.random() < self.consistency
        else:
            # Unknown word - usually wrong, but 10% lucky guess
            return random.random() < 0.10
```

**Example:**
- User with `vocab_boundary=2000` knows words at ranks 1-2000
- Question at rank 1500 → User answers correctly (95% chance)
- Question at rank 3000 → User answers incorrectly (90% chance)

---

### Step 2: Run Complete Survey

The test runs a **full survey** from start to finish, simulating the user answering each question.

```python
def test_volume_accuracy():
    """Test that calculated Volume matches known vocabulary size."""
    # Create user who knows 2000 words
    user = SimulatedUser(vocab_boundary=2000)
    
    # Initialize survey
    engine = LexiSurveyEngine(neo4j_conn)
    state = SurveyState(
        session_id="test",
        current_rank=2000,  # Start at median
        low_bound=1,
        high_bound=8000
    )
    
    # Run survey loop
    result = engine.process_step(state)  # Get first question
    
    while result.status == "continue":
        # User answers based on word rank
        question_rank = result.payload.rank
        is_correct = user.answer_question(question_rank)
        
        # Create answer submission
        answer = AnswerSubmission(
            question_id=result.payload.question_id,
            selected_option_ids=get_answer_options(result.payload, is_correct),
            time_taken=random.uniform(3, 8)
        )
        
        # Submit answer and get next question
        result = engine.process_step(state, answer, result.payload.dict())
    
    # Survey complete - check metrics
    assert 1700 <= result.metrics.volume <= 2300  # ±15% tolerance
```

---

### Step 3: Validate Metrics Against Ground Truth

Since we know the user's vocabulary boundary, we can validate the calculated metrics.

```python
# Ground Truth
user_knows_words_up_to_rank = 2000
expected_volume = ~2000 words
expected_reach = ~2000 rank

# Survey Results
calculated_volume = result.metrics.volume
calculated_reach = result.metrics.reach

# Validation
assert abs(calculated_volume - expected_volume) < expected_volume * 0.15
assert abs(calculated_reach - expected_reach) < expected_reach * 0.20
```

---

## Complete Test Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    LAYER 3 TEST FLOW                         │
└─────────────────────────────────────────────────────────────┘

1. SETUP
   ├── Create SimulatedUser with known vocab_boundary (e.g., 2000)
   ├── Initialize LexiSurveyEngine with mock/real Neo4j
   └── Create SurveyState (start at rank 2000)

2. SURVEY LOOP (15-20 questions)
   │
   ├── Question 1 (Phase 1)
   │   ├── Engine calculates next rank (e.g., 4000)
   │   ├── Engine generates question payload
   │   ├── User answers: knows rank 4000? → NO → Wrong
   │   ├── Engine updates bounds: high_bound = 4000
   │   └── Continue...
   │
   ├── Question 2 (Phase 1)
   │   ├── Engine calculates next rank (e.g., 2000)
   │   ├── Engine generates question payload
   │   ├── User answers: knows rank 2000? → YES → Correct
   │   ├── Engine updates bounds: low_bound = 2000
   │   └── Continue...
   │
   ├── ... (Questions 3-14)
   │
   └── Question 15 (Phase 3)
       ├── Engine checks: should complete? → YES
       ├── Engine calculates final metrics
       └── Return SurveyResult with metrics

3. VALIDATION
   ├── Compare calculated Volume vs expected (~2000)
   ├── Compare calculated Reach vs expected (~2000)
   ├── Check Density is reasonable (>0.7 for consistent user)
   └── Verify convergence (bounds are tight)

4. ASSERTIONS
   ├── Volume accuracy: ±15% tolerance
   ├── Reach accuracy: ±20% tolerance
   └── Density: >0.7 for consistent users
```

---

## Example Test Scenarios

### Scenario 1: Beginner User (Rank 1000)

```python
def test_beginner_user():
    """User knows ~1000 words."""
    user = SimulatedUser(vocab_boundary=1000, consistency=0.95)
    
    result = run_complete_survey(engine, user)
    
    # Validate
    assert 850 <= result.metrics.volume <= 1150  # ±15%
    assert 800 <= result.metrics.reach <= 1200  # ±20%
    assert result.metrics.density > 0.7  # Consistent user
```

### Scenario 2: Intermediate User (Rank 2000)

```python
def test_intermediate_user():
    """User knows ~2000 words."""
    user = SimulatedUser(vocab_boundary=2000, consistency=0.95)
    
    result = run_complete_survey(engine, user)
    
    # Validate
    assert 1700 <= result.metrics.volume <= 2300  # ±15%
    assert 1600 <= result.metrics.reach <= 2400  # ±20%
    assert result.metrics.density > 0.7
```

### Scenario 3: Advanced User (Rank 5000)

```python
def test_advanced_user():
    """User knows ~5000 words."""
    user = SimulatedUser(vocab_boundary=5000, consistency=0.95)
    
    result = run_complete_survey(engine, user)
    
    # Validate
    assert 4250 <= result.metrics.volume <= 5750  # ±15%
    assert 4000 <= result.metrics.reach <= 6000  # ±20%
    assert result.metrics.density > 0.7
```

### Scenario 4: Inconsistent User

```python
def test_inconsistent_user():
    """User with lower consistency (makes more mistakes)."""
    user = SimulatedUser(vocab_boundary=2000, consistency=0.70)
    
    result = run_complete_survey(engine, user)
    
    # Density should be lower due to inconsistency
    assert result.metrics.density < 0.8
    # But volume/reach should still be reasonable
    assert 1500 <= result.metrics.volume <= 2500
```

---

## Key Test Validations

### 1. Volume Accuracy
**Tests:** Does Volume match known vocabulary size?

```python
# Known: User knows 2000 words
# Calculated: result.metrics.volume
# Tolerance: ±15%

assert abs(calculated_volume - 2000) < 2000 * 0.15
```

### 2. Reach Accuracy
**Tests:** Does Reach match vocabulary boundary?

```python
# Known: User knows up to rank 2000
# Calculated: result.metrics.reach
# Tolerance: ±20%

assert abs(calculated_reach - 2000) < 2000 * 0.20
```

### 3. Density Validation
**Tests:** Does Density reflect user consistency?

```python
# Consistent user (95% accuracy) → density > 0.7
# Inconsistent user (70% accuracy) → density < 0.8

if user.consistency >= 0.9:
    assert result.metrics.density > 0.7
else:
    assert result.metrics.density < 0.8
```

### 4. Consistency Across Sessions
**Tests:** Same user should get similar results across multiple sessions.

```python
user = SimulatedUser(vocab_boundary=2000)
results = [run_complete_survey(engine, user) for _ in range(5)]

volumes = [r.metrics.volume for r in results]
reaches = [r.metrics.reach for r in results]

# Standard deviation should be <15% of mean
assert np.std(volumes) < np.mean(volumes) * 0.15
assert np.std(reaches) < np.mean(reaches) * 0.15
```

---

## Realistic Answer Behavior

The `SimulatedUser` models realistic behavior:

### Within Known Range (rank <= vocab_boundary)
- **95% correct** (consistency parameter)
- **5% mistakes** (realistic - users sometimes miss words they know)

### Outside Known Range (rank > vocab_boundary)
- **90% wrong** (user doesn't know the word)
- **10% lucky guess** (realistic - users sometimes guess correctly)

### Example Answer Pattern

```
User knows words up to rank 2000:

Question at rank 1000 → Correct (95% chance)
Question at rank 1500 → Correct (95% chance)
Question at rank 2000 → Correct (95% chance)
Question at rank 2500 → Wrong (90% chance)
Question at rank 3000 → Wrong (90% chance)
Question at rank 5000 → Wrong (90% chance)
```

---

## Test Execution Flow

```python
def run_complete_survey(engine, user):
    """Run a complete survey with simulated user."""
    # 1. Initialize
    state = SurveyState(
        session_id=str(uuid.uuid4()),
        current_rank=2000,
        low_bound=1,
        high_bound=8000
    )
    
    # 2. Get first question
    result = engine.process_step(state)
    
    # 3. Answer loop
    while result.status == "continue":
        # User answers based on word rank
        question_rank = result.payload.rank
        is_correct = user.answer_question(question_rank)
        
        # Create answer
        answer = create_answer(result.payload, is_correct)
        
        # Submit and get next question
        result = engine.process_step(state, answer, result.payload.dict())
    
    # 4. Return final result
    return result
```

---

## What Layer 3 Tests

✅ **Metric Accuracy**: Volume/Reach/Density match ground truth  
✅ **Algorithm Effectiveness**: Survey converges to correct boundary  
✅ **Consistency**: Same user gets similar results across sessions  
✅ **Realistic Behavior**: Handles user mistakes and lucky guesses  
✅ **Edge Cases**: Works at different vocabulary levels (1000, 2000, 5000)

## What Layer 3 Doesn't Test

❌ **Question Quality**: That's Layer 1 (data audit)  
❌ **Algorithm Logic**: That's Layer 2 (unit tests)  
❌ **LLM Evaluation**: That's Layer 4 (holistic review)

---

## Expected Test Results

For a user with `vocab_boundary=2000`:

```
Expected Metrics:
- Volume: ~2000 words (±15% = 1700-2300)
- Reach: ~2000 rank (±20% = 1600-2400)
- Density: >0.7 (consistent user)

Test Passes If:
✅ Volume within 1700-2300
✅ Reach within 1600-2400
✅ Density > 0.7
✅ Bounds converged (high_bound - low_bound < 1000)
✅ Survey completed in 15-20 questions
```

---

## Summary

**Layer 3** validates that the **complete survey system** produces **accurate metrics** when given **realistic user behavior**. It's the bridge between:
- **Layer 2** (algorithm logic) → **Layer 3** (full system with simulated users) → **Layer 4** (real user validation)

By testing with known ground truth, we can confidently say: "If a user knows 2000 words, the survey will report ~2000 words (±15%)."


