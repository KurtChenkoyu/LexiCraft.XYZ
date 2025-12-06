"""
Layer 2: Algorithm Correctness Tests for V2 Engine

Tests the pure algorithm logic without real database calls.
Uses mocks to verify:
- Band-based vocabulary estimation
- Confidence calculation
- Stopping criteria
- Metric calculations (volume, reach, density)
- Band selection strategy

These tests ensure the V2 algorithm works correctly before integration.
"""

import pytest
import random
from unittest.mock import MagicMock, patch
from src.survey.lexisurvey_engine import LexiSurveyEngine
from src.survey.models import (
    SurveyState,
    AnswerSubmission,
    QuestionPayload,
    QuestionOption,
    TriMetricReport
)


# ============================================================================
# Test Fixtures
# ============================================================================

def make_mock_neo4j_conn():
    """Create a mock Neo4j connection."""
    mock_conn = MagicMock()
    mock_session = MagicMock()
    mock_conn.get_session.return_value.__enter__ = MagicMock(return_value=mock_session)
    mock_conn.get_session.return_value.__exit__ = MagicMock(return_value=False)
    return mock_conn


def make_state(
    session_id: str = "test_session",
    current_rank: int = 4000,
    low_bound: int = 1,
    high_bound: int = 8000,
    history: list = None,
    band_performance: dict = None,
    confidence: float = 0.0,
    estimated_vocab: int = 0
) -> SurveyState:
    """Create a SurveyState with given parameters."""
    return SurveyState(
        session_id=session_id,
        current_rank=current_rank,
        low_bound=low_bound,
        high_bound=high_bound,
        history=history or [],
        band_performance=band_performance,
        confidence=confidence,
        estimated_vocab=estimated_vocab
    )


def make_band_performance(accuracies: dict) -> dict:
    """
    Create band_performance dict from accuracy percentages.
    
    Args:
        accuracies: {band: accuracy} e.g., {1000: 0.9, 2000: 0.7, 3000: 0.4}
    """
    bands = [1000, 2000, 3000, 4000, 5000, 6000, 7000, 8000]
    result = {}
    for band in bands:
        if band in accuracies:
            # Create tested/correct to achieve the accuracy
            tested = 4
            correct = int(accuracies[band] * tested)
            result[band] = {"tested": tested, "correct": correct}
        else:
            result[band] = {"tested": 0, "correct": 0}
    return result


# ============================================================================
# Volume Calculation Tests
# ============================================================================

class TestVolumeCalculation:
    """Test the band-based volume estimation formula."""
    
    def test_volume_perfect_knowledge_all_bands(self):
        """User knows 100% of all bands → Volume = 8000."""
        engine = LexiSurveyEngine(make_mock_neo4j_conn())
        
        band_perf = make_band_performance({
            1000: 1.0, 2000: 1.0, 3000: 1.0, 4000: 1.0,
            5000: 1.0, 6000: 1.0, 7000: 1.0, 8000: 1.0
        })
        state = make_state(band_performance=band_perf)
        
        volume = engine._estimate_vocabulary_size(state)
        assert volume == 8000, f"100% accuracy all bands should give 8000, got {volume}"
    
    def test_volume_no_knowledge(self):
        """User knows 0% of all bands → Volume ≈ 0."""
        engine = LexiSurveyEngine(make_mock_neo4j_conn())
        
        band_perf = make_band_performance({
            1000: 0.0, 2000: 0.0, 3000: 0.0, 4000: 0.0,
            5000: 0.0, 6000: 0.0, 7000: 0.0, 8000: 0.0
        })
        state = make_state(band_performance=band_perf)
        
        volume = engine._estimate_vocabulary_size(state)
        assert volume < 500, f"0% accuracy should give low volume, got {volume}"
    
    def test_volume_typical_intermediate(self):
        """
        Typical intermediate learner:
        - 90% at 1K, 70% at 2K, 40% at 3K, 10% at 4K
        - Expected: 900 + 700 + 400 + 100 = 2100 (but untested bands contribute less)
        - With interpolation for 5K-8K bands, volume is lower
        """
        engine = LexiSurveyEngine(make_mock_neo4j_conn())
        
        band_perf = make_band_performance({
            1000: 0.9, 2000: 0.7, 3000: 0.4, 4000: 0.1
        })
        state = make_state(band_performance=band_perf)
        
        volume = engine._estimate_vocabulary_size(state)
        # With interpolation for untested bands, volume is ~1500-2500
        assert 1200 <= volume <= 2500, \
            f"Intermediate learner should have ~1500-2100, got {volume}"
    
    def test_volume_beginner(self):
        """
        Beginner: 80% at 1K, 20% at 2K, 0% above
        Expected: 800 + 200 = 1000 base, but untested bands contribute less
        """
        engine = LexiSurveyEngine(make_mock_neo4j_conn())
        
        band_perf = make_band_performance({
            1000: 0.8, 2000: 0.2, 3000: 0.0
        })
        state = make_state(band_performance=band_perf)
        
        volume = engine._estimate_vocabulary_size(state)
        # With interpolation for untested bands, volume is ~750-1200
        assert 600 <= volume <= 1200, f"Beginner should have ~750-1000, got {volume}"
    
    def test_volume_advanced(self):
        """
        Advanced: 100% at 1K-4K, 80% at 5K, 50% at 6K, 20% at 7K
        Expected: ~5500 words
        """
        engine = LexiSurveyEngine(make_mock_neo4j_conn())
        
        band_perf = make_band_performance({
            1000: 1.0, 2000: 1.0, 3000: 1.0, 4000: 1.0,
            5000: 0.8, 6000: 0.5, 7000: 0.2
        })
        state = make_state(band_performance=band_perf)
        
        volume = engine._estimate_vocabulary_size(state)
        assert 5000 <= volume <= 6500, f"Advanced should have ~5500, got {volume}"
    
    def test_volume_interpolates_untested_bands(self):
        """
        If some bands aren't tested, volume should interpolate reasonably.
        """
        engine = LexiSurveyEngine(make_mock_neo4j_conn())
        
        # Only tested 2K and 4K bands
        band_perf = {
            1000: {"tested": 0, "correct": 0},
            2000: {"tested": 4, "correct": 4},  # 100%
            3000: {"tested": 0, "correct": 0},
            4000: {"tested": 4, "correct": 0},  # 0%
            5000: {"tested": 0, "correct": 0},
            6000: {"tested": 0, "correct": 0},
            7000: {"tested": 0, "correct": 0},
            8000: {"tested": 0, "correct": 0},
        }
        state = make_state(band_performance=band_perf)
        
        volume = engine._estimate_vocabulary_size(state)
        # Should estimate something reasonable between 2000-3000
        assert 1500 <= volume <= 3500, \
            f"Interpolated volume should be reasonable, got {volume}"


# ============================================================================
# Reach Calculation Tests
# ============================================================================

class TestReachCalculation:
    """Test the reach (vocabulary horizon) calculation."""
    
    def test_reach_finds_highest_50_percent_band(self):
        """Reach should be highest band with >=50% accuracy."""
        engine = LexiSurveyEngine(make_mock_neo4j_conn())
        
        band_perf = make_band_performance({
            1000: 1.0, 2000: 0.8, 3000: 0.6, 4000: 0.3  # 3K is highest with >50%
        })
        state = make_state(band_performance=band_perf)
        
        reach = engine._calculate_reach(state)
        assert reach == 3000, f"Reach should be 3000 (last band >50%), got {reach}"
    
    def test_reach_advanced_user(self):
        """Advanced user with high accuracy across bands."""
        engine = LexiSurveyEngine(make_mock_neo4j_conn())
        
        band_perf = make_band_performance({
            1000: 1.0, 2000: 1.0, 3000: 0.9, 4000: 0.8, 
            5000: 0.6, 6000: 0.4  # 5K is highest with >50%
        })
        state = make_state(band_performance=band_perf)
        
        reach = engine._calculate_reach(state)
        assert reach == 5000, f"Advanced reach should be 5000, got {reach}"
    
    def test_reach_beginner_user(self):
        """Beginner user with low reach."""
        engine = LexiSurveyEngine(make_mock_neo4j_conn())
        
        band_perf = make_band_performance({
            1000: 0.7, 2000: 0.3, 3000: 0.0  # Only 1K has >50%
        })
        state = make_state(band_performance=band_perf)
        
        reach = engine._calculate_reach(state)
        assert reach == 1000, f"Beginner reach should be 1000, got {reach}"
    
    def test_reach_requires_minimum_samples(self):
        """Reach should prefer bands with enough samples."""
        engine = LexiSurveyEngine(make_mock_neo4j_conn())
        
        # 4K has 100% but only 1 sample, 3K has 60% with enough samples
        band_perf = {
            1000: {"tested": 4, "correct": 4},
            2000: {"tested": 4, "correct": 3},
            3000: {"tested": 4, "correct": 3},  # 75%, enough samples
            4000: {"tested": 1, "correct": 1},  # 100% but not enough samples
            5000: {"tested": 0, "correct": 0},
            6000: {"tested": 0, "correct": 0},
            7000: {"tested": 0, "correct": 0},
            8000: {"tested": 0, "correct": 0},
        }
        state = make_state(band_performance=band_perf)
        
        reach = engine._calculate_reach(state)
        # Should still find 4K as fallback since it has 100%
        assert reach >= 3000, f"Reach should consider single samples, got {reach}"


# ============================================================================
# Density Calculation Tests
# ============================================================================

class TestDensityCalculation:
    """Test the density (monotonicity) calculation."""
    
    def test_density_perfect_consistency(self):
        """Perfectly consistent user: correct below boundary, wrong above."""
        engine = LexiSurveyEngine(make_mock_neo4j_conn())
        
        history = [
            {"rank": 1000, "correct": True},
            {"rank": 1500, "correct": True},
            {"rank": 2000, "correct": True},
            {"rank": 2500, "correct": False},
            {"rank": 3000, "correct": False},
        ]
        state = make_state(history=history)
        
        density = engine._calculate_density(state)
        assert density == 1.0, f"Perfect consistency should give 1.0, got {density}"
    
    def test_density_with_gaps(self):
        """User with gaps: wrong at lower rank, correct at higher."""
        engine = LexiSurveyEngine(make_mock_neo4j_conn())
        
        history = [
            {"rank": 1000, "correct": False},  # Gap!
            {"rank": 1500, "correct": True},   # Reversal
            {"rank": 2000, "correct": True},
            {"rank": 2500, "correct": False},
        ]
        state = make_state(history=history)
        
        density = engine._calculate_density(state)
        # One reversal out of 3 pairs = 2/3 consistent
        assert 0.6 <= density <= 0.7, f"One gap should give ~0.67, got {density}"
    
    def test_density_all_wrong(self):
        """All wrong answers → density = 0."""
        engine = LexiSurveyEngine(make_mock_neo4j_conn())
        
        history = [
            {"rank": 1000, "correct": False},
            {"rank": 2000, "correct": False},
            {"rank": 3000, "correct": False},
        ]
        state = make_state(history=history)
        
        density = engine._calculate_density(state)
        assert density == 0.0, f"All wrong should give 0, got {density}"
    
    def test_density_all_correct(self):
        """All correct answers → density = 1."""
        engine = LexiSurveyEngine(make_mock_neo4j_conn())
        
        history = [
            {"rank": 1000, "correct": True},
            {"rank": 2000, "correct": True},
            {"rank": 3000, "correct": True},
        ]
        state = make_state(history=history)
        
        density = engine._calculate_density(state)
        assert density == 1.0, f"All correct should give 1.0, got {density}"


# ============================================================================
# Confidence Calculation Tests
# ============================================================================

class TestConfidenceCalculation:
    """Test confidence calculation for stopping criteria."""
    
    def test_confidence_increases_with_questions(self):
        """More questions should increase confidence."""
        engine = LexiSurveyEngine(make_mock_neo4j_conn())
        
        # 5 questions
        state5 = make_state(
            history=[{"rank": i*500, "correct": True} for i in range(1, 6)],
            band_performance=make_band_performance({1000: 1.0, 2000: 0.5})
        )
        conf5 = engine._calculate_confidence(state5)
        
        # 15 questions
        state15 = make_state(
            history=[{"rank": i*500, "correct": True} for i in range(1, 16)],
            band_performance=make_band_performance({1000: 1.0, 2000: 0.8, 3000: 0.5})
        )
        conf15 = engine._calculate_confidence(state15)
        
        assert conf15 > conf5, \
            f"15 questions should have higher confidence than 5: {conf15} vs {conf5}"
    
    def test_confidence_increases_with_band_coverage(self):
        """Testing more bands should increase confidence."""
        engine = LexiSurveyEngine(make_mock_neo4j_conn())
        
        # Only 2 bands tested
        state_few = make_state(
            history=[{"rank": i*500, "correct": True} for i in range(1, 11)],
            band_performance=make_band_performance({1000: 1.0, 2000: 0.5})
        )
        conf_few = engine._calculate_confidence(state_few)
        
        # 5 bands tested
        state_many = make_state(
            history=[{"rank": i*500, "correct": True} for i in range(1, 11)],
            band_performance=make_band_performance({
                1000: 1.0, 2000: 0.9, 3000: 0.7, 4000: 0.5, 5000: 0.2
            })
        )
        conf_many = engine._calculate_confidence(state_many)
        
        assert conf_many > conf_few, \
            f"More bands should increase confidence: {conf_many} vs {conf_few}"


# ============================================================================
# Stopping Criteria Tests
# ============================================================================

class TestStoppingCriteria:
    """Test when the survey should stop."""
    
    def test_stop_at_max_questions(self):
        """Survey stops at max questions regardless of confidence."""
        engine = LexiSurveyEngine(make_mock_neo4j_conn())
        
        # Create state with MAX_QUESTIONS history entries
        history = [{"rank": i*200, "correct": True} for i in range(engine.MAX_QUESTIONS)]
        state = make_state(
            history=history,
            band_performance=make_band_performance({1000: 0.5, 2000: 0.5})
        )
        
        should_stop = engine._should_complete_survey(state, confidence=0.3)
        assert should_stop, "Should stop at max questions even with low confidence"
    
    def test_no_stop_below_minimum(self):
        """Survey doesn't stop below minimum questions."""
        engine = LexiSurveyEngine(make_mock_neo4j_conn())
        
        # Only 5 questions
        history = [{"rank": i*500, "correct": True} for i in range(5)]
        state = make_state(
            history=history,
            band_performance=make_band_performance({1000: 1.0, 2000: 1.0})
        )
        
        should_stop = engine._should_complete_survey(state, confidence=0.95)
        assert not should_stop, "Should not stop below minimum questions even with high confidence"
    
    def test_stop_at_confidence_threshold(self):
        """Survey stops when confidence threshold reached."""
        engine = LexiSurveyEngine(make_mock_neo4j_conn())
        
        # 15 questions (above minimum)
        history = [{"rank": i*400, "correct": True} for i in range(15)]
        state = make_state(
            history=history,
            band_performance=make_band_performance({1000: 1.0, 2000: 0.8, 3000: 0.5})
        )
        
        should_stop = engine._should_complete_survey(state, confidence=0.85)
        assert should_stop, "Should stop when confidence >= threshold"


# ============================================================================
# Band Selection Tests
# ============================================================================

class TestBandSelection:
    """Test the information-gain based band selection."""
    
    def test_selects_undersampled_bands(self):
        """Should prioritize bands with few samples."""
        engine = LexiSurveyEngine(make_mock_neo4j_conn())
        
        # 3K band has no samples, others have plenty
        band_perf = {
            1000: {"tested": 6, "correct": 6},
            2000: {"tested": 6, "correct": 5},
            3000: {"tested": 0, "correct": 0},  # Undersampled!
            4000: {"tested": 6, "correct": 3},
            5000: {"tested": 6, "correct": 2},
            6000: {"tested": 6, "correct": 1},
            7000: {"tested": 6, "correct": 0},
            8000: {"tested": 6, "correct": 0},
        }
        state = make_state(band_performance=band_perf, estimated_vocab=3000)
        
        # Run selection many times, check 3K is selected frequently
        selections = [engine._select_next_band(state) for _ in range(30)]
        count_3k = selections.count(3000)
        
        assert count_3k >= 5, \
            f"Undersampled band 3K should be selected often, got {count_3k}/30"
    
    def test_selects_near_boundary(self):
        """Should prioritize bands near estimated vocabulary boundary."""
        engine = LexiSurveyEngine(make_mock_neo4j_conn())
        
        # All bands equally sampled, boundary around 3000
        band_perf = {band: {"tested": 2, "correct": 1} for band in engine.FREQUENCY_BANDS}
        state = make_state(band_performance=band_perf, estimated_vocab=3000)
        
        # Run selection many times
        selections = [engine._select_next_band(state) for _ in range(50)]
        
        # Bands 2000, 3000, 4000 should be selected most often
        near_boundary = sum(1 for s in selections if 2000 <= s <= 4000)
        
        assert near_boundary >= 25, \
            f"Bands near boundary should be selected often, got {near_boundary}/50"


# ============================================================================
# Integration Tests
# ============================================================================

class TestIntegration:
    """Test full survey flow with mocked database."""
    
    def test_survey_initializes_band_performance(self):
        """First call should initialize band_performance."""
        engine = LexiSurveyEngine(make_mock_neo4j_conn())
        state = make_state(band_performance=None)
        
        # Mock the question generation
        with patch.object(engine, '_generate_question_from_band') as mock_gen:
            mock_gen.return_value = QuestionPayload(
                question_id="q_2000_12345",
                word="test",
                rank=2000,
                options=[
                    QuestionOption(id="target_test_0", text="測試", type="target", is_correct=True),
                    QuestionOption(id="filler_1", text="其他1", type="filler", is_correct=False),
                    QuestionOption(id="filler_2", text="其他2", type="filler", is_correct=False),
                    QuestionOption(id="filler_3", text="其他3", type="filler", is_correct=False),
                    QuestionOption(id="filler_4", text="其他4", type="filler", is_correct=False),
                    QuestionOption(id="unknown_option", text="我不知道", type="unknown", is_correct=False),
                ],
                time_limit=12
            )
            
            result = engine.process_step(state)
        
        assert state.band_performance is not None
        assert len(state.band_performance) == 8  # All bands initialized
        assert result.status == "continue"
    
    def test_answer_updates_band_performance(self):
        """Answering should update band_performance correctly."""
        engine = LexiSurveyEngine(make_mock_neo4j_conn())
        
        band_perf = {band: {"tested": 0, "correct": 0} for band in engine.FREQUENCY_BANDS}
        state = make_state(band_performance=band_perf)
        
        # Simulate answering a question at rank 1500 (band 2000)
        answer = AnswerSubmission(
            question_id="q_1500_12345",
            selected_option_ids=["target_word_0"],
            time_taken=5.0
        )
        
        engine._grade_answer(state, answer, {"word": "test"})
        
        assert state.band_performance[2000]["tested"] == 1
        assert state.band_performance[2000]["correct"] == 1  # Correct answer
    
    def test_full_metrics_reasonable(self):
        """Final metrics should be reasonable for given band performance."""
        engine = LexiSurveyEngine(make_mock_neo4j_conn())
        
        # Simulate intermediate learner
        band_perf = make_band_performance({
            1000: 0.9, 2000: 0.75, 3000: 0.5, 4000: 0.25, 5000: 0.0
        })
        history = [
            {"rank": 1000, "correct": True},
            {"rank": 2000, "correct": True},
            {"rank": 2500, "correct": True},
            {"rank": 3000, "correct": False},
            {"rank": 3500, "correct": False},
        ]
        state = make_state(band_performance=band_perf, history=history)
        
        metrics = engine._calculate_final_metrics(state)
        
        # Volume should be ~2400 (900 + 750 + 500 + 250 + 0...)
        assert 2000 <= metrics.volume <= 3500, \
            f"Volume should be ~2400, got {metrics.volume}"
        
        # Reach should be 3000 (last band with >50%)
        assert 2000 <= metrics.reach <= 4000, \
            f"Reach should be ~3000, got {metrics.reach}"
        
        # Density should be high (consistent pattern)
        assert metrics.density >= 0.5, \
            f"Density should be reasonable, got {metrics.density}"


# ============================================================================
# Edge Cases
# ============================================================================

class TestEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def test_empty_history(self):
        """Handle empty history gracefully."""
        engine = LexiSurveyEngine(make_mock_neo4j_conn())
        state = make_state(history=[], band_performance={})
        
        confidence = engine._calculate_confidence(state)
        assert confidence == 0.0
        
        density = engine._calculate_density(state)
        assert density == 0.0
    
    def test_single_question(self):
        """Handle single question state."""
        engine = LexiSurveyEngine(make_mock_neo4j_conn())
        
        state = make_state(
            history=[{"rank": 2000, "correct": True}],
            band_performance={2000: {"tested": 1, "correct": 1}}
        )
        
        density = engine._calculate_density(state)
        assert density == 1.0  # Single correct = 1.0
    
    def test_all_bands_exhausted(self):
        """Handle case where all bands are well-sampled."""
        engine = LexiSurveyEngine(make_mock_neo4j_conn())
        
        band_perf = {band: {"tested": 10, "correct": 5} for band in engine.FREQUENCY_BANDS}
        state = make_state(band_performance=band_perf)
        
        # Should still select a band
        selected = engine._select_next_band(state)
        assert selected in engine.FREQUENCY_BANDS
    
    def test_rank_to_band_mapping(self):
        """Test rank to band conversion."""
        engine = LexiSurveyEngine(make_mock_neo4j_conn())
        
        assert engine._rank_to_band(500) == 1000
        assert engine._rank_to_band(1000) == 1000
        assert engine._rank_to_band(1001) == 2000
        assert engine._rank_to_band(2500) == 3000
        assert engine._rank_to_band(8000) == 8000
        assert engine._rank_to_band(9000) == 8000  # Capped

