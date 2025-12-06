"""
Survey API Endpoints for LexiSurvey V3 (Progressive Survey Model)

Implements the API layer for the LexiSurvey engine with PSM support:
- POST /api/v1/survey/start: Initialize a new survey session (with warm-start)
- POST /api/v1/survey/next: Process answer and get next question
- GET /api/v1/survey/history: Get user's survey history with progress

V3 Changes (Progressive Survey Model):
- Warm-start capability: Uses learning_progress data to reduce questions
- Multiple survey modes: cold_start, warm_start, quick_validation, deep_dive
- Survey metadata tracking for testimonials
- Previous survey comparison for progress visualization
"""

import uuid
import json
import logging
from datetime import datetime
from typing import Optional, Generator, List
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

# V2: Use the probability-based engine (now the main engine)
from src.survey.lexisurvey_engine import LexiSurveyEngine
from src.survey.models import SurveyState, AnswerSubmission, SurveyResult
from src.database.postgres_connection import PostgresConnection

# Neo4j is optional - VocabularyStore can be used as fallback
try:
    from src.database.neo4j_connection import Neo4jConnection
    NEO4J_AVAILABLE = True
except (ImportError, ValueError):
    NEO4J_AVAILABLE = False
    Neo4jConnection = None

# VocabularyStore fallback
try:
    from src.services.vocabulary_store import vocabulary_store
    VOCABULARY_STORE_AVAILABLE = vocabulary_store.is_loaded
except ImportError:
    VOCABULARY_STORE_AVAILABLE = False

# V3: Progressive Survey Model (warm-start)
from src.survey.warm_start import (
    initialize_warm_start,
    get_stopping_config,
    count_verified_between_surveys,
    calculate_efficiency_score,
    generate_efficiency_message,
    WarmStartResult,
    FREQUENCY_BANDS,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/survey", tags=["LexiSurvey"])

# Singleton instances
_engine: Optional[LexiSurveyEngine] = None
_postgres_conn: Optional[PostgresConnection] = None
_neo4j_conn: Optional[Neo4jConnection] = None

# Default anonymous user UUID for MVP
ANONYMOUS_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000000")


# --- Request Models ---
class StartSurveyRequest(BaseModel):
    """Request to start a new survey session."""
    cefr_level: Optional[str] = Field(
        default=None,
        description="CEFR level for calibration: A1, A2, B1, B2, C1, C2"
    )
    user_id: Optional[str] = Field(
        default=None,
        description="User UUID. In production, get from Auth Middleware"
    )
    # V3: Progressive Survey Model options
    survey_mode: Optional[str] = Field(
        default=None,
        description="Force survey mode: cold_start, warm_start, quick_validation, deep_dive. Auto-detected if not provided."
    )
    use_prior_knowledge: bool = Field(
        default=True,
        description="Whether to use learning_progress data for warm-start"
    )


# --- Dependency Injection ---
def get_engine() -> LexiSurveyEngine:
    """
    Creates a fresh instance of the engine with a Neo4j connection.
    
    Uses probability-based vocabulary estimation (V2 methodology).
    Falls back to VocabularyStore if Neo4j is not available.
    """
    global _engine, _neo4j_conn
    if _engine is None:
        # Try Neo4j first
        if NEO4J_AVAILABLE:
            try:
                if _neo4j_conn is None:
                    _neo4j_conn = Neo4jConnection()
                _engine = LexiSurveyEngine(_neo4j_conn)
                logger.info("Survey engine initialized with Neo4j")
            except Exception as e:
                logger.warning(f"Neo4j connection failed: {e}")
                if VOCABULARY_STORE_AVAILABLE:
                    _engine = LexiSurveyEngine(conn=None, use_vocabulary_store=True)
                    logger.info("Survey engine initialized with VocabularyStore fallback")
                else:
                    raise
        elif VOCABULARY_STORE_AVAILABLE:
            _engine = LexiSurveyEngine(conn=None, use_vocabulary_store=True)
            logger.info("Survey engine initialized with VocabularyStore (no Neo4j)")
        else:
            raise ValueError(
                "Neither Neo4j nor VocabularyStore available. "
                "Set NEO4J_* environment variables or run export_vocabulary_json.py"
            )
    return _engine


def get_postgres_conn() -> PostgresConnection:
    """Get or create the PostgresConnection instance (singleton)."""
    global _postgres_conn
    if _postgres_conn is None:
        _postgres_conn = PostgresConnection()
    return _postgres_conn


def get_db_session() -> Generator[Session, None, None]:
    """Get a database session (dependency for FastAPI)."""
    conn = get_postgres_conn()
    session = conn.get_session()
    try:
        yield session
    finally:
        session.close()


def _cefr_to_start_rank(cefr_level: Optional[str]) -> int:
    """
    Map CEFR level to starting rank.
    
    Args:
        cefr_level: CEFR level ('A1', 'A2', 'B1', 'B2', 'C1', 'C2') or None
        
    Returns:
        Starting rank (1-8000)
    """
    if not cefr_level:
        return 2000  # Default Market Median
    
    mapping = {
        "A1": 1000, "A2": 1500,
        "B1": 3500, "B2": 4500,
        "C1": 5500, "C2": 6500
    }
    return mapping.get(cefr_level.upper(), 2000)


@router.post("/start", response_model=SurveyResult)
async def start_survey(req: StartSurveyRequest, db: Session = Depends(get_db_session)):
    """
    Initializes a new Survey Session with Progressive Survey Model support.
    
    V3 Flow:
    1. Parse user_id
    2. Initialize warm-start (if authenticated user with learning data)
    3. Create DB session with survey_mode and prior_knowledge
    4. Initialize state with warm-start band_performance
    5. Generate first question
    6. Persist to PostgreSQL
    """
    # 1. Calibration Logic (Map CEFR to Rank)
    start_rank = _cefr_to_start_rank(req.cefr_level)
    
    # 2. Handle user_id
    if req.user_id:
        try:
            user_uuid = uuid.UUID(req.user_id)
        except ValueError:
            user_uuid = ANONYMOUS_USER_ID
    else:
        user_uuid = ANONYMOUS_USER_ID
    
    # 3. V3: Initialize warm-start if authenticated and using prior knowledge
    warm_start: Optional[WarmStartResult] = None
    survey_mode = "cold_start"
    initial_confidence = 0.0
    band_performance = None
    
    if user_uuid != ANONYMOUS_USER_ID and req.use_prior_knowledge:
        try:
            # Create temporary session ID for warm-start (will be replaced with real one)
            temp_session_id = uuid.uuid4()
            warm_start = initialize_warm_start(
                db=db,
                user_id=user_uuid,
                current_session_id=temp_session_id,
                force_mode=req.survey_mode,
            )
            survey_mode = warm_start.survey_mode
            initial_confidence = warm_start.initial_confidence
            band_performance = warm_start.band_performance
            
            logger.info(
                f"Survey warm-start: mode={survey_mode}, "
                f"prior_verified={warm_start.prior_knowledge.total_verified}, "
                f"initial_confidence={initial_confidence:.2f}"
            )
        except Exception as e:
            logger.warning(f"Warm-start initialization failed, falling back to cold_start: {e}")
            survey_mode = "cold_start"
    elif req.survey_mode == "deep_dive":
        # Allow deep_dive mode even for anonymous users
        survey_mode = "deep_dive"
    
    # 4. Create Session in Database (UUID primary key) with survey_mode
    try:
        # Try to insert with survey_mode column (V3 schema)
        try:
            result = db.execute(
                text("""
                    INSERT INTO survey_sessions (user_id, current_rank, status, start_time, survey_mode, prior_knowledge)
                    VALUES (:user_id, :current_rank, 'active', NOW(), :survey_mode, CAST(:prior_knowledge AS jsonb))
                    RETURNING id
                """),
                {
                    "user_id": user_uuid,
                    "current_rank": start_rank,
                    "survey_mode": survey_mode,
                    "prior_knowledge": json.dumps(warm_start.prior_knowledge.to_dict()) if warm_start else None,
                }
            )
        except Exception:
            # Fallback for older schema without survey_mode column
            result = db.execute(
                text("""
                    INSERT INTO survey_sessions (user_id, current_rank, status, start_time)
                    VALUES (:user_id, :current_rank, 'active', NOW())
                    RETURNING id
                """),
                {
                    "user_id": user_uuid,
                    "current_rank": start_rank,
                }
            )
        
        db_session_id = result.scalar()
        session_id = str(db_session_id)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create survey session: {str(e)}"
        )
    
    # 5. Initialize State (V3: includes warm-start band_performance)
    state = SurveyState(
        session_id=session_id,
        current_rank=start_rank,
        low_bound=1,
        high_bound=8000,
        history=[],
        band_performance=band_performance,  # V3: From warm-start if available
        phase=1,  # Deprecated in V2, kept for compatibility
        confidence=initial_confidence,  # V3: Start with prior confidence
        estimated_vocab=0,  # V3: Will be recalculated
        pivot_triggered=False,
    )
    
    # 6. Generate First Question (Engine Step)
    engine = get_engine()
    result = engine.process_step(state, previous_answer=None)
    
    # 7. Add warm-start debug info to result
    if warm_start and result.debug_info:
        result.debug_info["survey_mode"] = survey_mode
        result.debug_info["prior_verified_words"] = warm_start.prior_knowledge.total_verified
        result.debug_info["initial_confidence"] = round(initial_confidence, 3)
        result.debug_info["stopping_config"] = warm_start.stopping_config
    elif result.debug_info:
        result.debug_info["survey_mode"] = survey_mode
    
    # 8. Persist to PostgreSQL
    try:
        # Create History Record (Empty initially, or with first step if needed)
        db.execute(
            text("""
                INSERT INTO survey_history (session_id, history)
                VALUES (:session_id, CAST(:history AS jsonb))
            """),
            {
                "session_id": db_session_id,
                "history": json.dumps([h for h in state.history]),  # Already dicts
            }
        )
        
        # Store the first question payload if it exists
        if result.payload:
            try:
                # Include metadata in options when serializing
                options_with_metadata = []
                option_metadata = getattr(result.payload, '_option_metadata', {})
                for opt in result.payload.options:
                    opt_dict = opt.dict()
                    # Attach metadata if available for this option
                    if opt.id in option_metadata:
                        opt_dict.update(option_metadata[opt.id])
                    options_with_metadata.append(opt_dict)
                
                db.execute(
                    text("""
                        INSERT INTO survey_questions 
                        (session_id, question_id, question_number, word, rank, phase, options, time_limit)
                        VALUES (:session_id, :question_id, :question_number, :word, :rank, :phase, 
                                CAST(:options AS jsonb), :time_limit)
                    """),
                    {
                        "session_id": db_session_id,
                        "question_id": result.payload.question_id,
                        "question_number": 1,
                        "word": result.payload.word,
                        "rank": result.payload.rank,
                        "phase": 1,
                        "options": json.dumps(options_with_metadata),
                        "time_limit": result.payload.time_limit,
                    }
                )
            except Exception as e:
                print(f"Warning: Failed to store first question: {e}")
        
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save survey history: {str(e)}"
        )
    
    return result


@router.post("/next", response_model=SurveyResult)
async def next_question(
    submission: AnswerSubmission,
    session_id: str,
    db: Session = Depends(get_db_session)
):
    """
    Processes an answer and returns the next step.
    1. Loads history from DB.
    2. Runs Engine logic (Grade -> Algo -> Fetch).
    3. Updates DB.
    """
    engine = get_engine()
    
    # 1. Fetch Session & History from Postgres
    try:
        # Parse session_id as UUID
        try:
            db_session_id = uuid.UUID(session_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid session_id format")
        
        result = db.execute(
            text("""
                SELECT s.current_rank, s.status, h.history 
                FROM survey_sessions s
                LEFT JOIN survey_history h ON s.id = h.session_id
                WHERE s.id = :session_id
            """),
            {"session_id": db_session_id}
        )
        
        row = result.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Session not found")
        
        current_rank, status, history_json = row
        
        if status == 'completed':
            raise HTTPException(status_code=400, detail="Survey already completed")
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load session: {str(e)}"
        )
    
    # 2. Rehydrate State
    # History is already a list of dicts from JSONB
    history = history_json if history_json else []
    
    # Reconstruct bounds, phase, confidence from history
    low_bound = 1
    high_bound = 8000
    phase = 1
    confidence = 0.0
    pivot_triggered = False
    
    if history:
        # Calculate bounds from history
        correct_ranks = [h["rank"] for h in history if h.get("correct", False)]
        incorrect_ranks = [h["rank"] for h in history if not h.get("correct", False)]
        
        if correct_ranks:
            low_bound = max(correct_ranks)
        if incorrect_ranks:
            high_bound = min(incorrect_ranks)
        
        # Determine phase from question count
        question_count = len(history)
        if question_count < 5:
            phase = 1
        elif question_count < 12:
            phase = 2
        else:
            phase = 3
        
        # Calculate confidence
        correct_count = sum(1 for h in history if h.get("correct", False))
        confidence = correct_count / len(history) if len(history) > 0 else 0.0
    
    # V2: Reconstruct band_performance from history if available
    band_performance = None
    if history:
        bands = [1000, 2000, 3000, 4000, 5000, 6000, 7000, 8000]
        band_performance = {band: {"tested": 0, "correct": 0} for band in bands}
        for h in history:
            # Get band from history or calculate from rank
            band = h.get("band")
            if band is None:
                rank = h.get("rank", 0)
                for b in bands:
                    if rank <= b:
                        band = b
                        break
                if band is None:
                    band = bands[-1]
            if band in band_performance:
                band_performance[band]["tested"] += 1
                if h.get("correct", False):
                    band_performance[band]["correct"] += 1
    
    state = SurveyState(
        session_id=session_id,
        current_rank=current_rank or 2000,
        low_bound=low_bound,
        high_bound=high_bound,
        history=history,
        band_performance=band_performance,  # V2: Band tracking
        phase=phase,  # Deprecated in V2
        confidence=confidence,
        estimated_vocab=0,  # V2: Will be recalculated
        pivot_triggered=pivot_triggered,
    )
    
    # 3. Fetch Question Details for Grading
    question_details = None
    try:
        # Fetch the question that was answered to grade it properly
        q_result = db.execute(
            text("""
                SELECT word, rank, phase, options, question_number
                FROM survey_questions
                WHERE question_id = :question_id
                LIMIT 1
            """),
            {"question_id": submission.question_id}
        )
        q_row = q_result.fetchone()
        
        if q_row:
            question_details = {
                "word": q_row[0],
                "rank": q_row[1],
                "phase": q_row[2],
                "options": q_row[3] if isinstance(q_row[3], list) else json.loads(q_row[3]),
                "question_number": q_row[4]
            }
    except Exception as e:
        print(f"Warning: Could not fetch question details: {e}")
    
    # 4. Run Engine Logic
    # This grades the answer and calculates the next step
    try:
        result = engine.process_step(
            state, 
            previous_answer=submission, 
            question_details=question_details
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process survey step: {str(e)}"
        )
    
    # 5. Update Database
    try:
        # Update History (Append new interactions)
        db.execute(
            text("""
                UPDATE survey_history 
                SET history = CAST(:history AS jsonb),
                    updated_at = NOW()
                WHERE session_id = :session_id
            """),
            {
                "session_id": db_session_id,
                "history": json.dumps(state.history),
            }
        )
        
        # Update Rank & Status
        db.execute(
            text("""
                UPDATE survey_sessions 
                SET current_rank = :current_rank,
                    status = :status,
                    updated_at = NOW()
                WHERE id = :session_id
            """),
            {
                "session_id": db_session_id,
                "current_rank": state.current_rank,
                "status": result.status,
            }
        )
        
        # Store the new question payload if it exists
        if result.payload:
            try:
                db.execute(
                    text("""
                        INSERT INTO survey_questions 
                        (session_id, question_id, question_number, word, rank, phase, options, time_limit)
                        VALUES (:session_id, :question_id, :question_number, :word, :rank, :phase, 
                                CAST(:options AS jsonb), :time_limit)
                        ON CONFLICT (session_id, question_id) DO NOTHING
                    """),
                    {
                        "session_id": db_session_id,
                        "question_id": result.payload.question_id,
                        "question_number": len(state.history) + 1,  # Next question number
                        "word": result.payload.word,
                        "rank": result.payload.rank,
                        "phase": state.phase,  # Current phase
                        "options": json.dumps([
                            {**opt.dict(), **(getattr(result.payload, '_option_metadata', {}).get(opt.id, {}))}
                            for opt in result.payload.options
                        ]),
                        "time_limit": result.payload.time_limit,
                    }
                )
            except Exception as e:
                print(f"Warning: Failed to store question payload: {e}")
        
        # If Complete, Save Results and Metadata
        if result.status == 'complete' and result.metrics:
            # Save survey results
            db.execute(
                text("""
                    INSERT INTO survey_results (session_id, volume, reach, density, cefr_level)
                    VALUES (:session_id, :volume, :reach, :density, :cefr_level)
                    ON CONFLICT (session_id) DO UPDATE
                    SET volume = EXCLUDED.volume,
                        reach = EXCLUDED.reach,
                        density = EXCLUDED.density,
                        cefr_level = EXCLUDED.cefr_level
                """),
                {
                    "session_id": db_session_id,
                    "volume": result.metrics.volume,
                    "reach": result.metrics.reach,
                    "density": result.metrics.density,
                    "cefr_level": None,  # Could extract from request if stored
                }
            )
            
            # V3: Save survey metadata for PSM
            try:
                # Get user_id and survey_mode from session
                session_info = db.execute(
                    text("""
                        SELECT user_id, survey_mode, prior_knowledge, start_time
                        FROM survey_sessions WHERE id = :session_id
                    """),
                    {"session_id": db_session_id}
                ).fetchone()
                
                if session_info:
                    user_id, survey_mode, prior_knowledge_json, start_time = session_info
                    survey_mode = survey_mode or "cold_start"
                    
                    # Calculate metadata
                    questions_asked = len(state.history)
                    final_confidence = state.confidence
                    time_taken = int((datetime.now() - start_time).total_seconds()) if start_time else None
                    
                    # Extract prior knowledge stats
                    prior_verified = 0
                    prior_bands_with_data = 0
                    prior_confidence = 0.0
                    if prior_knowledge_json:
                        pk = prior_knowledge_json if isinstance(prior_knowledge_json, dict) else json.loads(prior_knowledge_json)
                        prior_verified = pk.get("total_verified", 0)
                        prior_bands_with_data = pk.get("bands_with_data", 0)
                        # Estimate questions saved (warm-start vs cold-start)
                        cold_start_avg = 25  # Average questions for cold-start
                        questions_saved = max(0, cold_start_avg - questions_asked) if survey_mode != "cold_start" else 0
                    else:
                        questions_saved = 0
                    
                    # Get previous survey for comparison
                    prev_survey = None
                    improvement_volume = None
                    improvement_reach = None
                    improvement_density = None
                    days_since_last = None
                    verified_between = None
                    efficiency_score = None
                    
                    if user_id and user_id != ANONYMOUS_USER_ID:
                        prev_result = db.execute(
                            text("""
                                SELECT ss.id, ss.start_time, sr.volume, sr.reach, sr.density
                                FROM survey_sessions ss
                                JOIN survey_results sr ON sr.session_id = ss.id
                                WHERE ss.user_id = :user_id
                                AND ss.status = 'completed'
                                AND ss.id != :current_id
                                ORDER BY ss.start_time DESC LIMIT 1
                            """),
                            {"user_id": user_id, "current_id": db_session_id}
                        ).fetchone()
                        
                        if prev_result:
                            prev_session_id, prev_date, prev_volume, prev_reach, prev_density = prev_result
                            prev_survey = prev_session_id
                            improvement_volume = result.metrics.volume - prev_volume
                            improvement_reach = result.metrics.reach - prev_reach
                            improvement_density = result.metrics.density - float(prev_density) if prev_density else None
                            days_since_last = (datetime.now() - prev_date).days if prev_date else None
                            
                            # Count verified words between surveys
                            if prev_date:
                                verified_between = count_verified_between_surveys(
                                    db, user_id, prev_date, datetime.now()
                                )
                                
                                # Calculate efficiency score
                                if days_since_last and days_since_last > 0:
                                    efficiency_score = calculate_efficiency_score(
                                        improvement_volume or 0,
                                        verified_between,
                                        days_since_last
                                    )
                    
                    # Insert survey metadata
                    db.execute(
                        text("""
                            INSERT INTO survey_metadata (
                                session_id, survey_mode,
                                prior_verified_words, prior_bands_with_data, prior_confidence,
                                questions_asked, questions_saved_by_prior, time_taken_seconds, final_confidence,
                                previous_session_id, improvement_volume, improvement_reach, improvement_density,
                                days_since_last_survey, verified_words_between_surveys,
                                learning_days_between_surveys, efficiency_score
                            ) VALUES (
                                :session_id, :survey_mode,
                                :prior_verified, :prior_bands, :prior_conf,
                                :questions, :questions_saved, :time_taken, :final_conf,
                                :prev_session, :imp_volume, :imp_reach, :imp_density,
                                :days_since, :verified_between,
                                :learning_days, :efficiency
                            )
                            ON CONFLICT (session_id) DO UPDATE SET
                                survey_mode = EXCLUDED.survey_mode,
                                questions_asked = EXCLUDED.questions_asked,
                                final_confidence = EXCLUDED.final_confidence
                        """),
                        {
                            "session_id": db_session_id,
                            "survey_mode": survey_mode,
                            "prior_verified": prior_verified,
                            "prior_bands": prior_bands_with_data,
                            "prior_conf": prior_confidence,
                            "questions": questions_asked,
                            "questions_saved": questions_saved,
                            "time_taken": time_taken,
                            "final_conf": final_confidence,
                            "prev_session": prev_survey,
                            "imp_volume": improvement_volume,
                            "imp_reach": improvement_reach,
                            "imp_density": improvement_density,
                            "days_since": days_since_last,
                            "verified_between": verified_between,
                            "learning_days": days_since_last,  # Simplified: assume all days are learning days
                            "efficiency": efficiency_score,
                        }
                    )
                    
                    # Add PSM metadata to result for frontend
                    if result.debug_info is None:
                        result.debug_info = {}
                    result.debug_info["survey_metadata"] = {
                        "survey_mode": survey_mode,
                        "questions_asked": questions_asked,
                        "questions_saved": questions_saved,
                        "time_taken_seconds": time_taken,
                        "prior_verified_words": prior_verified,
                        "improvement": {
                            "volume": improvement_volume,
                            "reach": improvement_reach,
                            "density": improvement_density,
                        } if improvement_volume is not None else None,
                        "efficiency_score": efficiency_score,
                        "efficiency_message": generate_efficiency_message(
                            efficiency_score, improvement_volume or 0, days_since_last or 0
                        ) if improvement_volume is not None else None,
                    }
                    
            except Exception as e:
                logger.warning(f"Failed to save survey metadata: {e}")
                # Don't fail the whole request if metadata fails
        
        db.commit()
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update database: {str(e)}"
        )
    
    return result


# --- V3: Survey History Endpoints ---

class SurveyHistoryEntry(BaseModel):
    """Single entry in survey history."""
    session_id: str
    date: datetime
    survey_mode: str
    volume: int
    reach: int
    density: float
    questions_asked: Optional[int]
    time_taken_seconds: Optional[int]
    improvement_volume: Optional[int]
    improvement_reach: Optional[int]
    days_since_last: Optional[int]
    efficiency_score: Optional[float]


class SurveyHistoryResponse(BaseModel):
    """Response for survey history endpoint."""
    user_id: str
    survey_count: int
    surveys: List[SurveyHistoryEntry]
    summary: Optional[dict]


@router.get("/history", response_model=SurveyHistoryResponse)
async def get_survey_history(
    user_id: str = Query(..., description="User UUID"),
    db: Session = Depends(get_db_session)
):
    """
    Get user's survey history with progress tracking.
    
    Returns all completed surveys for the user with improvement metrics.
    """
    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user_id format")
    
    try:
        # Query survey history with metadata
        result = db.execute(
            text("""
                SELECT 
                    ss.id as session_id,
                    ss.start_time as date,
                    COALESCE(ss.survey_mode, 'cold_start') as survey_mode,
                    sr.volume,
                    sr.reach,
                    sr.density,
                    sm.questions_asked,
                    sm.time_taken_seconds,
                    sm.improvement_volume,
                    sm.improvement_reach,
                    sm.days_since_last_survey,
                    sm.efficiency_score
                FROM survey_sessions ss
                JOIN survey_results sr ON sr.session_id = ss.id
                LEFT JOIN survey_metadata sm ON sm.session_id = ss.id
                WHERE ss.user_id = :user_id
                AND ss.status = 'completed'
                ORDER BY ss.start_time DESC
            """),
            {"user_id": user_uuid}
        )
        
        rows = result.fetchall()
        
        surveys = []
        for row in rows:
            surveys.append(SurveyHistoryEntry(
                session_id=str(row[0]),
                date=row[1],
                survey_mode=row[2],
                volume=row[3],
                reach=row[4],
                density=float(row[5]) if row[5] else 0.0,
                questions_asked=row[6],
                time_taken_seconds=row[7],
                improvement_volume=row[8],
                improvement_reach=row[9],
                days_since_last=row[10],
                efficiency_score=float(row[11]) if row[11] else None,
            ))
        
        # Calculate summary
        summary = None
        if len(surveys) >= 2:
            first = surveys[-1]  # Oldest
            latest = surveys[0]  # Newest
            total_growth = latest.volume - first.volume
            total_days = (latest.date - first.date).days if latest.date and first.date else 0
            
            summary = {
                "total_surveys": len(surveys),
                "first_volume": first.volume,
                "latest_volume": latest.volume,
                "total_growth": total_growth,
                "total_days": total_days,
                "avg_daily_growth": round(total_growth / total_days, 1) if total_days > 0 else 0,
                "growth_percentage": round((total_growth / first.volume) * 100, 1) if first.volume > 0 else 0,
            }
        
        return SurveyHistoryResponse(
            user_id=user_id,
            survey_count=len(surveys),
            surveys=surveys,
            summary=summary,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch survey history: {str(e)}"
        )
