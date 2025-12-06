"""
CRUD operations for Verification Schedule table.

Updated to support both SM-2+ and FSRS algorithms via algorithm interface.
"""
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import date, datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, text

from ..models import VerificationSchedule
from ...spaced_repetition import get_algorithm_for_user, CardState


def create_verification_schedule(
    session: Session,
    user_id: UUID,
    learning_progress_id: int,
    learning_point_id: str,
    initial_difficulty: float = 0.5,
    test_day: Optional[int] = None,  # Legacy parameter, kept for backward compatibility
    scheduled_date: Optional[date] = None,  # Will be calculated by algorithm
) -> VerificationSchedule:
    """
    Create a new verification schedule entry using the user's assigned algorithm.
    
    Uses the algorithm interface to initialize the card state, which determines:
    - Algorithm type (SM-2+ or FSRS)
    - Initial interval and scheduled date
    - Algorithm-specific state (ease_factor, stability, etc.)
    """
    # Get user's algorithm
    algorithm = get_algorithm_for_user(user_id, session)
    
    # Initialize card state using algorithm
    card_state = algorithm.initialize_card(
        user_id=user_id,
        learning_progress_id=learning_progress_id,
        learning_point_id=learning_point_id,
        initial_difficulty=initial_difficulty,
    )
    
    # Create schedule from card state
    schedule = VerificationSchedule(
        user_id=user_id,
        learning_progress_id=learning_progress_id,
        algorithm_type=card_state.algorithm_type,
        current_interval=card_state.current_interval,
        scheduled_date=scheduled_date or card_state.scheduled_date,
        test_day=test_day,  # Legacy field, may be None for FSRS
        ease_factor=card_state.ease_factor,
        consecutive_correct=card_state.consecutive_correct,
        stability=card_state.stability,
        difficulty=card_state.difficulty,
        retention_probability=card_state.retention_probability,
        fsrs_state=card_state.fsrs_state,
        last_review_date=card_state.last_review_date,
        mastery_level=card_state.mastery_level,
        is_leech=card_state.is_leech,
        total_reviews=card_state.total_reviews,
        total_correct=card_state.total_correct,
        avg_response_time_ms=card_state.avg_response_time_ms,
        completed=False
    )
    session.add(schedule)
    session.commit()
    session.refresh(schedule)
    return schedule


def get_verification_schedule_by_id(session: Session, schedule_id: int) -> Optional[VerificationSchedule]:
    """Get verification schedule by ID."""
    return session.query(VerificationSchedule).filter(VerificationSchedule.id == schedule_id).first()


def get_verification_schedules_by_user(
    session: Session,
    user_id: UUID,
    completed: Optional[bool] = None
) -> List[VerificationSchedule]:
    """Get all verification schedules for a user, optionally filtered by completion status."""
    query = session.query(VerificationSchedule).filter(VerificationSchedule.user_id == user_id)
    if completed is not None:
        query = query.filter(VerificationSchedule.completed == completed)
    return query.all()


def get_upcoming_verifications(
    session: Session,
    user_id: UUID,
    date_limit: Optional[date] = None
) -> List[VerificationSchedule]:
    """Get upcoming verification schedules for a user."""
    query = session.query(VerificationSchedule).filter(
        and_(
            VerificationSchedule.user_id == user_id,
            VerificationSchedule.completed == False,
            VerificationSchedule.scheduled_date >= date.today()
        )
    )
    if date_limit:
        query = query.filter(VerificationSchedule.scheduled_date <= date_limit)
    return query.order_by(VerificationSchedule.scheduled_date).all()


def complete_verification(
    session: Session,
    schedule_id: int,
    passed: bool,
    score: Optional[float] = None,
    questions: Optional[Dict[str, Any]] = None,
    answers: Optional[Dict[str, Any]] = None
) -> Optional[VerificationSchedule]:
    """Mark a verification as completed with results."""
    schedule = get_verification_schedule_by_id(session, schedule_id)
    if not schedule:
        return None
    
    schedule.completed = True
    schedule.completed_at = datetime.now()
    schedule.passed = passed
    if score is not None:
        schedule.score = score
    if questions is not None:
        schedule.questions = questions
    if answers is not None:
        schedule.answers = answers
    
    session.commit()
    session.refresh(schedule)
    return schedule


def delete_verification_schedule(session: Session, schedule_id: int) -> bool:
    """Delete a verification schedule entry."""
    schedule = get_verification_schedule_by_id(session, schedule_id)
    if not schedule:
        return False
    
    session.delete(schedule)
    session.commit()
    return True

