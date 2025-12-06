"""
Algorithm Assignment Service

Handles user assignment to SM-2+ or FSRS algorithms for A/B testing.

Features:
- Random 50/50 assignment for new users
- Manual assignment override
- Migration from SM-2+ to FSRS (after 100+ reviews)
- Assignment tracking and analytics
"""

import logging
import random
from datetime import datetime
from typing import Optional, Dict, Any, Tuple
from uuid import UUID
from enum import Enum

from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class AlgorithmType(str, Enum):
    SM2_PLUS = 'sm2_plus'
    FSRS = 'fsrs'


class AssignmentReason(str, Enum):
    RANDOM = 'random'
    MANUAL = 'manual'
    MIGRATION = 'migration'
    OPT_IN = 'opt_in'


class AssignmentService:
    """
    Service for managing algorithm assignments.
    
    Handles:
    - Initial assignment (random 50/50 split)
    - Assignment lookup
    - Migration eligibility
    - Assignment changes
    """
    
    # Minimum reviews required for FSRS migration
    MIN_REVIEWS_FOR_MIGRATION = 100
    
    # Assignment split (50% FSRS by default)
    FSRS_ASSIGNMENT_PROBABILITY = 0.5
    
    def __init__(self, db_session: Optional[Session] = None):
        """
        Initialize assignment service.
        
        Args:
            db_session: SQLAlchemy session (optional, can be passed to methods)
        """
        self._db = db_session
    
    def assign_algorithm(
        self,
        user_id: UUID,
        db: Optional[Session] = None,
        force_algorithm: Optional[AlgorithmType] = None,
        reason: AssignmentReason = AssignmentReason.RANDOM,
    ) -> AlgorithmType:
        """
        Assign an algorithm to a user.
        
        If force_algorithm is provided, uses that.
        Otherwise, randomly assigns based on probability split.
        
        Args:
            user_id: User UUID
            db: Database session
            force_algorithm: Force specific algorithm (optional)
            reason: Reason for assignment
            
        Returns:
            Assigned algorithm type
        """
        db = db or self._db
        if not db:
            logger.warning("No database session, defaulting to SM-2+")
            return AlgorithmType.SM2_PLUS
        
        # Check if already assigned
        existing = self.get_assignment(user_id, db)
        if existing:
            return existing
        
        # Determine algorithm
        if force_algorithm:
            algorithm = force_algorithm
        elif random.random() < self.FSRS_ASSIGNMENT_PROBABILITY:
            algorithm = AlgorithmType.FSRS
        else:
            algorithm = AlgorithmType.SM2_PLUS
        
        # Insert assignment
        try:
            db.execute(
                text("""
                    INSERT INTO user_algorithm_assignment (user_id, algorithm, assignment_reason)
                    VALUES (:user_id, :algorithm, :reason)
                    ON CONFLICT (user_id) DO NOTHING
                """),
                {
                    'user_id': user_id,
                    'algorithm': algorithm.value,
                    'reason': reason.value,
                }
            )
            db.commit()
            logger.info(f"Assigned algorithm {algorithm} to user {user_id}")
        except Exception as e:
            logger.error(f"Failed to assign algorithm: {e}")
            db.rollback()
        
        return algorithm
    
    def get_assignment(
        self,
        user_id: UUID,
        db: Optional[Session] = None,
    ) -> Optional[AlgorithmType]:
        """
        Get user's current algorithm assignment.
        
        Args:
            user_id: User UUID
            db: Database session
            
        Returns:
            Algorithm type or None if not assigned
        """
        db = db or self._db
        if not db:
            return None
        
        try:
            result = db.execute(
                text("""
                    SELECT algorithm
                    FROM user_algorithm_assignment
                    WHERE user_id = :user_id
                """),
                {'user_id': user_id}
            )
            row = result.fetchone()
            if row:
                return AlgorithmType(row[0])
            return None
        except Exception as e:
            logger.error(f"Failed to get assignment: {e}")
            return None
    
    def get_or_assign(
        self,
        user_id: UUID,
        db: Optional[Session] = None,
    ) -> AlgorithmType:
        """
        Get user's algorithm, assigning one if not assigned.
        
        Args:
            user_id: User UUID
            db: Database session
            
        Returns:
            Algorithm type
        """
        existing = self.get_assignment(user_id, db)
        if existing:
            return existing
        return self.assign_algorithm(user_id, db)
    
    def can_migrate_to_fsrs(
        self,
        user_id: UUID,
        db: Optional[Session] = None,
    ) -> Tuple[bool, int]:
        """
        Check if user can migrate to FSRS.
        
        Requires 100+ reviews for personalization.
        
        Args:
            user_id: User UUID
            db: Database session
            
        Returns:
            Tuple of (can_migrate, current_review_count)
        """
        db = db or self._db
        if not db:
            return False, 0
        
        try:
            result = db.execute(
                text("""
                    SELECT COUNT(*)
                    FROM fsrs_review_history
                    WHERE user_id = :user_id
                """),
                {'user_id': user_id}
            )
            count = result.scalar() or 0
            can_migrate = count >= self.MIN_REVIEWS_FOR_MIGRATION
            
            # Update the flag in assignment table
            if can_migrate:
                db.execute(
                    text("""
                        UPDATE user_algorithm_assignment
                        SET can_migrate_to_fsrs = TRUE
                        WHERE user_id = :user_id
                    """),
                    {'user_id': user_id}
                )
                db.commit()
            
            return can_migrate, count
        except Exception as e:
            logger.error(f"Failed to check migration eligibility: {e}")
            return False, 0
    
    def migrate_to_fsrs(
        self,
        user_id: UUID,
        db: Optional[Session] = None,
        force: bool = False,
    ) -> bool:
        """
        Migrate user from SM-2+ to FSRS.
        
        Args:
            user_id: User UUID
            db: Database session
            force: Force migration even if under 100 reviews
            
        Returns:
            True if migration successful
        """
        db = db or self._db
        if not db:
            return False
        
        # Check eligibility
        if not force:
            can_migrate, count = self.can_migrate_to_fsrs(user_id, db)
            if not can_migrate:
                logger.warning(
                    f"User {user_id} cannot migrate to FSRS yet "
                    f"({count}/{self.MIN_REVIEWS_FOR_MIGRATION} reviews)"
                )
                return False
        
        try:
            db.execute(
                text("""
                    UPDATE user_algorithm_assignment
                    SET algorithm = 'fsrs',
                        assignment_reason = 'migration',
                        updated_at = NOW()
                    WHERE user_id = :user_id
                """),
                {'user_id': user_id}
            )
            db.commit()
            logger.info(f"Migrated user {user_id} to FSRS")
            return True
        except Exception as e:
            logger.error(f"Failed to migrate user to FSRS: {e}")
            db.rollback()
            return False
    
    def get_assignment_stats(
        self,
        db: Optional[Session] = None,
    ) -> Dict[str, Any]:
        """
        Get aggregate assignment statistics.
        
        Returns counts of users in each algorithm group.
        """
        db = db or self._db
        if not db:
            return {}
        
        try:
            result = db.execute(
                text("""
                    SELECT 
                        algorithm,
                        COUNT(*) as count,
                        COUNT(*) FILTER (WHERE can_migrate_to_fsrs) as can_migrate_count
                    FROM user_algorithm_assignment
                    GROUP BY algorithm
                """)
            )
            
            stats = {
                'sm2_plus': {'count': 0, 'can_migrate': 0},
                'fsrs': {'count': 0, 'can_migrate': 0},
            }
            
            for row in result.fetchall():
                algo = row[0]
                stats[algo] = {
                    'count': row[1],
                    'can_migrate': row[2],
                }
            
            stats['total'] = stats['sm2_plus']['count'] + stats['fsrs']['count']
            
            return stats
        except Exception as e:
            logger.error(f"Failed to get assignment stats: {e}")
            return {}


# Module-level convenience functions

def get_user_algorithm(
    user_id: UUID,
    db_session: Optional[Session] = None,
) -> str:
    """
    Get user's assigned algorithm.
    
    Convenience function that wraps AssignmentService.
    
    Args:
        user_id: User UUID
        db_session: Database session (optional)
        
    Returns:
        Algorithm type string ('sm2_plus' or 'fsrs')
    """
    service = AssignmentService(db_session)
    algorithm = service.get_or_assign(user_id, db_session)
    return algorithm.value


def assign_user_algorithm(
    user_id: UUID,
    db_session: Optional[Session] = None,
    algorithm: Optional[str] = None,
) -> str:
    """
    Assign algorithm to user.
    
    Convenience function that wraps AssignmentService.
    
    Args:
        user_id: User UUID
        db_session: Database session (optional)
        algorithm: Force specific algorithm (optional)
        
    Returns:
        Assigned algorithm type string
    """
    service = AssignmentService(db_session)
    force_algo = AlgorithmType(algorithm) if algorithm else None
    result = service.assign_algorithm(user_id, db_session, force_algorithm=force_algo)
    return result.value


def can_migrate_to_fsrs(
    user_id: UUID,
    db_session: Optional[Session] = None,
) -> bool:
    """
    Check if user can migrate to FSRS.
    
    Args:
        user_id: User UUID
        db_session: Database session (optional)
        
    Returns:
        True if user has 100+ reviews
    """
    service = AssignmentService(db_session)
    can_migrate, _ = service.can_migrate_to_fsrs(user_id, db_session)
    return can_migrate

