"""
Analytics Module

Provides metrics and comparisons for spaced repetition algorithms.

Key Components:
- algorithm_comparison.py: Compare SM-2+ vs FSRS performance
"""

from .algorithm_comparison import (
    AlgorithmComparisonService,
    get_comparison_metrics,
    calculate_daily_metrics,
)

__all__ = [
    'AlgorithmComparisonService',
    'get_comparison_metrics',
    'calculate_daily_metrics',
]

