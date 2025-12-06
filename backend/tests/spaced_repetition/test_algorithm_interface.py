"""
Unit tests for Algorithm Interface.
"""

import pytest
from datetime import date
from uuid import uuid4

from src.spaced_repetition.algorithm_interface import (
    CardState,
    ReviewResult,
    PerformanceRating,
    MasteryLevel,
)


class TestCardState:
    """Test CardState dataclass."""
    
    def test_card_state_creation(self):
        """Test creating a CardState."""
        user_id = uuid4()
        state = CardState(
            user_id=user_id,
            learning_progress_id=1,
            learning_point_id="test_123",
        )
        
        assert state.user_id == user_id
        assert state.algorithm_type == 'sm2_plus'
        assert state.current_interval == 1
        assert state.ease_factor == 2.5
    
    def test_card_state_to_dict(self):
        """Test converting CardState to dict."""
        state = CardState(
            user_id=uuid4(),
            learning_progress_id=1,
            learning_point_id="test_123",
        )
        
        state_dict = state.to_dict()
        
        assert isinstance(state_dict, dict)
        assert 'user_id' in state_dict
        assert 'algorithm_type' in state_dict
        assert 'current_interval' in state_dict
    
    def test_card_state_from_dict(self):
        """Test creating CardState from dict."""
        user_id = uuid4()
        state_dict = {
            'user_id': str(user_id),
            'learning_progress_id': 1,
            'learning_point_id': 'test_123',
            'algorithm_type': 'sm2_plus',
            'current_interval': 7,
            'ease_factor': 2.6,
        }
        
        state = CardState.from_dict(state_dict)
        
        assert state.user_id == user_id
        assert state.current_interval == 7
        assert state.ease_factor == 2.6


class TestReviewResult:
    """Test ReviewResult dataclass."""
    
    def test_review_result_creation(self):
        """Test creating a ReviewResult."""
        new_state = CardState(
            user_id=uuid4(),
            learning_progress_id=1,
            learning_point_id="test_123",
        )
        
        result = ReviewResult(
            new_state=new_state,
            next_review_date=date.today(),
            next_interval_days=7,
            was_correct=True,
        )
        
        assert result.was_correct is True
        assert result.next_interval_days == 7
        assert result.new_state == new_state
    
    def test_review_result_to_dict(self):
        """Test converting ReviewResult to dict."""
        new_state = CardState(
            user_id=uuid4(),
            learning_progress_id=1,
            learning_point_id="test_123",
        )
        
        result = ReviewResult(
            new_state=new_state,
            next_review_date=date.today(),
            next_interval_days=7,
            was_correct=True,
        )
        
        result_dict = result.to_dict()
        
        assert isinstance(result_dict, dict)
        assert 'was_correct' in result_dict
        assert 'next_interval_days' in result_dict


class TestPerformanceRating:
    """Test PerformanceRating enum."""
    
    def test_rating_values(self):
        """Test rating enum values."""
        assert PerformanceRating.AGAIN == 0
        assert PerformanceRating.HARD == 1
        assert PerformanceRating.GOOD == 2
        assert PerformanceRating.EASY == 3
        assert PerformanceRating.PERFECT == 4
    
    def test_rating_comparison(self):
        """Test rating comparisons."""
        assert PerformanceRating.GOOD >= PerformanceRating.HARD
        assert PerformanceRating.EASY > PerformanceRating.GOOD
        assert PerformanceRating.AGAIN < PerformanceRating.PERFECT

