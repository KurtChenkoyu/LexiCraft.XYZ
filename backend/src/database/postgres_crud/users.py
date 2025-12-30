"""
CRUD operations for Users, UserRoles, and UserRelationships.
"""
from typing import Optional, List, Tuple
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import and_, text

from ..models import User, UserRole, UserRelationship


# ========== User CRUD ==========

def create_user(
    session: Session,
    email: str,
    password_hash: Optional[str] = None,
    name: Optional[str] = None,
    phone: Optional[str] = None,
    country: str = 'TW',
    age: Optional[int] = None
) -> User:
    """Create a new user (can be parent, child, or learner)."""
    user = User(
        email=email,
        password_hash=password_hash,
        name=name,
        phone=phone,
        country=country,
        age=age
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def create_user_no_commit(
    session: Session,
    email: str,
    password_hash: Optional[str] = None,
    name: Optional[str] = None,
    phone: Optional[str] = None,
    country: str = 'TW',
    age: Optional[int] = None
) -> User:
    """Create a new user without committing (for transaction atomicity)."""
    user = User(
        email=email,
        password_hash=password_hash,
        name=name,
        phone=phone,
        country=country,
        age=age
    )
    session.add(user)
    session.flush()  # Flush to get ID but don't commit
    session.refresh(user)
    return user


def get_user_by_id(session: Session, user_id: UUID) -> Optional[User]:
    """Get user by ID."""
    return session.query(User).filter(User.id == user_id).first()


def get_user_by_email(session: Session, email: str) -> Optional[User]:
    """Get user by email."""
    return session.query(User).filter(User.email == email).first()


def update_user(
    session: Session,
    user_id: UUID,
    name: Optional[str] = None,
    phone: Optional[str] = None,
    country: Optional[str] = None,
    age: Optional[int] = None
) -> Optional[User]:
    """Update user information."""
    user = get_user_by_id(session, user_id)
    if not user:
        return None
    
    if name is not None:
        user.name = name
    if phone is not None:
        user.phone = phone
    if country is not None:
        user.country = country
    if age is not None:
        user.age = age
    
    session.commit()
    session.refresh(user)
    return user


def delete_user(session: Session, user_id: UUID) -> bool:
    """Delete a user (cascades to relationships and related data)."""
    user = get_user_by_id(session, user_id)
    if not user:
        return False
    
    session.delete(user)
    session.commit()
    return True


# ========== User Roles CRUD ==========

def add_user_role(session: Session, user_id: UUID, role: str) -> UserRole:
    """Add a role to a user."""
    user_role = UserRole(user_id=user_id, role=role)
    session.add(user_role)
    session.commit()
    session.refresh(user_role)
    return user_role


def add_user_role_no_commit(session: Session, user_id: UUID, role: str) -> UserRole:
    """Add a role to a user without committing (for transaction atomicity)."""
    user_role = UserRole(user_id=user_id, role=role)
    session.add(user_role)
    session.flush()  # Flush to check constraints but don't commit
    session.refresh(user_role)
    return user_role


def remove_user_role(session: Session, user_id: UUID, role: str) -> bool:
    """Remove a role from a user."""
    user_role = session.query(UserRole).filter(
        and_(UserRole.user_id == user_id, UserRole.role == role)
    ).first()
    if not user_role:
        return False
    
    session.delete(user_role)
    session.commit()
    return True


def get_user_roles(session: Session, user_id: UUID) -> List[str]:
    """Get all roles for a user."""
    roles = session.query(UserRole.role).filter(UserRole.user_id == user_id).all()
    return [r[0] for r in roles]


def user_has_role(session: Session, user_id: UUID, role: str) -> bool:
    """Check if user has a specific role."""
    return session.query(UserRole).filter(
        and_(UserRole.user_id == user_id, UserRole.role == role)
    ).first() is not None


# ========== User Relationships CRUD ==========

def create_user_relationship(
    session: Session,
    from_user_id: UUID,
    to_user_id: UUID,
    relationship_type: str,
    status: str = 'active',
    permissions: Optional[dict] = None,
    metadata: Optional[dict] = None,
    requested_by: Optional[UUID] = None,
    approved_by: Optional[UUID] = None
) -> UserRelationship:
    """Create a user relationship (parent_child, coach_student, etc.)."""
    if from_user_id == to_user_id:
        raise ValueError("Users cannot have relationship with themselves")
    
    # Default permissions for parent_child
    if permissions is None and relationship_type == 'parent_child':
        permissions = {
            "can_view_progress": True,
            "can_assign_work": True,
            "can_verify_learning": False,
            "can_withdraw": True,
            "can_manage_account": True,
            "can_view_financials": True
        }
    
    relationship = UserRelationship(
        from_user_id=from_user_id,
        to_user_id=to_user_id,
        relationship_type=relationship_type,
        status=status,
        permissions=permissions or {},
        relationship_metadata=metadata or {},  # Using relationship_metadata (maps to 'metadata' column)
        requested_by=requested_by,
        approved_by=approved_by
    )
    session.add(relationship)
    session.commit()
    session.refresh(relationship)
    return relationship


def create_user_relationship_no_commit(
    session: Session,
    from_user_id: UUID,
    to_user_id: UUID,
    relationship_type: str,
    status: str = 'active',
    permissions: Optional[dict] = None,
    metadata: Optional[dict] = None,
    requested_by: Optional[UUID] = None,
    approved_by: Optional[UUID] = None
) -> UserRelationship:
    """Create a user relationship without committing (for transaction atomicity)."""
    if from_user_id == to_user_id:
        raise ValueError("Users cannot have relationship with themselves")
    
    # Default permissions for parent_child
    if permissions is None and relationship_type == 'parent_child':
        permissions = {
            "can_view_progress": True,
            "can_assign_work": True,
            "can_verify_learning": False,
            "can_withdraw": True,
            "can_manage_account": True,
            "can_view_financials": True
        }
    
    relationship = UserRelationship(
        from_user_id=from_user_id,
        to_user_id=to_user_id,
        relationship_type=relationship_type,
        status=status,
        permissions=permissions or {},
        relationship_metadata=metadata or {},
        requested_by=requested_by,
        approved_by=approved_by
    )
    session.add(relationship)
    session.flush()  # Flush to check constraints but don't commit
    session.refresh(relationship)
    return relationship


def get_user_children(session: Session, parent_id: UUID) -> List[User]:
    """Get all children for a parent (parent_child relationships)."""
    return session.query(User).join(
        UserRelationship,
        User.id == UserRelationship.to_user_id
    ).filter(
        and_(
            UserRelationship.from_user_id == parent_id,
            UserRelationship.relationship_type == 'parent_child',
            UserRelationship.status == 'active'
        )
    ).all()


def get_user_parents(session: Session, child_id: UUID) -> List[User]:
    """Get all parents for a child (parent_child relationships)."""
    return session.query(User).join(
        UserRelationship,
        User.id == UserRelationship.from_user_id
    ).filter(
        and_(
            UserRelationship.to_user_id == child_id,
            UserRelationship.relationship_type == 'parent_child',
            UserRelationship.status == 'active'
        )
    ).all()


def is_parent_of(session: Session, parent_id: UUID, child_id: UUID) -> bool:
    """Check if user is parent of another user."""
    return session.query(UserRelationship).filter(
        and_(
            UserRelationship.from_user_id == parent_id,
            UserRelationship.to_user_id == child_id,
            UserRelationship.relationship_type == 'parent_child',
            UserRelationship.status == 'active'
        )
    ).first() is not None


def get_user_relationships(
    session: Session,
    user_id: UUID,
    relationship_type: Optional[str] = None,
    direction: str = 'both'  # 'from', 'to', or 'both'
) -> List[UserRelationship]:
    """Get all relationships for a user, optionally filtered by type and direction."""
    query = session.query(UserRelationship)
    
    if direction == 'from':
        query = query.filter(UserRelationship.from_user_id == user_id)
    elif direction == 'to':
        query = query.filter(UserRelationship.to_user_id == user_id)
    else:  # both
        query = query.filter(
            (UserRelationship.from_user_id == user_id) |
            (UserRelationship.to_user_id == user_id)
        )
    
    if relationship_type:
        query = query.filter(UserRelationship.relationship_type == relationship_type)
    
    return query.all()


def delete_user_relationship(
    session: Session,
    from_user_id: UUID,
    to_user_id: UUID,
    relationship_type: str
) -> bool:
    """Delete a user relationship."""
    relationship = session.query(UserRelationship).filter(
        and_(
            UserRelationship.from_user_id == from_user_id,
            UserRelationship.to_user_id == to_user_id,
            UserRelationship.relationship_type == relationship_type
        )
    ).first()
    if not relationship:
        return False
    
    session.delete(relationship)
    session.commit()
    return True


# Convenience functions for backward compatibility
def create_parent_child_relationship(
    session: Session,
    parent_id: UUID,
    child_id: UUID,
    relationship_type: str = 'parent_child'
) -> UserRelationship:
    """Create a parent-child relationship (convenience wrapper)."""
    return create_user_relationship(
        session=session,
        from_user_id=parent_id,
        to_user_id=child_id,
        relationship_type=relationship_type,
        status='active'
    )


def delete_parent_child_relationship(
    session: Session,
    parent_id: UUID,
    child_id: UUID
) -> bool:
    """Delete a parent-child relationship (convenience wrapper)."""
    return delete_user_relationship(
        session=session,
        from_user_id=parent_id,
        to_user_id=child_id,
        relationship_type='parent_child'
    )


# ========== Child Account Creation ==========

def _age_to_age_group(age: int) -> str:
    """
    Convert age to age_group format.
    
    Age groups: '1', '2', '3', ..., '19' (simple format for now)
    Future: Could use ranges like '3-5', '6-8', '9-12', etc.
    
    Args:
        age: Child's age (1-19)
    
    Returns:
        Age group string (e.g., '8' for age 8)
    
    Raises:
        ValueError: If age is out of valid range
    """
    if age < 1 or age >= 20:
        raise ValueError(f"Invalid age for age_group conversion: {age}")
    return str(age)


def create_child_account(
    session: Session,
    parent_id: UUID,
    child_name: str,
    child_age: int,
    create_auth_account: bool = False
) -> Tuple[User, Optional[str]]:
    """
    Create a child account with placeholder email.
    
    Args:
        session: Database session
        parent_id: UUID of parent user
        child_name: Name of the child
        child_age: Age of the child (must be < 20)
        create_auth_account: If True, also create Supabase Auth account (not implemented yet)
    
    Returns:
        Tuple of (child_user, password) - password is None if create_auth_account=False
    
    Raises:
        ValueError: If child_age >= 20 or parent doesn't exist
    """
    if child_age >= 20:
        raise ValueError("Child must be under 20 years old (Taiwan age of majority)")
    
    # Verify parent exists
    parent = get_user_by_id(session, parent_id)
    if not parent:
        raise ValueError("Parent user not found")
    
    # Generate unique placeholder email
    import uuid as uuid_lib
    child_uuid = uuid_lib.uuid4()
    placeholder_email = f"child-{child_uuid}@lexicraft.xyz"
    
    # Ensure email is unique (should be, but check anyway)
    while get_user_by_email(session, placeholder_email):
        child_uuid = uuid_lib.uuid4()
        placeholder_email = f"child-{child_uuid}@lexicraft.xyz"
    
    # Create child user (no commit - caller handles transaction)
    child_user = create_user_no_commit(
        session=session,
        email=placeholder_email,
        name=child_name,
        age=child_age,
        country=parent.country  # Inherit parent's country
    )
    
    # Assign 'learner' role (no commit - caller handles transaction)
    add_user_role_no_commit(session, child_user.id, 'learner')
    
    # Create parent-child relationship (no commit - caller handles transaction)
    create_user_relationship_no_commit(
        session=session,
        from_user_id=parent_id,
        to_user_id=child_user.id,
        relationship_type='parent_child',
        status='active'
    )
    
    # Create corresponding Learner profile
    # This ensures the child appears in PlayerSwitcher and can be switched to
    age_group = _age_to_age_group(child_age)
    
    # Insert into learners table
    result = session.execute(
        text("""
            INSERT INTO public.learners (
                guardian_id,
                display_name,
                avatar_emoji,
                age_group,
                is_parent_profile,
                is_independent,
                user_id
            )
            VALUES (
                :guardian_id,
                :display_name,
                :avatar_emoji,
                :age_group,
                false,
                false,
                NULL
            )
            RETURNING id
        """),
        {
            'guardian_id': parent_id,  # Parent's auth.users.id
            'display_name': child_name,
            'avatar_emoji': '👧',  # Default child emoji
            'age_group': age_group
        }
    )
    
    learner_id = result.fetchone()[0]
    # CRITICAL: This function does NOT commit - caller must handle transaction
    # All operations (user, role, relationship, learner profile) are in the same transaction
    # Caller must: flush -> verify -> commit (or rollback on error)
    
    # Option B: Create Supabase Auth account (not implemented yet)
    password = None
    if create_auth_account:
        # TODO: Integrate with Supabase Auth API
        # This would require:
        # 1. Supabase Admin API client
        # 2. Create auth user with placeholder email
        # 3. Generate random password
        # 4. Return password for parent to share with child
        pass
    
    return child_user, password


def backfill_learner_profiles_for_children(
    session: Session,
    parent_id: UUID
) -> int:
    """
    Backfill Learner profiles for existing children that don't have them.
    
    This is a migration function to sync old system (User + Relationship) 
    with new system (Learner profiles).
    
    Args:
        session: Database session
        parent_id: UUID of parent user
    
    Returns:
        Number of learner profiles created
    """
    # Get all children for this parent
    children = get_user_children(session, parent_id)
    
    if not children:
        return 0
    
    created_count = 0
    
    for child in children:
        # Check if this child already has a learner profile
        # We check by guardian_id and display_name since user_id is NULL for children
        existing_learner = session.execute(
            text("""
                SELECT id FROM public.learners
                WHERE guardian_id = :guardian_id
                AND display_name = :display_name
                AND is_parent_profile = false
                AND user_id IS NULL
            """),
            {
                'guardian_id': parent_id,
                'display_name': child.name or f"Child {child.id}"
            }
        ).fetchone()
        
        if existing_learner:
            # Already has a learner profile, skip
            continue
        
        # Create learner profile for this child
        try:
            age_group = _age_to_age_group(child.age) if child.age else '8'  # Default to 8 if age missing
            
            session.execute(
                text("""
                    INSERT INTO public.learners (
                        guardian_id,
                        display_name,
                        avatar_emoji,
                        age_group,
                        is_parent_profile,
                        is_independent,
                        user_id
                    )
                    VALUES (
                        :guardian_id,
                        :display_name,
                        :avatar_emoji,
                        :age_group,
                        false,
                        false,
                        NULL
                    )
                """),
                {
                    'guardian_id': parent_id,
                    'display_name': child.name or f"Child {child.id}",
                    'avatar_emoji': '👧',  # Default child emoji
                    'age_group': age_group
                }
            )
            created_count += 1
        except Exception as e:
            # Log error but continue with other children
            print(f"Warning: Failed to create learner profile for child {child.id}: {e}")
            continue
    
    # Note: Don't commit here - let the caller handle transaction
    return created_count

