"""
FSRS (Free Spaced Repetition Scheduler) Service

Wraps the fsrs Python library to provide FSRS algorithm support.

FSRS is a modern, machine learning-based spaced repetition algorithm that:
- Learns your personal forgetting curve
- Predicts optimal review times
- Reduces reviews by 20-30% vs traditional algorithms

Key Concepts:
- Stability: How well you know this word (memory strength)
- Difficulty: How hard this word is (learned from all users)
- Retention: Probability you'll remember at review time

Reference: https://github.com/open-spaced-repetition/fsrs4anki
"""

import logging
from datetime import date, datetime, timedelta
from typing import Optional, Dict, Any
from uuid import UUID
import json

try:
    from fsrs import FSRS, Card, Rating, State
    FSRS_AVAILABLE = True
except ImportError:
    FSRS_AVAILABLE = False
    logging.warning("FSRS library not installed. Run: pip install fsrs")

from .algorithm_interface import (
    SpacedRepetitionAlgorithm,
    CardState,
    ReviewResult,
    PerformanceRating,
)

logger = logging.getLogger(__name__)


class FSRSService(SpacedRepetitionAlgorithm):
    """
    FSRS Algorithm Implementation.
    
    Uses the fsrs Python library for scheduling calculations.
    Provides wrapper methods that integrate with our CardState system.
    """
    
    # Default FSRS parameters (can be personalized after 100+ reviews)
    DEFAULT_PARAMETERS = None  # Use library defaults
    
    # Target retention (90% is typical)
    TARGET_RETENTION = 0.9
    
    # Maximum interval
    MAX_INTERVAL = 365 * 2  # 2 years
    
    def __init__(self, parameters: Optional[Dict[str, Any]] = None):
        """
        Initialize FSRS service.
        
        Args:
            parameters: Custom FSRS parameters (for personalized models)
        """
        if not FSRS_AVAILABLE:
            raise RuntimeError("FSRS library not installed. Run: pip install fsrs")
        
        self._fsrs = FSRS()
        
        # Apply custom parameters if provided
        if parameters:
            self._apply_parameters(parameters)
    
    def _apply_parameters(self, parameters: Dict[str, Any]) -> None:
        """Apply custom FSRS parameters."""
        # The fsrs library allows parameter customization
        # Parameters are typically learned from user review history
        if 'w' in parameters:
            self._fsrs.w = parameters['w']
        if 'request_retention' in parameters:
            self._fsrs.request_retention = parameters['request_retention']
        if 'maximum_interval' in parameters:
            self._fsrs.maximum_interval = parameters['maximum_interval']
    
    @property
    def algorithm_type(self) -> str:
        return 'fsrs'
    
    def _map_rating(self, rating: PerformanceRating) -> 'Rating':
        """
        Map our rating to FSRS Rating enum.
        
        Our scale: 0-4 (Again, Hard, Good, Easy, Perfect)
        FSRS scale: Again(1), Hard(2), Good(3), Easy(4)
        """
        mapping = {
            PerformanceRating.AGAIN: Rating.Again,
            PerformanceRating.HARD: Rating.Hard,
            PerformanceRating.GOOD: Rating.Good,
            PerformanceRating.EASY: Rating.Easy,
            PerformanceRating.PERFECT: Rating.Easy,  # Map Perfect to Easy
        }
        return mapping[rating]
    
    def _card_to_fsrs_card(self, state: CardState) -> 'Card':
        """
        Convert our CardState to FSRS Card.
        
        If we have stored FSRS state, restore it.
        Otherwise, create a new Card.
        """
        if state.fsrs_state:
            # Restore from stored state
            try:
                card = Card()
                card.stability = state.fsrs_state.get('stability', 0)
                card.difficulty = state.fsrs_state.get('difficulty', 0.5)
                card.reps = state.fsrs_state.get('reps', 0)
                card.lapses = state.fsrs_state.get('lapses', 0)
                card.elapsed_days = state.fsrs_state.get('elapsed_days', 0)
                card.scheduled_days = state.fsrs_state.get('scheduled_days', 0)
                card.state = State(state.fsrs_state.get('state', 0))
                if state.fsrs_state.get('due'):
                    card.due = datetime.fromisoformat(state.fsrs_state['due'])
                if state.fsrs_state.get('last_review'):
                    card.last_review = datetime.fromisoformat(state.fsrs_state['last_review'])
                return card
            except Exception as e:
                logger.warning(f"Failed to restore FSRS state, creating new card: {e}")
        
        # Create new card
        return Card()
    
    def _fsrs_card_to_state(self, card: 'Card') -> Dict[str, Any]:
        """
        Extract FSRS state for storage.
        """
        return {
            'stability': card.stability,
            'difficulty': card.difficulty,
            'reps': card.reps,
            'lapses': card.lapses,
            'elapsed_days': card.elapsed_days,
            'scheduled_days': card.scheduled_days,
            'state': card.state.value if hasattr(card.state, 'value') else int(card.state),
            'due': card.due.isoformat() if card.due else None,
            'last_review': card.last_review.isoformat() if card.last_review else None,
        }
    
    def initialize_card(
        self,
        user_id: UUID,
        learning_progress_id: int,
        learning_point_id: str,
        initial_difficulty: float = 0.5,
    ) -> CardState:
        """Initialize a new FSRS card."""
        # Create FSRS Card
        fsrs_card = Card()
        
        # Note: FSRS difficulty is learned, not set initially
        # We store initial_difficulty for our own tracking
        
        return CardState(
            user_id=user_id,
            learning_progress_id=learning_progress_id,
            learning_point_id=learning_point_id,
            algorithm_type='fsrs',
            current_interval=1,
            scheduled_date=date.today() + timedelta(days=1),
            ease_factor=2.5,  # Placeholder for compatibility
            consecutive_correct=0,
            stability=fsrs_card.stability,
            difficulty=initial_difficulty,
            fsrs_state=self._fsrs_card_to_state(fsrs_card),
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
        Process a review using FSRS algorithm.
        
        FSRS calculates optimal next review based on:
        - Current memory stability
        - Word difficulty
        - Elapsed time since last review
        - Target retention (90%)
        """
        review_datetime = datetime.combine(
            review_date or date.today(),
            datetime.min.time()
        )
        
        # Convert to FSRS Card
        fsrs_card = self._card_to_fsrs_card(state)
        
        # Get FSRS rating
        fsrs_rating = self._map_rating(rating)
        
        # Store state before review
        stability_before = fsrs_card.stability
        difficulty_before = fsrs_card.difficulty
        
        # Process review with FSRS
        scheduling_info = self._fsrs.repeat(fsrs_card, review_datetime)
        
        # Get the scheduled card for our rating
        scheduled = scheduling_info[fsrs_rating]
        new_fsrs_card = scheduled.card
        
        # Determine if correct
        was_correct = rating >= PerformanceRating.GOOD
        
        # Update consecutive correct
        if was_correct:
            new_consecutive = state.consecutive_correct + 1
        else:
            new_consecutive = 0
        
        # Calculate interval
        new_interval = new_fsrs_card.scheduled_days
        new_interval = min(new_interval, self.MAX_INTERVAL)
        
        # Get retention prediction
        retention = self._fsrs.get_retrievability(new_fsrs_card, review_datetime)
        
        # Update totals
        new_total_reviews = state.total_reviews + 1
        new_total_correct = state.total_correct + (1 if was_correct else 0)
        
        # Update response time average
        if response_time_ms is not None:
            if state.avg_response_time_ms is not None:
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
            algorithm_type='fsrs',
            current_interval=new_interval,
            scheduled_date=(review_date or date.today()) + timedelta(days=new_interval),
            last_review_date=review_date or date.today(),
            total_reviews=new_total_reviews,
            total_correct=new_total_correct,
            ease_factor=state.ease_factor,  # Keep for compatibility
            consecutive_correct=new_consecutive,
            stability=new_fsrs_card.stability,
            difficulty=new_fsrs_card.difficulty,
            retention_probability=retention,
            fsrs_state=self._fsrs_card_to_state(new_fsrs_card),
            avg_response_time_ms=new_avg_time,
        )
        
        # Check for leech
        new_state.is_leech = self.detect_leech(new_state)
        
        # Calculate mastery level
        old_mastery = state.mastery_level
        new_state.mastery_level = self._calculate_fsrs_mastery(new_state)
        mastery_changed = old_mastery != new_state.mastery_level
        
        return ReviewResult(
            new_state=new_state,
            next_review_date=new_state.scheduled_date,
            next_interval_days=new_interval,
            was_correct=was_correct,
            retention_predicted=retention,
            mastery_changed=mastery_changed,
            new_mastery_level=new_state.mastery_level if mastery_changed else None,
            became_leech=new_state.is_leech and not state.is_leech,
            algorithm_type='fsrs',
            debug_info={
                'stability_before': round(stability_before, 3) if stability_before else None,
                'stability_after': round(new_fsrs_card.stability, 3),
                'difficulty_before': round(difficulty_before, 3) if difficulty_before else None,
                'difficulty_after': round(new_fsrs_card.difficulty, 3),
                'fsrs_state': new_fsrs_card.state.name if hasattr(new_fsrs_card.state, 'name') else str(new_fsrs_card.state),
                'reps': new_fsrs_card.reps,
                'lapses': new_fsrs_card.lapses,
            },
        )
    
    def predict_retention(
        self,
        state: CardState,
        target_date: Optional[date] = None,
    ) -> float:
        """
        Predict retention probability at target date.
        
        FSRS has native retention prediction using its forgetting curve model.
        """
        target_datetime = datetime.combine(
            target_date or date.today(),
            datetime.min.time()
        )
        
        fsrs_card = self._card_to_fsrs_card(state)
        
        try:
            retention = self._fsrs.get_retrievability(fsrs_card, target_datetime)
            return max(0.0, min(1.0, retention))
        except Exception as e:
            logger.warning(f"FSRS retention prediction failed: {e}")
            return 0.5  # Default to 50%
    
    def _calculate_fsrs_mastery(self, state: CardState) -> str:
        """
        Calculate mastery level using FSRS-specific thresholds.
        
        Uses stability as primary indicator.
        """
        if state.is_leech:
            return 'leech'
        
        stability = state.stability or 0
        
        if stability < 5:  # Less than 5 days stability
            return 'learning'
        elif stability < 30:  # Less than 1 month
            return 'familiar'
        elif stability < 180:  # Less than 6 months
            return 'known'
        elif stability < 730:  # Less than 2 years
            return 'mastered'
        else:
            return 'permanent'
    
    def optimize_parameters(
        self,
        review_history: list,
        current_parameters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Optimize FSRS parameters based on user's review history.
        
        Should be called after user has 100+ reviews.
        
        Args:
            review_history: List of review records
            current_parameters: Current parameters (optional)
            
        Returns:
            Optimized FSRS parameters
        """
        # The fsrs library includes an optimizer
        # This would require the fsrs-optimizer package
        # For now, return defaults
        logger.info(f"Parameter optimization called with {len(review_history)} reviews")
        
        # TODO: Implement actual optimization using fsrs-optimizer
        # This requires additional dependencies and significant computation
        
        return current_parameters or {}

