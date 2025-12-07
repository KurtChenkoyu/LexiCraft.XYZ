"""
Onboarding API endpoints for completing user setup after signup.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID

from ..database.postgres_connection import PostgresConnection
from ..database.postgres_crud import users as user_crud
from ..middleware.auth import get_current_user_id, get_or_create_user, get_db_session as auth_get_db_session

router = APIRouter(prefix="/api/users", tags=["onboarding"])


class OnboardingCompleteRequest(BaseModel):
    """Request model for completing onboarding."""
    account_type: str = Field(..., description="'parent', 'learner', or 'both'")
    parent_age: Optional[int] = Field(None, description="Age of parent (required if account_type is 'parent' or 'both')")
    child_name: Optional[str] = Field(None, description="Name of child (optional, for creating child account)")
    child_age: Optional[int] = Field(None, description="Age of child (required if child_name is provided)")
    learner_age: Optional[int] = Field(None, description="Age of learner (required if account_type is 'learner' or 'both')")
    cefr_level: Optional[str] = Field(None, description="CEFR level for initial survey (optional)")


class OnboardingCompleteResponse(BaseModel):
    """Response model for onboarding completion."""
    success: bool
    user_id: str
    roles: list[str]
    child_id: Optional[str] = None
    redirect_to: str = "/dashboard"


def get_db_session():
    """Get database session."""
    conn = PostgresConnection()
    return conn.get_session()


@router.post("/onboarding/complete", response_model=OnboardingCompleteResponse)
async def complete_onboarding(
    data: OnboardingCompleteRequest,
    current_user = Depends(get_or_create_user),  # Auto-creates user if not exists
    db: Session = Depends(get_db_session)
):
    """
    Complete user onboarding after signup.
    
    Handles:
    - Parent account setup
    - Child account creation (with placeholder email)
    - Role assignment
    - Parent-child relationship creation
    
    Args:
        data: Onboarding data
        current_user: User object (auto-created if not exists)
        db: Database session
    
    Returns:
        Onboarding completion response with user info and redirect path
    """
    parent_uuid = current_user.id
    parent_user = current_user
    
    child_user = None
    
    # Handle different account types
    if data.account_type == 'parent':
        # Parent account for managing child
        if not data.parent_age:
            raise HTTPException(status_code=400, detail="Parent age is required")
        
        if data.parent_age < 20:
            raise HTTPException(
                status_code=400,
                detail="Parent must be at least 20 years old (Taiwan age of majority)"
            )
        
        # Update parent info
        user_crud.update_user(db, parent_uuid, age=data.parent_age)
        
        # Add parent role if not already present
        if not user_crud.user_has_role(db, parent_uuid, 'parent'):
            user_crud.add_user_role(db, parent_uuid, 'parent')
        
        # Create child account if child info provided
        # IMPORTANT: Create child AFTER parent role is assigned
        if data.child_name and data.child_age:
            if data.child_age >= 20:
                raise HTTPException(
                    status_code=400,
                    detail="Child must be under 20 years old"
                )
            
            # Ensure parent role exists before creating child
            if not user_crud.user_has_role(db, parent_uuid, 'parent'):
                user_crud.add_user_role(db, parent_uuid, 'parent')
            
            child_user, _ = user_crud.create_child_account(
                session=db,
                parent_id=parent_uuid,
                child_name=data.child_name,
                child_age=data.child_age,
                create_auth_account=False  # Option A: no auth account (placeholder email)
            )
    
    elif data.account_type == 'learner':
        # Self-learner account
        if not data.learner_age:
            raise HTTPException(status_code=400, detail="Age is required")
        
        if data.learner_age < 20:
            raise HTTPException(
                status_code=400,
                detail="Users under 20 must have a parent account. Please sign up as a parent first."
            )
        
        # Update user info
        user_crud.update_user(db, parent_uuid, age=data.learner_age)
        
        # Role already set to 'learner' by trigger, but ensure it exists
        if not user_crud.user_has_role(db, parent_uuid, 'learner'):
            user_crud.add_user_role(db, parent_uuid, 'learner')
    
    elif data.account_type == 'both':
        # Parent who also wants to learn (same person, same age)
        if not data.parent_age:
            raise HTTPException(
                status_code=400,
                detail="Age is required"
            )
        
        # For "both", learner_age should be same as parent_age (same person)
        # But allow override if provided
        learner_age = data.learner_age if data.learner_age else data.parent_age
        
        if data.parent_age < 20:
            raise HTTPException(
                status_code=400,
                detail="Must be at least 20 years old"
            )
        
        # Update user info (same person for both roles)
        user_crud.update_user(db, parent_uuid, age=data.parent_age)
        
        # Add both roles
        if not user_crud.user_has_role(db, parent_uuid, 'parent'):
            user_crud.add_user_role(db, parent_uuid, 'parent')
        if not user_crud.user_has_role(db, parent_uuid, 'learner'):
            user_crud.add_user_role(db, parent_uuid, 'learner')
        
        # Create child account if provided
        # IMPORTANT: Create child AFTER parent role is assigned
        if data.child_name and data.child_age:
            if data.child_age >= 20:
                raise HTTPException(
                    status_code=400,
                    detail="Child must be under 20 years old"
                )
            
            # Ensure parent role exists before creating child
            if not user_crud.user_has_role(db, parent_uuid, 'parent'):
                user_crud.add_user_role(db, parent_uuid, 'parent')
            
            child_user, _ = user_crud.create_child_account(
                session=db,
                parent_id=parent_uuid,
                child_name=data.child_name,
                child_age=data.child_age,
                create_auth_account=False
            )
    
    else:
        raise HTTPException(
            status_code=400,
            detail="Invalid account_type. Must be 'parent', 'learner', or 'both'"
        )
    
    # Get final roles
    roles = user_crud.get_user_roles(db, parent_uuid)
    
    # Return response
    return OnboardingCompleteResponse(
        success=True,
        user_id=str(parent_uuid),
        roles=roles,
        child_id=str(child_user.id) if child_user else None,
        redirect_to="/dashboard"
    )


@router.get("/onboarding/status")
async def get_onboarding_status(
    current_user = Depends(get_or_create_user),  # Auto-creates user if not exists
    db: Session = Depends(get_db_session)
):
    """
    Check if user has completed onboarding.
    
    Returns:
        - completed: bool
        - roles: list of roles
        - missing_info: list of missing information
    """
    user_uuid = current_user.id
    user = current_user
    
    roles = user_crud.get_user_roles(db, user_uuid)
    missing_info = []
    
    # Check what's missing
    if not user.age:
        missing_info.append("age")
    if not roles:
        missing_info.append("role")
    
    return {
        "completed": len(missing_info) == 0,
        "roles": roles,
        "missing_info": missing_info,
        "has_age": user.age is not None
    }

