"""
Unit tests for Algorithm Assignment Service.
"""

import pytest
from uuid import uuid4
from unittest.mock import Mock, MagicMock

from src.spaced_repetition.assignment_service import (
    AssignmentService,
    AlgorithmType,
    AssignmentReason,
)


class TestAssignmentService:
    """Test algorithm assignment service."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.user_id = uuid4()
        self.mock_db = Mock()
    
    def test_assign_algorithm_random(self):
        """Test random algorithm assignment."""
        service = AssignmentService(self.mock_db)
        
        # Mock database query
        self.mock_db.execute.return_value.fetchone.return_value = None
        self.mock_db.commit = Mock()
        
        # Should assign an algorithm
        algorithm = service.assign_algorithm(self.user_id, self.mock_db)
        
        assert algorithm in [AlgorithmType.SM2_PLUS, AlgorithmType.FSRS]
        assert self.mock_db.execute.called
        assert self.mock_db.commit.called
    
    def test_get_assignment_existing(self):
        """Test getting existing assignment."""
        service = AssignmentService(self.mock_db)
        
        # Mock existing assignment
        mock_result = Mock()
        mock_result.fetchone.return_value = ('fsrs',)
        self.mock_db.execute.return_value = mock_result
        
        algorithm = service.get_assignment(self.user_id, self.mock_db)
        
        assert algorithm == AlgorithmType.FSRS
    
    def test_get_assignment_none(self):
        """Test getting assignment when none exists."""
        service = AssignmentService(self.mock_db)
        
        # Mock no assignment
        mock_result = Mock()
        mock_result.fetchone.return_value = None
        self.mock_db.execute.return_value = mock_result
        
        algorithm = service.get_assignment(self.user_id, self.mock_db)
        
        assert algorithm is None
    
    def test_can_migrate_to_fsrs_sufficient_reviews(self):
        """Test migration eligibility with sufficient reviews."""
        service = AssignmentService(self.mock_db)
        
        # Mock 100+ reviews
        mock_result = Mock()
        mock_result.scalar.return_value = 150
        self.mock_db.execute.return_value = mock_result
        self.mock_db.commit = Mock()
        
        can_migrate, count = service.can_migrate_to_fsrs(self.user_id, self.mock_db)
        
        assert can_migrate is True
        assert count == 150
    
    def test_can_migrate_to_fsrs_insufficient_reviews(self):
        """Test migration eligibility with insufficient reviews."""
        service = AssignmentService(self.mock_db)
        
        # Mock < 100 reviews
        mock_result = Mock()
        mock_result.scalar.return_value = 50
        self.mock_db.execute.return_value = mock_result
        
        can_migrate, count = service.can_migrate_to_fsrs(self.user_id, self.mock_db)
        
        assert can_migrate is False
        assert count == 50
    
    def test_migrate_to_fsrs(self):
        """Test migration to FSRS."""
        service = AssignmentService(self.mock_db)
        
        # Mock eligibility check
        mock_review_result = Mock()
        mock_review_result.scalar.return_value = 150
        self.mock_db.execute.return_value = mock_review_result
        self.mock_db.commit = Mock()
        
        # Mock migration update
        def execute_side_effect(query, params):
            if 'UPDATE' in str(query):
                return Mock()
            return mock_review_result
        
        self.mock_db.execute.side_effect = execute_side_effect
        
        success = service.migrate_to_fsrs(self.user_id, self.mock_db)
        
        assert success is True
        assert self.mock_db.commit.called

