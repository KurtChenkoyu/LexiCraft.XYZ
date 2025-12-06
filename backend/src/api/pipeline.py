"""
Pipeline API Endpoints

Provides REST API for monitoring and controlling the vocabulary pipeline.

Endpoints:
- GET /api/pipeline/status - Get current pipeline status
- POST /api/pipeline/start - Start the pipeline (background)
- POST /api/pipeline/stop - Request pipeline to stop
"""

import subprocess
import sys
from pathlib import Path
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional

from src.pipeline.status import get_status_manager, PipelineState


router = APIRouter(prefix="/api/pipeline", tags=["pipeline"])


class PipelineStatusResponse(BaseModel):
    """Pipeline status response."""
    state: str
    started_at: Optional[str]
    updated_at: Optional[str]
    completed_at: Optional[str]
    total_words: int
    processed_words: int
    current_word: Optional[str]
    progress_percent: float
    eta_minutes: Optional[float]
    total_senses: int
    validated_senses: int
    failed_senses: int
    errors: int
    last_error: Optional[str]
    ai_calls: int
    estimated_cost_usd: float
    run_id: Optional[str]


class StartRequest(BaseModel):
    """Request to start the pipeline."""
    limit: Optional[int] = None
    test_mode: bool = False
    daemon_mode: bool = True
    workers: int = 10


class ActionResponse(BaseModel):
    """Response for pipeline actions."""
    success: bool
    message: str


@router.get("/status", response_model=PipelineStatusResponse)
async def get_pipeline_status():
    """Get current pipeline status."""
    status_manager = get_status_manager()
    status = status_manager.get_status()
    
    return PipelineStatusResponse(
        state=status.state,
        started_at=status.started_at,
        updated_at=status.updated_at,
        completed_at=status.completed_at,
        total_words=status.total_words,
        processed_words=status.processed_words,
        current_word=status.current_word,
        progress_percent=status.progress_percent,
        eta_minutes=status.eta_minutes,
        total_senses=status.total_senses,
        validated_senses=status.validated_senses,
        failed_senses=status.failed_senses,
        errors=status.errors,
        last_error=status.last_error,
        ai_calls=status.ai_calls,
        estimated_cost_usd=status.estimated_cost_usd,
        run_id=status.run_id
    )


def _run_pipeline_process(limit: Optional[int], test_mode: bool, daemon_mode: bool, workers: int = 10):
    """Run the pipeline in a subprocess."""
    script_path = Path(__file__).parent.parent.parent / 'scripts' / 'enrich_vocabulary_v2.py'
    
    cmd = [sys.executable, str(script_path)]
    
    if test_mode:
        cmd.append('--test')
    if limit:
        cmd.extend(['--limit', str(limit)])
    if daemon_mode:
        cmd.append('--daemon')
    else:
        cmd.append('--resume')
    cmd.extend(['--workers', str(workers)])
    
    # Run in background
    subprocess.Popen(
        cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True
    )


@router.post("/start", response_model=ActionResponse)
async def start_pipeline(request: StartRequest, background_tasks: BackgroundTasks):
    """
    Start the vocabulary pipeline.
    
    The pipeline runs in the background and can be monitored via /status.
    """
    status_manager = get_status_manager()
    
    # Check if already running
    if status_manager.is_running():
        raise HTTPException(
            status_code=409,
            detail="Pipeline is already running. Use /stop to stop it first."
        )
    
    # Clear any old stop requests
    status_manager.clear_stop_request()
    
    # Start the pipeline in a subprocess
    _run_pipeline_process(
        limit=request.limit,
        test_mode=request.test_mode,
        daemon_mode=request.daemon_mode,
        workers=request.workers
    )
    
    return ActionResponse(
        success=True,
        message=f"Pipeline started. Limit: {request.limit or 'ALL'}, Mode: {'test' if request.test_mode else 'production'}, Workers: {request.workers}"
    )


@router.post("/stop", response_model=ActionResponse)
async def stop_pipeline():
    """
    Request the pipeline to stop gracefully.
    
    The pipeline will finish processing the current word and then stop.
    Progress is saved and can be resumed later.
    """
    status_manager = get_status_manager()
    
    if not status_manager.is_running():
        return ActionResponse(
            success=False,
            message="Pipeline is not running"
        )
    
    status_manager.request_stop()
    
    return ActionResponse(
        success=True,
        message="Stop requested. Pipeline will stop after current word completes."
    )


@router.post("/reset", response_model=ActionResponse)
async def reset_pipeline():
    """
    Reset pipeline status to idle.
    
    Use this if the pipeline is stuck in a bad state.
    """
    status_manager = get_status_manager()
    
    if status_manager.is_running():
        raise HTTPException(
            status_code=409,
            detail="Cannot reset while pipeline is running. Stop it first."
        )
    
    status_manager.reset()
    
    return ActionResponse(
        success=True,
        message="Pipeline status reset to idle"
    )

