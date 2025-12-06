"""
CRUD operations for Points Accounts and Points Transactions tables.
"""
from typing import Optional, List
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import and_

from ..models import PointsAccount, PointsTransaction


# ========== Points Account CRUD ==========

def create_points_account(session: Session, user_id: UUID) -> PointsAccount:
    """Create a new points account for a user."""
    account = PointsAccount(
        user_id=user_id,
        total_earned=0,
        available_points=0,
        locked_points=0,
        withdrawn_points=0,
        deficit_points=0
    )
    session.add(account)
    session.commit()
    session.refresh(account)
    return account


def get_points_account_by_user(session: Session, user_id: UUID) -> Optional[PointsAccount]:
    """Get points account for a user."""
    return session.query(PointsAccount).filter(PointsAccount.user_id == user_id).first()


def get_or_create_points_account(session: Session, user_id: UUID) -> PointsAccount:
    """Get points account or create if it doesn't exist."""
    account = get_points_account_by_user(session, user_id)
    if not account:
        account = create_points_account(session, user_id)
    return account


def update_points_account(
    session: Session,
    user_id: UUID,
    total_earned: Optional[int] = None,
    available_points: Optional[int] = None,
    locked_points: Optional[int] = None,
    withdrawn_points: Optional[int] = None,
    deficit_points: Optional[int] = None
) -> Optional[PointsAccount]:
    """Update points account balances."""
    account = get_points_account_by_user(session, user_id)
    if not account:
        return None
    
    if total_earned is not None:
        account.total_earned = total_earned
    if available_points is not None:
        account.available_points = available_points
    if locked_points is not None:
        account.locked_points = locked_points
    if withdrawn_points is not None:
        account.withdrawn_points = withdrawn_points
    if deficit_points is not None:
        account.deficit_points = deficit_points
    
    session.commit()
    session.refresh(account)
    return account


# ========== Points Transaction CRUD ==========

def create_points_transaction(
    session: Session,
    user_id: UUID,
    transaction_type: str,
    points: int,
    learning_progress_id: Optional[int] = None,
    bonus_type: Optional[str] = None,
    tier: Optional[int] = None,
    description: Optional[str] = None
) -> PointsTransaction:
    """Create a new points transaction."""
    transaction = PointsTransaction(
        user_id=user_id,
        learning_progress_id=learning_progress_id,
        transaction_type=transaction_type,
        bonus_type=bonus_type,
        points=points,
        tier=tier,
        description=description
    )
    session.add(transaction)
    session.commit()
    session.refresh(transaction)
    return transaction


def get_points_transaction_by_id(session: Session, transaction_id: int) -> Optional[PointsTransaction]:
    """Get points transaction by ID."""
    return session.query(PointsTransaction).filter(PointsTransaction.id == transaction_id).first()


def get_points_transactions_by_user(
    session: Session,
    user_id: UUID,
    transaction_type: Optional[str] = None,
    limit: Optional[int] = None
) -> List[PointsTransaction]:
    """Get all points transactions for a user, optionally filtered by type."""
    query = session.query(PointsTransaction).filter(PointsTransaction.user_id == user_id)
    if transaction_type:
        query = query.filter(PointsTransaction.transaction_type == transaction_type)
    query = query.order_by(PointsTransaction.created_at.desc())
    if limit:
        query = query.limit(limit)
    return query.all()


def get_points_transactions_by_learning_progress(
    session: Session,
    learning_progress_id: int
) -> List[PointsTransaction]:
    """Get all points transactions for a specific learning progress entry."""
    return session.query(PointsTransaction).filter(
        PointsTransaction.learning_progress_id == learning_progress_id
    ).all()

