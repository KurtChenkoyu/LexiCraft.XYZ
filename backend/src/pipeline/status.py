"""
Pipeline Status Manager

Tracks the status of the vocabulary pipeline and provides
a way to query progress from the API or command line.
"""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
from dataclasses import dataclass, asdict
from enum import Enum
import fcntl


class PipelineState(str, Enum):
    """Pipeline states."""
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    STOPPED = "stopped"


@dataclass
class PipelineStatus:
    """Current pipeline status."""
    state: str = PipelineState.IDLE.value
    started_at: Optional[str] = None
    updated_at: Optional[str] = None
    completed_at: Optional[str] = None
    
    # Progress tracking
    total_words: int = 0
    processed_words: int = 0
    current_word: Optional[str] = None
    
    # Sense tracking
    total_senses: int = 0
    validated_senses: int = 0
    failed_senses: int = 0
    
    # Error tracking
    errors: int = 0
    last_error: Optional[str] = None
    last_error_at: Optional[str] = None
    consecutive_errors: int = 0
    
    # API usage
    ai_calls: int = 0
    estimated_cost_usd: float = 0.0
    
    # Run info
    run_id: Optional[str] = None
    pid: Optional[int] = None
    
    @property
    def progress_percent(self) -> float:
        if self.total_words == 0:
            return 0.0
        return (self.processed_words / self.total_words) * 100
    
    @property
    def eta_minutes(self) -> Optional[float]:
        """Estimate time remaining in minutes."""
        if not self.started_at or self.processed_words == 0:
            return None
        
        try:
            started = datetime.fromisoformat(self.started_at)
            elapsed = (datetime.now() - started).total_seconds()
            words_remaining = self.total_words - self.processed_words
            time_per_word = elapsed / self.processed_words
            return (words_remaining * time_per_word) / 60
        except Exception:
            return None
    
    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d['progress_percent'] = round(self.progress_percent, 2)
        d['eta_minutes'] = round(self.eta_minutes, 1) if self.eta_minutes else None
        return d


class StatusManager:
    """Manages pipeline status with file-based persistence."""
    
    def __init__(self, status_dir: Optional[Path] = None):
        if status_dir is None:
            status_dir = Path(__file__).parent.parent.parent / 'logs'
        
        self.status_dir = Path(status_dir)
        self.status_dir.mkdir(parents=True, exist_ok=True)
        
        self.status_file = self.status_dir / 'pipeline_status.json'
        self.lock_file = self.status_dir / 'pipeline.lock'
        
        self._status: Optional[PipelineStatus] = None
    
    def _read_status(self) -> PipelineStatus:
        """Read status from file."""
        if self.status_file.exists():
            try:
                with open(self.status_file, 'r') as f:
                    data = json.load(f)
                return PipelineStatus(**data)
            except (json.JSONDecodeError, TypeError):
                pass
        return PipelineStatus()
    
    def _write_status(self, status: PipelineStatus):
        """Write status to file with file locking."""
        with open(self.status_file, 'w') as f:
            # Get exclusive lock
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
            try:
                json.dump(asdict(status), f, indent=2)
            finally:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)
    
    def get_status(self) -> PipelineStatus:
        """Get current pipeline status."""
        return self._read_status()
    
    def start_run(self, total_words: int, run_id: Optional[str] = None) -> PipelineStatus:
        """Mark the start of a pipeline run."""
        status = PipelineStatus(
            state=PipelineState.RUNNING.value,
            started_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            total_words=total_words,
            run_id=run_id or datetime.now().strftime('%Y%m%d_%H%M%S'),
            pid=os.getpid()
        )
        self._write_status(status)
        return status
    
    def update_progress(
        self,
        processed_words: int,
        current_word: str,
        total_senses: int = 0,
        validated_senses: int = 0,
        failed_senses: int = 0,
        ai_calls: int = 0,
        estimated_cost_usd: float = 0.0
    ):
        """Update progress during a run."""
        status = self._read_status()
        status.processed_words = processed_words
        status.current_word = current_word
        status.total_senses = total_senses
        status.validated_senses = validated_senses
        status.failed_senses = failed_senses
        status.ai_calls = ai_calls
        status.estimated_cost_usd = estimated_cost_usd
        status.updated_at = datetime.now().isoformat()
        status.consecutive_errors = 0  # Reset on successful progress
        self._write_status(status)
    
    def record_error(self, error_message: str):
        """Record an error."""
        status = self._read_status()
        status.errors += 1
        status.consecutive_errors += 1
        status.last_error = error_message[:500]  # Truncate long errors
        status.last_error_at = datetime.now().isoformat()
        status.updated_at = datetime.now().isoformat()
        self._write_status(status)
    
    def mark_paused(self):
        """Mark the pipeline as paused."""
        status = self._read_status()
        status.state = PipelineState.PAUSED.value
        status.updated_at = datetime.now().isoformat()
        self._write_status(status)
    
    def mark_completed(self):
        """Mark the pipeline as completed."""
        status = self._read_status()
        status.state = PipelineState.COMPLETED.value
        status.completed_at = datetime.now().isoformat()
        status.updated_at = datetime.now().isoformat()
        self._write_status(status)
    
    def mark_failed(self, error_message: str):
        """Mark the pipeline as failed."""
        status = self._read_status()
        status.state = PipelineState.FAILED.value
        status.last_error = error_message[:500]
        status.last_error_at = datetime.now().isoformat()
        status.updated_at = datetime.now().isoformat()
        self._write_status(status)
    
    def mark_stopped(self):
        """Mark the pipeline as stopped (user requested)."""
        status = self._read_status()
        status.state = PipelineState.STOPPED.value
        status.updated_at = datetime.now().isoformat()
        self._write_status(status)
    
    def is_running(self) -> bool:
        """Check if pipeline is currently running."""
        status = self._read_status()
        if status.state != PipelineState.RUNNING.value:
            return False
        
        # Check if the process is actually alive
        if status.pid:
            try:
                os.kill(status.pid, 0)  # Doesn't actually kill, just checks
                return True
            except OSError:
                # Process doesn't exist, mark as failed
                status.state = PipelineState.FAILED.value
                status.last_error = "Process died unexpectedly"
                status.updated_at = datetime.now().isoformat()
                self._write_status(status)
                return False
        
        return False
    
    def should_stop(self) -> bool:
        """Check if the pipeline should stop (user requested stop)."""
        stop_file = self.status_dir / 'pipeline_stop'
        return stop_file.exists()
    
    def request_stop(self):
        """Request the pipeline to stop gracefully."""
        stop_file = self.status_dir / 'pipeline_stop'
        stop_file.touch()
    
    def clear_stop_request(self):
        """Clear any stop request."""
        stop_file = self.status_dir / 'pipeline_stop'
        if stop_file.exists():
            stop_file.unlink()
    
    def reset(self):
        """Reset status to idle."""
        status = PipelineStatus()
        self._write_status(status)
        self.clear_stop_request()


# Singleton instance
_manager: Optional[StatusManager] = None


def get_status_manager() -> StatusManager:
    """Get the global status manager instance."""
    global _manager
    if _manager is None:
        _manager = StatusManager()
    return _manager


if __name__ == '__main__':
    # Test status manager
    manager = StatusManager()
    
    print("Current status:")
    status = manager.get_status()
    print(json.dumps(status.to_dict(), indent=2))

