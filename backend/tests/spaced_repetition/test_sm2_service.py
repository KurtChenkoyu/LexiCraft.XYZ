"""
Unit tests for SM-2+ Algorithm Service.
"""

import pytest
from datetime import date, timedelta
from uuid import uuid4

from src.spaced_repetition.sm2_service import SM2PlusService
from src.spaced_repetition.algorithm_interface import CardState, PerformanceRating


class TestSM2PlusService:
    """Test SM-2+ algorithm implementation."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.service = SM2PlusService()
        self.user_id = uuid4()
        self.learning_progress_id = 1
        self.learning_point_id = "test_word_123"
    
    def test_initialize_card(self):
        """Test card initialization."""
        card = self.service.initialize_card(
            user_id=self.user_id,
            learning_progress_id=self.learning_progress_id,
            learning_point_id=self.learning_point_id,
            initial_difficulty=0.5,
        )
        
        assert card.algorithm_type == 'sm2_plus'
        assert card.ease_factor == pytest.approx(2.5, abs=0.1)
        assert card.current_interval == 1
        assert card.consecutive_correct == 0
        assert card.mastery_level == 'learning'
        assert card.scheduled_date >= date.today()
    
    def test_process_review_perfect(self):
        """Test processing a perfect review."""
        card = self.service.initialize_card(
            self.user_id, self.learning_progress_id, self.learning_point_id
        )
        
        result = self.service.process_review(
            card, PerformanceRating.PERFECT, response_time_ms=1000
        )
        
        assert result.was_correct is True
        assert result.next_interval_days >= 1
        assert result.new_state.ease_factor > card.ease_factor
        assert result.new_state.consecutive_correct == 1
        assert result.new_state.total_reviews == 1
        assert result.new_state.total_correct == 1
    
    def test_process_review_again(self):
        """Test processing a failed review."""
        card = self.service.initialize_card(
            self.user_id, self.learning_progress_id, self.learning_point_id
        )
        card.consecutive_correct = 3
        card.current_interval = 7
        
        result = self.service.process_review(
            card, PerformanceRating.AGAIN
        )
        
        assert result.was_correct is False
        assert result.next_interval_days == 1
        assert result.new_state.ease_factor < card.ease_factor
        assert result.new_state.consecutive_correct == 0
        assert result.new_state.total_reviews == 1
        assert result.new_state.total_correct == 0
    
    def test_interval_progression(self):
        """Test interval progression with consecutive correct reviews."""
        card = self.service.initialize_card(
            self.user_id, self.learning_progress_id, self.learning_point_id
        )
        
        intervals = []
        for i in range(5):
            result = self.service.process_review(
                card, PerformanceRating.GOOD
            )
            intervals.append(result.next_interval_days)
            card = result.new_state
        
        # Should follow: 1, 3, 7, then multiply by ease_factor
        assert intervals[0] == 1
        assert intervals[1] == 3
        assert intervals[2] == 7
        assert intervals[3] > 7  # Multiplied by ease_factor
        assert intervals[4] > intervals[3]  # Continues growing
    
    def test_predict_retention(self):
        """Test retention prediction."""
        card = self.service.initialize_card(
            self.user_id, self.learning_progress_id, self.learning_point_id
        )
        card.last_review_date = date.today() - timedelta(days=1)
        card.current_interval = 7
        
        retention = self.service.predict_retention(card)
        
        assert 0.0 <= retention <= 1.0
        assert retention > 0.5  # Should be high for recent review
    
    def test_detect_leech(self):
        """Test leech detection."""
        card = self.service.initialize_card(
            self.user_id, self.learning_progress_id, self.learning_point_id
        )
        card.ease_factor = 1.2  # Very low
        card.consecutive_correct = -3  # Multiple failures
        
        is_leech = self.service.detect_leech(card)
        assert is_leech is True
    
    def test_calculate_mastery_level(self):
        """Test mastery level calculation."""
        card = self.service.initialize_card(
            self.user_id, self.learning_progress_id, self.learning_point_id
        )
        
        # Learning
        assert self.service.calculate_mastery_level(card) == 'learning'
        
        # Familiar
        card.consecutive_correct = 3
        assert self.service.calculate_mastery_level(card) == 'familiar'
        
        # Known
        card.consecutive_correct = 5
        card.current_interval = 100
        assert self.service.calculate_mastery_level(card) == 'known'
        
        # Mastered
        card.current_interval = 200
        assert self.service.calculate_mastery_level(card) == 'mastered'
        
        # Permanent
        card.current_interval = 800
        assert self.service.calculate_mastery_level(card) == 'permanent'

