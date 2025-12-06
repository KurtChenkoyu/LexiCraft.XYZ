"""
Spaced Repetition Algorithm Interface

Provides an abstract interface for spaced repetition algorithms,
allowing SM-2+ and FSRS to be used interchangeably.

Key Classes:
- CardState: Represents the state of a learning card
- ReviewResult: Result of processing a review
- SpacedRepetitionAlgorithm: Abstract base class for algorithms
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, date, timedelta
from typing import Optional, Dict, Any, List
from uuid import UUID
from enum import IntEnum
import json


class PerformanceRating(IntEnum):
    """
    Performance rating scale (0-4).
    
    Used by both SM-2+ and FSRS:
    - FSRS native scale: Again(0), Hard(1), Good(2), Easy(3)
    - SM-2+ maps this to its 0-5 scale internally
    """
    AGAIN = 0       # Complete blackout, need to relearn
    HARD = 1        # Incorrect or barely remembered
    GOOD = 2        # Correct with some effort
    EASY = 3        # Correct, instant recall
    PERFECT = 4     # Perfect, trivially easy (bonus for SM-2+)


class MasteryLevel(IntEnum):
    """Mastery level progression."""
    LEARNING = 0     # < 3 correct in a row
    FAMILIAR = 1     # 3-4 correct in a row
    KNOWN = 2        # 5+ correct, EF > 2.5 (or stability > threshold)
    MASTERED = 3     # 5+ correct, EF > 2.8, interval > 180 days
    PERMANENT = 4    # Mastered for 2+ years


@dataclass
class CardState:
    """
    Represents the state of a learning card.
    
    Contains all information needed by both SM-2+ and FSRS algorithms.
    Algorithm-specific fields may be None for the other algorithm.
    """
    # Identity
    user_id: UUID
    learning_progress_id: int
    learning_point_id: str  # Neo4j reference
    
    # Algorithm type
    algorithm_type: str = 'sm2_plus'  # 'sm2_plus' or 'fsrs'
    
    # Common fields
    current_interval: int = 1  # days until next review
    scheduled_date: date = field(default_factory=date.today)
    last_review_date: Optional[date] = None
    total_reviews: int = 0
    total_correct: int = 0
    mastery_level: str = 'learning'
    is_leech: bool = False
    
    # SM-2+ specific
    ease_factor: float = 2.5  # 1.3 - 3.0
    consecutive_correct: int = 0
    
    # FSRS specific
    stability: Optional[float] = None  # Memory stability
    difficulty: float = 0.5  # Word difficulty (0-1)
    retention_probability: Optional[float] = None
    fsrs_state: Optional[Dict[str, Any]] = None  # Full FSRS state object
    
    # Performance tracking
    avg_response_time_ms: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dict."""
        return {
            'user_id': str(self.user_id),
            'learning_progress_id': self.learning_progress_id,
            'learning_point_id': self.learning_point_id,
            'algorithm_type': self.algorithm_type,
            'current_interval': self.current_interval,
            'scheduled_date': self.scheduled_date.isoformat() if self.scheduled_date else None,
            'last_review_date': self.last_review_date.isoformat() if self.last_review_date else None,
            'total_reviews': self.total_reviews,
            'total_correct': self.total_correct,
            'mastery_level': self.mastery_level,
            'is_leech': self.is_leech,
            'ease_factor': self.ease_factor,
            'consecutive_correct': self.consecutive_correct,
            'stability': self.stability,
            'difficulty': self.difficulty,
            'retention_probability': self.retention_probability,
            'fsrs_state': self.fsrs_state,
            'avg_response_time_ms': self.avg_response_time_ms,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CardState':
        """Create from dict."""
        return cls(
            user_id=UUID(data['user_id']) if isinstance(data['user_id'], str) else data['user_id'],
            learning_progress_id=data['learning_progress_id'],
            learning_point_id=data['learning_point_id'],
            algorithm_type=data.get('algorithm_type', 'sm2_plus'),
            current_interval=data.get('current_interval', 1),
            scheduled_date=date.fromisoformat(data['scheduled_date']) if data.get('scheduled_date') else date.today(),
            last_review_date=date.fromisoformat(data['last_review_date']) if data.get('last_review_date') else None,
            total_reviews=data.get('total_reviews', 0),
            total_correct=data.get('total_correct', 0),
            mastery_level=data.get('mastery_level', 'learning'),
            is_leech=data.get('is_leech', False),
            ease_factor=data.get('ease_factor', 2.5),
            consecutive_correct=data.get('consecutive_correct', 0),
            stability=data.get('stability'),
            difficulty=data.get('difficulty', 0.5),
            retention_probability=data.get('retention_probability'),
            fsrs_state=data.get('fsrs_state'),
            avg_response_time_ms=data.get('avg_response_time_ms'),
        )


@dataclass
class ReviewResult:
    """
    Result of processing a review.
    
    Contains updated card state and scheduling information.
    """
    # Updated state
    new_state: CardState
    
    # Scheduling
    next_review_date: date
    next_interval_days: int
    
    # Performance feedback
    was_correct: bool
    retention_predicted: Optional[float] = None
    
    # Mastery changes
    mastery_changed: bool = False
    new_mastery_level: Optional[str] = None
    became_leech: bool = False
    
    # Algorithm-specific info
    algorithm_type: str = 'sm2_plus'
    debug_info: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dict."""
        return {
            'new_state': self.new_state.to_dict(),
            'next_review_date': self.next_review_date.isoformat(),
            'next_interval_days': self.next_interval_days,
            'was_correct': self.was_correct,
            'retention_predicted': self.retention_predicted,
            'mastery_changed': self.mastery_changed,
            'new_mastery_level': self.new_mastery_level,
            'became_leech': self.became_leech,
            'algorithm_type': self.algorithm_type,
            'debug_info': self.debug_info,
        }


class SpacedRepetitionAlgorithm(ABC):
    """
    Abstract base class for spaced repetition algorithms.
    
    Implementations:
    - SM2PlusService: Traditional rule-based algorithm
    - FSRSService: Machine learning-based algorithm
    """
    
    @property
    @abstractmethod
    def algorithm_type(self) -> str:
        """Return algorithm type identifier."""
        pass
    
    @abstractmethod
    def initialize_card(
        self,
        user_id: UUID,
        learning_progress_id: int,
        learning_point_id: str,
        initial_difficulty: float = 0.5,
    ) -> CardState:
        """
        Initialize a new card for learning.
        
        Args:
            user_id: User UUID
            learning_progress_id: Reference to learning_progress table
            learning_point_id: Neo4j learning point ID
            initial_difficulty: Initial difficulty estimate (0-1)
            
        Returns:
            Initial CardState for this card
        """
        pass
    
    @abstractmethod
    def process_review(
        self,
        state: CardState,
        rating: PerformanceRating,
        response_time_ms: Optional[int] = None,
        review_date: Optional[date] = None,
    ) -> ReviewResult:
        """
        Process a review and calculate next interval.
        
        Args:
            state: Current card state
            rating: User's performance rating (0-4)
            response_time_ms: Time taken to answer (optional)
            review_date: Date of review (default: today)
            
        Returns:
            ReviewResult with updated state and next review date
        """
        pass
    
    @abstractmethod
    def predict_retention(
        self,
        state: CardState,
        target_date: Optional[date] = None,
    ) -> float:
        """
        Predict retention probability at target date.
        
        Args:
            state: Current card state
            target_date: Date to predict for (default: today)
            
        Returns:
            Probability of remembering (0-1)
        """
        pass
    
    def calculate_mastery_level(self, state: CardState) -> str:
        """
        Calculate mastery level from card state.
        
        Common implementation for both algorithms.
        """
        if state.is_leech:
            return 'leech'
        
        if state.consecutive_correct < 3:
            return 'learning'
        elif state.consecutive_correct < 5:
            return 'familiar'
        elif state.current_interval < 180:
            return 'known'
        elif state.current_interval < 365 * 2:
            return 'mastered'
        else:
            return 'permanent'
    
    def detect_leech(
        self,
        state: CardState,
        failure_threshold: int = 3,
        ease_threshold: float = 1.5,
    ) -> bool:
        """
        Detect if card is a leech (repeatedly fails).
        
        Args:
            state: Current card state
            failure_threshold: Consecutive failures to trigger leech
            ease_threshold: Ease factor below which to flag as leech
            
        Returns:
            True if card is a leech
        """
        # Already marked as leech
        if state.is_leech:
            return True
        
        # Check consecutive failures (consecutive_correct will be 0 or negative)
        if state.consecutive_correct <= -failure_threshold:
            return True
        
        # Check ease factor (SM-2+ specific)
        if state.ease_factor < ease_threshold:
            return True
        
        # Check stability (FSRS specific)
        if state.stability is not None and state.stability < 0.5:
            return True
        
        # Check overall performance
        if state.total_reviews >= 5:
            correct_rate = state.total_correct / state.total_reviews
            if correct_rate < 0.3:  # Less than 30% correct
                return True
        
        return False


# Factory function
def get_algorithm_for_user(user_id: UUID, db_session=None) -> SpacedRepetitionAlgorithm:
    """
    Get the appropriate algorithm for a user.
    
    Looks up user's algorithm assignment and returns the corresponding service.
    
    Args:
        user_id: User UUID
        db_session: Optional database session (for looking up assignment)
        
    Returns:
        SpacedRepetitionAlgorithm instance (SM2PlusService or FSRSService)
    """
    from .sm2_service import SM2PlusService
    from .fsrs_service import FSRSService
    from .assignment_service import get_user_algorithm
    
    algorithm_type = get_user_algorithm(user_id, db_session)
    
    if algorithm_type == 'fsrs':
        return FSRSService()
    else:
        return SM2PlusService()

