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


class LearnerProfile(BaseModel):
    """Learner profile from learners table."""
    id: str  # learner.id (UUID)
    user_id: Optional[str]  # auth.users.id (NULL for children without accounts)
    guardian_id: str  # Parent's auth.users.id
    display_name: str
    avatar_emoji: str
    age_group: Optional[str]
    is_parent_profile: bool
    is_independent: bool
    settings: dict


class CreateChildRequest(BaseModel):
    """Request to create a child account."""
    name: str = Field(..., description="Child's name")
    age: int = Field(..., description="Child's age (must be < 20)")


class CreateLearnerRequest(BaseModel):
    """Request to create a learner profile (for multi-profile system)."""
    display_name: str = Field(..., description="Learner's display name")
    avatar_emoji: str = Field(..., description="Avatar emoji (e.g., 🦄)")
    age_group: Optional[str] = Field(None, description="Age group (e.g., '3-5', '6-8', '9+')")


class CreateLearnerResponse(BaseModel):
    """Response after creating a learner profile."""
    success: bool
    learner_id: str
    display_name: str
    avatar_emoji: str
    message: str


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


class SetBirthdayRequest(BaseModel):
    """Request to set birthday (for birthday celebrations)."""
    month: int = Field(..., ge=1, le=12, description="Birth month (1-12)")
    day: int = Field(..., ge=1, le=31, description="Birth day (1-31)")


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


@router.get("/me/birthday")
async def get_birthday(
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db_session)
):
    """
    Get current user's birthday info.
    """
    try:
        user = user_crud.get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        has_birthday = user.birth_month is not None and user.birth_day is not None
        edits_remaining = 3 - (user.birthday_edit_count or 0)
        
        return {
            "has_birthday": has_birthday,
            "birth_month": user.birth_month,
            "birth_day": user.birth_day,
            "edits_remaining": max(0, edits_remaining),
            "can_edit": edits_remaining > 0
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get birthday: {str(e)}")
    finally:
        db.close()


@router.put("/me/birthday")
async def set_birthday(
    data: SetBirthdayRequest,
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db_session)
):
    """
    Set or update birthday (for birthday celebrations).
    
    🎂 Add your birthday for a special surprise on your special day!
    
    Note: You can only edit this 3 times, so choose carefully!
    """
    try:
        user = user_crud.get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Check edit limit
        current_edits = user.birthday_edit_count or 0
        if current_edits >= 3:
            raise HTTPException(
                status_code=400,
                detail="You've used all 3 birthday edits! Contact support if you made a mistake. 😅"
            )
        
        # Validate day for the month (basic validation)
        days_in_month = {
            1: 31, 2: 29, 3: 31, 4: 30, 5: 31, 6: 30,
            7: 31, 8: 31, 9: 30, 10: 31, 11: 30, 12: 31
        }
        if data.day > days_in_month.get(data.month, 31):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid day {data.day} for month {data.month}"
            )
        
        # Update birthday
        user.birth_month = data.month
        user.birth_day = data.day
        user.birthday_edit_count = current_edits + 1
        db.commit()
        
        edits_remaining = 3 - user.birthday_edit_count
        
        # Fun messages based on edits remaining
        if edits_remaining == 2:
            message = "🎂 Birthday set! You have 2 edits remaining."
        elif edits_remaining == 1:
            message = "🎂 Birthday updated! ⚠️ Only 1 edit left - make it count!"
        else:
            message = "🎂 Birthday updated! That was your last edit - hope it's correct! 🎉"
        
        return {
            "success": True,
            "birth_month": data.month,
            "birth_day": data.day,
            "edits_remaining": edits_remaining,
            "message": message
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to set birthday: {str(e)}")
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


@router.post("/me/learners", response_model=CreateLearnerResponse)
async def create_learner(
    data: CreateLearnerRequest,
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db_session)
):
    """
    Create a new learner profile for the current user (parent).
    
    Creates a learner profile in the learners table. This is for the multi-profile system
    where children don't need their own auth accounts - they're managed by the parent.
    
    The learner profile will be linked to the parent via guardian_id.
    """
    try:
        # Insert into learners table
        result = db.execute(
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
                'guardian_id': user_id,
                'display_name': data.display_name,
                'avatar_emoji': data.avatar_emoji,
                'age_group': data.age_group
            }
        )
        
        learner_id = result.fetchone()[0]
        db.commit()
        
        return CreateLearnerResponse(
            success=True,
            learner_id=str(learner_id),
            display_name=data.display_name,
            avatar_emoji=data.avatar_emoji,
            message="Learner profile created successfully"
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create learner: {str(e)}")
    finally:
        db.close()


@router.get("/me/learners", response_model=List[LearnerProfile])
async def get_my_learners(
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db_session)
):
    """
    Get all learner profiles managed by the current user (parent).
    
    Returns list of learners including:
    - Parent's own learner profile (is_parent_profile=true)
    - All children's learner profiles (is_parent_profile=false)
    
    This is the new multi-profile system that enables parent-child switching.
    """
    try:
        # Query learners table for all profiles where user is guardian
        result = db.execute(
            text("""
                SELECT 
                    l.id,
                    l.user_id,
                    l.guardian_id,
                    l.display_name,
                    l.avatar_emoji,
                    l.age_group,
                    l.is_parent_profile,
                    l.is_independent,
                    l.settings
                FROM public.learners l
                WHERE l.guardian_id = :guardian_id
                ORDER BY l.is_parent_profile DESC, l.display_name ASC
            """),
            {"guardian_id": user_id}
        )
        
        learners = []
        for row in result:
            learners.append(LearnerProfile(
                id=str(row.id),
                user_id=str(row.user_id) if row.user_id else None,
                guardian_id=str(row.guardian_id),
                display_name=row.display_name,
                avatar_emoji=row.avatar_emoji or '🦄',
                age_group=row.age_group,
                is_parent_profile=row.is_parent_profile,
                is_independent=row.is_independent,
                settings=row.settings or {}
            ))
        
        return learners
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to get learners: {str(e)}")
    finally:
        db.close()


class ChildSummary(BaseModel):
    """Lightweight child summary for parent quick view."""
    id: str
    name: Optional[str]
    age: Optional[int]
    email: str
    # Summary stats
    level: int
    total_xp: int
    current_streak: int
    vocabulary_size: int
    words_learned_this_week: int
    last_active_date: Optional[str]


@router.get("/me/children/summary", response_model=List[ChildSummary])
async def get_children_summary(
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db_session)
):
    """
    Get lightweight summary of all children for quick parent view.
    
    Returns minimal data (level, streak, today's progress) for each child.
    Much faster than full CoachDashboard.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"📊 Getting children summary for user {user_id}")
        
        # Verify parent role
        if not user_crud.user_has_role(db, user_id, 'parent'):
            raise HTTPException(status_code=403, detail="Must be a parent")
        
        # Get children
        children = user_crud.get_user_children(db, user_id)
        logger.info(f"📊 Found {len(children)} children")
        summaries = []
        
        # Import services
        from ..services.levels import LevelService
        from ..services.learning_velocity import LearningVelocityService
        from ..services.vocabulary_size import VocabularySizeService
        
        for child in children:
            logger.info(f"📊 Processing child {child.id} ({child.name})")
            
            # Check if child user actually exists (handle orphaned relationships)
            user_exists = user_crud.get_user_by_id(db, child.id)
            if not user_exists:
                logger.warning(f"  ⚠️ Child {child.id} has no user record (orphaned relationship), skipping")
                continue
            
            try:
                # Get basic stats (lightweight queries)
                level_service = LevelService(db)
                level_info = level_service.get_level_info(child.id)
                logger.info(f"  ✅ Level: {level_info}")
                
                velocity_service = LearningVelocityService(db)
                activity = velocity_service.get_activity_summary(child.id)
                logger.info(f"  ✅ Activity: {activity}")
                
                vocab_service = VocabularySizeService(db)
                vocab = vocab_service.get_vocabulary_stats(child.id)
                logger.info(f"  ✅ Vocab: {vocab}")
                
                summaries.append(ChildSummary(
                    id=str(child.id),
                    name=child.name,
                    age=child.age,
                    email=child.email,
                    level=level_info['level'],
                    total_xp=level_info['total_xp'],
                    current_streak=activity['activity_streak_days'],
                    vocabulary_size=vocab['vocabulary_size'],
                    words_learned_this_week=activity.get('words_learned_this_week', 0),
                    last_active_date=activity.get('last_active_date')
                ))
                logger.info(f"  ✅ Added summary for {child.name}")
            except Exception as child_error:
                logger.error(f"  ❌ Failed to get stats for child {child.id}: {child_error}")
                import traceback
                traceback.print_exc()
                # Rollback the transaction to recover
                db.rollback()
                # Add child with default values (Level 1, no progress)
                summaries.append(ChildSummary(
                    id=str(child.id),
                    name=child.name,
                    age=child.age,
                    email=child.email,
                    level=1,
                    total_xp=0,
                    current_streak=0,
                    vocabulary_size=0,
                    words_learned_this_week=0,
                    last_active_date=None
                ))
                logger.info(f"  ⚠️ Added default summary for {child.name} (new learner with no progress yet)")
        
        logger.info(f"✅ Returning {len(summaries)} summaries")
        return summaries
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Children summary failed: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to get children summary: {str(e)}")
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


@router.post("/me/learners/backfill", response_model=dict)
async def backfill_learner_profiles(
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db_session)
):
    """
    Backfill Learner profiles for existing children that don't have them.
    
    This syncs old system (User + Relationship) with new system (Learner profiles).
    Only creates profiles for children that don't already have them.
    
    Returns:
        Number of learner profiles created
    """
    try:
        # Verify user is a parent
        if not user_crud.user_has_role(db, user_id, 'parent'):
            raise HTTPException(
                status_code=403,
                detail="You must be a parent to backfill learner profiles"
            )
        
        created_count = user_crud.backfill_learner_profiles_for_children(db, user_id)
        
        # Explicitly commit the transaction to ensure learners are visible immediately
        db.commit()
        
        return {
            "success": True,
            "created_count": created_count,
            "message": f"Created {created_count} learner profile(s) for existing children"
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to backfill learner profiles: {str(e)}")
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

