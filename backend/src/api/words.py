"""
Words API Endpoints

Handles starting verification for words/learning points.

Endpoints:
- POST /api/v1/words/start-verification - Start verification for a word
"""

import logging
from typing import Optional, Generator
from uuid import UUID
from datetime import date

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import text

from src.database.postgres_connection import PostgresConnection
from src.middleware.auth import get_current_user_id
from src.database.postgres_crud.progress import (
    create_learning_progress,
    get_learning_progress_by_learning_point,
)
from src.database.postgres_crud.verification import create_verification_schedule

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/words", tags=["Words"])

# Database connection
_postgres_conn: Optional[PostgresConnection] = None


def get_postgres_conn() -> PostgresConnection:
    global _postgres_conn
    if _postgres_conn is None:
        _postgres_conn = PostgresConnection()
    return _postgres_conn


def get_db_session() -> Generator[Session, None, None]:
    conn = get_postgres_conn()
    session = conn.get_session()
    try:
        yield session
    finally:
        session.close()


# Request/Response Models

class StartVerificationRequest(BaseModel):
    """Request to start verification for a word."""
    learning_point_id: str = Field(..., description="The learning point ID")
    tier: int = Field(..., ge=1, le=5, description="Initial tier (1-5)")
    initial_difficulty: float = Field(0.5, ge=0.0, le=1.0, description="Initial difficulty")


class StartVerificationResponse(BaseModel):
    """Response after starting verification."""
    success: bool
    learning_progress_id: int
    verification_schedule_id: int
    learning_point_id: str
    status: str
    scheduled_date: str
    algorithm_type: str
    mastery_level: str
    message: str


# Endpoints

@router.post("/start-verification", response_model=StartVerificationResponse)
async def start_verification(
    request: StartVerificationRequest,
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db_session),
):
    """
    Start verification for a word/learning point.
    
    Creates:
    - A learning_progress entry with status='pending'
    - A verification_schedule entry using the user's assigned algorithm
    
    The verification schedule will be initialized with the appropriate
    algorithm (SM-2+ or FSRS) and scheduled for the first review.
    """
    try:
        # Check if learning_progress already exists for this user + learning_point_id
        existing_progress = get_learning_progress_by_learning_point(
            session=db,
            user_id=user_id,
            learning_point_id=request.learning_point_id,
        )
        
        if existing_progress:
            # Check if verification schedule also exists
            result = db.execute(
                text("""
                    SELECT id, algorithm_type, scheduled_date, mastery_level
                    FROM verification_schedule
                    WHERE user_id = :user_id
                    AND learning_progress_id = :learning_progress_id
                """),
                {
                    'user_id': user_id,
                    'learning_progress_id': existing_progress.id,
                }
            )
            schedule_row = result.fetchone()
            
            if schedule_row:
                # Both exist, return existing entry info
                return StartVerificationResponse(
                    success=True,
                    learning_progress_id=existing_progress.id,
                    verification_schedule_id=schedule_row[0],
                    learning_point_id=request.learning_point_id,
                    status=existing_progress.status or 'pending',
                    scheduled_date=schedule_row[2].isoformat() if schedule_row[2] else date.today().isoformat(),
                    algorithm_type=schedule_row[1] or 'sm2_plus',
                    mastery_level=schedule_row[3] or 'learning',
                    message="Verification already exists for this word",
                )
            else:
                # Learning progress exists but no schedule - create schedule only
                schedule = create_verification_schedule(
                    session=db,
                    user_id=user_id,
                    learning_progress_id=existing_progress.id,
                    learning_point_id=request.learning_point_id,
                    initial_difficulty=request.initial_difficulty,
                )
                
                return StartVerificationResponse(
                    success=True,
                    learning_progress_id=existing_progress.id,
                    verification_schedule_id=schedule.id,
                    learning_point_id=request.learning_point_id,
                    status=existing_progress.status or 'pending',
                    scheduled_date=schedule.scheduled_date.isoformat() if schedule.scheduled_date else date.today().isoformat(),
                    algorithm_type=schedule.algorithm_type or 'sm2_plus',
                    mastery_level=schedule.mastery_level or 'learning',
                    message="Verification schedule created for existing learning progress",
                )
        
        # Create new learning_progress entry with status='pending'
        progress = create_learning_progress(
            session=db,
            user_id=user_id,
            learning_point_id=request.learning_point_id,
            tier=request.tier,
            status='pending',  # Use 'pending' as specified
        )
        
        # Create verification_schedule entry
        # This automatically uses the user's assigned algorithm
        schedule = create_verification_schedule(
            session=db,
            user_id=user_id,
            learning_progress_id=progress.id,
            learning_point_id=request.learning_point_id,
            initial_difficulty=request.initial_difficulty,
        )
        
        return StartVerificationResponse(
            success=True,
            learning_progress_id=progress.id,
            verification_schedule_id=schedule.id,
            learning_point_id=request.learning_point_id,
            status=progress.status or 'pending',
            scheduled_date=schedule.scheduled_date.isoformat() if schedule.scheduled_date else date.today().isoformat(),
            algorithm_type=schedule.algorithm_type or 'sm2_plus',
            mastery_level=schedule.mastery_level or 'learning',
            message="Verification started successfully",
        )
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Invalid input: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid input: {str(e)}")
    except Exception as e:
        logger.error(f"Failed to start verification: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to start verification: {str(e)}")

