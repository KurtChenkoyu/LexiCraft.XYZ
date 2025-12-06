"""
LexiSurvey Data Models (V8 - Probability-Based)

Pydantic models for survey state, questions, answers, and results.

V8 Changes:
- Added BandPerformance for frequency band tracking
- Updated SurveyState to track performance by band
- Removed fixed phase concept (now adaptive)
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class BandPerformance(BaseModel):
    """
    Track performance within a frequency band.
    
    Used for probability-based vocabulary estimation.
    Each band represents ~1000 words (e.g., 0-1000, 1000-2000, etc.)
    """
    tested: int = Field(default=0, ge=0, description="Number of words tested in this band")
    correct: int = Field(default=0, ge=0, description="Number of correct answers in this band")
    
    @property
    def accuracy(self) -> float:
        """Calculate accuracy rate for this band."""
        return self.correct / self.tested if self.tested > 0 else 0.5
    
    @property  
    def has_enough_samples(self) -> bool:
        """Check if band has enough samples for reliable estimate."""
        return self.tested >= 2
    
    class Config:
        json_schema_extra = {
            "example": {
                "tested": 4,
                "correct": 3
            }
        }


class SurveyState(BaseModel):
    """
    Survey session state tracking.
    
    V8: Uses probability-based approach with frequency band tracking
    instead of fixed phases and binary search.
    
    Tracks:
    - Performance by frequency band (for vocabulary estimation)
    - Question history with band information
    - Confidence level (determines when to stop)
    """
    session_id: str = Field(..., description="Unique session identifier")
    current_rank: int = Field(..., ge=1, le=8000, description="Current frequency rank being tested")
    low_bound: int = Field(default=1, ge=1, le=8000, description="Lower bound estimate")
    high_bound: int = Field(default=8000, ge=1, le=8000, description="Upper bound estimate")
    history: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of answer records: {rank, correct, time_taken, band, ...}"
    )
    
    # V8: Band-based tracking (replaces phase-based approach)
    band_performance: Optional[Dict[int, Dict[str, int]]] = Field(
        default=None,
        description="Performance by frequency band: {1000: {tested: N, correct: M}, ...}"
    )
    
    # Legacy phase field (kept for backward compatibility, not used in V8)
    phase: int = Field(
        default=1,
        ge=1,
        le=3,
        description="[DEPRECATED in V8] Current phase"
    )
    
    confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Current confidence level (0.0-1.0) - determines when to stop"
    )
    
    # V8: Track estimated vocabulary for convergence detection
    estimated_vocab: int = Field(
        default=0,
        ge=0,
        description="Current vocabulary size estimate"
    )
    
    pivot_triggered: bool = Field(
        default=False,
        description="[DEPRECATED in V8] Whether pivot was triggered"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "sess_12345",
                "current_rank": 3500,
                "low_bound": 2000,
                "high_bound": 4000,
                "history": [
                    {"rank": 2000, "correct": True, "time_taken": 4.5, "band": 2000},
                    {"rank": 3500, "correct": False, "time_taken": 8.2, "band": 4000}
                ],
                "band_performance": {
                    "1000": {"tested": 2, "correct": 2},
                    "2000": {"tested": 3, "correct": 2},
                    "3000": {"tested": 2, "correct": 1},
                    "4000": {"tested": 2, "correct": 0}
                },
                "phase": 1,
                "confidence": 0.75,
                "estimated_vocab": 2500,
                "pivot_triggered": False
            }
        }


class QuestionOption(BaseModel):
    """
    Individual option in a survey question.
    """
    id: str = Field(..., description="Unique option identifier (e.g., 'opt_a')")
    text: str = Field(..., description="Option text (Traditional Chinese definition)")
    type: str = Field(..., description="Option type: 'target', 'trap', 'filler', 'unknown'")
    is_correct: bool = Field(..., description="Whether this option is a correct answer")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "opt_a",
                "text": "建立",
                "type": "target",
                "is_correct": True
            }
        }


class QuestionPayload(BaseModel):
    """
    Question data structure for survey questions.
    
    Contains the word being tested, its rank, and 6 options
    (variable correct answers: 1-5 targets).
    """
    question_id: str = Field(..., description="Unique question identifier (e.g., 'q_3500')")
    word: str = Field(..., description="The word being tested")
    rank: int = Field(..., ge=1, le=8000, description="Frequency rank of the word")
    options: List[QuestionOption] = Field(..., min_items=6, max_items=6, description="6 options for the question")
    time_limit: int = Field(default=12, ge=1, description="Suggested time limit in seconds")
    
    class Config:
        json_schema_extra = {
            "example": {
                "question_id": "q_3500",
                "word": "Establish",
                "rank": 3500,
                "options": [
                    {"id": "opt_a", "text": "建立", "type": "target", "is_correct": True},
                    {"id": "opt_b", "text": "估計", "type": "trap", "is_correct": False},
                    {"id": "opt_c", "text": "完成", "type": "target", "is_correct": True},
                    {"id": "opt_d", "text": "開始", "type": "filler", "is_correct": False},
                    {"id": "opt_e", "text": "結束", "type": "filler", "is_correct": False},
                    {"id": "opt_f", "text": "我不知道", "type": "unknown", "is_correct": False}
                ],
                "time_limit": 12
            }
        }


class QuestionHistory(BaseModel):
    """
    History record for a single question in the survey.
    
    Stored in SurveyState.history as a list of these records.
    """
    rank: int = Field(..., ge=1, le=8000, description="Frequency rank of the question")
    correct: bool = Field(..., description="Whether the user answered correctly")
    time_taken: float = Field(..., ge=0.0, description="Time taken to answer in seconds")
    
    # Detailed reporting fields
    word: Optional[str] = Field(None, description="Word that was tested")
    question_id: Optional[str] = Field(None, description="Question identifier")
    phase: Optional[int] = Field(None, ge=1, le=3, description="Phase when answered")
    question_number: Optional[int] = Field(None, ge=1, description="Question sequence number")
    selected_option_ids: Optional[List[str]] = Field(None, description="User's selected option IDs")
    correct_option_ids: Optional[List[str]] = Field(None, description="Correct option IDs (target options)")
    all_options: Optional[List[Dict[str, Any]]] = Field(None, description="All options with their details")
    
    class Config:
        json_schema_extra = {
            "example": {
                "rank": 3500,
                "correct": True,
                "time_taken": 4.5,
                "word": "Establish",
                "question_id": "q_3500_12345",
                "phase": 1,
                "question_number": 1
            }
        }


class AnswerSubmission(BaseModel):
    """
    User's answer submission for a survey question.
    """
    question_id: str = Field(..., description="Question identifier being answered")
    selected_option_ids: List[str] = Field(
        ...,
        min_items=1,
        description="List of selected option IDs (multi-select)"
    )
    time_taken: float = Field(..., ge=0.0, description="Time taken to answer in seconds")
    
    class Config:
        json_schema_extra = {
            "example": {
                "question_id": "q_3500",
                "selected_option_ids": ["opt_a", "opt_c"],
                "time_taken": 4.5
            }
        }


class TriMetricReport(BaseModel):
    """
    Tri-Metric Report: The Financial Asset Report.
    
    Three metrics that describe the user's vocabulary knowledge:
    - Volume (Est. Reserves / 資產總量): Area under the probability curve
    - Reach (Horizon / 有效邊界): Highest rank where reliability > 50%
    - Density (Solidity / 資產密度): Consistency within the owned zone
    """
    volume: int = Field(..., ge=0, description="Est. Reserves (資產總量) - Estimated word count owned")
    reach: int = Field(..., ge=0, le=8000, description="Horizon (有效邊界) - Highest reliable rank")
    density: float = Field(..., ge=0.0, le=1.0, description="Solidity (資產密度) - Consistency score (0.0-1.0)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "volume": 2400,
                "reach": 4200,
                "density": 0.87
            }
        }


class SurveyResult(BaseModel):
    """
    Survey result response structure.
    
    Used for both intermediate responses (status="continue") and
    final completion responses (status="complete").
    
    Includes the "Tri-Metric" fields (volume, reach, density) in metrics
    when status="complete".
    """
    status: str = Field(..., description="Survey status: 'continue' or 'complete'")
    session_id: str = Field(..., description="Session identifier")
    payload: Optional[QuestionPayload] = Field(
        default=None,
        description="Question payload (present when status='continue')"
    )
    metrics: Optional[TriMetricReport] = Field(
        default=None,
        description="Tri-Metric report (present when status='complete') - includes volume, reach, density"
    )
    
    # New reporting fields
    detailed_history: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Detailed question-by-question history (present when status='complete')"
    )
    methodology: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Survey methodology explanation (present when status='complete')"
    )
    
    debug_info: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Debug information (phase, confidence, etc.)"
    )
    
    class Config:
        json_schema_extra = {
            "example_continue": {
                "status": "continue",
                "session_id": "sess_12345",
                "payload": {
                    "question_id": "q_3500",
                    "word": "Establish",
                    "rank": 3500,
                    "options": [],
                    "time_limit": 12
                },
                "debug_info": {
                    "current_confidence": 0.45,
                    "phase": 1
                }
            },
            "example_complete": {
                "status": "complete",
                "session_id": "sess_12345",
                "metrics": {
                    "volume": 2400,
                    "reach": 4200,
                    "density": 0.87
                },
                "detailed_history": [],
                "methodology": {},
                "debug_info": {
                    "phase": 3,
                    "confidence": 0.92
                }
            }
        }
