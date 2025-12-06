"""
Spaced Repetition Module

Implements adaptive spaced repetition with A/B testing support for:
- SM-2+ Algorithm (rule-based, legacy)
- FSRS Algorithm (machine learning, modern)

Key Components:
- algorithm_interface.py: Abstract interface for both algorithms
- fsrs_service.py: FSRS library wrapper
- sm2_service.py: SM-2+ implementation
- assignment_service.py: User algorithm assignment for A/B testing
"""

from .algorithm_interface import (
    SpacedRepetitionAlgorithm,
    ReviewResult,
    CardState,
    PerformanceRating,
    get_algorithm_for_user,
)
from .fsrs_service import FSRSService
from .sm2_service import SM2PlusService
from .assignment_service import (
    AssignmentService,
    assign_user_algorithm,
    get_user_algorithm,
    can_migrate_to_fsrs,
)

__all__ = [
    # Interface
    'SpacedRepetitionAlgorithm',
    'ReviewResult',
    'CardState',
    'PerformanceRating',
    'get_algorithm_for_user',
    # Services
    'FSRSService',
    'SM2PlusService',
    'AssignmentService',
    # Assignment functions
    'assign_user_algorithm',
    'get_user_algorithm',
    'can_migrate_to_fsrs',
]

