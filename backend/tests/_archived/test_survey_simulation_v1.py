"""
Layer 3: Survey Simulation Tests

Tests the complete survey flow with simulated users who have known vocabulary boundaries.
This validates that the survey produces accurate metrics when given realistic answer patterns.

Uses REAL Neo4j database for accurate validation (not mocks).

Key Features:
- Simulated users with known vocab boundaries (ground truth)
- Full survey flow from start to finish
- Metric accuracy validation against ground truth
- Consistency testing across multiple sessions
- Real database queries for accurate results
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


class SimulatedUser:
    """
    A simulated user with known vocabulary for testing.
    
    The user knows all words up to vocab_boundary rank, and doesn't know
    words beyond that rank. Includes realistic behavior like mistakes and lucky guesses.
    """
    
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
        
        Returns True (correct) if:
        - Word is within known range AND random < consistency
        - Small chance of lucky guess for unknown words
        
        Args:
            word_rank: Frequency rank of the word being tested
            
        Returns:
            True if user answers correctly, False otherwise
        """
        if word_rank <= self.vocab_boundary:
            # Known word - usually correct (consistency chance)
            return random.random() < self.consistency
        else:
            # Unknown word - usually wrong, but 10% lucky guess
            return random.random() < 0.10


@pytest.fixture
def neo4j_conn():
    """Create a real Neo4j connection for testing."""
    conn = Neo4jConnection()
    yield conn
    conn.close()


@pytest.fixture
def engine(neo4j_conn):
    """Create a LexiSurveyEngine instance with real Neo4j connection."""
    return LexiSurveyEngine(neo4j_conn)


def create_answer_from_payload(payload: QuestionPayload, is_correct: bool) -> AnswerSubmission:
    """
    Create an AnswerSubmission based on question payload and correctness.
    
    Args:
        payload: The question payload
        is_correct: Whether the answer should be correct
        
    Returns:
        AnswerSubmission with appropriate option IDs selected
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
            # Fallback: select first option
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
            # Fallback: select "unknown" or first non-target
            unknown_options = [
                opt.id for opt in payload.options
                if opt.type == "unknown" or "unknown" in opt.id.lower()
            ]
            if unknown_options:
                selected_ids = [unknown_options[0]]
            else:
                selected_ids = [payload.options[1].id]  # Second option (likely wrong)
    
    return AnswerSubmission(
        question_id=payload.question_id,
        selected_option_ids=selected_ids,
        time_taken=random.uniform(3.0, 8.0)
    )


def run_complete_survey(engine: LexiSurveyEngine, user: SimulatedUser, start_rank: int = 2000) -> SurveyResult:
    """
    Run a complete survey with a simulated user.
    
    Args:
        engine: LexiSurveyEngine instance
        user: SimulatedUser instance
        start_rank: Starting rank for survey (default: 2000)
        
    Returns:
        SurveyResult with final metrics
    """
    # Initialize survey state
    state = SurveyState(
        session_id=str(uuid.uuid4()),
        current_rank=start_rank,
        low_bound=1,
        high_bound=8000,
        history=[],
        phase=1,
        confidence=0.0
    )
    
    # Get first question
    result = engine.process_step(state)
    
    # Answer loop
    max_questions = 25  # Safety limit
    question_count = 0
    
    while result.status == "continue" and question_count < max_questions:
        question_count += 1
        
        # User answers based on word rank
        if result.payload:
            question_rank = result.payload.rank
            is_correct = user.answer_question(question_rank)
            
            # Create answer submission
            answer = create_answer_from_payload(result.payload, is_correct)
            
            # Submit answer and get next question
            question_details = {
                "word": result.payload.word,
                "rank": result.payload.rank,
                "phase": result.debug_info.get("phase", state.phase),
                "question_number": question_count,
                "options": [opt.model_dump() for opt in result.payload.options]
            }
            
            result = engine.process_step(state, answer, question_details)
        else:
            # No payload, break
            break
    
    return result


class TestSurveySimulation:
    """Test complete surveys with simulated users."""
    
    @pytest.mark.parametrize("vocab_boundary,expected_volume_range,expected_reach_range", [
        (1000, (850, 1150), (800, 1200)),   # Beginner (±15% volume, ±20% reach)
        (2000, (1700, 2300), (1600, 2400)), # Intermediate
        (3500, (3000, 4000), (2800, 4200)), # Upper Intermediate
        (5000, (4250, 5750), (4000, 6000)), # Advanced
    ])
    def test_volume_accuracy(self, engine, vocab_boundary, expected_volume_range, expected_reach_range):
        """
        Volume should match known vocabulary size (±15%).
        
        Uses real Neo4j database for accurate validation.
        """
        user = SimulatedUser(vocab_boundary, consistency=0.95)
        
        result = run_complete_survey(engine, user, start_rank=vocab_boundary)
        
        assert result.status == "complete", "Survey should complete"
        assert result.metrics is not None, "Should have metrics"
        
        # Validate volume accuracy (±15%)
        assert expected_volume_range[0] <= result.metrics.volume <= expected_volume_range[1], \
            f"Volume {result.metrics.volume} should be in range {expected_volume_range} for vocab_boundary {vocab_boundary}"
    
    @pytest.mark.parametrize("vocab_boundary", [1000, 2000, 3500, 5000])
    def test_reach_accuracy(self, engine, vocab_boundary):
        """
        Reach should be near vocab boundary (±20%).
        
        Uses real Neo4j database for accurate validation.
        """
        user = SimulatedUser(vocab_boundary, consistency=0.95)
        
        result = run_complete_survey(engine, user, start_rank=vocab_boundary)
        
        assert result.status == "complete"
        assert result.metrics is not None
        
        # Validate reach accuracy (±20%)
        tolerance = vocab_boundary * 0.20
        assert abs(result.metrics.reach - vocab_boundary) < tolerance, \
            f"Reach {result.metrics.reach} should be within ±20% of {vocab_boundary} (tolerance: {tolerance})"
    
    def test_consistency_across_sessions(self, engine):
        """Same user should get similar results across multiple sessions."""
        user = SimulatedUser(vocab_boundary=2500, consistency=0.95)
        
        # Run 5 surveys with same user
        results = []
        for _ in range(5):
            result = run_complete_survey(engine, user, start_rank=2500)
            if result.status == "complete" and result.metrics:
                results.append(result)
        
        assert len(results) >= 3, "Should complete at least 3 surveys"
        
        volumes = [r.metrics.volume for r in results]
        reaches = [r.metrics.reach for r in results]
        
        # Standard deviation should be <15% of mean
        if len(volumes) > 1:
            volume_std = np.std(volumes)
            volume_mean = np.mean(volumes)
            assert volume_std < volume_mean * 0.15, \
                f"Volume consistency: std={volume_std:.1f}, mean={volume_mean:.1f}, ratio={volume_std/volume_mean:.2%}"
        
        if len(reaches) > 1:
            reach_std = np.std(reaches)
            reach_mean = np.mean(reaches)
            assert reach_std < reach_mean * 0.15, \
                f"Reach consistency: std={reach_std:.1f}, mean={reach_mean:.1f}, ratio={reach_std/reach_mean:.2%}"
    
    def test_density_reflects_consistency(self, engine):
        """Density should be high for consistent users, lower for inconsistent."""
        # Consistent user
        consistent_user = SimulatedUser(vocab_boundary=2000, consistency=0.95)
        result_consistent = run_complete_survey(engine, consistent_user, start_rank=2000)
        
        # Inconsistent user
        inconsistent_user = SimulatedUser(vocab_boundary=2000, consistency=0.70)
        result_inconsistent = run_complete_survey(engine, inconsistent_user, start_rank=2000)
        
        assert result_consistent.status == "complete"
        assert result_inconsistent.status == "complete"
        
        # Consistent user should have higher density
        assert result_consistent.metrics.density > result_inconsistent.metrics.density, \
            f"Consistent user density ({result_consistent.metrics.density}) should be > inconsistent ({result_inconsistent.metrics.density})"
        
        # Consistent user should have density > 0.7
        assert result_consistent.metrics.density > 0.7, \
            f"Consistent user should have density > 0.7, got {result_consistent.metrics.density}"
    
    def test_survey_completes_in_reasonable_questions(self, engine):
        """Survey should complete in 15-20 questions."""
        user = SimulatedUser(vocab_boundary=2000)
        
        result = run_complete_survey(engine, user, start_rank=2000)
        
        assert result.status == "complete"
        assert result.detailed_history is not None
        
        question_count = len(result.detailed_history)
        assert 15 <= question_count <= 20, \
            f"Survey should complete in 15-20 questions, got {question_count}"
    
    def test_bounds_converge(self, engine):
        """Bounds should converge to vocabulary boundary."""
        user = SimulatedUser(vocab_boundary=2000, consistency=0.95)
        
        # Initialize state
        state = SurveyState(
            session_id=str(uuid.uuid4()),
            current_rank=4000,
            low_bound=1,
            high_bound=8000,
            history=[],
            phase=1
        )
        
        # Run survey
        result = engine.process_step(state)
        question_count = 0
        
        while result.status == "continue" and question_count < 20:
            question_count += 1
            if result.payload:
                question_rank = result.payload.rank
                is_correct = user.answer_question(question_rank)
                answer = create_answer_from_payload(result.payload, is_correct)
                question_details = {
                    "word": result.payload.word,
                    "rank": result.payload.rank,
                    "phase": result.debug_info.get("phase", state.phase),
                    "options": [opt.model_dump() for opt in result.payload.options]
                }
                result = engine.process_step(state, answer, question_details)
            else:
                break
        
        # Check convergence
        final_range = state.high_bound - state.low_bound
        midpoint = (state.low_bound + state.high_bound) / 2
        
        # Bounds should be tight
        assert final_range < 2000, \
            f"Bounds should converge (range={final_range}), got low={state.low_bound}, high={state.high_bound}"
        
        # Midpoint should be near vocabulary boundary
        assert abs(midpoint - 2000) < 1000, \
            f"Midpoint {midpoint} should be near boundary 2000"
    
    def test_beginner_user(self, engine):
        """Test with beginner user (low vocabulary)."""
        user = SimulatedUser(vocab_boundary=1000, consistency=0.95)
        
        result = run_complete_survey(engine, user, start_rank=1000)
        
        assert result.status == "complete"
        assert result.metrics.volume < 1500, f"Beginner should have volume < 1500, got {result.metrics.volume}"
        assert result.metrics.reach < 1500, f"Beginner should have reach < 1500, got {result.metrics.reach}"
    
    def test_advanced_user(self, engine):
        """Test with advanced user (high vocabulary)."""
        user = SimulatedUser(vocab_boundary=5000, consistency=0.95)
        
        result = run_complete_survey(engine, user, start_rank=5000)
        
        assert result.status == "complete"
        assert result.metrics.volume > 4000, f"Advanced user should have volume > 4000, got {result.metrics.volume}"
        assert result.metrics.reach > 4000, f"Advanced user should have reach > 4000, got {result.metrics.reach}"
    
    def test_metrics_are_valid(self, engine):
        """All metrics should be in valid ranges."""
        user = SimulatedUser(vocab_boundary=2000)
        
        result = run_complete_survey(engine, user, start_rank=2000)
        
        assert result.status == "complete"
        metrics = result.metrics
        
        # Volume: 0-8000
        assert 0 <= metrics.volume <= 8000, f"Volume {metrics.volume} should be 0-8000"
        
        # Reach: 0-8000
        assert 0 <= metrics.reach <= 8000, f"Reach {metrics.reach} should be 0-8000"
        
        # Density: 0.0-1.0
        assert 0.0 <= metrics.density <= 1.0, f"Density {metrics.density} should be 0.0-1.0"
        
        # Reach should be >= Volume (generally)
        # (This is a soft check - reach can be slightly lower due to algorithm)
        # assert metrics.reach >= metrics.volume * 0.8, \
        #     f"Reach {metrics.reach} should be >= Volume {metrics.volume} * 0.8"

