"""
Sync API Endpoints

Handles batch synchronization of user actions from the client.
This enables offline-first behavior where clients queue actions locally
and sync them in batches.
"""

from typing import List, Optional, Generator
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import text

from ..database.postgres_connection import PostgresConnection
from ..middleware.auth import get_current_user_id
from ..database.postgres_crud.progress import create_learning_progress
from ..database.postgres_crud.verification import create_verification_schedule


router = APIRouter(prefix="/api/v1/sync", tags=["Sync"])


# --- Request/Response Models ---

class SyncAction(BaseModel):
    """A single user action to sync."""
    type: str = Field(..., description="Action type: START_FORGING, COMPLETE_VERIFICATION, UPDATE_PROGRESS")
    sense_id: str = Field(..., description="Sense ID the action applies to")
    payload: Optional[dict] = Field(None, description="Additional action data")
    timestamp: int = Field(..., description="Client timestamp (ms since epoch)")


class BatchSyncRequest(BaseModel):
    """Batch sync request from client."""
    actions: List[SyncAction] = Field(..., description="List of actions to sync")


class BatchSyncResponse(BaseModel):
    """Batch sync response."""
    synced: int = Field(..., description="Number of successfully synced actions")
    failed: int = Field(..., description="Number of failed actions")
    errors: Optional[List[str]] = Field(None, description="Error messages for failed actions")


# --- Dependency Injection ---

def get_db_session() -> Generator[Session, None, None]:
    """Get database session."""
    db = PostgresConnection().get_session()
    try:
        yield db
    finally:
        db.close()


# --- Endpoints ---

@router.post("", response_model=BatchSyncResponse)
async def batch_sync(
    request: BatchSyncRequest,
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db_session)
):
    """
    Process a batch of user actions.
    
    Supports the following action types:
    - START_FORGING: Begin learning a new block
    - COMPLETE_VERIFICATION: Mark a verification as complete
    - UPDATE_PROGRESS: Update learning progress
    """
    synced = 0
    failed = 0
    errors: List[str] = []
    
    for action in request.actions:
        try:
            if action.type == "START_FORGING":
                # Check if already exists
                existing = db.execute(
                    text("""
                        SELECT id FROM learning_progress
                        WHERE user_id = :user_id AND learning_point_id = :sense_id
                    """),
                    {"user_id": user_id, "sense_id": action.sense_id}
                ).fetchone()
                
                if not existing:
                    # Create new learning progress
                    progress = create_learning_progress(
                        session=db,
                        user_id=user_id,
                        learning_point_id=action.sense_id,
                        tier=1,
                        status='pending'
                    )
                    
                    # Create verification schedule
                    create_verification_schedule(
                        session=db,
                        user_id=user_id,
                        learning_progress_id=progress.id,
                        learning_point_id=action.sense_id,
                        initial_difficulty=0.5
                    )
                
                synced += 1
                
            elif action.type == "COMPLETE_VERIFICATION":
                # Update verification status
                verification_id = action.payload.get("verification_id") if action.payload else None
                passed = action.payload.get("passed", False) if action.payload else False
                
                if verification_id:
                    db.execute(
                        text("""
                            UPDATE verification_schedule
                            SET completed = true,
                                completed_at = NOW(),
                                passed = :passed
                            WHERE id = :verification_id
                            AND user_id = :user_id
                        """),
                        {"verification_id": verification_id, "passed": passed, "user_id": user_id}
                    )
                    synced += 1
                else:
                    failed += 1
                    errors.append(f"Missing verification_id for COMPLETE_VERIFICATION")
                    
            elif action.type == "UPDATE_PROGRESS":
                # Update learning progress status
                new_status = action.payload.get("status") if action.payload else None
                
                if new_status:
                    db.execute(
                        text("""
                            UPDATE learning_progress
                            SET status = :status, updated_at = NOW()
                            WHERE user_id = :user_id
                            AND learning_point_id = :sense_id
                        """),
                        {"status": new_status, "user_id": user_id, "sense_id": action.sense_id}
                    )
                    synced += 1
                else:
                    failed += 1
                    errors.append(f"Missing status for UPDATE_PROGRESS")
                    
            else:
                failed += 1
                errors.append(f"Unknown action type: {action.type}")
                
        except Exception as e:
            failed += 1
            errors.append(f"Error processing {action.type} for {action.sense_id}: {str(e)}")
    
    # Commit all changes
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        return BatchSyncResponse(
            synced=0,
            failed=len(request.actions),
            errors=[f"Database commit failed: {str(e)}"]
        )
    
    return BatchSyncResponse(
        synced=synced,
        failed=failed,
        errors=errors if errors else None
    )

