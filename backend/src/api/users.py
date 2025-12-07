"""
User API Endpoints

Endpoints for user management and relationships.
"""

from fastapi import APIRouter, HTTPException, Depends, Query, Header
from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import text

from ..database.postgres_connection import PostgresConnection
from ..database.postgres_crud import users as user_crud
from ..middleware.auth import get_current_user_id, get_or_create_user

router = APIRouter(prefix="/api/users", tags=["Users"])


class UserInfo(BaseModel):
    """User information response."""
    id: str
    email: str
    name: Optional[str]
    age: Optional[int]
    roles: List[str]
    email_confirmed: bool


class ChildInfo(BaseModel):
    """Child/learner information."""
    id: str
    name: Optional[str]
    age: Optional[int]
    email: str  # Placeholder email for children


class CreateChildRequest(BaseModel):
    """Request to create a child account."""
    name: str = Field(..., description="Child's name")
    age: int = Field(..., description="Child's age (must be < 20)")


class CreateChildResponse(BaseModel):
    """Response after creating a child."""
    success: bool
    child_id: str
    child_name: str
    message: str


class UpdateProfileRequest(BaseModel):
    """Request to update user profile."""
    name: Optional[str] = Field(None, description="User's display name")
    age: Optional[int] = Field(None, description="User's age")


class UpdateChildRequest(BaseModel):
    """Request to update child info."""
    name: Optional[str] = Field(None, description="Child's name")
    age: Optional[int] = Field(None, description="Child's age (must be < 20)")


class AddRoleRequest(BaseModel):
    """Request to add a role."""
    role: str = Field(..., description="Role to add: 'parent' or 'learner'")


def get_db_session():
    """Get database session."""
    conn = PostgresConnection()
    return conn.get_session()


@router.get("/me", response_model=UserInfo)
async def get_me(
    current_user = Depends(get_or_create_user),  # Auto-creates user if not exists
    db: Session = Depends(get_db_session)
):
    """
    Get current user information.
    Auto-creates user record if they authenticated via Supabase but don't exist in DB.
    """
    try:
        user = current_user
        roles = user_crud.get_user_roles(db, user.id)
        
        return UserInfo(
            id=str(user.id),
            email=user.email,
            name=user.name,
            age=user.age,
            roles=roles,
            email_confirmed=user.email_confirmed
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get user: {str(e)}")
    finally:
        db.close()


@router.put("/me", response_model=UserInfo)
async def update_profile(
    data: UpdateProfileRequest,
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db_session)
):
    """
    Update current user's profile.
    
    Editable fields:
    - name: Can be changed freely
    - age: Can increase, but cannot decrease below 20 if user has parent role
    """
    try:
        user = user_crud.get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        roles = user_crud.get_user_roles(db, user_id)
        
        # Validate age change
        if data.age is not None:
            # Cannot set age below 20 if user is a parent
            if 'parent' in roles and data.age < 20:
                raise HTTPException(
                    status_code=400,
                    detail="Parents must be at least 20 years old"
                )
            # Cannot decrease age below current if already set (prevent gaming)
            if user.age is not None and data.age < user.age:
                raise HTTPException(
                    status_code=400,
                    detail="Age cannot be decreased"
                )
        
        # Build update kwargs
        update_kwargs = {}
        if data.name is not None:
            update_kwargs['name'] = data.name
        if data.age is not None:
            update_kwargs['age'] = data.age
        
        if update_kwargs:
            user_crud.update_user(db, user_id, **update_kwargs)
            user = user_crud.get_user_by_id(db, user_id)  # Refresh
        
        return UserInfo(
            id=str(user.id),
            email=user.email,
            name=user.name,
            age=user.age,
            roles=roles,
            email_confirmed=user.email_confirmed
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update profile: {str(e)}")
    finally:
        db.close()


@router.post("/me/roles")
async def add_role(
    data: AddRoleRequest,
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db_session)
):
    """
    Add a role to current user.
    
    Valid roles: 'parent', 'learner'
    """
    try:
        if data.role not in ['parent', 'learner']:
            raise HTTPException(
                status_code=400,
                detail="Invalid role. Must be 'parent' or 'learner'"
            )
        
        user = user_crud.get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Check age requirements
        if data.role == 'parent' and user.age is not None and user.age < 20:
            raise HTTPException(
                status_code=400,
                detail="Must be at least 20 years old to be a parent"
            )
        
        if not user_crud.user_has_role(db, user_id, data.role):
            user_crud.add_user_role(db, user_id, data.role)
        
        roles = user_crud.get_user_roles(db, user_id)
        
        return {
            "success": True,
            "roles": roles,
            "message": f"Role '{data.role}' added successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add role: {str(e)}")
    finally:
        db.close()


@router.get("/me/children", response_model=List[ChildInfo])
async def get_my_children(
    user_id: UUID = Depends(get_current_user_id),  # Get from auth middleware
    db: Session = Depends(get_db_session)
):
    """
    Get all children for the current user (parent).
    
    Returns list of children with their information.
    """
    try:
        # Verify user is a parent
        if not user_crud.user_has_role(db, user_id, 'parent'):
            raise HTTPException(
                status_code=403,
                detail="You must be a parent to view children"
            )
        
        # Get children via relationships
        children = user_crud.get_user_children(db, user_id)
        
        return [
            ChildInfo(
                id=str(child.id),
                name=child.name,
                age=child.age,
                email=child.email
            )
            for child in children
        ]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get children: {str(e)}")
    finally:
        db.close()


@router.get("/debug/token")
async def debug_token(
    authorization: Optional[str] = Header(None)
):
    """
    Debug endpoint to check token extraction and verification.
    This endpoint helps diagnose authentication issues.
    """
    from ..middleware.auth import extract_token_from_header, verify_supabase_token
    
    try:
        if not authorization:
            return {
                "error": "No Authorization header",
                "status": "missing_header"
            }
        
        token = extract_token_from_header(authorization)
        payload = verify_supabase_token(token)
        
        return {
            "status": "success",
            "token_length": len(token),
            "user_id": payload.get("sub"),
            "email": payload.get("email"),
            "payload_keys": list(payload.keys())
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "error_type": type(e).__name__
        }


@router.put("/children/{child_id}", response_model=ChildInfo)
async def update_child(
    child_id: str,
    data: UpdateChildRequest,
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db_session)
):
    """
    Update a child's information.
    
    Only the parent can update their child's info.
    """
    try:
        child_uuid = UUID(child_id)
        
        # Verify user is parent of this child
        if not user_crud.is_parent_of(db, user_id, child_uuid):
            raise HTTPException(
                status_code=403,
                detail="You can only update your own children"
            )
        
        child = user_crud.get_user_by_id(db, child_uuid)
        if not child:
            raise HTTPException(status_code=404, detail="Child not found")
        
        # Validate age
        if data.age is not None:
            if data.age >= 20:
                raise HTTPException(
                    status_code=400,
                    detail="Child must be under 20 years old"
                )
            if data.age < 1:
                raise HTTPException(
                    status_code=400,
                    detail="Age must be at least 1"
                )
        
        # Build update kwargs
        update_kwargs = {}
        if data.name is not None:
            update_kwargs['name'] = data.name
        if data.age is not None:
            update_kwargs['age'] = data.age
        
        if update_kwargs:
            user_crud.update_user(db, child_uuid, **update_kwargs)
            child = user_crud.get_user_by_id(db, child_uuid)  # Refresh
        
        return ChildInfo(
            id=str(child.id),
            name=child.name,
            age=child.age,
            email=child.email
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid child ID format")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update child: {str(e)}")
    finally:
        db.close()


@router.post("/children", response_model=CreateChildResponse)
async def create_child(
    data: CreateChildRequest,
    user_id: UUID = Depends(get_current_user_id),  # Get from auth middleware
    db: Session = Depends(get_db_session)
):
    """
    Create a child account for the current user (parent).
    
    Requires parent role. Creates child with placeholder email.
    """
    try:
        # Verify user is a parent
        if not user_crud.user_has_role(db, user_id, 'parent'):
            # Auto-assign parent role if user doesn't have it
            user_crud.add_user_role(db, user_id, 'parent')
        
        # Validate age
        if data.age >= 20:
            raise HTTPException(
                status_code=400,
                detail="Child must be under 20 years old"
            )
        
        # Create child account
        child_user, _ = user_crud.create_child_account(
            session=db,
            parent_id=user_id,
            child_name=data.name,
            child_age=data.age,
            create_auth_account=False
        )
        
        return CreateChildResponse(
            success=True,
            child_id=str(child_user.id),
            child_name=child_user.name or data.name,
            message="Child account created successfully"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create child: {str(e)}")
    finally:
        db.close()


@router.get("/{user_id}", response_model=UserInfo)
async def get_user(
    user_id: str,
    db: Session = Depends(get_db_session)
):
    """
    Get user information by ID.
    """
    try:
        user_uuid = UUID(user_id)
        user = user_crud.get_user_by_id(db, user_uuid)
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        roles = user_crud.get_user_roles(db, user_uuid)
        
        return UserInfo(
            id=str(user.id),
            email=user.email,
            name=user.name,
            age=user.age,
            roles=roles,
            email_confirmed=user.email_confirmed
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID format")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get user: {str(e)}")
    finally:
        db.close()

