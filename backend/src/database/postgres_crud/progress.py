"""
CRUD operations for Learning Progress table.
"""
from typing import Optional, List
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import and_, text

from ..models import LearningProgress


def _get_learner_id_for_user(session: Session, user_id: UUID) -> Optional[UUID]:
    """
    Get the learner_id for a user_id (parent's own learner profile).
    
    Returns the learner profile ID where user_id matches and is_parent_profile=true.
    Returns None if no learner profile found (shouldn't happen in normal flow).
    """
    result = session.execute(
        text("""
            SELECT id FROM public.learners
            WHERE user_id = :user_id AND is_parent_profile = true
            LIMIT 1
        """),
        {'user_id': user_id}
    ).fetchone()
    return result[0] if result else None


def create_learning_progress(
    session: Session,
    user_id: UUID,
    learning_point_id: str,
    tier: int,
    status: str = 'learning',
    learner_id: Optional[UUID] = None  # Optional - will auto-resolve if not provided
) -> LearningProgress:
    """Create a new learning progress entry."""
    import os
    # Auto-resolve learner_id if not provided
    if learner_id is None:
        learner_id = _get_learner_id_for_user(session, user_id)
        if os.getenv("DEBUG_LEARNER_PIPELINE") == "true":
            print(f"[create_learning_progress] Auto-resolved learner_id={learner_id} for user_id={user_id}")
    elif os.getenv("DEBUG_LEARNER_PIPELINE") == "true":
        print(f"[create_learning_progress] Using provided learner_id={learner_id} for user_id={user_id}")
    
    progress = LearningProgress(
        user_id=user_id,
        learner_id=learner_id,  # Now always set
        learning_point_id=learning_point_id,
        rank=tier,  # Parameter name kept as tier for backward compatibility, but column is rank
        status=status
    )
    session.add(progress)
    try:
        session.commit()
        session.refresh(progress)
        
        if os.getenv("DEBUG_LEARNER_PIPELINE") == "true":
            print(f"[create_learning_progress] Created progress.id={progress.id}, progress.learner_id={progress.learner_id}, learning_point_id={learning_point_id}")
        
        return progress
    except Exception as e:
        session.rollback()
        # Check if it's a unique constraint violation
        error_str = str(e).lower()
        if 'unique' in error_str or 'duplicate' in error_str or 'constraint' in error_str:
            if os.getenv("DEBUG_LEARNER_PIPELINE") == "true":
                print(f"[create_learning_progress] Constraint violation - progress already exists for learner_id={learner_id}, learning_point_id={learning_point_id}")
            # Try to fetch the existing row
            from sqlalchemy import and_
            existing = session.query(LearningProgress).filter(
                and_(
                    LearningProgress.learner_id == learner_id,
                    LearningProgress.learning_point_id == learning_point_id,
                    LearningProgress.rank == tier  # Column is rank, parameter is tier
                )
            ).first()
            if existing:
                return existing
        # Re-raise if it's not a constraint violation or we can't find existing
        raise


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
    tier: Optional[int] = None  # Parameter name kept as tier for backward compatibility
) -> Optional[LearningProgress]:
    """Get learning progress for a specific learning point."""
    query = session.query(LearningProgress).filter(
        and_(
            LearningProgress.user_id == user_id,
            LearningProgress.learning_point_id == learning_point_id
        )
    )
    if tier is not None:
        query = query.filter(LearningProgress.rank == tier)  # Column is rank
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

