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
from ..middleware.auth import get_current_user_id, get_current_user_id_and_email

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


def get_or_create_user_with_session(
    auth_info: tuple,
    db: Session
):
    """Get or create user using the provided session."""
    import logging
    logger = logging.getLogger(__name__)
    
    user_id, email, name = auth_info
    from uuid import UUID
    from sqlalchemy import text
    user_uuid = UUID(user_id) if isinstance(user_id, str) else user_id
    
    # CRITICAL: Always prioritize the auth user_id over email matches
    # The auth user_id is the source of truth - we must create/use that ID
    user = user_crud.get_user_by_id(db, user_uuid)
    
    # If user with auth ID doesn't exist, we MUST create it
    # Handle email conflicts by deleting old user with same email but different ID
    if not user:
        logger.info(f"User {user_uuid} not found. Creating with email {email}")
        try:
            # Check if email conflict exists (user with same email but different ID)
            email_conflict = user_crud.get_user_by_email(db, email)
            if email_conflict and email_conflict.id != user_uuid:
                logger.warning(f"⚠️ Email {email} exists with different ID {email_conflict.id}. Deleting old user to fix inconsistency.")
                # Delete the old user to resolve the email conflict
                # This ensures data consistency - auth.users.id is the source of truth
                try:
                    db.execute(
                        text("DELETE FROM public.users WHERE id = :old_id"),
                        {'old_id': email_conflict.id}
                    )
                    db.commit()
                    logger.info(f"✅ Deleted old user {email_conflict.id} to resolve email conflict")
                except Exception as del_err:
                    logger.error(f"Failed to delete old user: {del_err}", exc_info=True)
                    db.rollback()
            
            # Create user with the specific ID from auth system
            # Use raw SQL with ON CONFLICT to handle race conditions
            try:
                db.execute(
                    text("""
                        INSERT INTO public.users (id, email, name, country, created_at, updated_at)
                        VALUES (:id, :email, :name, :country, NOW(), NOW())
                        ON CONFLICT (id) DO UPDATE
                        SET email = EXCLUDED.email,
                            name = COALESCE(EXCLUDED.name, users.name),
                            updated_at = NOW()
                    """),
                    {
                        'id': user_uuid,
                        'email': email,
                        'name': name or 'User',
                        'country': 'TW'
                    }
                )
                db.commit()
                logger.info(f"✅ Created/updated user {user_uuid} with email {email} using raw SQL")
            except Exception as sql_err:
                logger.error(f"Failed to create user with raw SQL: {sql_err}", exc_info=True)
                db.rollback()
                # Fallback to ORM method
                from ..database.models import User
                new_user = User(
                    id=user_uuid,
                    email=email,
                    name=name,
                    country='TW'
                )
                db.add(new_user)
                db.commit()
                db.refresh(new_user)
                logger.info(f"✅ Created user {user_uuid} using ORM fallback")
            
            # Verify user was created successfully
            verify_user = user_crud.get_user_by_id(db, user_uuid)
            if not verify_user:
                # Force a fresh query by committing and trying again
                db.commit()
                verify_user = user_crud.get_user_by_id(db, user_uuid)
                if not verify_user:
                    raise Exception(f"User {user_uuid} was not found in database after creation. This is a critical error.")
            
            logger.info(f"✅ Verified user {user_uuid} exists in database")
            return verify_user
        except Exception as e:
            logger.error(f"Failed to auto-create user: {e}", exc_info=True)
            db.rollback()
            # Try one more time to get user (in case it was created by another process)
            user = user_crud.get_user_by_id(db, user_id)
            if user:
                logger.info(f"User {user_id} found after rollback (created by another process)")
                return user
            raise HTTPException(status_code=500, detail=f"Failed to create user: {str(e)}")
    
    if not user:
        raise HTTPException(
            status_code=404, 
            detail=f"User {user_id} not found and could not be created. Please ensure you are authenticated."
        )
    
    return user


@router.post("/onboarding/complete", response_model=OnboardingCompleteResponse)
async def complete_onboarding(
    data: OnboardingCompleteRequest,
    auth_info: tuple = Depends(get_current_user_id_and_email),
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
        auth_info: Auth info from JWT token
        db: Database session
    
    Returns:
        Onboarding completion response with user info and redirect path
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        # Get or create user using the SAME session for all operations
        current_user = get_or_create_user_with_session(auth_info, db)
        parent_uuid = current_user.id
        parent_user = current_user
        
        # CRITICAL: Ensure user is committed and verify it exists in database
        # Flush any pending changes and refresh to ensure we have the latest state
        db.flush()
        db.refresh(current_user)
        
        # Explicitly commit the user creation to ensure it's persisted
        # This is critical to prevent foreign key violations when creating learner profiles
        try:
            db.commit()
            logger.info(f"✅ Committed user {parent_uuid} to database")
        except Exception as commit_err:
            # If commit fails, rollback and try again
            logger.warning(f"⚠️ Initial commit failed for user {parent_uuid}: {commit_err}. Retrying...")
            db.rollback()
            # Re-fetch user to ensure we have the latest state
            current_user = get_or_create_user_with_session(auth_info, db)
            parent_uuid = current_user.id
            parent_user = current_user
            db.commit()
        
        # Double-check user exists in database before proceeding
        # This prevents foreign key constraint violations
        verify_user = user_crud.get_user_by_id(db, parent_uuid)
        if not verify_user:
            logger.error(f"User {parent_uuid} not found after commit")
            raise HTTPException(
                status_code=500,
                detail=f"User {parent_uuid} was not found in database after creation. Please try again or contact support."
            )
            
        logger.info(f"✅ User {parent_uuid} verified in database. Proceeding with onboarding for account_type={data.account_type}")
        
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
                
                try:
                    child_user, _ = user_crud.create_child_account(
                        session=db,
                        parent_id=parent_uuid,
                        child_name=data.child_name,
                        child_age=data.child_age,
                        create_auth_account=False  # Option A: no auth account (placeholder email)
                    )
                    
                    # CRITICAL: Flush to send data to DB transaction buffer and check constraints
                    db.flush()
                    
                    # CRITICAL: Verify child learner profile was created BEFORE committing
                    from sqlalchemy import text
                    learner_check = db.execute(
                        text("""
                            SELECT id, display_name FROM public.learners
                            WHERE guardian_id = :guardian_id
                            AND display_name = :display_name
                            AND is_parent_profile = false
                        """),
                        {
                            'guardian_id': parent_uuid,
                            'display_name': data.child_name
                        }
                    ).fetchone()
                    
                    if not learner_check:
                        # Verification failed - rollback and raise error
                        logger.error(f"❌ Child learner profile NOT found after creation! Child: {child_user.id}, Name: {data.child_name}")
                        db.rollback()
                        raise HTTPException(
                            status_code=500,
                            detail=f"Failed to create child learner profile. Child user was created but learner profile is missing. Please contact support."
                        )
                    
                    # Verification passed - now commit the transaction
                    db.commit()
                    logger.info(f"✅ Created child account {child_user.id} with learner profile {learner_check[0]} for parent {parent_uuid}")
                except Exception as child_err:
                    logger.error(f"❌ Failed to create child account: {child_err}", exc_info=True)
                    db.rollback()
                    raise HTTPException(
                        status_code=500,
                        detail=f"Failed to create child account: {str(child_err)}"
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
            
            # Create learner profile for self-learner (is_parent_profile=false, but user_id set)
            from sqlalchemy import text
            from ..database.postgres_crud.users import _age_to_age_group
            
            # Check if learner profile already exists
            existing_profile = db.execute(
                text("""
                    SELECT id FROM public.learners
                    WHERE user_id = :user_id
                """),
                {'user_id': parent_uuid}
            ).fetchone()
            
            if not existing_profile:
                # CRITICAL: Verify user exists before creating learner profile
                verify_user = user_crud.get_user_by_id(db, parent_uuid)
                if not verify_user:
                    raise HTTPException(
                        status_code=500,
                        detail=f"User {parent_uuid} not found. Cannot create learner profile."
                    )
                
                # Create learner profile
                # For learners >= 20, use age as string directly (age_group accepts any string)
                try:
                    age_group = _age_to_age_group(data.learner_age)
                except ValueError:
                    # Age >= 20, use age as string
                    age_group = str(data.learner_age)
                try:
                    result = db.execute(
                        text("""
                            INSERT INTO public.learners (
                                guardian_id,
                                user_id,
                                display_name,
                                avatar_emoji,
                                age_group,
                                is_parent_profile,
                                is_independent,
                                settings
                            )
                            VALUES (
                                :guardian_id,
                                :user_id,
                                :display_name,
                                :avatar_emoji,
                                :age_group,
                                false,
                                true,
                                '{}'::jsonb
                            )
                            RETURNING id
                        """),
                        {
                            'guardian_id': parent_uuid,  # Self-guardian for independent learners
                            'user_id': parent_uuid,
                            'display_name': parent_user.name or 'Learner',
                            'avatar_emoji': '👤',
                            'age_group': age_group
                        }
                    )
                    db.commit()
                except Exception as e:
                    db.rollback()
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f"Failed to create learner profile: {e}", exc_info=True)
                    raise HTTPException(
                        status_code=500,
                        detail=f"Failed to create learner profile: {str(e)}"
                    )
        
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
            
            # Create parent's own learner profile (is_parent_profile=true)
            # This allows parent to switch to learner view and use learner endpoints
            from sqlalchemy import text
            from ..database.postgres_crud.users import _age_to_age_group
            
            # Check if parent learner profile already exists
            existing_profile = db.execute(
                text("""
                    SELECT id FROM public.learners
                    WHERE user_id = :user_id AND is_parent_profile = true
                """),
                {'user_id': parent_uuid}
            ).fetchone()
            
            if not existing_profile:
                # CRITICAL: Verify user exists before creating learner profile
                # Ensure any pending changes are committed first
                db.flush()
                verify_user = user_crud.get_user_by_id(db, parent_uuid)
                if not verify_user:
                    # Try committing and checking again
                    db.commit()
                    verify_user = user_crud.get_user_by_id(db, parent_uuid)
                    if not verify_user:
                        logger.error(f"User {parent_uuid} not found even after commit. Cannot create learner profile.")
                        raise HTTPException(
                            status_code=500,
                            detail=f"User {parent_uuid} not found in database. Cannot create learner profile. Please try again or contact support."
                        )
                
                logger.info(f"✅ Verified user {parent_uuid} exists before creating learner profile")
                
                # Create parent's learner profile
                # For parents >= 20, use age as string directly (age_group accepts any string)
                try:
                    age_group = _age_to_age_group(data.parent_age)
                except ValueError:
                    # Age >= 20, use age as string
                    age_group = str(data.parent_age)
                try:
                    result = db.execute(
                        text("""
                            INSERT INTO public.learners (
                                guardian_id,
                                user_id,
                                display_name,
                                avatar_emoji,
                                age_group,
                                is_parent_profile,
                                is_independent,
                                settings
                            )
                            VALUES (
                                :guardian_id,
                                :user_id,
                                :display_name,
                                :avatar_emoji,
                                :age_group,
                                true,
                                true,
                                '{}'::jsonb
                            )
                            RETURNING id
                        """),
                        {
                            'guardian_id': parent_uuid,
                            'user_id': parent_uuid,
                            'display_name': parent_user.name or 'Parent',
                            'avatar_emoji': '👨',  # Default, can be customized later
                            'age_group': age_group
                        }
                    )
                    db.commit()
                except Exception as e:
                    db.rollback()
                    logger.error(f"Failed to create learner profile: {e}", exc_info=True)
                    raise HTTPException(
                        status_code=500,
                        detail=f"Failed to create learner profile: {str(e)}"
                    )
            
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
                
                try:
                    child_user, _ = user_crud.create_child_account(
                        session=db,
                        parent_id=parent_uuid,
                        child_name=data.child_name,
                        child_age=data.child_age,
                        create_auth_account=False
                    )
                    
                    # CRITICAL: Flush to send data to DB transaction buffer and check constraints
                    db.flush()
                    
                    # CRITICAL: Verify child learner profile was created BEFORE committing
                    from sqlalchemy import text
                    learner_check = db.execute(
                        text("""
                            SELECT id, display_name FROM public.learners
                            WHERE guardian_id = :guardian_id
                            AND display_name = :display_name
                            AND is_parent_profile = false
                        """),
                        {
                            'guardian_id': parent_uuid,
                            'display_name': data.child_name
                        }
                    ).fetchone()
                    
                    if not learner_check:
                        # Verification failed - rollback and raise error
                        logger.error(f"❌ Child learner profile NOT found after creation! Child: {child_user.id}, Name: {data.child_name}")
                        db.rollback()
                        raise HTTPException(
                            status_code=500,
                            detail=f"Failed to create child learner profile. Child user was created but learner profile is missing. Please contact support."
                        )
                    
                    # Verification passed - now commit the transaction
                    db.commit()
                    logger.info(f"✅ Created child account {child_user.id} with learner profile {learner_check[0]} for parent {parent_uuid}")
                except Exception as child_err:
                    logger.error(f"❌ Failed to create child account: {child_err}", exc_info=True)
                    db.rollback()
                    raise HTTPException(
                        status_code=500,
                        detail=f"Failed to create child account: {str(child_err)}"
                    )
        
        else:
            raise HTTPException(
                status_code=400,
                detail="Invalid account_type. Must be 'parent', 'learner', or 'both'"
            )
        
        # Get final roles
        roles = user_crud.get_user_roles(db, parent_uuid)
        
        logger.info(f"✅ Onboarding completed successfully for user {parent_uuid} with roles: {roles}")
        
        # Return response
        return OnboardingCompleteResponse(
            success=True,
            user_id=str(parent_uuid),
            roles=roles,
            child_id=str(child_user.id) if child_user else None,
            redirect_to="/dashboard"
        )
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        # Log unexpected errors and provide helpful error message
        logger.error(f"Unexpected error during onboarding: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred during onboarding: {str(e)}. Please try again or contact support."
        )
    finally:
        db.close()


@router.get("/onboarding/status")
async def get_onboarding_status(
    auth_info: tuple = Depends(get_current_user_id_and_email),
    db: Session = Depends(get_db_session)
):
    """
    Check if user has completed onboarding.
    
    Returns:
        - completed: bool
        - roles: list of roles
        - missing_info: list of missing information
    """
    # Get or create user using the SAME session
    current_user = get_or_create_user_with_session(auth_info, db)
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

