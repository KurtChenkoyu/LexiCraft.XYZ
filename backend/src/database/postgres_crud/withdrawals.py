"""
CRUD operations for Withdrawal Requests table.
"""
from typing import Optional, List
from uuid import UUID
from decimal import Decimal
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_

from ..models import WithdrawalRequest


def create_withdrawal_request(
    session: Session,
    user_id: UUID,
    parent_id: UUID,
    amount_ntd: Decimal,
    points_amount: int,
    bank_account: Optional[str] = None
) -> WithdrawalRequest:
    """Create a new withdrawal request."""
    request = WithdrawalRequest(
        user_id=user_id,
        parent_id=parent_id,
        amount_ntd=amount_ntd,
        points_amount=points_amount,
        bank_account=bank_account,
        status='pending'
    )
    session.add(request)
    session.commit()
    session.refresh(request)
    return request


def get_withdrawal_request_by_id(session: Session, request_id: int) -> Optional[WithdrawalRequest]:
    """Get withdrawal request by ID."""
    return session.query(WithdrawalRequest).filter(WithdrawalRequest.id == request_id).first()


def get_withdrawal_requests_by_user(
    session: Session,
    user_id: UUID,
    status: Optional[str] = None
) -> List[WithdrawalRequest]:
    """Get all withdrawal requests for a user (learner), optionally filtered by status."""
    query = session.query(WithdrawalRequest).filter(WithdrawalRequest.user_id == user_id)
    if status:
        query = query.filter(WithdrawalRequest.status == status)
    return query.order_by(WithdrawalRequest.created_at.desc()).all()


def get_withdrawal_requests_by_parent(
    session: Session,
    parent_id: UUID,
    status: Optional[str] = None
) -> List[WithdrawalRequest]:
    """Get all withdrawal requests for a parent, optionally filtered by status."""
    query = session.query(WithdrawalRequest).filter(WithdrawalRequest.parent_id == parent_id)
    if status:
        query = query.filter(WithdrawalRequest.status == status)
    return query.order_by(WithdrawalRequest.created_at.desc()).all()


def update_withdrawal_request_status(
    session: Session,
    request_id: int,
    status: str,
    transaction_id: Optional[str] = None
) -> Optional[WithdrawalRequest]:
    """Update withdrawal request status."""
    request = get_withdrawal_request_by_id(session, request_id)
    if not request:
        return None
    
    request.status = status
    if transaction_id:
        request.transaction_id = transaction_id
    
    if status in ['completed', 'failed']:
        request.completed_at = datetime.now()
    
    session.commit()
    session.refresh(request)
    return request


def delete_withdrawal_request(session: Session, request_id: int) -> bool:
    """Delete a withdrawal request."""
    request = get_withdrawal_request_by_id(session, request_id)
    if not request:
        return False
    
    session.delete(request)
    session.commit()
    return True

