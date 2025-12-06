"""
Layer 4: Holistic LLM Review

Uses LLM to evaluate complete survey sessions holistically.
One comprehensive evaluation per session (not per-question micromanagement).

Key Features:
- Single LLM call per complete survey session
- Comprehensive evaluation of entire experience
- Quality scoring across multiple dimensions
- Identifies critical issues and minor problems
"""

import pytest
import json
import os
from typing import Dict, Any, Optional
from src.survey.models import SurveyResult
from src.database.neo4j_connection import Neo4jConnection
from dotenv import load_dotenv

load_dotenv()

# LLM Configuration
try:
    import google.generativeai as genai
    API_KEY = os.getenv("GOOGLE_API_KEY")
    if API_KEY:
        genai.configure(api_key=API_KEY)
        LLM_AVAILABLE = True
    else:
        LLM_AVAILABLE = False
        print("⚠️  GOOGLE_API_KEY not found. LLM evaluation will be skipped.")
except ImportError:
    LLM_AVAILABLE = False
    print("⚠️  google-generativeai not installed. LLM evaluation will be skipped.")


HOLISTIC_EVALUATION_PROMPT = """
You are evaluating a complete LexiSurvey vocabulary assessment session.

LexiSurvey is a vocabulary assessment system that:
- Uses frequency-ranked words (1-8000) to estimate vocabulary size
- Tests users with 15-20 questions using binary search
- Generates three metrics: Volume (word count), Reach (highest rank), Density (consistency)
- Uses 3-phase algorithm: Coarse sweep (Q1-Q5), Fine tuning (Q6-Q12), Verification (Q13-Q15)

SESSION DATA:
{session_json}

EVALUATE THE ENTIRE SESSION on these criteria:

1. ALGORITHM BEHAVIOR (30% weight)
   - Did the survey converge efficiently? (bounds narrowed appropriately)
   - Were questions distributed across appropriate rank ranges?
   - Did phase transitions make sense? (Q5, Q12)
   - Were step sizes appropriate for each phase?

2. QUESTION QUALITY (30% weight)
   - Were word difficulties appropriate for their ranks?
   - Were Chinese definitions clear and accurate?
   - Were trap options genuinely confusing (not obvious)?
   - Were there duplicate words in the session?

3. METRIC PLAUSIBILITY (25% weight)
   - Do Volume/Reach/Density make sense given the answer pattern?
   - Are there any contradictions? (e.g., high reach but all wrong answers)
   - Do metrics align with the user's answer history?

4. USER EXPERIENCE (15% weight)
   - Was question count reasonable (15-20)?
   - Was the survey flow smooth?
   - Any obvious issues a user would notice?

OUTPUT FORMAT (JSON):
{{
    "overall": "PASS" | "FAIL" | "NEEDS_REVIEW",
    "score": 0.0-1.0,
    "algorithm_score": 0.0-1.0,
    "quality_score": 0.0-1.0,
    "metric_score": 0.0-1.0,
    "ux_score": 0.0-1.0,
    "critical_issues": ["List any FAIL-worthy problems"],
    "minor_issues": ["List minor problems"],
    "summary": "2-3 sentence overall assessment"
}}

EVALUATION CRITERIA:
- PASS: All scores ≥0.7, no critical issues
- FAIL: Any score <0.5 OR any critical issue
- NEEDS_REVIEW: Between PASS and FAIL

Be thorough but fair. Most well-functioning surveys should PASS.
Only flag genuine problems.
"""


class HolisticSurveyEvaluator:
    """
    Evaluates complete survey sessions using LLM.
    
    One comprehensive evaluation per session, not per-question.
    """
    
    def __init__(self, model_name: str = "gemini-2.0-flash"):
        """
        Initialize the evaluator.
        
        Args:
            model_name: Gemini model to use
        """
        if not LLM_AVAILABLE:
            raise ValueError("LLM not available. Check GOOGLE_API_KEY environment variable.")
        
        self.model = genai.GenerativeModel(model_name)
        self.evaluation_cache = {}  # Cache evaluations for identical sessions
    
    def evaluate_survey_session(self, survey_result: SurveyResult) -> Dict[str, Any]:
        """
        Evaluate a complete survey session holistically.
        
        Args:
            survey_result: Complete SurveyResult with metrics and history
            
        Returns:
            Dictionary with evaluation scores and issues
        """
        if survey_result.status != "complete":
            return {
                "overall": "FAIL",
                "score": 0.0,
                "error": "Survey not complete"
            }
        
        # Prepare session data for evaluation
        session_data = {
            "metrics": {
                "volume": survey_result.metrics.volume if survey_result.metrics else 0,
                "reach": survey_result.metrics.reach if survey_result.metrics else 0,
                "density": survey_result.metrics.density if survey_result.metrics else 0.0
            },
            "question_count": len(survey_result.detailed_history) if survey_result.detailed_history else 0,
            "history": survey_result.detailed_history or [],
            "methodology": survey_result.methodology or {},
            "debug_info": survey_result.debug_info or {}
        }
        
        # Create cache key
        cache_key = self._create_cache_key(session_data)
        if cache_key in self.evaluation_cache:
            return self.evaluation_cache[cache_key]
        
        # Format prompt
        prompt = HOLISTIC_EVALUATION_PROMPT.format(
            session_json=json.dumps(session_data, ensure_ascii=False, indent=2)
        )
        
        try:
            # Call LLM
            response = self.model.generate_content(
                prompt,
                generation_config={
                    "response_mime_type": "application/json",
                    "temperature": 0.1  # Low temperature for consistency
                }
            )
            
            # Parse response
            evaluation = json.loads(response.text)
            
            # Cache result
            self.evaluation_cache[cache_key] = evaluation
            
            return evaluation
            
        except json.JSONDecodeError as e:
            return {
                "overall": "NEEDS_REVIEW",
                "score": 0.5,
                "error": f"Failed to parse LLM response: {e}",
                "raw_response": response.text if 'response' in locals() else None
            }
        except Exception as e:
            return {
                "overall": "NEEDS_REVIEW",
                "score": 0.5,
                "error": f"LLM evaluation failed: {e}"
            }
    
    def _create_cache_key(self, session_data: Dict[str, Any]) -> str:
        """Create a cache key for session data."""
        # Use metrics and question count as key (history may vary slightly)
        metrics = session_data.get("metrics", {})
        return f"{metrics.get('volume', 0)}_{metrics.get('reach', 0)}_{metrics.get('density', 0)}_{session_data.get('question_count', 0)}"


@pytest.fixture
def neo4j_conn():
    """Create a Neo4j connection for testing."""
    conn = Neo4jConnection()
    yield conn
    conn.close()


@pytest.fixture
def evaluator():
    """Create a HolisticSurveyEvaluator instance."""
    if not LLM_AVAILABLE:
        pytest.skip("LLM not available. Set GOOGLE_API_KEY environment variable.")
    return HolisticSurveyEvaluator()


class TestHolisticQuality:
    """Test holistic LLM evaluation of survey sessions."""
    
    @pytest.mark.skipif(not LLM_AVAILABLE, reason="LLM not available")
    def test_evaluator_initializes(self, evaluator):
        """Test that evaluator initializes correctly."""
        assert evaluator is not None
        assert evaluator.model is not None
    
    @pytest.mark.skipif(not LLM_AVAILABLE, reason="LLM not available")
    def test_evaluates_complete_session(self, evaluator):
        """
        Test that evaluator can evaluate a complete survey session.
        
        This test requires:
        1. A complete SurveyResult (from Layer 3 tests or real survey)
        2. LLM API key configured
        """
        # Create a sample complete survey result
        from src.survey.models import TriMetricReport
        
        sample_result = SurveyResult(
            status="complete",
            session_id="test_session",
            metrics=TriMetricReport(
                volume=2000,
                reach=2000,
                density=0.85
            ),
            detailed_history=[
                {"rank": 1000, "correct": True, "time_taken": 5.0},
                {"rank": 2000, "correct": True, "time_taken": 4.5},
                {"rank": 3000, "correct": False, "time_taken": 8.0},
            ],
            methodology={
                "total_questions": 15,
                "phases": {
                    "phase_1": {"questions": 5},
                    "phase_2": {"questions": 7},
                    "phase_3": {"questions": 3}
                }
            },
            debug_info={
                "phase": 3,
                "confidence": 0.9,
                "question_count": 15
            }
        )
        
        evaluation = evaluator.evaluate_survey_session(sample_result)
        
        # Validate evaluation structure
        assert "overall" in evaluation
        assert evaluation["overall"] in ["PASS", "FAIL", "NEEDS_REVIEW"]
        assert "score" in evaluation
        assert 0.0 <= evaluation["score"] <= 1.0
        assert "algorithm_score" in evaluation
        assert "quality_score" in evaluation
        assert "metric_score" in evaluation
        assert "ux_score" in evaluation
    
    @pytest.mark.skipif(not LLM_AVAILABLE, reason="LLM not available")
    def test_evaluates_real_survey_session(self, evaluator, neo4j_conn):
        """
        Test evaluation with a real survey session.
        
        This test runs a complete survey and then evaluates it.
        Requires real Neo4j connection.
        """
        from src.survey.lexisurvey_engine import LexiSurveyEngine
        from tests.test_survey_simulation import SimulatedUser, run_complete_survey
        
        # Run a complete survey
        engine = LexiSurveyEngine(neo4j_conn)
        user = SimulatedUser(vocab_boundary=2000, consistency=0.95)
        
        result = run_complete_survey(engine, user, start_rank=2000)
        
        if result.status != "complete":
            pytest.skip("Survey did not complete, cannot evaluate")
        
        # Evaluate the session
        evaluation = evaluator.evaluate_survey_session(result)
        
        # Validate evaluation
        assert "overall" in evaluation
        assert evaluation["overall"] in ["PASS", "FAIL", "NEEDS_REVIEW"]
        assert "score" in evaluation
        assert "critical_issues" in evaluation
        assert "minor_issues" in evaluation
        assert "summary" in evaluation
        
        # Log evaluation for review
        print(f"\n📊 Holistic Evaluation Results:")
        print(f"Overall: {evaluation['overall']}")
        print(f"Score: {evaluation['score']:.2f}")
        print(f"Algorithm: {evaluation.get('algorithm_score', 0):.2f}")
        print(f"Quality: {evaluation.get('quality_score', 0):.2f}")
        print(f"Metrics: {evaluation.get('metric_score', 0):.2f}")
        print(f"UX: {evaluation.get('ux_score', 0):.2f}")
        if evaluation.get('critical_issues'):
            print(f"⚠️  Critical Issues: {evaluation['critical_issues']}")
        if evaluation.get('minor_issues'):
            print(f"ℹ️  Minor Issues: {evaluation['minor_issues']}")
        print(f"Summary: {evaluation.get('summary', 'N/A')}")
    
    @pytest.mark.skipif(not LLM_AVAILABLE, reason="LLM not available")
    def test_evaluation_caching(self, evaluator):
        """Test that evaluations are cached for identical sessions."""
        from src.survey.models import TriMetricReport
        
        # Create identical survey results
        result1 = SurveyResult(
            status="complete",
            session_id="test1",
            metrics=TriMetricReport(volume=2000, reach=2000, density=0.85),
            detailed_history=[{"rank": 2000, "correct": True}],
            debug_info={"question_count": 1}
        )
        
        result2 = SurveyResult(
            status="complete",
            session_id="test2",  # Different session ID
            metrics=TriMetricReport(volume=2000, reach=2000, density=0.85),
            detailed_history=[{"rank": 2000, "correct": True}],
            debug_info={"question_count": 1}
        )
        
        # Evaluate both
        eval1 = evaluator.evaluate_survey_session(result1)
        eval2 = evaluator.evaluate_survey_session(result2)
        
        # Should use cache for second evaluation
        # (Cache key is based on metrics, not session_id)
        assert eval1["score"] == eval2["score"], "Cached evaluation should return same score"
    
    @pytest.mark.skipif(not LLM_AVAILABLE, reason="LLM not available")
    def test_handles_incomplete_survey(self, evaluator):
        """Test that evaluator handles incomplete surveys."""
        incomplete_result = SurveyResult(
            status="continue",
            session_id="test",
            payload=None
        )
        
        evaluation = evaluator.evaluate_survey_session(incomplete_result)
        
        assert evaluation["overall"] == "FAIL"
        assert evaluation["score"] == 0.0
        assert "error" in evaluation
    
    @pytest.mark.skipif(not LLM_AVAILABLE, reason="LLM not available")
    def test_evaluation_scores_are_reasonable(self, evaluator):
        """Test that evaluation scores are in valid ranges."""
        from src.survey.models import TriMetricReport
        
        result = SurveyResult(
            status="complete",
            session_id="test",
            metrics=TriMetricReport(volume=2000, reach=2000, density=0.85),
            detailed_history=[
                {"rank": 1000, "correct": True},
                {"rank": 2000, "correct": True},
                {"rank": 3000, "correct": False},
            ],
            debug_info={"question_count": 15}
        )
        
        evaluation = evaluator.evaluate_survey_session(result)
        
        # All scores should be 0.0-1.0
        assert 0.0 <= evaluation["score"] <= 1.0
        assert 0.0 <= evaluation.get("algorithm_score", 0) <= 1.0
        assert 0.0 <= evaluation.get("quality_score", 0) <= 1.0
        assert 0.0 <= evaluation.get("metric_score", 0) <= 1.0
        assert 0.0 <= evaluation.get("ux_score", 0) <= 1.0


