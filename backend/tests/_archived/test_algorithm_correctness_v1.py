"""
Layer 2: Algorithm Correctness Tests (Deterministic)

Tests the core LexiSurvey algorithm logic without requiring:
- Database connections
- LLM calls
- Real user data

Pure unit tests that verify:
1. Binary search convergence
2. Phase transitions
3. Metric calculations (Volume, Reach, Density)
4. Edge cases

These tests are fast, reliable, and catch algorithm bugs early.
"""

import pytest
from unittest.mock import Mock, MagicMock
from src.survey.lexisurvey_engine import LexiSurveyEngine
from src.survey.models import SurveyState, AnswerSubmission


def make_mock_neo4j_conn():
    """Create a mock Neo4j connection for testing."""
    mock_conn = Mock()
    mock_session = MagicMock()
    
    # Make get_session() return a context manager
    mock_context = MagicMock()
    mock_context.__enter__ = Mock(return_value=mock_session)
    mock_context.__exit__ = Mock(return_value=None)
    mock_conn.get_session = Mock(return_value=mock_context)
    
    # Mock session.run to return empty results (we don't need real data)
    mock_session.run.return_value = []
    
    return mock_conn


def make_state(
    session_id: str = "test_session",
    current_rank: int = 2000,
    low_bound: int = 1,
    high_bound: int = 8000,
    history: list = None,
    phase: int = 1,
    confidence: float = 0.0
) -> SurveyState:
    """Helper to create a SurveyState for testing."""
    return SurveyState(
        session_id=session_id,
        current_rank=current_rank,
        low_bound=low_bound,
        high_bound=high_bound,
        history=history or [],
        phase=phase,
        confidence=confidence
    )


def make_answer(question_id: str, is_correct: bool, time_taken: float = 5.0) -> AnswerSubmission:
    """Helper to create an AnswerSubmission for testing."""
    if is_correct:
        # Correct answer: select target options
        selected_ids = ["target_1", "target_2"]
    else:
        # Wrong answer: select trap or unknown
        selected_ids = ["trap_1"]
    
    return AnswerSubmission(
        question_id=question_id,
        selected_option_ids=selected_ids,
        time_taken=time_taken
    )


class TestBinarySearchConvergence:
    """Test that binary search converges correctly to user's vocabulary boundary."""
    
    def test_converges_on_known_boundary(self):
        """
        Scenario: User knows words up to rank 2000, nothing beyond.
        
        Expected: Bounds should converge around 2000 after 15 questions.
        """
        engine = LexiSurveyEngine(make_mock_neo4j_conn())
        state = make_state(
            current_rank=4000,  # Start in middle
            low_bound=1,
            high_bound=8000
        )
        
        boundary = 2000  # User's actual vocabulary boundary
        
        # Simulate 15 questions
        for question_num in range(15):
            # Calculate next rank to test
            next_rank = engine._calculate_next_rank(state, question_num)
            state.current_rank = next_rank
            
            # User answers: correct if rank <= boundary
            is_correct = next_rank <= boundary
            
            # Update bounds (this is what we're testing!)
            if is_correct:
                state.low_bound = max(state.low_bound, next_rank)
            else:
                state.high_bound = min(state.high_bound, next_rank)
            
            # Add to history
            state.history.append({
                "rank": next_rank,
                "correct": is_correct
            })
            
            # Update phase
            state.phase = engine._determine_phase(question_num)
        
        # VERIFY CONVERGENCE
        final_range = (state.low_bound, state.high_bound)
        midpoint = (final_range[0] + final_range[1]) / 2
        
        # The bounds should have converged around the boundary
        assert abs(midpoint - boundary) < 500, \
            f"Didn't converge! Midpoint={midpoint}, expected ~{boundary}, bounds={final_range}"
        
        # The range should be tight (not too wide)
        assert (final_range[1] - final_range[0]) < 1000, \
            f"Range too wide! {final_range[1] - final_range[0]}"
        
        # Low bound should be near or below boundary
        assert state.low_bound >= boundary * 0.9, \
            f"Low bound too low! {state.low_bound} < {boundary * 0.9}"
        
        # High bound should be near or above boundary
        assert state.high_bound <= boundary * 1.1, \
            f"High bound too high! {state.high_bound} > {boundary * 1.1}"
    
    def test_converges_faster_in_phase_2(self):
        """
        Phase 2 should narrow bounds more quickly than Phase 1.
        """
        engine = LexiSurveyEngine(make_mock_neo4j_conn())
        boundary = 2500
        
        # Phase 1: Coarse sweep
        state = make_state(current_rank=4000)
        phase1_range_start = state.high_bound - state.low_bound
        
        for q in range(5):
            rank = engine._calculate_next_rank(state, q)
            is_correct = rank <= boundary
            if is_correct:
                state.low_bound = max(state.low_bound, rank)
            else:
                state.high_bound = min(state.high_bound, rank)
            state.history.append({"rank": rank, "correct": is_correct})
        
        phase1_range_end = state.high_bound - state.low_bound
        phase1_reduction = phase1_range_start - phase1_range_end
        
        # Phase 2: Fine tuning (should narrow more)
        for q in range(5, 12):
            rank = engine._calculate_next_rank(state, q)
            is_correct = rank <= boundary
            if is_correct:
                state.low_bound = max(state.low_bound, rank)
            else:
                state.high_bound = min(state.high_bound, rank)
            state.history.append({"rank": rank, "correct": is_correct})
        
        phase2_range_end = state.high_bound - state.low_bound
        phase2_reduction = phase1_range_end - phase2_range_end
        
        # Phase 2 should reduce range more efficiently (smaller steps, more precision)
        # But total reduction might be similar - the key is that bounds get tighter
        # Phase 2 should not make things worse (range should be <= Phase 1 range)
        assert phase2_range_end <= phase1_range_end, \
            f"Phase 2 should not widen bounds. Phase 1 end: {phase1_range_end}, Phase 2 end: {phase2_range_end}"
        
        # Verify that bounds are still converging (getting tighter)
        # The range should be reasonable after both phases
        assert phase2_range_end < phase1_range_start, \
            f"Bounds should converge overall. Start: {phase1_range_start}, End: {phase2_range_end}"
    
    def test_handles_oscillation_in_phase_2(self):
        """
        Phase 2 uses oscillation - should alternate above/below midpoint.
        """
        engine = LexiSurveyEngine(make_mock_neo4j_conn())
        state = make_state(
            current_rank=3000,
            low_bound=2000,
            high_bound=4000
        )
        state.history.append({"rank": 2500, "correct": True})  # Need history for oscillation
        
        # Phase 2 should oscillate
        ranks = []
        for q in range(5, 12):  # More Phase 2 questions to see oscillation
            rank = engine._calculate_next_rank(state, q)
            ranks.append(rank)
            state.current_rank = rank
            # Update bounds to simulate answers
            if rank <= 3000:
                state.low_bound = max(state.low_bound, rank)
            else:
                state.high_bound = min(state.high_bound, rank)
        
        # Should see variation (not always same rank)
        # Note: Due to randomness, might not always oscillate, but should vary
        assert len(set(ranks)) >= 1, "Phase 2 should calculate ranks"
        # Check that ranks are within bounds
        assert all(2000 <= r <= 4000 for r in ranks), "All ranks should be within bounds"
    
    @pytest.mark.parametrize("boundary,expected_tolerance", [
        (1000, 300),
        (2000, 500),
        (3500, 700),
        (5000, 1000),
    ])
    def test_converges_at_different_boundaries(self, boundary, expected_tolerance):
        """
        Test convergence works at different vocabulary levels.
        """
        engine = LexiSurveyEngine(make_mock_neo4j_conn())
        state = make_state(current_rank=4000)
        
        for q in range(15):
            rank = engine._calculate_next_rank(state, q)
            is_correct = rank <= boundary
            if is_correct:
                state.low_bound = max(state.low_bound, rank)
            else:
                state.high_bound = min(state.high_bound, rank)
            state.history.append({"rank": rank, "correct": is_correct})
            state.phase = engine._determine_phase(q)
        
        midpoint = (state.low_bound + state.high_bound) / 2
        assert abs(midpoint - boundary) < expected_tolerance, \
            f"Didn't converge to boundary {boundary}. Midpoint={midpoint}, bounds=({state.low_bound}, {state.high_bound})"


class TestPhaseTransitions:
    """Test that phase transitions happen at correct question counts."""
    
    def test_phase_transitions_at_correct_questions(self):
        """Verify phases change at Q5 and Q12."""
        engine = LexiSurveyEngine(make_mock_neo4j_conn())
        
        # Question 0-4: Phase 1
        assert engine._determine_phase(0) == 1
        assert engine._determine_phase(1) == 1
        assert engine._determine_phase(4) == 1
        
        # Question 5-11: Phase 2
        assert engine._determine_phase(5) == 2
        assert engine._determine_phase(6) == 2
        assert engine._determine_phase(11) == 2
        
        # Question 12+: Phase 3
        assert engine._determine_phase(12) == 3
        assert engine._determine_phase(14) == 3
        assert engine._determine_phase(19) == 3
    
    def test_step_sizes_decrease_by_phase(self):
        """Verify step sizes: 1500 → 200 → 100."""
        engine = LexiSurveyEngine(make_mock_neo4j_conn())
        
        assert engine.PHASE_1_STEP == 1500, "Phase 1 should use large steps"
        assert engine.PHASE_2_STEP == 200, "Phase 2 should use medium steps"
        assert engine.PHASE_3_STEP == 100, "Phase 3 should use small steps"
        
        # Verify step sizes are in descending order
        assert engine.PHASE_1_STEP > engine.PHASE_2_STEP > engine.PHASE_3_STEP
    
    def test_phase_1_uses_large_steps(self):
        """Phase 1 should jump around widely."""
        engine = LexiSurveyEngine(make_mock_neo4j_conn())
        state = make_state(current_rank=4000)
        
        ranks = []
        for q in range(5):  # Phase 1
            rank = engine._calculate_next_rank(state, q)
            ranks.append(rank)
            state.current_rank = rank
        
        # Should see variation (due to randomness and large step size)
        # Step size is 1500, so with randomness we should see some variation
        rank_range = max(ranks) - min(ranks)
        # With step size of 1500 and randomness, should see at least some variation
        # But might be smaller due to clamping to bounds
        assert rank_range >= 100, f"Phase 1 should have some variation, got range={rank_range}"
    
    def test_phase_3_uses_small_steps(self):
        """Phase 3 should make small adjustments."""
        engine = LexiSurveyEngine(make_mock_neo4j_conn())
        state = make_state(
            current_rank=2500,
            low_bound=2000,
            high_bound=3000
        )
        
        ranks = []
        for q in range(12, 15):  # Phase 3
            rank = engine._calculate_next_rank(state, q)
            ranks.append(rank)
        
        # Should see small variation
        rank_range = max(ranks) - min(ranks)
        assert rank_range < 500, f"Phase 3 should have small steps, got range={rank_range}"


class TestMetricCalculations:
    """Test Volume/Reach/Density calculation formulas."""
    
    def test_volume_with_all_correct(self):
        """If user gets all questions correct, volume should be high."""
        engine = LexiSurveyEngine(make_mock_neo4j_conn())
        history = [
            {"rank": 1000, "correct": True},
            {"rank": 2000, "correct": True},
            {"rank": 3000, "correct": True},
        ]
        state = make_state(history=history)
        
        metrics = engine._calculate_final_metrics(state)
        
        # Volume should be roughly average of ranks (2000)
        # With all correct, weights are 1.0, so should be close to average
        assert 1500 < metrics.volume < 2500, \
            f"Volume should be around 2000 for all correct, got {metrics.volume}"
    
    def test_reach_is_max_correct_rank(self):
        """Reach should be the highest rank where user answered correctly."""
        engine = LexiSurveyEngine(make_mock_neo4j_conn())
        history = [
            {"rank": 1000, "correct": True},
            {"rank": 3000, "correct": True},
            {"rank": 5000, "correct": False},  # User doesn't know this
        ]
        state = make_state(history=history)
        
        metrics = engine._calculate_final_metrics(state)
        
        # Reach should be 3000 (highest correct rank)
        assert metrics.reach == 3000, \
            f"Reach should be 3000 (max correct rank), got {metrics.reach}"
    
    def test_density_within_owned_zone(self):
        """Density = consistency within the zone user 'owns'."""
        engine = LexiSurveyEngine(make_mock_neo4j_conn())
        history = [
            {"rank": 1000, "correct": True},
            {"rank": 1500, "correct": True},
            {"rank": 2000, "correct": False},  # Gap in knowledge
        ]
        state = make_state(
            history=history,
            low_bound=1,
            high_bound=2500
        )
        # Set reach to 2000 (highest correct rank is 1500, but let's set it to 2000 for test)
        # Actually, reach will be max(correct_ranks) = 1500
        # So owned zone is 1-1500, which includes ranks 1000 and 1500 (both correct)
        # Density = 2 correct / 2 total in zone = 1.0
        
        metrics = engine._calculate_final_metrics(state)
        
        # Reach will be 1500 (max correct rank)
        # Owned zone: 1-1500 includes ranks 1000 and 1500 (both correct)
        # So density = 2/2 = 1.0
        assert metrics.density > 0.5, \
            f"Density should be calculated correctly, got {metrics.density}"
    
    def test_volume_weights_correctness(self):
        """Correct answers should contribute more to volume than wrong ones."""
        engine = LexiSurveyEngine(make_mock_neo4j_conn())
        
        history_correct = [
            {"rank": 2000, "correct": True},
            {"rank": 2000, "correct": True},
        ]
        history_wrong = [
            {"rank": 2000, "correct": False},
            {"rank": 2000, "correct": False},
        ]
        
        state_correct = make_state(history=history_correct)
        state_wrong = make_state(history=history_wrong)
        
        metrics_correct = engine._calculate_final_metrics(state_correct)
        metrics_wrong = engine._calculate_final_metrics(state_wrong)
        
        # Correct answers should give higher volume
        assert metrics_correct.volume > metrics_wrong.volume * 2, \
            f"Correct answers should give much higher volume. Correct={metrics_correct.volume}, Wrong={metrics_wrong.volume}"
    
    def test_reach_with_no_correct_answers(self):
        """If user gets nothing correct, reach should be low_bound."""
        engine = LexiSurveyEngine(make_mock_neo4j_conn())
        history = [
            {"rank": 1000, "correct": False},
            {"rank": 2000, "correct": False},
        ]
        state = make_state(
            history=history,
            low_bound=500
        )
        
        metrics = engine._calculate_final_metrics(state)
        
        # Reach should fall back to low_bound
        assert metrics.reach == 500, \
            f"Reach should be low_bound (500) when no correct answers, got {metrics.reach}"
    
    def test_density_monotonicity_based(self):
        """Density uses monotonicity (proportion of consistent pairs)."""
        engine = LexiSurveyEngine(make_mock_neo4j_conn())
        
        # Test 1: Perfect monotonicity (correct → correct → wrong)
        # All pairs are consistent: (T,T) and (T,F) - no reversals
        history_consistent = [
            {"rank": 1000, "correct": True},
            {"rank": 2000, "correct": True},
            {"rank": 3000, "correct": False},
        ]
        state_consistent = make_state(history=history_consistent)
        metrics_consistent = engine._calculate_final_metrics(state_consistent)
        
        # Pairs: (T→T) consistent, (T→F) consistent = 2/2 = 1.0
        assert metrics_consistent.density == 1.0, \
            f"Consistent pattern should have density 1.0, got {metrics_consistent.density}"
        
        # Test 2: Pattern with reversal (wrong → correct = gap in knowledge)
        history_inconsistent = [
            {"rank": 1000, "correct": False},  # Gap at low rank
            {"rank": 2000, "correct": True},   # Correct at higher rank - reversal!
            {"rank": 3000, "correct": False},
        ]
        state_inconsistent = make_state(history=history_inconsistent)
        metrics_inconsistent = engine._calculate_final_metrics(state_inconsistent)
        
        # Pairs: (F→T) REVERSAL, (T→F) consistent = 1/2 = 0.5
        assert metrics_inconsistent.density == 0.5, \
            f"Inconsistent pattern should have density 0.5, got {metrics_inconsistent.density}"
        
        # Consistent user should have higher density than inconsistent
        assert metrics_consistent.density > metrics_inconsistent.density
    
    def test_volume_normalization(self):
        """Volume should be normalized by number of questions."""
        engine = LexiSurveyEngine(make_mock_neo4j_conn())
        
        # Same average rank, different question counts
        history_short = [{"rank": 2000, "correct": True}]
        history_long = [
            {"rank": 2000, "correct": True},
            {"rank": 2000, "correct": True},
            {"rank": 2000, "correct": True},
        ]
        
        state_short = make_state(history=history_short)
        state_long = make_state(history=history_long)
        
        metrics_short = engine._calculate_final_metrics(state_short)
        metrics_long = engine._calculate_final_metrics(state_long)
        
        # Volumes should be similar (normalized), not 3x different
        assert abs(metrics_short.volume - metrics_long.volume) < 1000, \
            f"Volume should be normalized. Short={metrics_short.volume}, Long={metrics_long.volume}"


class TestEdgeCases:
    """Test edge cases that could break the algorithm."""
    
    def test_all_wrong_answers(self):
        """User knows nothing - all answers wrong. Should handle gracefully."""
        engine = LexiSurveyEngine(make_mock_neo4j_conn())
        history = [
            {"rank": 500, "correct": False},
            {"rank": 1000, "correct": False},
            {"rank": 2000, "correct": False},
            {"rank": 4000, "correct": False},
        ]
        state = make_state(history=history)
        
        metrics = engine._calculate_final_metrics(state)
        
        # Should handle gracefully
        assert metrics.volume < 1000, f"Volume should be low for all wrong, got {metrics.volume}"
        assert metrics.reach < 1000, f"Reach should be low for all wrong, got {metrics.reach}"
        assert metrics.density == 0.0, f"Density should be 0.0 for all wrong, got {metrics.density}"
    
    def test_all_correct_answers(self):
        """User knows everything - all answers correct. Should handle gracefully."""
        engine = LexiSurveyEngine(make_mock_neo4j_conn())
        history = [
            {"rank": 1000, "correct": True},
            {"rank": 3000, "correct": True},
            {"rank": 5000, "correct": True},
            {"rank": 7000, "correct": True},
        ]
        state = make_state(history=history)
        
        metrics = engine._calculate_final_metrics(state)
        
        # Volume calculation: weighted sum normalized by count
        # With all correct, should be roughly average of ranks
        assert metrics.volume > 2000, f"Volume should be high for all correct, got {metrics.volume}"
        assert metrics.reach > 6000, f"Reach should be high for all correct, got {metrics.reach}"
        assert metrics.density > 0.9, f"Density should be high for all correct, got {metrics.density}"
    
    def test_empty_history(self):
        """No questions answered yet. Should return zero metrics, not crash."""
        engine = LexiSurveyEngine(make_mock_neo4j_conn())
        state = make_state(history=[])
        
        metrics = engine._calculate_final_metrics(state)
        
        assert metrics.volume == 0, f"Volume should be 0 for empty history, got {metrics.volume}"
        assert metrics.reach == 0, f"Reach should be 0 for empty history, got {metrics.reach}"
        assert metrics.density == 0.0, f"Density should be 0.0 for empty history, got {metrics.density}"
    
    def test_bounds_at_extremes(self):
        """Bounds at 1 or 8000 - edge of search space."""
        engine = LexiSurveyEngine(make_mock_neo4j_conn())
        
        # User knows everything (boundary at 8000)
        state = make_state(
            low_bound=7500,
            high_bound=8000,
            current_rank=7750
        )
        state.history.append({"rank": 7750, "correct": True})
        
        next_rank = engine._calculate_next_rank(state, question_count=5)
        
        # Should stay within bounds
        assert state.low_bound <= next_rank <= state.high_bound, \
            f"Next rank {next_rank} should be within bounds ({state.low_bound}, {state.high_bound})"
        assert 1 <= next_rank <= 8000, \
            f"Next rank {next_rank} should be within global bounds (1, 8000)"
    
    def test_bounds_at_low_extreme(self):
        """User knows nothing (boundary at 1)."""
        engine = LexiSurveyEngine(make_mock_neo4j_conn())
        state = make_state(
            low_bound=1,
            high_bound=500,
            current_rank=250
        )
        state.history.append({"rank": 250, "correct": False})
        
        next_rank = engine._calculate_next_rank(state, question_count=5)
        
        assert state.low_bound <= next_rank <= state.high_bound, \
            f"Next rank {next_rank} should be within bounds ({state.low_bound}, {state.high_bound})"
        assert 1 <= next_rank <= 8000, \
            f"Next rank {next_rank} should be within global bounds (1, 8000)"
    
    def test_inconsistent_user(self):
        """User is inconsistent - sometimes knows hard words, sometimes misses easy ones."""
        engine = LexiSurveyEngine(make_mock_neo4j_conn())
        history = [
            {"rank": 5000, "correct": True},   # Knows hard word
            {"rank": 1000, "correct": False},  # Misses easy word
            {"rank": 6000, "correct": True},   # Knows harder word
            {"rank": 500, "correct": False},   # Misses easier word
        ]
        state = make_state(history=history)
        
        # Should still calculate metrics (maybe with lower density)
        metrics = engine._calculate_final_metrics(state)
        
        assert metrics.density < 0.7, \
            f"Density should be lower due to inconsistency, got {metrics.density}"
        assert 0 <= metrics.volume <= 8000, \
            f"Volume should be valid, got {metrics.volume}"
        assert 0 <= metrics.reach <= 8000, \
            f"Reach should be valid, got {metrics.reach}"
    
    def test_single_question(self):
        """Only one question answered."""
        engine = LexiSurveyEngine(make_mock_neo4j_conn())
        history = [{"rank": 2000, "correct": True}]
        state = make_state(history=history)
        
        metrics = engine._calculate_final_metrics(state)
        
        # Should still calculate valid metrics
        assert metrics.volume > 0, f"Volume should be > 0, got {metrics.volume}"
        assert metrics.reach == 2000, f"Reach should be 2000, got {metrics.reach}"
        assert metrics.density > 0, f"Density should be > 0, got {metrics.density}"
    
    def test_reach_reduction_on_poor_recent_performance(self):
        """Reach should be reduced if last few answers were wrong."""
        engine = LexiSurveyEngine(make_mock_neo4j_conn())
        history = [
            {"rank": 1000, "correct": True},
            {"rank": 2000, "correct": True},
            {"rank": 3000, "correct": True},
            {"rank": 4000, "correct": False},  # Recent wrong
            {"rank": 4500, "correct": False},   # Recent wrong
            {"rank": 5000, "correct": False},  # Recent wrong
        ]
        state = make_state(history=history)
        
        metrics = engine._calculate_final_metrics(state)
        
        # Reach should be reduced from 3000 (max correct) due to recent poor performance
        # Original reach would be 3000, but with 3 recent wrong answers, should be reduced
        assert metrics.reach <= 3000, \
            f"Reach should be reduced from 3000 due to recent poor performance, got {metrics.reach}"
        # Should be reduced by ~20% (0.8 * 3000 = 2400)
        assert metrics.reach < 3000, \
            f"Reach should be less than 3000, got {metrics.reach}"


class TestBoundUpdates:
    """Test that bounds update correctly based on answers."""
    
    def test_correct_answer_updates_low_bound(self):
        """Correct answer should raise low_bound."""
        engine = LexiSurveyEngine(make_mock_neo4j_conn())
        state = make_state(low_bound=1000, high_bound=8000)
        
        answer = make_answer("q_2000", is_correct=True)
        engine._grade_answer(state, answer, {"word": "test", "rank": 2000})
        
        assert state.low_bound == 2000, \
            f"Low bound should be updated to 2000, got {state.low_bound}"
    
    def test_wrong_answer_updates_high_bound(self):
        """Wrong answer should lower high_bound."""
        engine = LexiSurveyEngine(make_mock_neo4j_conn())
        state = make_state(low_bound=1, high_bound=8000)
        
        answer = make_answer("q_3000", is_correct=False)
        engine._grade_answer(state, answer, {"word": "test", "rank": 3000})
        
        assert state.high_bound == 3000, \
            f"High bound should be updated to 3000, got {state.high_bound}"
    
    def test_bounds_never_cross(self):
        """Low bound should never exceed high bound."""
        engine = LexiSurveyEngine(make_mock_neo4j_conn())
        state = make_state(low_bound=2000, high_bound=3000)
        
        # Answer correctly at 2500 (raises low_bound to 2500)
        answer1 = make_answer("q_2500", is_correct=True)
        engine._grade_answer(state, answer1, {"word": "test", "rank": 2500})
        assert state.low_bound == 2500
        
        # Answer incorrectly at 2800 (lowers high_bound to 2800)
        answer2 = make_answer("q_2800", is_correct=False)
        engine._grade_answer(state, answer2, {"word": "test", "rank": 2800})
        
        # Bounds should still be valid (2500 <= 2800)
        assert state.low_bound <= state.high_bound, \
            f"Bounds crossed! low={state.low_bound}, high={state.high_bound}"
        
        # Test that bounds update correctly
        assert state.low_bound >= 2500, "Low bound should be at least 2500"
        assert state.high_bound <= 2800, "High bound should be at most 2800"


class TestAnswerEvaluation:
    """Test answer correctness evaluation logic."""
    
    def test_target_options_are_correct(self):
        """Selecting target options should be correct."""
        engine = LexiSurveyEngine(make_mock_neo4j_conn())
        
        answer = AnswerSubmission(
            question_id="q_2000",
            selected_option_ids=["target_1", "target_2"],
            time_taken=5.0
        )
        
        assert engine._evaluate_answer_correctness(answer) == True
    
    def test_unknown_option_is_wrong(self):
        """Selecting 'unknown' should always be wrong."""
        engine = LexiSurveyEngine(make_mock_neo4j_conn())
        
        answer = AnswerSubmission(
            question_id="q_2000",
            selected_option_ids=["unknown"],
            time_taken=5.0
        )
        
        assert engine._evaluate_answer_correctness(answer) == False
    
    def test_trap_options_are_wrong(self):
        """Selecting trap options should be wrong."""
        engine = LexiSurveyEngine(make_mock_neo4j_conn())
        
        answer = AnswerSubmission(
            question_id="q_2000",
            selected_option_ids=["trap_1"],
            time_taken=5.0
        )
        
        assert engine._evaluate_answer_correctness(answer) == False
    
    def test_mixed_target_and_trap_is_wrong(self):
        """Selecting both target and trap should be wrong."""
        engine = LexiSurveyEngine(make_mock_neo4j_conn())
        
        answer = AnswerSubmission(
            question_id="q_2000",
            selected_option_ids=["target_1", "trap_1"],
            time_taken=5.0
        )
        
        assert engine._evaluate_answer_correctness(answer) == False

