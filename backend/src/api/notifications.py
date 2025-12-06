"""
Notifications API

Endpoints for user notifications.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session

from ..database.postgres_connection import PostgresConnection
from ..middleware.auth import get_current_user_id
from ..services.notifications import NotificationService

router = APIRouter(prefix="/api/v1/notifications", tags=["Notifications"])


# --- Response Models ---

class NotificationResponse(BaseModel):
    """Notification response."""
    id: str
    type: str
    title_en: str
    title_zh: Optional[str]
    message_en: Optional[str]
    message_zh: Optional[str]
    data: dict
    read: bool
    created_at: str


class MarkReadRequest(BaseModel):
    """Request to mark notifications as read."""
    notification_ids: List[str]


# --- Dependency Injection ---

def get_db_session():
    """Get database session."""
    conn = PostgresConnection()
    return conn.get_session()


@router.get("", response_model=List[NotificationResponse])
async def get_notifications(
    unread_only: bool = Query(False),
    limit: int = Query(50, ge=1, le=100),
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db_session)
):
    """
    Get notifications for the current user.
    
    Parameters:
    - unread_only: Only return unread notifications
    - limit: Maximum number of notifications to return (1-100)
    """
    try:
        notification_service = NotificationService(db)
        notifications = notification_service.get_notifications(
            user_id, unread_only=unread_only, limit=limit
        )
        
        return [NotificationResponse(**n) for n in notifications]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get notifications: {str(e)}")
    finally:
        db.close()


@router.post("/read")
async def mark_as_read(
    request: MarkReadRequest,
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db_session)
):
    """
    Mark specific notifications as read.
    
    Provide a list of notification IDs to mark as read.
    """
    try:
        notification_service = NotificationService(db)
        
        # Convert string IDs to UUIDs
        notification_ids = [UUID(nid) for nid in request.notification_ids]
        
        count = notification_service.mark_as_read(notification_ids, user_id)
        
        return {
            'message': f'Marked {count} notification(s) as read',
            'count': count
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid notification ID: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to mark notifications as read: {str(e)}")
    finally:
        db.close()


@router.post("/read-all")
async def mark_all_as_read(
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db_session)
):
    """
    Mark all notifications as read for the current user.
    """
    try:
        notification_service = NotificationService(db)
        count = notification_service.mark_all_as_read(user_id)
        
        return {
            'message': f'Marked {count} notification(s) as read',
            'count': count
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to mark all notifications as read: {str(e)}")
    finally:
        db.close()


@router.get("/unread-count")
async def get_unread_count(
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db_session)
):
    """
    Get count of unread notifications.
    
    Useful for showing a badge count in the UI.
    """
    try:
        notification_service = NotificationService(db)
        count = notification_service.get_unread_count(user_id)
        
        return {'unread_count': count}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get unread count: {str(e)}")
    finally:
        db.close()


@router.post("/check-streak-risk")
async def check_streak_risk(
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db_session)
):
    """
    Manually check if streak is at risk and create notification if needed.
    
    This is typically called automatically, but can be triggered manually.
    """
    try:
        notification_service = NotificationService(db)
        notification = notification_service.check_streak_risk(user_id)
        
        if notification:
            return {
                'message': 'Streak risk notification created',
                'notification': NotificationResponse(**notification)
            }
        else:
            return {
                'message': 'No streak risk (streak is safe or already notified)',
                'notification': None
            }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to check streak risk: {str(e)}")
    finally:
        db.close()


@router.post("/check-milestones")
async def check_milestones(
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db_session)
):
    """
    Manually check for milestone achievements and create notifications.
    
    This checks for:
    - Newly unlocked achievements
    - Level ups
    - Goal progress milestones
    """
    try:
        notification_service = NotificationService(db)
        
        # Check achievements and level ups
        milestone_notifications = notification_service.check_milestone_notifications(user_id)
        
        # Check goal progress
        goal_notifications = notification_service.check_goal_progress_notifications(user_id)
        
        all_notifications = milestone_notifications + goal_notifications
        
        return {
            'message': f'Created {len(all_notifications)} milestone notification(s)',
            'count': len(all_notifications),
            'notifications': [NotificationResponse(**n) for n in all_notifications]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to check milestones: {str(e)}")
    finally:
        db.close()


