"""
Mine API Endpoints

Handles block exploration in The Mine (vocabulary universe).

V2: Now uses VocabularyStore for vocabulary data, Neo4j is optional fallback.
Frontend should use local vocabulary data - these APIs are primarily for user progress.
"""

from fastapi import APIRouter, HTTPException, Depends, Query, Body
from pydantic import BaseModel
from typing import Dict, List, Optional, Generator
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import text
import os

from ..database.postgres_connection import PostgresConnection
from ..middleware.auth import get_current_user_id
from ..services.vocabulary_store import vocabulary_store
from ..database.postgres_crud.progress import create_learning_progress, _get_learner_id_for_user
from ..database.postgres_crud.verification import create_verification_schedule

# Optional Neo4j import for legacy support
try:
    from ..database.neo4j_connection import Neo4jConnection
    from ..services.mine import MineService
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False

router = APIRouter(prefix="/api/v1/mine", tags=["Mine"])


# --- Request Models ---

class StartForgingRequest(BaseModel):
    """Optional body for specifying learner when starting to forge."""
    learner_id: Optional[UUID] = None


class MineBatchRequest(BaseModel):
    """Request to mine a batch of words."""
    sense_ids: List[str]
    tier: int = 1


# --- Response Models ---

class BlockConnection(BaseModel):
    """Block connection information."""
    sense_id: str
    word: str
    type: str
    status: Optional[str] = None


class Block(BaseModel):
    """Block information."""
    sense_id: str
    word: str
    definition_preview: str
    tier: int
    base_xp: int
    connection_count: int
    total_value: int
    status: str  # 'raw' | 'hollow' | 'solid'
    rank: Optional[int] = None
    source: Optional[str] = None  # 'gap', 'prerequisite', 'RELATED_TO', etc.


class BlockDetail(BaseModel):
    """Full block detail."""
    sense_id: str
    word: str
    tier: int
    base_xp: int
    connection_count: int
    total_value: int
    rank: Optional[int] = None
    definition_en: Optional[str] = None
    definition_zh: Optional[str] = None
    example_en: Optional[str] = None
    example_zh: Optional[str] = None
    connections: List[BlockConnection]
    user_progress: Optional[Dict] = None


class UserStats(BaseModel):
    """User statistics for The Mine."""
    total_discovered: int
    solid_count: int
    hollow_count: int
    raw_count: int


class MineExploreResponse(BaseModel):
    """Response for exploring The Mine."""
    mode: str  # 'starter' | 'personalized'
    blocks: List[Block]
    user_stats: UserStats
    gaps_count: Optional[int] = None
    prerequisites_count: Optional[int] = None


class StartForgingResponse(BaseModel):
    """Response for starting to forge a block."""
    success: bool
    learning_progress_id: int
    sense_id: str
    status: str
    message: str
    # Delta Strategy fields (instant UI update)
    delta_xp: int = 0           # XP gained for discovery
    delta_sparks: int = 0       # Sparks earned
    delta_discovered: int = 0   # +1 for new word
    delta_hollow: int = 0       # +1 for in-progress word


# --- Additional Response Models for Progress API ---

class BlockProgress(BaseModel):
    """Block progress information."""
    sense_id: str
    status: str  # 'raw' | 'hollow' | 'solid' | 'learning' | 'pending' | 'verified' | 'mastered'
    tier: Optional[int] = None
    started_at: Optional[str] = None
    mastery_level: Optional[str] = None


class UserProgressResponse(BaseModel):
    """User progress response."""
    progress: List[BlockProgress]
    stats: UserStats


# --- Dependency Injection ---

def get_db_session() -> Generator[Session, None, None]:
    """Get database session."""
    db = PostgresConnection().get_session()
    try:
        yield db
    finally:
        db.close()


# --- Endpoints ---

@router.get("/progress", response_model=UserProgressResponse)
async def get_user_progress(
    learner_id: Optional[UUID] = Query(None, description="Learner ID (defaults to parent's learner profile)"),
    user_id: UUID = Depends(get_current_user_id),  # Auth user (parent)
    db: Session = Depends(get_db_session)
):
    """
    Get learning progress for a learner.
    
    Unified pipeline rules:
    - Progress is always keyed by learner_id when a learner profile exists
      (parent profile or child profile).
    - If learner_id is provided, we verify the authenticated user manages that
      learner and then return ONLY rows for that learner_id.
    - If learner_id is omitted, we look up the parent's own learner profile
      and return rows for that learner_id.
    - The legacy user_id-only path is kept only for accounts without any
      learner profiles yet, and is considered backward-compatibility only.
    
    Frontend MUST always pass learner_id for multi-learner flows so that
    parent and children share the exact same pipeline.
    Vocabulary data comes from the client cache; this endpoint only returns
    progress rows + stats.
    """
    try:
        # 1. Determine target learner_id
        target_learner_id = None
        
        if learner_id:
            # Security check: Verify user is guardian/owner of this learner
            # NOTE: This intentionally mirrors the check in start_forging so
            # that read/write semantics are identical for parent + children.
            learner_check = db.execute(
                text("""
                    SELECT id FROM public.learners
                    WHERE id = :learner_id
                      AND (guardian_id = :guardian_id OR user_id = :guardian_id)
                """),
                {'learner_id': learner_id, 'guardian_id': user_id}
            ).fetchone()
            
            if not learner_check:
                raise HTTPException(
                    status_code=403,
                    detail="You can only view progress for learners you manage"
                )
            target_learner_id = learner_id
        else:
            # Fallback: Find parent's own learner profile
            parent_learner = db.execute(
                text("""
                    SELECT id FROM public.learners
                    WHERE user_id = :user_id AND is_parent_profile = true
                """),
                {'user_id': user_id}
            ).fetchone()
            
            if parent_learner:
                target_learner_id = parent_learner[0]
            else:
                # Legacy fallback: use user_id directly (for backward compatibility during transition)
                target_learner_id = None
        
        # 2. Query progress (prefer learner_id, fallback to user_id for legacy)
        if target_learner_id:
            # New system: Use learner_id
            if os.getenv("DEBUG_LEARNER_PIPELINE") == "true":
                print(f"[get_user_progress] Querying progress for learner_id={target_learner_id}")
            
            result = db.execute(
                text("""
                    SELECT 
                        lp.learning_point_id as sense_id,
                        lp.status,
                        lp.tier,
                        lp.learned_at as started_at,
                        COALESCE(vs.mastery_level, 'learning') as mastery_level
                    FROM learning_progress lp
                    LEFT JOIN verification_schedule vs ON lp.id = vs.learning_progress_id
                    WHERE lp.learner_id = :learner_id
                """),
                {'learner_id': target_learner_id}
            )
            
            if os.getenv("DEBUG_LEARNER_PIPELINE") == "true":
                rows = result.fetchall()
                print(f"[get_user_progress] Found {len(rows)} progress rows for learner_id={target_learner_id}")
                if len(rows) > 0:
                    print(f"[get_user_progress] Sample rows: {[(r[0], r[1]) for r in rows[:3]]}")
                # Re-execute since fetchall() consumed the cursor
                result = db.execute(
                    text("""
                        SELECT 
                            lp.learning_point_id as sense_id,
                            lp.status,
                            lp.tier,
                            lp.learned_at as started_at,
                            COALESCE(vs.mastery_level, 'learning') as mastery_level
                        FROM learning_progress lp
                        LEFT JOIN verification_schedule vs ON lp.id = vs.learning_progress_id
                        WHERE lp.learner_id = :learner_id
                    """),
                    {'learner_id': target_learner_id}
                )
            
            stats_result = db.execute(
                text("""
                    SELECT 
                        COUNT(*) as total,
                        COUNT(*) FILTER (WHERE status = 'verified') as solid,
                        COUNT(*) FILTER (WHERE status IN ('learning', 'pending')) as hollow
                    FROM learning_progress lp
                    WHERE lp.learner_id = :learner_id
                """),
                {'learner_id': target_learner_id}
            )
        else:
            # Legacy: Use user_id (backward compatibility)
            result = db.execute(
                text("""
                    SELECT 
                        lp.learning_point_id as sense_id,
                        lp.status,
                        lp.tier,
                        lp.learned_at as started_at,
                        COALESCE(vs.mastery_level, 'learning') as mastery_level
                    FROM learning_progress lp
                    LEFT JOIN verification_schedule vs ON lp.id = vs.learning_progress_id
                    WHERE lp.user_id = :user_id
                """),
                {'user_id': user_id}
            )
            
            stats_result = db.execute(
                text("""
                    SELECT 
                        COUNT(*) as total,
                        COUNT(*) FILTER (WHERE status = 'verified') as solid,
                        COUNT(*) FILTER (WHERE status IN ('learning', 'pending')) as hollow
                    FROM learning_progress lp
                    WHERE lp.user_id = :user_id
                """),
                {'user_id': user_id}
            )
        
        progress = []
        for row in result.fetchall():
            status = row[1] or 'pending'
            mastery_level = row[4] or 'learning'  # Use real mastery_level from JOIN
            progress.append(BlockProgress(
                sense_id=row[0],
                status=status,
                tier=row[2],
                started_at=row[3].isoformat() if row[3] else None,
                mastery_level=mastery_level,  # Real SRS mastery level
            ))
        
        # Calculate stats (already executed above based on target)
        stats_row = stats_result.fetchone()
        total = stats_row[0] if stats_row else 0
        solid = stats_row[1] if stats_row else 0
        hollow = stats_row[2] if stats_row else 0
        
        return UserProgressResponse(
            progress=progress,
            stats=UserStats(
                total_discovered=total,
                solid_count=solid,
                hollow_count=hollow,
                raw_count=max(0, total - solid - hollow),
            )
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get progress: {str(e)}")


@router.get("/progress/{sense_id}", response_model=Optional[BlockProgress])
async def get_block_progress(
    sense_id: str,
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db_session)
):
    """
    Get progress for a specific block.
    """
    try:
        result = db.execute(
            text("""
                SELECT 
                    lp.learning_point_id as sense_id,
                    lp.status,
                    lp.tier,
                    lp.learned_at as started_at
                FROM learning_progress lp
                WHERE lp.user_id = :user_id
                AND lp.learning_point_id = :sense_id
                LIMIT 1
            """),
            {'user_id': user_id, 'sense_id': sense_id}
        )
        
        row = result.fetchone()
        if not row:
            return None
        
        status = row[1] or 'pending'
        mastery = 'mastered' if status == 'verified' else status
        
        return BlockProgress(
            sense_id=row[0],
            status=status,
            tier=row[2],
            started_at=row[3].isoformat() if row[3] else None,
            mastery_level=mastery,
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get block progress: {str(e)}")

@router.get("/explore", response_model=MineExploreResponse)
async def explore_mine(
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db_session)
):
    """
    Explore The Mine - get blocks to discover.
    
    V2: Uses VocabularyStore (in-memory JSON) for vocabulary data.
    Falls back to Neo4j only if VocabularyStore is not loaded.
    
    NOTE: Frontend should use local vocabulary data. This endpoint is
    primarily for backward compatibility.
    
    Returns:
    - Starter pack (for users without survey): ~50 diverse blocks across frequency bands
    - Personalized blocks (for surveyed users): missed words + prerequisites + connections
    """
    try:
        # Try VocabularyStore first (fast, in-memory)
        if vocabulary_store.is_loaded:
            blocks = vocabulary_store.get_starter_pack(limit=50)
            mode = 'starter'
            
            # Enrich with user progress status
            progress_result = db.execute(
                text("""
                    SELECT learning_point_id, status
                    FROM learning_progress
                    WHERE user_id = :user_id
                """),
                {'user_id': user_id}
            )
            progress_map = {row[0]: row[1] for row in progress_result.fetchall()}
            
            for block in blocks:
                progress_status = progress_map.get(block['sense_id'])
                if progress_status in ('verified', 'mastered'):
                    block['status'] = 'solid'
                elif progress_status in ('learning', 'pending'):
                    block['status'] = 'hollow'
                else:
                    block['status'] = 'raw'
            
        # Fallback to Neo4j if VocabularyStore not loaded
        elif NEO4J_AVAILABLE:
            neo4j = None
            try:
                neo4j = Neo4jConnection()
                mine_service = MineService(db, neo4j)
                
                # Check if user has completed survey
                has_survey = mine_service.has_completed_survey(user_id)
                
                if has_survey:
                    blocks, _ = mine_service.get_personalized_blocks(user_id, limit=50)
                    mode = 'personalized'
                else:
                    blocks = mine_service.get_starter_pack(limit=50)
                    mode = 'starter'
                
                blocks = mine_service.enrich_blocks_with_user_status(blocks, user_id)
            finally:
                if neo4j:
                    neo4j.close()
        else:
            raise HTTPException(
                status_code=503,
                detail="Vocabulary data not available. Run export_vocabulary_json.py first."
            )
        
        # Get user stats (using learning_progress.status, not verification_schedule.mastery_level)
        user_stats_result = db.execute(
            text("""
                SELECT 
                    COUNT(*) as total,
                    COUNT(*) FILTER (WHERE status = 'verified') as solid,
                    COUNT(*) FILTER (WHERE status IN ('learning', 'pending')) as hollow
                FROM learning_progress lp
                WHERE lp.user_id = :user_id
            """),
            {'user_id': user_id}
        )
        
        stats_row = user_stats_result.fetchone()
        total_discovered = stats_row[0] if stats_row else 0
        solid_count = stats_row[1] if stats_row else 0
        hollow_count = stats_row[2] if stats_row else 0
        raw_count = len(blocks) - solid_count - hollow_count
        
        user_stats = UserStats(
            total_discovered=total_discovered,
            solid_count=solid_count,
            hollow_count=hollow_count,
            raw_count=max(0, raw_count)
        )
        
        return MineExploreResponse(
            mode=mode,
            blocks=[Block(**block) for block in blocks],
            user_stats=user_stats,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_detail = str(e)
        traceback_str = traceback.format_exc()
        print(f"ERROR in explore_mine: {error_detail}")
        print(f"TRACEBACK: {traceback_str}")
        raise HTTPException(status_code=500, detail=f"Failed to explore mine: {error_detail}")


@router.get("/blocks/{sense_id}", response_model=BlockDetail)
async def get_block_detail(
    sense_id: str,
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db_session)
):
    """
    Get full block detail with connections and user progress.
    
    V2: Uses VocabularyStore for vocabulary data, falls back to Neo4j.
    NOTE: Frontend should use local vocabulary data for instant lookups.
    
    Args:
        sense_id: Sense.id (block identifier)
    """
    try:
        block_detail = None
        
        # Try VocabularyStore first (fast, in-memory)
        if vocabulary_store.is_loaded:
            block_detail = vocabulary_store.get_block_detail(sense_id)
            if not block_detail:
                raise HTTPException(status_code=404, detail=f"Block not found: {sense_id}")
        
        # Fallback to Neo4j
        elif NEO4J_AVAILABLE:
            neo4j = None
            try:
                neo4j = Neo4jConnection()
                mine_service = MineService(db, neo4j)
                block_detail = mine_service.get_block_detail(sense_id, user_id)
            finally:
                if neo4j:
                    neo4j.close()
        else:
            raise HTTPException(
                status_code=503,
                detail="Vocabulary data not available. Run export_vocabulary_json.py first."
            )
        
        # Get user progress for this block
        progress_result = db.execute(
            text("""
                SELECT 
                    lp.status,
                    lp.tier,
                    lp.learned_at
                FROM learning_progress lp
                WHERE lp.user_id = :user_id
                AND lp.learning_point_id = :sense_id
                LIMIT 1
            """),
            {'user_id': user_id, 'sense_id': sense_id}
        )
        
        progress_row = progress_result.fetchone()
        if progress_row:
            status = progress_row[0] or 'pending'
            mastery = 'mastered' if status == 'verified' else status
            block_detail['user_progress'] = {
                'status': status,
                'tier': progress_row[1],
                'started_at': progress_row[2].isoformat() if progress_row[2] else None,
                'mastery_level': mastery,
            }
        
        # Enrich connections with user status
        connection_sense_ids = [c['sense_id'] for c in block_detail.get('connections', []) if c.get('sense_id')]
        if connection_sense_ids:
            conn_progress_result = db.execute(
                text("""
                    SELECT 
                        learning_point_id,
                        status
                    FROM learning_progress
                    WHERE user_id = :user_id
                    AND learning_point_id = ANY(:sense_ids)
                """),
                {'user_id': user_id, 'sense_ids': connection_sense_ids}
            )
            
            progress_map = {}
            for row in conn_progress_result.fetchall():
                conn_sense_id = row[0]
                status = row[1] or 'pending'
                if status == 'verified':
                    progress_map[conn_sense_id] = 'solid'
                else:
                    progress_map[conn_sense_id] = 'hollow'
            
            # Add status to connections
            for conn in block_detail.get('connections', []):
                if conn.get('sense_id'):
                    conn['status'] = progress_map.get(conn['sense_id'], 'raw')
        
        return BlockDetail(**block_detail)
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get block detail: {str(e)}")


@router.post("/blocks/{sense_id}/start", response_model=StartForgingResponse)
async def start_forging(
    sense_id: str,
    request: Optional[StartForgingRequest] = Body(default=None),
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db_session),
):
    """
    Start forging a block (begin learning process).
    
    Creates learning_progress entry and verification schedule.
    
    Args:
        sense_id: Neo4j Sense.id (block identifier)
    """
    try:
        # Resolve effective learner_id: either a specific child or the parent's own learner profile
        effective_learner_id: Optional[UUID] = None

        # DEBUG: Log incoming request
        if os.getenv("DEBUG_LEARNER_PIPELINE") == "true":
            print(f"[start_forging] sense_id={sense_id}, request={request}, user_id={user_id}")
            if request:
                print(f"[start_forging] request.learner_id={request.learner_id}")

        if request and request.learner_id:
            # Security check: verify user is guardian/owner of this learner
            learner_check = db.execute(
                text(
                    """
                    SELECT id FROM public.learners
                    WHERE id = :learner_id
                      AND (guardian_id = :guardian_id OR user_id = :guardian_id)
                    """
                ),
                {"learner_id": request.learner_id, "guardian_id": user_id},
            ).fetchone()

            if not learner_check:
                raise HTTPException(
                    status_code=403,
                    detail="You can only start forging for learners you manage",
                )
            effective_learner_id = learner_check[0]
            if os.getenv("DEBUG_LEARNER_PIPELINE") == "true":
                print(f"[start_forging] Using provided learner_id: {effective_learner_id}")
        else:
            # Parent forging for themselves: use their own learner profile
            effective_learner_id = _get_learner_id_for_user(db, user_id)
            if os.getenv("DEBUG_LEARNER_PIPELINE") == "true":
                print(f"[start_forging] Auto-resolved learner_id: {effective_learner_id}")

        # Check if already exists for this learner
        # NOTE: We check by learner_id (not user_id) because progress is now keyed per learner
        if effective_learner_id is None:
            raise HTTPException(
                status_code=400,
                detail="Cannot start forging: No learner profile found. Please complete onboarding first."
            )
        
        existing_result = db.execute(
            text(
                """
                SELECT id, status
                FROM learning_progress
                WHERE learner_id = :learner_id
                  AND learning_point_id = :sense_id
                  AND tier = 1
                """
            ),
            {
                "learner_id": effective_learner_id,
                "sense_id": sense_id,
            },
        )

        existing = existing_result.fetchone()

        if existing:
            # Already exists - no deltas (already counted)
            return StartForgingResponse(
                success=True,
                learning_progress_id=existing[0],
                sense_id=sense_id,
                status=existing[1] or "pending",
                message="Block already in learning progress",
                delta_xp=0,
                delta_sparks=0,
                delta_discovered=0,
                delta_hollow=0,
            )

        # Create new learning progress entry
        # Default tier to 1 (can be refined based on block type later)
        if os.getenv("DEBUG_LEARNER_PIPELINE") == "true":
            print(f"[start_forging] Creating learning_progress: sense_id={sense_id}, learner_id={effective_learner_id}, user_id={user_id}")
        
        try:
            progress = create_learning_progress(
                session=db,
                user_id=user_id,
                learning_point_id=sense_id,
                tier=1,
                status="pending",
                learner_id=effective_learner_id,
            )
            
            if os.getenv("DEBUG_LEARNER_PIPELINE") == "true":
                print(f"[start_forging] Created learning_progress.id={progress.id}, learner_id={progress.learner_id}")
        except Exception as create_error:
            import traceback
            error_msg = str(create_error)
            traceback_str = traceback.format_exc()
            print(f"[start_forging] ERROR creating learning_progress: {error_msg}")
            print(f"[start_forging] TRACEBACK: {traceback_str}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to create learning progress: {error_msg}"
            )

        # Create verification schedule
        try:
            schedule = create_verification_schedule(
                session=db,
                user_id=user_id,
                learning_progress_id=progress.id,
                learning_point_id=sense_id,
                initial_difficulty=0.5,
            )
            if os.getenv("DEBUG_LEARNER_PIPELINE") == "true":
                print(f"[start_forging] Created verification_schedule.id={schedule.id}")
        except Exception as schedule_error:
            import traceback
            error_msg = str(schedule_error)
            traceback_str = traceback.format_exc()
            print(f"[start_forging] ERROR creating verification_schedule: {error_msg}")
            print(f"[start_forging] TRACEBACK: {traceback_str}")
            # Rollback the learning_progress creation
            db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Failed to create verification schedule: {error_msg}"
            )

        # Delta Strategy: Award discovery bonus (5 XP, 1 spark for new word)
        DISCOVERY_XP = 5
        DISCOVERY_SPARKS = 1

        return StartForgingResponse(
            success=True,
            learning_progress_id=progress.id,
            sense_id=sense_id,
            status=progress.status or "pending",
            message="Started forging block successfully",
            delta_xp=DISCOVERY_XP,
            delta_sparks=DISCOVERY_SPARKS,
            delta_discovered=1,
            delta_hollow=1,
        )

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_detail = str(e)
        traceback_str = traceback.format_exc()
        print(f"ERROR in start_forging: {error_detail}")
        print(f"TRACEBACK: {traceback_str}")
        raise HTTPException(status_code=500, detail=f"Failed to start forging: {error_detail}")


@router.get("/debug/learner-progress/{learner_id}")
async def debug_learner_progress(
    learner_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db_session)
):
    """
    DEBUG ENDPOINT: Check what progress rows exist for a learner_id.
    
    This helps verify that start_forging is creating rows with the correct learner_id
    and that get_user_progress can find them.
    
    Returns:
    - Raw database rows for this learner_id
    - Count of rows
    - Sample sense_ids
    """
    try:
        # Security check: verify user is guardian/owner of this learner
        learner_check = db.execute(
            text("""
                SELECT id FROM public.learners
                WHERE id = :learner_id
                  AND (guardian_id = :guardian_id OR user_id = :guardian_id)
            """),
            {'learner_id': learner_id, 'guardian_id': user_id}
        ).fetchone()
        
        if not learner_check:
            raise HTTPException(
                status_code=403,
                detail="You can only view progress for learners you manage"
            )
        
        # Query all progress rows for this learner
        result = db.execute(
            text("""
                SELECT 
                    lp.id,
                    lp.learning_point_id as sense_id,
                    lp.status,
                    lp.tier,
                    lp.learner_id,
                    lp.user_id,
                    lp.learned_at
                FROM learning_progress lp
                WHERE lp.learner_id = :learner_id
                ORDER BY lp.learned_at DESC
                LIMIT 50
            """),
            {'learner_id': learner_id}
        )
        
        rows = result.fetchall()
        
        return {
            "learner_id": str(learner_id),
            "total_rows": len(rows),
            "rows": [
                {
                    "id": row[0],
                    "sense_id": row[1],
                    "status": row[2],
                    "tier": row[3],
                    "learner_id": str(row[4]) if row[4] else None,
                    "user_id": str(row[5]) if row[5] else None,
                    "learned_at": row[6].isoformat() if row[6] else None,
                }
                for row in rows
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Debug query failed: {str(e)}")


@router.post("/batch")
async def mine_batch(
    request: MineBatchRequest,
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db_session)
):
    """
    Mine a batch of words (Phase 5b - Backend Persistence).
    
    Creates learning progress entries for mined words and awards points.
    
    Request Body:
        - sense_ids: List of sense IDs to mine
        - tier: Tier level (default 1)
    
    Returns:
        - success: bool
        - mined_count: int (newly added)
        - skipped_count: int (already existed)
        - new_wallet_balance: dict with current balance
        - xp_gained: int
    """
    try:
        # Validate input
        if not request.sense_ids:
            raise HTTPException(status_code=400, detail="sense_ids cannot be empty")
        
        if len(request.sense_ids) > 100:
            raise HTTPException(status_code=400, detail="Cannot mine more than 100 words at once")
        
        # Use MineService to process
        if NEO4J_AVAILABLE:
            mine_service = MineService(db)
        else:
            # Fallback: process without Neo4j
            from ..services.mine import MineService
            mine_service = MineService(db, neo4j=None)
        
        result = mine_service.process_mining_batch(
            user_id=user_id,
            sense_ids=request.sense_ids,
            tier=request.tier
        )
        
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"Error in mine_batch: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to mine batch: {str(e)}")

