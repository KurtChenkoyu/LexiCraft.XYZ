"""
Goals API

Endpoints for learning goal management.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID
from datetime import date
from sqlalchemy.orm import Session

from ..database.postgres_connection import PostgresConnection
from ..middleware.auth import get_current_user_id
from ..services.goals import GoalsService

router = APIRouter(prefix="/api/v1/goals", tags=["Goals"])


# --- Request/Response Models ---

class CreateGoalRequest(BaseModel):
    """Request to create a goal."""
    goal_type: str  # 'daily_words', 'weekly_words', 'monthly_words', 'streak', 'vocabulary_size'
    target_value: int
    end_date: str  # ISO date string


class GoalResponse(BaseModel):
    """Goal response."""
    id: str
    goal_type: str
    target_value: int
    current_value: int
    start_date: Optional[str]
    end_date: Optional[str]
    status: str
    created_at: Optional[str]
    completed_at: Optional[str]
    progress_percentage: int


class GoalSuggestion(BaseModel):
    """Goal suggestion."""
    goal_type: str
    target_value: int
    end_date: str
    reason: str


# --- Dependency Injection ---

def get_db_session():
    """Get database session."""
    conn = PostgresConnection()
    return conn.get_session()


@router.get("", response_model=List[GoalResponse])
async def get_goals(
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db_session)
):
    """
    Get all goals for the current user.
    
    Returns all goals (active, completed, failed) with current progress.
    """
    try:
        goals_service = GoalsService(db)
        goals = goals_service.get_active_goals(user_id)
        
        return [GoalResponse(**goal) for goal in goals]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get goals: {str(e)}")
    finally:
        db.close()


@router.post("", response_model=GoalResponse)
async def create_goal(
    request: CreateGoalRequest,
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db_session)
):
    """
    Create a new learning goal.
    
    Goal types:
    - daily_words: Learn X words in a day
    - weekly_words: Learn X words in a week
    - monthly_words: Learn X words in a month
    - streak: Maintain X-day streak
    - vocabulary_size: Reach X total vocabulary size
    """
    try:
        goals_service = GoalsService(db)
        
        # Parse end_date
        try:
            end_date = date.fromisoformat(request.end_date)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid end_date format. Use ISO format (YYYY-MM-DD)")
        
        goal = goals_service.create_goal(
            user_id=user_id,
            goal_type=request.goal_type,
            target_value=request.target_value,
            end_date=end_date
        )
        
        return GoalResponse(**goal)
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create goal: {str(e)}")
    finally:
        db.close()


@router.put("/{goal_id}", response_model=GoalResponse)
async def update_goal(
    goal_id: UUID,
    request: CreateGoalRequest,
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db_session)
):
    """
    Update an existing goal.
    
    Note: Only active goals can be updated. Completed or failed goals are read-only.
    """
    try:
        from sqlalchemy import text
        
        # Check if goal exists and belongs to user
        result = db.execute(
            text("""
                SELECT id, status FROM learning_goals
                WHERE id = :goal_id AND user_id = :user_id
            """),
            {'goal_id': goal_id, 'user_id': user_id}
        )
        goal = result.fetchone()
        
        if not goal:
            raise HTTPException(status_code=404, detail="Goal not found")
        
        if goal[1] != 'active':
            raise HTTPException(status_code=400, detail="Only active goals can be updated")
        
        # Parse end_date
        try:
            end_date = date.fromisoformat(request.end_date)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid end_date format. Use ISO format (YYYY-MM-DD)")
        
        # Update goal
        db.execute(
            text("""
                UPDATE learning_goals
                SET goal_type = :goal_type,
                    target_value = :target_value,
                    end_date = :end_date,
                    updated_at = NOW()
                WHERE id = :goal_id AND user_id = :user_id
            """),
            {
                'goal_id': goal_id,
                'user_id': user_id,
                'goal_type': request.goal_type,
                'target_value': request.target_value,
                'end_date': end_date
            }
        )
        db.commit()
        
        # Get updated goal
        goals_service = GoalsService(db)
        goals = goals_service.get_active_goals(user_id)
        updated_goal = next((g for g in goals if g['id'] == str(goal_id)), None)
        
        if not updated_goal:
            raise HTTPException(status_code=500, detail="Failed to retrieve updated goal")
        
        return GoalResponse(**updated_goal)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update goal: {str(e)}")
    finally:
        db.close()


@router.delete("/{goal_id}")
async def delete_goal(
    goal_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db_session)
):
    """
    Delete a goal.
    
    Only active goals can be deleted.
    """
    try:
        goals_service = GoalsService(db)
        deleted = goals_service.delete_goal(goal_id, user_id)
        
        if not deleted:
            raise HTTPException(status_code=404, detail="Goal not found")
        
        return {"message": "Goal deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete goal: {str(e)}")
    finally:
        db.close()


@router.get("/suggestions", response_model=List[GoalSuggestion])
async def get_goal_suggestions(
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db_session)
):
    """
    Get AI-suggested goals based on user's learning history.
    
    Returns personalized goal suggestions based on:
    - Current learning rate
    - Current streak
    - Vocabulary milestones
    """
    try:
        goals_service = GoalsService(db)
        suggestions = goals_service.get_goal_suggestions(user_id)
        
        return [GoalSuggestion(**s) for s in suggestions]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get goal suggestions: {str(e)}")
    finally:
        db.close()


@router.post("/{goal_id}/complete", response_model=GoalResponse)
async def complete_goal(
    goal_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db_session)
):
    """
    Manually mark a goal as completed.
    
    Awards XP for goal completion.
    """
    try:
        goals_service = GoalsService(db)
        goal = goals_service.complete_goal(goal_id, user_id)
        
        return GoalResponse(**goal)
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to complete goal: {str(e)}")
    finally:
        db.close()


