"""
SM-2+ Spaced Repetition Algorithm Service

Implements the SM-2+ algorithm (modified SuperMemo 2) for spaced repetition.

Key Features:
- Per-word ease factor (1.3 - 3.0)
- Performance-based interval adjustment
- Leech detection
- Mastery levels

Formula:
    ease_factor += (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02))
    interval = previous_interval * ease_factor
"""

import logging
from datetime import date, timedelta
from typing import Optional
from uuid import UUID

from .algorithm_interface import (
    SpacedRepetitionAlgorithm,
    CardState,
    ReviewResult,
    PerformanceRating,
)

logger = logging.getLogger(__name__)


class SM2PlusService(SpacedRepetitionAlgorithm):
    """
    SM-2+ Algorithm Implementation.
    
    Enhanced version of SuperMemo 2 with:
    - Wider ease factor range (1.3 - 3.0 vs 1.3 - 2.5)
    - More granular performance scale (0-4 mapped to 0-5)
    - Response time consideration
    - Leech detection
    """
    
    # Configuration
    EF_MIN = 1.3
    EF_MAX = 3.0
    EF_DEFAULT = 2.5
    
    INTERVAL_MAX = 365  # 1 year max
    
    # Initial intervals for first 3 correct reviews
    INITIAL_INTERVALS = [1, 3, 7]
    
    # Leech thresholds
    LEECH_CONSECUTIVE_FAILURES = 3
    LEECH_EF_THRESHOLD = 1.5
    
    @property
    def algorithm_type(self) -> str:
        return 'sm2_plus'
    
    def initialize_card(
        self,
        user_id: UUID,
        learning_progress_id: int,
        learning_point_id: str,
        initial_difficulty: float = 0.5,
    ) -> CardState:
        """Initialize a new SM-2+ card."""
        # Map initial difficulty (0-1) to ease factor
        # Higher difficulty = lower ease factor
        initial_ef = self.EF_DEFAULT - (initial_difficulty - 0.5) * 0.6
        initial_ef = max(self.EF_MIN, min(self.EF_MAX, initial_ef))
        
        return CardState(
            user_id=user_id,
            learning_progress_id=learning_progress_id,
            learning_point_id=learning_point_id,
            algorithm_type='sm2_plus',
            current_interval=1,
            scheduled_date=date.today() + timedelta(days=1),
            ease_factor=initial_ef,
            consecutive_correct=0,
            difficulty=initial_difficulty,
            mastery_level='learning',
        )
    
    def process_review(
        self,
        state: CardState,
        rating: PerformanceRating,
        response_time_ms: Optional[int] = None,
        review_date: Optional[date] = None,
    ) -> ReviewResult:
        """
        Process a review using SM-2+ algorithm.
        
        Maps 0-4 rating to SM-2's internal scale and updates ease factor.
        """
        review_date = review_date or date.today()
        
        # Map 0-4 rating to SM-2's 0-5 scale
        # 0 (Again) → 1, 1 (Hard) → 2, 2 (Good) → 3, 3 (Easy) → 4, 4 (Perfect) → 5
        q = int(rating) + 1
        
        # Determine if correct (rating >= GOOD)
        was_correct = rating >= PerformanceRating.GOOD
        
        # Update ease factor using SM-2 formula
        # EF' = EF + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02))
        ef_change = 0.1 - (5 - q) * (0.08 + (5 - q) * 0.02)
        new_ef = state.ease_factor + ef_change
        new_ef = max(self.EF_MIN, min(self.EF_MAX, new_ef))
        
        # Update consecutive correct count
        if was_correct:
            new_consecutive = state.consecutive_correct + 1
        else:
            new_consecutive = 0  # Reset on failure
        
        # Calculate next interval
        if not was_correct:
            # Failed - reset to beginning
            new_interval = 1
        elif new_consecutive <= len(self.INITIAL_INTERVALS):
            # Use fixed initial intervals
            new_interval = self.INITIAL_INTERVALS[new_consecutive - 1]
        else:
            # Multiply by ease factor
            new_interval = int(state.current_interval * new_ef)
        
        # Cap at max interval
        new_interval = min(new_interval, self.INTERVAL_MAX)
        
        # Update total reviews and correct count
        new_total_reviews = state.total_reviews + 1
        new_total_correct = state.total_correct + (1 if was_correct else 0)
        
        # Update response time average
        if response_time_ms is not None:
            if state.avg_response_time_ms is not None:
                # Rolling average
                new_avg_time = int(
                    (state.avg_response_time_ms * state.total_reviews + response_time_ms) 
                    / (state.total_reviews + 1)
                )
            else:
                new_avg_time = response_time_ms
        else:
            new_avg_time = state.avg_response_time_ms
        
        # Create updated state
        new_state = CardState(
            user_id=state.user_id,
            learning_progress_id=state.learning_progress_id,
            learning_point_id=state.learning_point_id,
            algorithm_type='sm2_plus',
            current_interval=new_interval,
            scheduled_date=review_date + timedelta(days=new_interval),
            last_review_date=review_date,
            total_reviews=new_total_reviews,
            total_correct=new_total_correct,
            ease_factor=new_ef,
            consecutive_correct=new_consecutive,
            difficulty=self._calculate_difficulty(new_ef, new_total_reviews, new_total_correct),
            avg_response_time_ms=new_avg_time,
        )
        
        # Check for leech
        new_state.is_leech = self.detect_leech(new_state)
        
        # Calculate mastery level
        old_mastery = state.mastery_level
        new_state.mastery_level = self.calculate_mastery_level(new_state)
        mastery_changed = old_mastery != new_state.mastery_level
        
        # Predict retention (simplified for SM-2+)
        retention = self._estimate_retention(new_state, review_date)
        new_state.retention_probability = retention
        
        return ReviewResult(
            new_state=new_state,
            next_review_date=new_state.scheduled_date,
            next_interval_days=new_interval,
            was_correct=was_correct,
            retention_predicted=retention,
            mastery_changed=mastery_changed,
            new_mastery_level=new_state.mastery_level if mastery_changed else None,
            became_leech=new_state.is_leech and not state.is_leech,
            algorithm_type='sm2_plus',
            debug_info={
                'q_score': q,
                'ef_change': round(ef_change, 3),
                'old_ef': round(state.ease_factor, 3),
                'new_ef': round(new_ef, 3),
                'consecutive_correct': new_consecutive,
            },
        )
    
    def predict_retention(
        self,
        state: CardState,
        target_date: Optional[date] = None,
    ) -> float:
        """
        Predict retention probability at target date.
        
        Uses a simplified exponential forgetting curve.
        SM-2+ doesn't have native retention prediction, so we estimate.
        """
        return self._estimate_retention(state, target_date)
    
    def _estimate_retention(
        self,
        state: CardState,
        target_date: Optional[date] = None,
    ) -> float:
        """
        Estimate retention using simplified forgetting curve.
        
        Formula: R = e^(-t/S)
        Where t is elapsed time and S is "stability" (derived from ease factor)
        """
        target_date = target_date or date.today()
        
        if state.last_review_date is None:
            return 0.5  # Unknown, assume 50%
        
        elapsed_days = (target_date - state.last_review_date).days
        
        if elapsed_days <= 0:
            return 1.0  # Just reviewed
        
        # Estimate stability from ease factor
        # Higher EF = more stable memory
        stability = state.current_interval * (state.ease_factor / self.EF_DEFAULT)
        
        if stability <= 0:
            stability = 1
        
        # Exponential forgetting
        import math
        retention = math.exp(-elapsed_days / stability)
        
        return max(0.0, min(1.0, retention))
    
    def _calculate_difficulty(
        self,
        ease_factor: float,
        total_reviews: int,
        total_correct: int,
    ) -> float:
        """
        Calculate difficulty score (0-1) from SM-2+ parameters.
        
        Used for compatibility with global difficulty tracking.
        """
        # EF 2.5 (default) → 0.5 difficulty
        # EF 1.3 (hard) → 1.0 difficulty
        # EF 3.0 (easy) → 0.0 difficulty
        ef_factor = 1.0 - (ease_factor - self.EF_MIN) / (self.EF_MAX - self.EF_MIN)
        
        # Also consider error rate
        if total_reviews > 0:
            error_rate = 1.0 - (total_correct / total_reviews)
        else:
            error_rate = 0.5
        
        # Weighted combination
        difficulty = 0.6 * ef_factor + 0.4 * error_rate
        
        return max(0.0, min(1.0, difficulty))

