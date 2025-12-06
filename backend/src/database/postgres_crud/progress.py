"""
CRUD operations for Learning Progress table.
"""
from typing import Optional, List
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import and_

from ..models import LearningProgress


def create_learning_progress(
    session: Session,
    user_id: UUID,
    learning_point_id: str,
    tier: int,
    status: str = 'learning'
) -> LearningProgress:
    """Create a new learning progress entry."""
    progress = LearningProgress(
        user_id=user_id,
        learning_point_id=learning_point_id,
        tier=tier,
        status=status
    )
    session.add(progress)
    session.commit()
    session.refresh(progress)
    return progress


def get_learning_progress_by_id(session: Session, progress_id: int) -> Optional[LearningProgress]:
    """Get learning progress by ID."""
    return session.query(LearningProgress).filter(LearningProgress.id == progress_id).first()


def get_learning_progress_by_user(
    session: Session,
    user_id: UUID,
    status: Optional[str] = None
) -> List[LearningProgress]:
    """Get all learning progress for a user, optionally filtered by status."""
    query = session.query(LearningProgress).filter(LearningProgress.user_id == user_id)
    if status:
        query = query.filter(LearningProgress.status == status)
    return query.all()


def get_learning_progress_by_learning_point(
    session: Session,
    user_id: UUID,
    learning_point_id: str,
    tier: Optional[int] = None
) -> Optional[LearningProgress]:
    """Get learning progress for a specific learning point."""
    query = session.query(LearningProgress).filter(
        and_(
            LearningProgress.user_id == user_id,
            LearningProgress.learning_point_id == learning_point_id
        )
    )
    if tier is not None:
        query = query.filter(LearningProgress.tier == tier)
    return query.first()


def update_learning_progress_status(
    session: Session,
    progress_id: int,
    status: str
) -> Optional[LearningProgress]:
    """Update learning progress status."""
    progress = get_learning_progress_by_id(session, progress_id)
    if not progress:
        return None
    
    progress.status = status
    session.commit()
    session.refresh(progress)
    return progress


def get_user_known_components(session: Session, user_id: UUID) -> List[str]:
    """
    Get all learning point IDs that the user has learned (verified status).
    Used for relationship discovery.
    """
    results = session.query(LearningProgress.learning_point_id).filter(
        and_(
            LearningProgress.user_id == user_id,
            LearningProgress.status == 'verified'
        )
    ).all()
    return [row[0] for row in results]


def delete_learning_progress(session: Session, progress_id: int) -> bool:
    """Delete a learning progress entry."""
    progress = get_learning_progress_by_id(session, progress_id)
    if not progress:
        return False
    
    session.delete(progress)
    session.commit()
    return True

