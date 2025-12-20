"""
Leaderboard API

Endpoints for leaderboard rankings and social connections.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import text

from ..database.postgres_connection import PostgresConnection
from ..middleware.auth import get_current_user_id
from ..services.leaderboards import LeaderboardService

router = APIRouter(prefix="/api/v1/leaderboards", tags=["Leaderboards"])


# --- Response Models ---

class LeaderboardEntry(BaseModel):
    """Leaderboard entry."""
    rank: int
    user_id: str
    name: str
    avatar: Optional[str] = '🦄'  # Avatar emoji, default to unicorn
    email: Optional[str] = None
    score: int
    longest_streak: int
    current_streak: int
    is_me: Optional[bool] = False


class UserRank(BaseModel):
    """User rank information."""
    rank: int
    user_id: str
    score: int
    period: str
    metric: str


# --- Dependency Injection ---

def get_db_session():
    """Get database session."""
    conn = PostgresConnection()
    return conn.get_session()


@router.get("/global", response_model=List[LeaderboardEntry])
async def get_global_leaderboard(
    period: str = Query('weekly', regex='^(weekly|monthly|all_time)$'),
    limit: int = Query(50, ge=1, le=100),
    metric: str = Query('xp', regex='^(xp|words|streak)$'),
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db_session)
):
    """
    Get global leaderboard.
    
    Periods:
    - weekly: Last 7 days
    - monthly: Last 30 days
    - all_time: All time
    
    Metrics:
    - xp: Experience points
    - words: Words learned
    - streak: Longest streak
    """
    try:
        print(f"🔍 [LEADERBOARD API] Starting get_global_leaderboard: period={period}, limit={limit}, metric={metric}")
        leaderboard_service = LeaderboardService(db)
        print(f"🔍 [LEADERBOARD API] Created LeaderboardService, calling get_global_leaderboard...")
        entries = leaderboard_service.get_global_leaderboard(period, limit, metric)
        print(f"🔍 [LEADERBOARD API] Got {len(entries)} entries from service")
        
        # Get my learner IDs to identify "is_me"
        # Note: entry['user_id'] actually holds learner_id now
        my_learners_result = db.execute(
            text("SELECT id FROM public.learners WHERE user_id = :user_id OR guardian_id = :user_id"),
            {'user_id': user_id}
        )
        my_learner_ids = {str(row[0]) for row in my_learners_result.fetchall()}
        
        # Mark entries
        for entry in entries:
            if entry['user_id'] in my_learner_ids:
                entry['is_me'] = True
        
        # Debug: Print first entry structure
        if entries:
            print(f"🔍 First leaderboard entry: {entries[0]}")
        
        # Convert to LeaderboardEntry models
        try:
            result = [LeaderboardEntry(**entry) for entry in entries]
            print(f"✅ Successfully created {len(result)} LeaderboardEntry objects")
            return result
        except Exception as model_err:
            print(f"❌ Failed to create LeaderboardEntry: {model_err}")
            print(f"❌ Entry structure: {entries[0] if entries else 'No entries'}")
            import traceback
            traceback.print_exc()
            raise
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        import traceback
        error_detail = str(e)
        traceback.print_exc()
        print(f"❌ Leaderboard API error: {error_detail}")
        raise HTTPException(status_code=500, detail=f"Failed to get leaderboard: {error_detail}")
    finally:
        db.close()


@router.get("/friends", response_model=List[LeaderboardEntry])
async def get_friends_leaderboard(
    period: str = Query('weekly', regex='^(weekly|monthly|all_time)$'),
    metric: str = Query('xp', regex='^(xp|words|streak)$'),
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db_session)
):
    """
    Get leaderboard for user's friends/classmates.
    
    Only shows users that are connected as friends or classmates.
    """
    try:
        leaderboard_service = LeaderboardService(db)
        entries = leaderboard_service.get_friends_leaderboard(user_id, period, metric)
        
        return [LeaderboardEntry(**entry) for entry in entries]
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get friends leaderboard: {str(e)}")
    finally:
        db.close()


@router.get("/rank", response_model=UserRank)
async def get_user_rank(
    period: str = Query('weekly', regex='^(weekly|monthly|all_time)$'),
    metric: str = Query('xp', regex='^(xp|words|streak)$'),
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db_session)
):
    """
    Get user's rank in global leaderboard.
    
    Returns None if user is not ranked (score is 0).
    """
    try:
        leaderboard_service = LeaderboardService(db)
        rank_info = leaderboard_service.get_user_rank(user_id, period, metric)
        
        if not rank_info:
            raise HTTPException(status_code=404, detail="User not ranked")
        
        return UserRank(**rank_info)
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get user rank: {str(e)}")
    finally:
        db.close()


@router.post("/connections/{connected_user_id}")
async def add_connection(
    connected_user_id: UUID,
    connection_type: str = Query('friend', regex='^(friend|classmate)$'),
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db_session)
):
    """
    Add a connection (friend or classmate).
    
    Creates a bidirectional connection between users.
    """
    try:
        if connected_user_id == user_id:
            raise HTTPException(status_code=400, detail="Cannot connect to yourself")
        
        leaderboard_service = LeaderboardService(db)
        
        # Add connection in both directions
        added1 = leaderboard_service.add_connection(user_id, connected_user_id, connection_type)
        added2 = leaderboard_service.add_connection(connected_user_id, user_id, connection_type)
        
        if added1 or added2:
            return {"message": "Connection added successfully"}
        else:
            return {"message": "Connection already exists"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add connection: {str(e)}")
    finally:
        db.close()


@router.get("/connections", response_model=List[dict])
async def get_connections(
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db_session)
):
    """
    Get user's connections (friends/classmates).
    """
    try:
        leaderboard_service = LeaderboardService(db)
        connections = leaderboard_service.get_connections(user_id)
        
        return connections
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get connections: {str(e)}")
    finally:
        db.close()


