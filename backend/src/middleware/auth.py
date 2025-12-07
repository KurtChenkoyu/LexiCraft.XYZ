"""
Authentication middleware for FastAPI.

Extracts and verifies Supabase JWT tokens from Authorization header.
"""

import os
import jwt
from typing import Optional
from fastapi import HTTPException, Header, Depends
from uuid import UUID
from sqlalchemy.orm import Session

from src.database.postgres_connection import PostgresConnection
from src.database.postgres_crud import users as user_crud
from typing import Generator


# Supabase JWT configuration
SUPABASE_URL = os.getenv("SUPABASE_URL") or os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET")

# Fallback: If JWT_SECRET is not set, we'll try to get it from Supabase
# For now, we'll decode without verification if secret is not available
# In production, you should always set SUPABASE_JWT_SECRET


# Database session dependency
def get_db_session() -> Generator[Session, None, None]:
    """Get database session."""
    conn = PostgresConnection()
    db = conn.get_session()
    try:
        yield db
    finally:
        db.close()


def extract_token_from_header(authorization: Optional[str] = Header(None)) -> str:
    """
    Extract JWT token from Authorization header.
    
    Args:
        authorization: Authorization header value (e.g., "Bearer <token>")
    
    Returns:
        JWT token string
    
    Raises:
        HTTPException: If token is missing or invalid format
    """
    import logging
    logger = logging.getLogger(__name__)
    
    if not authorization:
        logger.warning("Missing Authorization header")
        raise HTTPException(
            status_code=401,
            detail="Missing Authorization header. Please provide a Bearer token."
        )
    
    # Check if it's a Bearer token
    if not authorization.startswith("Bearer "):
        logger.warning(f"Invalid Authorization header format: {authorization[:50]}...")
        raise HTTPException(
            status_code=401,
            detail="Invalid Authorization header format. Expected: 'Bearer <token>'"
        )
    
    # Extract token
    token = authorization.replace("Bearer ", "").strip()
    
    if not token:
        logger.warning("Empty token in Authorization header")
        raise HTTPException(
            status_code=401,
            detail="Empty token in Authorization header"
        )
    
    logger.debug(f"Token extracted (length: {len(token)})")
    return token


def verify_supabase_token(token: str) -> dict:
    """
    Verify Supabase JWT token and extract payload.
    
    Args:
        token: JWT token string
    
    Returns:
        Decoded token payload (dict with user info)
    
    Raises:
        HTTPException: If token is invalid or expired
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        # Decode token (without verification if secret not set)
        # In production, you should always verify with the secret
        if SUPABASE_JWT_SECRET:
            logger.info(f"Verifying token with secret (length: {len(SUPABASE_JWT_SECRET)})")
            # Verify token with secret
            # Supabase tokens have aud="authenticated", so we need to verify audience
            payload = jwt.decode(
                token,
                SUPABASE_JWT_SECRET,
                algorithms=["HS256"],
                options={"verify_signature": True},
                audience="authenticated"  # Supabase uses "authenticated" as audience
            )
            logger.info(f"Token verified successfully. User ID: {payload.get('sub')}")
        else:
            logger.warning("SUPABASE_JWT_SECRET not set. Decoding without verification.")
            # Decode without verification (for development only)
            # WARNING: This is insecure and should only be used in development
            payload = jwt.decode(
                token,
                options={"verify_signature": False}
            )
            logger.info(f"Token decoded (no verification). User ID: {payload.get('sub')}")
        
        return payload
    
    except jwt.ExpiredSignatureError:
        logger.error("Token has expired")
        raise HTTPException(
            status_code=401,
            detail="Token has expired. Please sign in again."
        )
    except jwt.InvalidTokenError as e:
        logger.error(f"Invalid token: {str(e)}")
        raise HTTPException(
            status_code=401,
            detail=f"Invalid token: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Token verification failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=401,
            detail=f"Token verification failed: {str(e)}"
        )


def get_current_user_id(
    authorization: Optional[str] = Header(None)
) -> UUID:
    """
    Get current authenticated user ID from JWT token.
    
    This is a FastAPI dependency that:
    1. Extracts JWT token from Authorization header
    2. Verifies token with Supabase
    3. Returns user_id from token
    
    Usage:
        @router.get("/me")
        async def get_me(user_id: UUID = Depends(get_current_user_id)):
            ...
    
    Args:
        authorization: Authorization header (automatically injected by FastAPI)
    
    Returns:
        UUID of authenticated user
    
    Raises:
        HTTPException: If authentication fails
    """
    # Extract token
    token = extract_token_from_header(authorization)
    
    # Verify token and get payload
    payload = verify_supabase_token(token)
    
    # Extract user_id from token
    # Supabase JWT tokens have 'sub' field with user ID
    user_id_str = payload.get("sub") or payload.get("user_id") or payload.get("id")
    
    if not user_id_str:
        raise HTTPException(
            status_code=401,
            detail="Token does not contain user ID"
        )
    
    # Convert to UUID
    try:
        user_id = UUID(user_id_str)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid user ID format in token: {user_id_str}"
        )
    
    return user_id


def get_current_user_id_and_email(
    authorization: Optional[str] = Header(None)
) -> tuple[UUID, Optional[str], Optional[str]]:
    """
    Get current authenticated user ID, email, and name from JWT token.
    
    Returns:
        Tuple of (user_id, email, name)
    """
    token = extract_token_from_header(authorization)
    payload = verify_supabase_token(token)
    
    user_id_str = payload.get("sub") or payload.get("user_id") or payload.get("id")
    if not user_id_str:
        raise HTTPException(status_code=401, detail="Token does not contain user ID")
    
    try:
        user_id = UUID(user_id_str)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid user ID format: {user_id_str}")
    
    # Extract email and name from token
    email = payload.get("email")
    user_metadata = payload.get("user_metadata", {})
    name = user_metadata.get("full_name") or user_metadata.get("name")
    
    return user_id, email, name


def get_or_create_user(
    auth_info: tuple = Depends(get_current_user_id_and_email),
    db: Session = Depends(get_db_session)
):
    """
    Get current user or create if not exists.
    
    This auto-creates a user record when they first authenticate via Supabase.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    user_id, email, name = auth_info
    
    user = user_crud.get_user_by_id(db, user_id)
    
    if not user and email:
        # Auto-create user from Supabase auth info
        logger.info(f"Auto-creating user {user_id} with email {email}")
        try:
            # Check if user exists by email (might have different ID)
            existing = user_crud.get_user_by_email(db, email)
            if existing:
                logger.warning(f"User with email {email} exists with different ID")
                return existing
            
            # Create new user with Supabase user ID
            from ..database.models import User
            new_user = User(
                id=user_id,
                email=email,
                name=name,
                country='TW'
            )
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
            logger.info(f"Created user {user_id}")
            return new_user
        except Exception as e:
            logger.error(f"Failed to auto-create user: {e}")
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to create user: {str(e)}")
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found and could not be created")
    
    return user


def get_current_user(
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db_session)
) -> dict:
    """
    Get current authenticated user object from database.
    
    This dependency combines authentication with database lookup.
    
    Usage:
        @router.get("/me")
        async def get_me(user = Depends(get_current_user)):
            return user
    
    Args:
        user_id: Authenticated user ID (from get_current_user_id)
        db: Database session
    
    Returns:
        User object from database
    
    Raises:
        HTTPException: If user not found
    """
    user = user_crud.get_user_by_id(db, user_id)
    
    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found in database"
        )
    
    return user

