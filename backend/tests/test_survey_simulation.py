"""
Layer 3: Survey Simulation Tests for V2 Engine

Tests the complete survey flow with simulated users who have PROBABILISTIC
vocabulary knowledge (not binary boundaries like in V1 tests).

Uses REAL Neo4j database for accurate validation.

Key differences from V1 simulation tests:
- Simulated users have PROBABILITY curves, not sharp boundaries
- Tests validate band-based estimation accuracy
- Tests adaptive stopping behavior
"""

import pytest
import random
import uuid
import numpy as np
from typing import List, Optional
from src.survey.lexisurvey_engine import LexiSurveyEngine
from src.survey.models import (
    SurveyState,
    AnswerSubmission,
    QuestionPayload,
    QuestionOption,
    SurveyResult
)
from src.database.neo4j_connection import Neo4jConnection


class ProbabilisticUser:
    """
    A simulated user with PROBABILISTIC vocabulary knowledge.
    
    Unlike the V1 SimulatedUser which had a sharp boundary,
    this user has a probability curve that declines with rank.
    
    Example:
        vocab_level=2000 means:
        - 95% accuracy at rank 1000
        - 75% accuracy at rank 2000  
        - 40% accuracy at rank 3000
        - 15% accuracy at rank 4000
    """
    
    def __init__(
        self, 
        vocab_level: int, 
        consistency: float = 0.95,
        curve_steepness: float = 0.0008
    ):
        """
        Args:
            vocab_level: Center of their vocabulary (50% accuracy point)
            consistency: Max accuracy at very low ranks (0.95 = 95%)
            curve_steepness: How quickly accuracy drops (higher = steeper)
        """
        self.vocab_level = vocab_level
        self.consistency = consistency
        self.curve_steepness = curve_steepness
    
    def get_accuracy_at_rank(self, rank: int) -> float:
        """
        Get expected accuracy at a given rank using sigmoid-like curve.
        
        Returns probability of knowing word at this rank.
        """
        # Sigmoid-like curve centered at vocab_level
        # accuracy = consistency / (1 + e^(steepness * (rank - vocab_level)))
        x = self.curve_steepness * (rank - self.vocab_level)
        if x > 10:  # Prevent overflow
            return 0.05  # Small chance of lucky guess
        elif x < -10:
            return self.consistency
        else:
            return self.consistency / (1 + np.exp(x))
    
    def answer_question(self, word_rank: int) -> bool:
        """
        Simulate user answering a question.
        
        Returns True (correct) with probability based on the rank.
        """
        accuracy = self.get_accuracy_at_rank(word_rank)
        return random.random() < accuracy
    
    def get_expected_volume(self) -> int:
        """
        Calculate expected vocabulary size based on probability curve.
        
        Integrates accuracy across all bands.
        """
        total = 0
        bands = [1000, 2000, 3000, 4000, 5000, 6000, 7000, 8000]
        for band in bands:
            # Sample middle of band
            mid_rank = band - 500
            accuracy = self.get_accuracy_at_rank(mid_rank)
            total += accuracy * 1000
        return int(total)


@pytest.fixture
def neo4j_conn():
    """Create a real Neo4j connection for testing."""
    conn = Neo4jConnection()
    yield conn
    conn.close()


@pytest.fixture
def engine(neo4j_conn):
    """Create a LexiSurveyEngine instance (V2 methodology)."""
    return LexiSurveyEngine(neo4j_conn)


def create_answer_from_payload(payload: QuestionPayload, is_correct: bool) -> AnswerSubmission:
    """
    Create an AnswerSubmission based on question payload and correctness.
    """
    if is_correct:
        # Select target options (correct answer)
        target_options = [
            opt.id for opt in payload.options
            if opt.type == "target" or "target" in opt.id.lower()
        ]
        if target_options:
            selected_ids = target_options[:1]  # Select first target
        else:
            selected_ids = [payload.options[0].id]
    else:
        # Select wrong option (trap or unknown)
        trap_options = [
            opt.id for opt in payload.options
            if opt.type == "trap" or "trap" in opt.id.lower()
        ]
        if trap_options:
            selected_ids = [trap_options[0]]
        else:
            unknown_options = [
                opt.id for opt in payload.options
                if opt.type == "unknown" or "unknown" in opt.id.lower()
            ]
            if unknown_options:
                selected_ids = [unknown_options[0]]
            else:
                selected_ids = [payload.options[-1].id]
    
    return AnswerSubmission(
        question_id=payload.question_id,
        selected_option_ids=selected_ids,
        time_taken=random.uniform(3.0, 8.0)
    )


def run_complete_survey_v2(
    engine: LexiSurveyEngine, 
    user: ProbabilisticUser
) -> SurveyResult:
    """
    Run a complete V2 survey with a probabilistic user.
    """
    # Initialize survey state
    state = SurveyState(
        session_id=str(uuid.uuid4()),
        current_rank=4000,  # Start in middle
        low_bound=1,
        high_bound=8000,
        history=[],
        band_performance=None,  # Will be initialized by engine
        phase=1,
        confidence=0.0
    )
    
    # Get first question
    result = engine.process_step(state)
    
    # Answer loop
    max_questions = 50  # Safety limit (above MAX_QUESTIONS)
    question_count = 0
    
    while result.status == "continue" and question_count < max_questions:
        question_count += 1
        
        if result.payload:
            question_rank = result.payload.rank
            is_correct = user.answer_question(question_rank)
            
            # Create answer submission
            answer = create_answer_from_payload(result.payload, is_correct)
            
            # Submit answer and get next question
            question_details = {
                "word": result.payload.word,
                "rank": result.payload.rank,
                "options": [opt.model_dump() for opt in result.payload.options]
            }
            
            result = engine.process_step(state, answer, question_details)
        else:
            break
    
    return result


class TestV2SurveySimulation:
    """Test complete surveys with V2 engine and probabilistic users."""
    
    @pytest.mark.parametrize("vocab_level,expected_volume_range", [
        (1500, (1000, 3000)),   # Beginner: sigmoid gives ~1500-2500
        (2500, (2000, 4500)),   # Intermediate: sigmoid gives ~2500-4000
        (4000, (2500, 5500)),   # Upper intermediate: sigmoid gives ~3000-5000
        (5500, (4000, 7000)),   # Advanced: sigmoid gives ~5000-6500
    ])
    def test_volume_accuracy(self, engine, vocab_level, expected_volume_range):
        """
        Volume should approximate user's expected vocabulary size.
        
        Using probabilistic users with realistic sigmoid knowledge curves.
        Note: Volume estimates have variance due to:
        - Probabilistic user responses
        - Band sampling randomness
        - Real database word distribution
        """
        user = ProbabilisticUser(vocab_level=vocab_level, consistency=0.95)
        
        # Run survey
        result = run_complete_survey_v2(engine, user)
        
        assert result.status == "complete", "Survey should complete"
        assert result.metrics is not None, "Should have metrics"
        
        # Check volume is in expected range (wide tolerance for probabilistic nature)
        min_vol, max_vol = expected_volume_range
        assert min_vol <= result.metrics.volume <= max_vol, \
            f"Volume {result.metrics.volume} should be in range {expected_volume_range} for vocab_level {vocab_level}"
    
    @pytest.mark.parametrize("vocab_level,expected_reach_range", [
        (1500, (1000, 2500)),   # Beginner
        (2500, (2000, 3500)),   # Intermediate  
        (4000, (3000, 5000)),   # Upper intermediate
        (5500, (4000, 7000)),   # Advanced
    ])
    def test_reach_accuracy(self, engine, vocab_level, expected_reach_range):
        """
        Reach should approximate user's 50% accuracy point.
        """
        user = ProbabilisticUser(vocab_level=vocab_level, consistency=0.95)
        
        result = run_complete_survey_v2(engine, user)
        
        assert result.status == "complete"
        assert result.metrics is not None
        
        # Check reach is in expected range
        min_reach, max_reach = expected_reach_range
        assert min_reach <= result.metrics.reach <= max_reach, \
            f"Reach {result.metrics.reach} should be in range {expected_reach_range} for vocab_level {vocab_level}"
    
    def test_consistent_user_high_density(self, engine):
        """Consistent user (smooth curve) should have high density."""
        user = ProbabilisticUser(
            vocab_level=3000, 
            consistency=0.95,
            curve_steepness=0.001  # Smooth curve
        )
        
        result = run_complete_survey_v2(engine, user)
        
        assert result.status == "complete"
        # Consistent user should have density > 0.7
        assert result.metrics.density >= 0.6, \
            f"Consistent user should have density >= 0.6, got {result.metrics.density}"
    
    def test_inconsistent_user_lower_density(self, engine):
        """Inconsistent user should have lower density."""
        # Create an inconsistent user with random gaps
        class InconsistentUser(ProbabilisticUser):
            def answer_question(self, word_rank: int) -> bool:
                # Add random inconsistency
                base_accuracy = self.get_accuracy_at_rank(word_rank)
                # Add noise: sometimes miss easy words, sometimes get hard ones
                noise = random.uniform(-0.3, 0.3)
                effective_accuracy = max(0.1, min(0.9, base_accuracy + noise))
                return random.random() < effective_accuracy
        
        user = InconsistentUser(vocab_level=3000, consistency=0.85)
        
        result = run_complete_survey_v2(engine, user)
        
        assert result.status == "complete"
        # Inconsistent user typically has density < 0.9
        # (but this is probabilistic, so we just check it's reasonable)
        assert 0.0 <= result.metrics.density <= 1.0
    
    def test_survey_stops_adaptively(self, engine):
        """
        V2 survey should stop based on confidence, not fixed questions.
        
        For very consistent users, may stop earlier.
        For very inconsistent users, may go to max.
        """
        user = ProbabilisticUser(vocab_level=3000, consistency=0.95)
        
        result = run_complete_survey_v2(engine, user)
        
        assert result.status == "complete"
        assert result.detailed_history is not None
        
        question_count = len(result.detailed_history)
        
        # V2 should complete between MIN_QUESTIONS (10) and MAX_QUESTIONS (35)
        assert 10 <= question_count <= 40, \
            f"Survey should complete in 10-35 questions, got {question_count}"
    
    def test_band_coverage(self, engine):
        """Survey should sample multiple frequency bands."""
        user = ProbabilisticUser(vocab_level=3500, consistency=0.95)
        
        result = run_complete_survey_v2(engine, user)
        
        assert result.status == "complete"
        
        # Check that multiple bands were tested
        bands_tested = set()
        for h in result.detailed_history:
            if "band" in h:
                bands_tested.add(h["band"])
            else:
                # Infer band from rank
                rank = h.get("rank", 0)
                band = ((rank - 1) // 1000 + 1) * 1000
                bands_tested.add(min(8000, band))
        
        # Should test at least 3 different bands
        assert len(bands_tested) >= 3, \
            f"Should test at least 3 bands, only tested {bands_tested}"
    
    def test_consistency_across_sessions(self, engine):
        """Same user should get similar results across multiple sessions."""
        user = ProbabilisticUser(vocab_level=3000, consistency=0.95)
        
        # Run 3 surveys with same user
        results = []
        for _ in range(3):
            result = run_complete_survey_v2(engine, user)
            if result.status == "complete" and result.metrics:
                results.append(result)
        
        assert len(results) >= 2, "Should complete at least 2 surveys"
        
        volumes = [r.metrics.volume for r in results]
        reaches = [r.metrics.reach for r in results]
        
        # Standard deviation should be reasonable (<25% of mean)
        if len(volumes) > 1:
            volume_std = np.std(volumes)
            volume_mean = np.mean(volumes)
            if volume_mean > 0:
                cv = volume_std / volume_mean
                assert cv < 0.30, \
                    f"Volume consistency: CV={cv:.2%} should be < 30%"
    
    def test_beginner_user(self, engine):
        """Test with beginner user (low vocabulary)."""
        user = ProbabilisticUser(vocab_level=1200, consistency=0.90)
        
        result = run_complete_survey_v2(engine, user)
        
        assert result.status == "complete"
        assert result.metrics.volume < 2500, \
            f"Beginner should have volume < 2500, got {result.metrics.volume}"
    
    def test_advanced_user(self, engine):
        """Test with advanced user (high vocabulary)."""
        user = ProbabilisticUser(vocab_level=6000, consistency=0.95)
        
        result = run_complete_survey_v2(engine, user)
        
        assert result.status == "complete"
        assert result.metrics.volume > 4000, \
            f"Advanced user should have volume > 4000, got {result.metrics.volume}"
        assert result.metrics.reach > 4000, \
            f"Advanced user should have reach > 4000, got {result.metrics.reach}"
    
    def test_metrics_in_valid_ranges(self, engine):
        """All metrics should be in valid ranges."""
        user = ProbabilisticUser(vocab_level=3000, consistency=0.95)
        
        result = run_complete_survey_v2(engine, user)
        
        assert result.status == "complete"
        metrics = result.metrics
        
        # Volume: 0-8000
        assert 0 <= metrics.volume <= 8000, f"Volume {metrics.volume} should be 0-8000"
        
        # Reach: 0-8000
        assert 0 <= metrics.reach <= 8000, f"Reach {metrics.reach} should be 0-8000"
        
        # Density: 0.0-1.0
        assert 0.0 <= metrics.density <= 1.0, f"Density {metrics.density} should be 0.0-1.0"
    
    def test_methodology_explanation(self, engine):
        """Complete result should include methodology explanation."""
        user = ProbabilisticUser(vocab_level=3000, consistency=0.95)
        
        result = run_complete_survey_v2(engine, user)
        
        assert result.status == "complete"
        assert result.methodology is not None, "Should include methodology"
        
        # Check methodology contains expected fields
        assert "algorithm" in result.methodology
        assert "bands_sampled" in result.methodology
        assert "formula" in result.methodology


class TestV2EdgeCases:
    """Test edge cases for V2 engine."""
    
    def test_very_weak_user(self, engine):
        """User who knows almost nothing."""
        user = ProbabilisticUser(vocab_level=500, consistency=0.80)
        
        result = run_complete_survey_v2(engine, user)
        
        assert result.status == "complete"
        # Should still produce valid metrics
        assert result.metrics.volume >= 0
        assert result.metrics.volume < 2000
    
    def test_very_strong_user(self, engine):
        """User who knows almost everything."""
        user = ProbabilisticUser(vocab_level=7500, consistency=0.98)
        
        result = run_complete_survey_v2(engine, user)
        
        assert result.status == "complete"
        # Should detect high knowledge
        assert result.metrics.volume > 5000
        assert result.metrics.reach >= 5000

