# Layer 2: Algorithm Correctness Tests

**Status:** ✅ Complete  
**Test File:** `test_algorithm_correctness.py`  
**Tests:** 33 tests, all passing

## Overview

Layer 2 provides **deterministic unit tests** for the LexiSurvey algorithm. These tests verify the core algorithm logic without requiring:
- Database connections
- LLM calls
- Real user data

**Key Benefits:**
- ⚡ **Fast**: Runs in <1 second
- 🎯 **Reliable**: Deterministic, same results every time
- 🐛 **Catches bugs early**: Finds algorithm errors before integration
- 📚 **Documents behavior**: Tests serve as specifications

## Test Coverage

### 1. Binary Search Convergence (4 tests)
Tests that the binary search algorithm correctly narrows bounds to find the user's vocabulary boundary.

- ✅ `test_converges_on_known_boundary` - Verifies convergence around a known boundary (e.g., rank 2000)
- ✅ `test_converges_faster_in_phase_2` - Phase 2 should narrow bounds more efficiently
- ✅ `test_handles_oscillation_in_phase_2` - Phase 2 oscillation logic works
- ✅ `test_converges_at_different_boundaries` - Works at various vocabulary levels (1000, 2000, 3500, 5000)

### 2. Phase Transitions (4 tests)
Tests that phase transitions happen at correct question counts and step sizes are appropriate.

- ✅ `test_phase_transitions_at_correct_questions` - Phases change at Q5 and Q12
- ✅ `test_step_sizes_decrease_by_phase` - Step sizes: 1500 → 200 → 100
- ✅ `test_phase_1_uses_large_steps` - Phase 1 has large variation
- ✅ `test_phase_3_uses_small_steps` - Phase 3 has small variation

### 3. Metric Calculations (7 tests)
Tests the Volume, Reach, and Density calculation formulas.

- ✅ `test_volume_with_all_correct` - Volume calculation with all correct answers
- ✅ `test_reach_is_max_correct_rank` - Reach = highest rank with correct answer
- ✅ `test_density_within_owned_zone` - Density = consistency within owned zone
- ✅ `test_volume_weights_correctness` - Correct answers contribute more to volume
- ✅ `test_reach_with_no_correct_answers` - Reach falls back to low_bound when no correct
- ✅ `test_density_fallback_to_overall_consistency` - Density uses overall consistency when no owned zone
- ✅ `test_volume_normalization` - Volume is normalized by question count

### 4. Edge Cases (8 tests)
Tests extreme scenarios to ensure the algorithm doesn't break.

- ✅ `test_all_wrong_answers` - User knows nothing, all answers wrong
- ✅ `test_all_correct_answers` - User knows everything, all answers correct
- ✅ `test_empty_history` - No questions answered yet
- ✅ `test_bounds_at_extremes` - Bounds at high extreme (8000)
- ✅ `test_bounds_at_low_extreme` - Bounds at low extreme (1)
- ✅ `test_inconsistent_user` - User with inconsistent answers
- ✅ `test_single_question` - Only one question answered
- ✅ `test_reach_reduction_on_poor_recent_performance` - Reach reduced when recent answers wrong

### 5. Bound Updates (3 tests)
Tests that bounds update correctly based on answers.

- ✅ `test_correct_answer_updates_low_bound` - Correct answer raises low_bound
- ✅ `test_wrong_answer_updates_high_bound` - Wrong answer lowers high_bound
- ✅ `test_bounds_never_cross` - Bounds remain valid (low <= high)

### 6. Answer Evaluation (4 tests)
Tests answer correctness evaluation logic.

- ✅ `test_target_options_are_correct` - Selecting target options is correct
- ✅ `test_unknown_option_is_wrong` - Selecting "unknown" is always wrong
- ✅ `test_trap_options_are_wrong` - Selecting trap options is wrong
- ✅ `test_mixed_target_and_trap_is_wrong` - Mixing target and trap is wrong

## Running the Tests

```bash
cd backend
source venv/bin/activate
pytest tests/test_algorithm_correctness.py -v
```

## Test Structure

Each test class focuses on a specific aspect of the algorithm:

```python
class TestBinarySearchConvergence:
    """Test that binary search converges correctly."""
    # Tests convergence logic

class TestPhaseTransitions:
    """Test phase transitions happen at correct times."""
    # Tests phase logic

class TestMetricCalculations:
    """Test Volume/Reach/Density formulas."""
    # Tests metric calculations

class TestEdgeCases:
    """Test edge cases that could break algorithm."""
    # Tests error handling

class TestBoundUpdates:
    """Test that bounds update correctly."""
    # Tests bound update logic

class TestAnswerEvaluation:
    """Test answer correctness evaluation."""
    # Tests answer evaluation
```

## Mocking Strategy

Tests use a mock Neo4j connection to avoid requiring a real database:

```python
def make_mock_neo4j_conn():
    """Create a mock Neo4j connection for testing."""
    mock_conn = Mock()
    mock_session = MagicMock()
    # ... setup context manager
    return mock_conn
```

This allows testing pure algorithm logic without database dependencies.

## What These Tests Don't Cover

Layer 2 focuses on **algorithm correctness**, not:
- Database queries (covered in integration tests)
- Question generation (covered in Layer 1 - data audit)
- Real user behavior (covered in Layer 3 - simulation)
- LLM evaluation (covered in Layer 4 - holistic review)

## Next Steps

After Layer 2 is complete, proceed to:
1. **Layer 1**: Data Quality Audit (one-time data fixes)
2. **Layer 3**: Survey Simulation (ground truth testing)
3. **Layer 4**: Holistic LLM Review (quality validation)

## Maintenance

When modifying the algorithm:
1. Run Layer 2 tests first to catch algorithm bugs
2. Update tests if algorithm behavior intentionally changes
3. Add new tests for new algorithm features

---

**Last Updated:** 2025-01-XX  
**Test Count:** 33  
**Status:** ✅ All Passing


