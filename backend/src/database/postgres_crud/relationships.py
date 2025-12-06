"""
CRUD operations for Relationship Discoveries table.
"""
from typing import Optional, List
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import and_

from ..models import RelationshipDiscovery


def create_relationship_discovery(
    session: Session,
    user_id: UUID,
    source_learning_point_id: str,
    target_learning_point_id: str,
    relationship_type: str,
    bonus_awarded: bool = False
) -> RelationshipDiscovery:
    """Create a new relationship discovery entry."""
    discovery = RelationshipDiscovery(
        user_id=user_id,
        source_learning_point_id=source_learning_point_id,
        target_learning_point_id=target_learning_point_id,
        relationship_type=relationship_type,
        bonus_awarded=bonus_awarded
    )
    session.add(discovery)
    session.commit()
    session.refresh(discovery)
    return discovery


def get_relationship_discovery_by_id(session: Session, discovery_id: int) -> Optional[RelationshipDiscovery]:
    """Get relationship discovery by ID."""
    return session.query(RelationshipDiscovery).filter(RelationshipDiscovery.id == discovery_id).first()


def get_relationship_discoveries_by_user(
    session: Session,
    user_id: UUID,
    bonus_awarded: Optional[bool] = None
) -> List[RelationshipDiscovery]:
    """Get all relationship discoveries for a user, optionally filtered by bonus status."""
    query = session.query(RelationshipDiscovery).filter(RelationshipDiscovery.user_id == user_id)
    if bonus_awarded is not None:
        query = query.filter(RelationshipDiscovery.bonus_awarded == bonus_awarded)
    return query.order_by(RelationshipDiscovery.discovered_at.desc()).all()


def get_relationship_discoveries_by_source(
    session: Session,
    user_id: UUID,
    source_learning_point_id: str
) -> List[RelationshipDiscovery]:
    """Get all relationship discoveries for a specific source learning point."""
    return session.query(RelationshipDiscovery).filter(
        and_(
            RelationshipDiscovery.user_id == user_id,
            RelationshipDiscovery.source_learning_point_id == source_learning_point_id
        )
    ).all()


def check_relationship_exists(
    session: Session,
    user_id: UUID,
    source_learning_point_id: str,
    target_learning_point_id: str,
    relationship_type: str
) -> bool:
    """Check if a relationship discovery already exists."""
    discovery = session.query(RelationshipDiscovery).filter(
        and_(
            RelationshipDiscovery.user_id == user_id,
            RelationshipDiscovery.source_learning_point_id == source_learning_point_id,
            RelationshipDiscovery.target_learning_point_id == target_learning_point_id,
            RelationshipDiscovery.relationship_type == relationship_type
        )
    ).first()
    return discovery is not None


def mark_bonus_awarded(
    session: Session,
    discovery_id: int
) -> Optional[RelationshipDiscovery]:
    """Mark a relationship discovery as having bonus awarded."""
    discovery = get_relationship_discovery_by_id(session, discovery_id)
    if not discovery:
        return None
    
    discovery.bonus_awarded = True
    session.commit()
    session.refresh(discovery)
    return discovery


def delete_relationship_discovery(session: Session, discovery_id: int) -> bool:
    """Delete a relationship discovery entry."""
    discovery = get_relationship_discovery_by_id(session, discovery_id)
    if not discovery:
        return False
    
    session.delete(discovery)
    session.commit()
    return True

