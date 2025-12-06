"""
CRUD operations for MCQ Statistics and Adaptive Selection.

Provides:
- MCQ pool management (store/retrieve generated MCQs)
- Attempt tracking (record user answers)
- Statistics retrieval (quality metrics)
- Adaptive selection helpers (get MCQs by difficulty)
"""
from typing import Optional, List, Dict, Any, Tuple
from uuid import UUID
from datetime import datetime
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc

from ..models import MCQPool, MCQStatistics, MCQAttempt


# ============================================
# MCQ Pool Operations
# ============================================

def create_mcq(
    session: Session,
    sense_id: str,
    word: str,
    mcq_type: str,
    question: str,
    options: List[Dict],
    correct_index: int,
    context: Optional[str] = None,
    explanation: Optional[str] = None,
    metadata: Optional[Dict] = None
) -> MCQPool:
    """
    Create a new MCQ in the pool.
    
    Args:
        session: Database session
        sense_id: Neo4j sense ID
        word: The word being tested
        mcq_type: 'meaning', 'usage', or 'discrimination'
        question: The question text
        options: List of option dicts [{text, is_correct, source, source_word}]
        correct_index: Index of correct option (0-based)
        context: Example sentence providing context
        explanation: Explanation shown after answering
        metadata: Additional metadata
    
    Returns:
        Created MCQPool instance
    """
    mcq = MCQPool(
        sense_id=sense_id,
        word=word,
        mcq_type=mcq_type,
        question=question,
        options=options,
        correct_index=correct_index,
        context=context,
        explanation=explanation,
        mcq_metadata=metadata or {}
    )
    session.add(mcq)
    session.commit()
    session.refresh(mcq)
    return mcq


def get_mcq_by_id(session: Session, mcq_id: UUID) -> Optional[MCQPool]:
    """Get MCQ by ID."""
    return session.query(MCQPool).filter(MCQPool.id == mcq_id).first()


def get_mcqs_for_sense(
    session: Session,
    sense_id: str,
    mcq_type: Optional[str] = None,
    active_only: bool = True
) -> List[MCQPool]:
    """
    Get all MCQs for a sense.
    
    Args:
        session: Database session
        sense_id: Neo4j sense ID
        mcq_type: Optional filter by type ('meaning', 'usage', 'discrimination')
        active_only: Only return active MCQs
    
    Returns:
        List of MCQPool instances
    """
    query = session.query(MCQPool).filter(MCQPool.sense_id == sense_id)
    
    if mcq_type:
        query = query.filter(MCQPool.mcq_type == mcq_type)
    
    if active_only:
        query = query.filter(MCQPool.is_active == True)
    
    return query.all()


def get_mcqs_for_word(
    session: Session,
    word: str,
    active_only: bool = True
) -> List[MCQPool]:
    """Get all MCQs for a word (across all senses)."""
    query = session.query(MCQPool).filter(MCQPool.word == word)
    
    if active_only:
        query = query.filter(MCQPool.is_active == True)
    
    return query.all()


def get_mcqs_by_difficulty_range(
    session: Session,
    sense_id: str,
    min_difficulty: float = 0.0,
    max_difficulty: float = 1.0,
    active_only: bool = True,
    limit: int = 10
) -> List[MCQPool]:
    """
    Get MCQs within a difficulty range for adaptive selection.
    
    Args:
        session: Database session
        sense_id: Neo4j sense ID
        min_difficulty: Minimum difficulty index (0.0-1.0)
        max_difficulty: Maximum difficulty index (0.0-1.0)
        active_only: Only return active MCQs
        limit: Maximum number of MCQs to return
    
    Returns:
        List of MCQPool instances sorted by quality score
    """
    query = session.query(MCQPool).filter(
        MCQPool.sense_id == sense_id
    )
    
    if active_only:
        query = query.filter(MCQPool.is_active == True)
    
    # Filter by difficulty range (if difficulty is calculated)
    query = query.filter(
        or_(
            MCQPool.difficulty_index.is_(None),  # Include new MCQs
            and_(
                MCQPool.difficulty_index >= min_difficulty,
                MCQPool.difficulty_index <= max_difficulty
            )
        )
    )
    
    # Sort by quality score (best first), then by newest
    query = query.order_by(
        desc(MCQPool.quality_score.is_(None)),  # NULL quality last
        desc(MCQPool.quality_score),
        desc(MCQPool.created_at)
    )
    
    return query.limit(limit).all()


def update_mcq_status(
    session: Session,
    mcq_id: UUID,
    is_active: Optional[bool] = None,
    needs_review: Optional[bool] = None,
    review_reason: Optional[str] = None
) -> Optional[MCQPool]:
    """Update MCQ status flags."""
    mcq = get_mcq_by_id(session, mcq_id)
    if not mcq:
        return None
    
    if is_active is not None:
        mcq.is_active = is_active
    if needs_review is not None:
        mcq.needs_review = needs_review
    if review_reason is not None:
        mcq.review_reason = review_reason
    
    session.commit()
    session.refresh(mcq)
    return mcq


def bulk_create_mcqs(
    session: Session,
    mcqs_data: List[Dict]
) -> List[MCQPool]:
    """
    Bulk create MCQs.
    
    Args:
        session: Database session
        mcqs_data: List of dicts with MCQ data
    
    Returns:
        List of created MCQPool instances
    """
    mcqs = []
    for data in mcqs_data:
        mcq = MCQPool(
            sense_id=data['sense_id'],
            word=data['word'],
            mcq_type=data['mcq_type'],
            question=data['question'],
            options=data['options'],
            correct_index=data['correct_index'],
            context=data.get('context'),
            explanation=data.get('explanation'),
            mcq_metadata=data.get('metadata', {})
        )
        mcqs.append(mcq)
        session.add(mcq)
    
    session.commit()
    for mcq in mcqs:
        session.refresh(mcq)
    
    return mcqs


# ============================================
# MCQ Attempt Operations
# ============================================

def record_attempt(
    session: Session,
    user_id: UUID,
    mcq_id: UUID,
    sense_id: str,
    is_correct: bool,
    response_time_ms: Optional[int] = None,
    selected_option_index: Optional[int] = None,
    selected_option_source: Optional[str] = None,
    user_ability_estimate: Optional[float] = None,
    verification_schedule_id: Optional[int] = None,
    attempt_context: str = 'verification'
) -> MCQAttempt:
    """
    Record an MCQ attempt and update statistics.
    
    Args:
        session: Database session
        user_id: User who attempted
        mcq_id: MCQ attempted
        sense_id: Sense being tested
        is_correct: Whether answer was correct
        response_time_ms: Time taken to answer (milliseconds)
        selected_option_index: Which option was selected (0-based)
        selected_option_source: Source of selected option ('target', 'confused', etc.)
        user_ability_estimate: Estimated ability at time of attempt (0.0-1.0)
        verification_schedule_id: Link to spaced rep schedule (optional)
        attempt_context: Context ('verification', 'practice', 'survey')
    
    Returns:
        Created MCQAttempt instance
    """
    attempt = MCQAttempt(
        user_id=user_id,
        mcq_id=mcq_id,
        sense_id=sense_id,
        is_correct=is_correct,
        response_time_ms=response_time_ms,
        selected_option_index=selected_option_index,
        selected_option_source=selected_option_source,
        user_ability_estimate=Decimal(str(user_ability_estimate)) if user_ability_estimate is not None else None,
        verification_schedule_id=verification_schedule_id,
        attempt_context=attempt_context
    )
    session.add(attempt)
    session.commit()
    session.refresh(attempt)
    
    # Update MCQ statistics (Python-side since DB trigger may not exist)
    _update_mcq_statistics(session, mcq_id, is_correct, response_time_ms, 
                           selected_option_source, user_ability_estimate)
    
    return attempt


def _update_mcq_statistics(
    session: Session,
    mcq_id: UUID,
    is_correct: bool,
    response_time_ms: Optional[int],
    selected_option_source: Optional[str],
    user_ability_estimate: Optional[float]
):
    """Update MCQ statistics after an attempt."""
    stats = session.query(MCQStatistics).filter(MCQStatistics.mcq_id == mcq_id).first()
    
    if not stats:
        # Create new stats record
        stats = MCQStatistics(
            mcq_id=mcq_id,
            total_attempts=0,
            correct_attempts=0,
            total_response_time_ms=0,
            distractor_selections={},
            ability_sum_correct=Decimal('0'),
            ability_sum_wrong=Decimal('0'),
            ability_count_correct=0,
            ability_count_wrong=0,
            needs_recalculation=True
        )
        session.add(stats)
    
    # Update counts
    stats.total_attempts += 1
    if is_correct:
        stats.correct_attempts += 1
    
    # Update response time
    if response_time_ms:
        stats.total_response_time_ms = (stats.total_response_time_ms or 0) + response_time_ms
        stats.avg_response_time_ms = stats.total_response_time_ms // stats.total_attempts
    
    # Update distractor selections
    if selected_option_source:
        selections = dict(stats.distractor_selections or {})
        selections[selected_option_source] = selections.get(selected_option_source, 0) + 1
        stats.distractor_selections = selections
    
    # Update ability sums for discrimination calculation
    if user_ability_estimate is not None:
        if is_correct:
            stats.ability_sum_correct = (stats.ability_sum_correct or Decimal('0')) + Decimal(str(user_ability_estimate))
            stats.ability_count_correct += 1
        else:
            stats.ability_sum_wrong = (stats.ability_sum_wrong or Decimal('0')) + Decimal(str(user_ability_estimate))
            stats.ability_count_wrong += 1
    
    # Calculate difficulty index
    stats.difficulty_index = Decimal(str(stats.correct_attempts / stats.total_attempts))
    
    # Mark for full quality recalculation
    stats.needs_recalculation = True
    
    session.commit()


def get_user_attempts_for_sense(
    session: Session,
    user_id: UUID,
    sense_id: str,
    limit: int = 50
) -> List[MCQAttempt]:
    """Get user's recent attempts for a sense."""
    return session.query(MCQAttempt).filter(
        MCQAttempt.user_id == user_id,
        MCQAttempt.sense_id == sense_id
    ).order_by(desc(MCQAttempt.created_at)).limit(limit).all()


def get_user_recent_attempts(
    session: Session,
    user_id: UUID,
    limit: int = 100
) -> List[MCQAttempt]:
    """Get user's most recent attempts across all senses."""
    return session.query(MCQAttempt).filter(
        MCQAttempt.user_id == user_id
    ).order_by(desc(MCQAttempt.created_at)).limit(limit).all()


def count_user_attempts(
    session: Session,
    user_id: UUID,
    sense_id: Optional[str] = None
) -> Tuple[int, int]:
    """
    Count user's attempts and correct answers.
    
    Returns:
        Tuple of (total_attempts, correct_attempts)
    """
    query = session.query(MCQAttempt).filter(MCQAttempt.user_id == user_id)
    
    if sense_id:
        query = query.filter(MCQAttempt.sense_id == sense_id)
    
    total = query.count()
    correct = query.filter(MCQAttempt.is_correct == True).count()
    
    return total, correct


# ============================================
# MCQ Statistics Operations
# ============================================

def get_mcq_statistics(session: Session, mcq_id: UUID) -> Optional[MCQStatistics]:
    """Get statistics for an MCQ."""
    return session.query(MCQStatistics).filter(MCQStatistics.mcq_id == mcq_id).first()


def get_mcqs_needing_review(session: Session, limit: int = 50) -> List[MCQPool]:
    """Get MCQs flagged for review."""
    return session.query(MCQPool).filter(
        MCQPool.needs_review == True
    ).order_by(desc(MCQPool.updated_at)).limit(limit).all()


def get_low_quality_mcqs(
    session: Session,
    quality_threshold: float = 0.3,
    min_attempts: int = 10,
    limit: int = 50
) -> List[Tuple[MCQPool, MCQStatistics]]:
    """
    Get MCQs with low quality scores.
    
    Args:
        session: Database session
        quality_threshold: Maximum quality score to consider "low"
        min_attempts: Minimum attempts required for reliable stats
        limit: Maximum number to return
    
    Returns:
        List of (MCQPool, MCQStatistics) tuples
    """
    return session.query(MCQPool, MCQStatistics).join(
        MCQStatistics, MCQStatistics.mcq_id == MCQPool.id
    ).filter(
        MCQStatistics.total_attempts >= min_attempts,
        or_(
            MCQStatistics.quality_score < quality_threshold,
            MCQStatistics.quality_score.is_(None)
        )
    ).order_by(MCQStatistics.quality_score).limit(limit).all()


def get_quality_summary(session: Session) -> Dict[str, Any]:
    """
    Get summary statistics for MCQ quality.
    
    Returns:
        Dict with quality summary
    """
    # Total MCQs
    total_mcqs = session.query(func.count(MCQPool.id)).scalar()
    active_mcqs = session.query(func.count(MCQPool.id)).filter(MCQPool.is_active == True).scalar()
    
    # MCQs needing review
    needs_review = session.query(func.count(MCQPool.id)).filter(MCQPool.needs_review == True).scalar()
    
    # Quality distribution
    excellent = session.query(func.count(MCQPool.id)).filter(MCQPool.quality_score >= 0.7).scalar()
    good = session.query(func.count(MCQPool.id)).filter(
        and_(MCQPool.quality_score >= 0.5, MCQPool.quality_score < 0.7)
    ).scalar()
    fair = session.query(func.count(MCQPool.id)).filter(
        and_(MCQPool.quality_score >= 0.3, MCQPool.quality_score < 0.5)
    ).scalar()
    poor = session.query(func.count(MCQPool.id)).filter(MCQPool.quality_score < 0.3).scalar()
    uncalculated = session.query(func.count(MCQPool.id)).filter(MCQPool.quality_score.is_(None)).scalar()
    
    # Average quality (where calculated)
    avg_quality = session.query(func.avg(MCQPool.quality_score)).filter(
        MCQPool.quality_score.isnot(None)
    ).scalar()
    
    # Total attempts
    total_attempts = session.query(func.sum(MCQStatistics.total_attempts)).scalar() or 0
    
    return {
        'total_mcqs': total_mcqs,
        'active_mcqs': active_mcqs,
        'needs_review': needs_review,
        'quality_distribution': {
            'excellent': excellent,
            'good': good,
            'fair': fair,
            'poor': poor,
            'uncalculated': uncalculated
        },
        'avg_quality_score': float(avg_quality) if avg_quality else None,
        'total_attempts': total_attempts
    }


# ============================================
# Adaptive Selection Helpers
# ============================================

def estimate_user_ability_from_history(
    session: Session,
    user_id: UUID,
    sense_id: Optional[str] = None,
    recent_limit: int = 50
) -> float:
    """
    Estimate user's ability from their MCQ attempt history.
    
    Uses recent attempts to estimate current ability level.
    
    Args:
        session: Database session
        user_id: User to estimate ability for
        sense_id: Optional sense to estimate ability for (otherwise global)
        recent_limit: Number of recent attempts to consider
    
    Returns:
        Estimated ability (0.0-1.0)
    """
    query = session.query(MCQAttempt).filter(MCQAttempt.user_id == user_id)
    
    if sense_id:
        query = query.filter(MCQAttempt.sense_id == sense_id)
    
    recent_attempts = query.order_by(desc(MCQAttempt.created_at)).limit(recent_limit).all()
    
    if not recent_attempts:
        return 0.5  # Default: middle ability
    
    # Weight more recent attempts higher
    total_weight = 0
    weighted_correct = 0
    
    for i, attempt in enumerate(recent_attempts):
        # More recent = higher weight (exponential decay)
        weight = 0.95 ** i
        total_weight += weight
        if attempt.is_correct:
            weighted_correct += weight
    
    base_ability = weighted_correct / total_weight if total_weight > 0 else 0.5
    
    # Adjust for MCQ difficulty if we have stats
    # (correct on hard MCQ = higher ability)
    difficulty_adjustments = []
    for attempt in recent_attempts[:20]:  # Only use recent for difficulty adjustment
        stats = get_mcq_statistics(session, attempt.mcq_id)
        if stats and stats.difficulty_index:
            if attempt.is_correct:
                # Correct on hard MCQ = bonus
                adjustment = (1 - float(stats.difficulty_index)) * 0.1
            else:
                # Wrong on easy MCQ = penalty
                adjustment = -float(stats.difficulty_index) * 0.1
            difficulty_adjustments.append(adjustment)
    
    difficulty_bonus = sum(difficulty_adjustments) / len(difficulty_adjustments) if difficulty_adjustments else 0
    
    final_ability = base_ability + difficulty_bonus
    return max(0.0, min(1.0, final_ability))  # Clamp to [0, 1]


def select_adaptive_mcq(
    session: Session,
    sense_id: str,
    user_ability: float,
    exclude_mcq_ids: Optional[List[UUID]] = None,
    mcq_type: Optional[str] = None
) -> Optional[MCQPool]:
    """
    Select an MCQ adaptively based on user ability.
    
    Selects MCQ with difficulty matching user ability for optimal learning.
    
    Args:
        session: Database session
        sense_id: Sense to get MCQ for
        user_ability: User's estimated ability (0.0-1.0)
        exclude_mcq_ids: MCQ IDs to exclude (e.g., recently shown)
        mcq_type: Optional filter by MCQ type
    
    Returns:
        Selected MCQPool or None if no suitable MCQ found
    """
    # Target difficulty range: ability ± 0.15
    target_min = max(0.0, user_ability - 0.15)
    target_max = min(1.0, user_ability + 0.15)
    
    query = session.query(MCQPool).filter(
        MCQPool.sense_id == sense_id,
        MCQPool.is_active == True
    )
    
    if mcq_type:
        query = query.filter(MCQPool.mcq_type == mcq_type)
    
    if exclude_mcq_ids:
        query = query.filter(~MCQPool.id.in_(exclude_mcq_ids))
    
    # First try: MCQs in optimal difficulty range
    optimal_query = query.filter(
        or_(
            MCQPool.difficulty_index.is_(None),  # New MCQs are fine
            and_(
                MCQPool.difficulty_index >= target_min,
                MCQPool.difficulty_index <= target_max
            )
        )
    ).order_by(
        desc(MCQPool.quality_score),  # Best quality first
        func.random()  # Random among equal quality
    )
    
    result = optimal_query.first()
    if result:
        return result
    
    # Fallback: any MCQ for this sense
    return query.order_by(desc(MCQPool.quality_score), func.random()).first()


def get_mcq_pool_for_verification(
    session: Session,
    sense_id: str,
    user_id: UUID,
    mcq_type: Optional[str] = None,
    count: int = 3
) -> List[MCQPool]:
    """
    Get a pool of MCQs for a verification session.
    
    Selects multiple MCQs adaptively, avoiding recently shown MCQs.
    
    Args:
        session: Database session
        sense_id: Sense to verify
        user_id: User being verified
        mcq_type: Optional filter by MCQ type
        count: Number of MCQs to return
    
    Returns:
        List of MCQPool instances
    """
    # Get user's ability estimate
    user_ability = estimate_user_ability_from_history(session, user_id, sense_id)
    
    # Get recently shown MCQs for this user/sense
    recent_mcq_ids = [
        a.mcq_id for a in session.query(MCQAttempt.mcq_id).filter(
            MCQAttempt.user_id == user_id,
            MCQAttempt.sense_id == sense_id
        ).order_by(desc(MCQAttempt.created_at)).limit(10).all()
    ]
    
    selected = []
    exclude_ids = list(recent_mcq_ids)
    
    for _ in range(count):
        mcq = select_adaptive_mcq(
            session, sense_id, user_ability, 
            exclude_mcq_ids=exclude_ids,
            mcq_type=mcq_type
        )
        if mcq:
            selected.append(mcq)
            exclude_ids.append(mcq.id)
    
    return selected

