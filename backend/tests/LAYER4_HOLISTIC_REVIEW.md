# Layer 4: Holistic LLM Review

**Status:** ✅ Implementation Complete (Not Yet Run)  
**Test File:** `test_holistic_quality.py`  
**Purpose:** Comprehensive quality evaluation of complete survey sessions

---

## Overview

Layer 4 uses **one LLM call per complete survey session** to evaluate the entire experience holistically. This is more efficient and comprehensive than per-question evaluation.

**Key Philosophy:**
- **One evaluation per session** (not per question)
- **Comprehensive assessment** of entire experience
- **Quality scoring** across multiple dimensions
- **Issue identification** (critical vs minor)

---

## What It Does

### Evaluation Dimensions

1. **Algorithm Behavior (30% weight)**
   - Convergence efficiency
   - Question distribution
   - Phase transitions
   - Step sizes

2. **Question Quality (30% weight)**
   - Word difficulty appropriateness
   - Chinese definition clarity
   - Trap option quality
   - Duplicate detection

3. **Metric Plausibility (25% weight)**
   - Volume/Reach/Density consistency
   - Contradiction detection
   - Alignment with answer history

4. **User Experience (15% weight)**
   - Question count (15-20)
   - Survey flow smoothness
   - Obvious user-facing issues

### Output Format

```json
{
    "overall": "PASS" | "FAIL" | "NEEDS_REVIEW",
    "score": 0.0-1.0,
    "algorithm_score": 0.0-1.0,
    "quality_score": 0.0-1.0,
    "metric_score": 0.0-1.0,
    "ux_score": 0.0-1.0,
    "critical_issues": ["List of FAIL-worthy problems"],
    "minor_issues": ["List of minor problems"],
    "summary": "2-3 sentence overall assessment"
}
```

### Evaluation Criteria

- **PASS**: All scores ≥0.7, no critical issues
- **FAIL**: Any score <0.5 OR any critical issue
- **NEEDS_REVIEW**: Between PASS and FAIL

---

## Implementation

### HolisticSurveyEvaluator Class

```python
evaluator = HolisticSurveyEvaluator()
evaluation = evaluator.evaluate_survey_session(survey_result)
```

**Features:**
- Single LLM call per session
- Caching for identical sessions
- Low temperature (0.1) for consistency
- JSON output for programmatic use

### Test Structure

```python
class TestHolisticQuality:
    def test_evaluates_complete_session(self, evaluator):
        # Test with sample data
    
    def test_evaluates_real_survey_session(self, evaluator, neo4j_conn):
        # Test with real survey from Layer 3
    
    def test_evaluation_caching(self, evaluator):
        # Test caching works
    
    def test_handles_incomplete_survey(self, evaluator):
        # Test error handling
```

---

## Usage

### Prerequisites

1. **LLM API Key Required**
   ```bash
   export GOOGLE_API_KEY=your_api_key_here
   ```

2. **Real Survey Results**
   - Can use results from Layer 3 tests
   - Or real survey sessions from production

### Running Tests

```bash
cd backend
source venv/bin/activate

# Run all Layer 4 tests
pytest tests/test_holistic_quality.py -v

# Run specific test
pytest tests/test_holistic_quality.py::TestHolisticQuality::test_evaluates_real_survey_session -v
```

**Note:** Tests will skip if `GOOGLE_API_KEY` is not set.

---

## Cost Estimate

**Per Evaluation:**
- Input tokens: ~500-800 tokens (session data)
- Output tokens: ~200-300 tokens (evaluation JSON)
- **Cost per evaluation: ~$0.0001-0.0002**

**For 20 Survey Sessions:**
- Total cost: **~$0.002-0.004** (less than 1 cent)

**Free Tier:**
- 1M tokens/day limit
- Can evaluate ~1000 sessions/day on free tier

---

## When to Use

### Development/Testing
- Evaluate test survey sessions from Layer 3
- Validate algorithm improvements
- Check metric accuracy

### Production
- Periodic quality audits (weekly/monthly)
- Validate production survey quality
- Identify issues before users notice

### Not For
- ❌ Per-question evaluation (too expensive, not needed)
- ❌ Real-time validation (too slow)
- ❌ Every single survey (use sampling)

---

## Integration with Other Layers

```
Layer 2 (Algorithm) → Validates logic ✅
    ↓
Layer 3 (Simulation) → Validates flow with real data ✅
    ↓
Layer 4 (Holistic Review) → Validates quality holistically ✅
    ↓
Production → Deploy with confidence
```

---

## Expected Results

### Good Survey Session
```json
{
    "overall": "PASS",
    "score": 0.85,
    "algorithm_score": 0.9,
    "quality_score": 0.8,
    "metric_score": 0.85,
    "ux_score": 0.9,
    "critical_issues": [],
    "minor_issues": ["One duplicate word detected"],
    "summary": "Survey completed successfully with good convergence and appropriate metrics."
}
```

### Problematic Survey Session
```json
{
    "overall": "FAIL",
    "score": 0.45,
    "algorithm_score": 0.4,
    "quality_score": 0.5,
    "metric_score": 0.3,
    "ux_score": 0.6,
    "critical_issues": [
        "Density calculation appears backwards (consistent user has low density)",
        "Volume significantly underestimates vocabulary size"
    ],
    "minor_issues": ["Bounds did not converge tightly"],
    "summary": "Survey has critical metric calculation issues that need immediate attention."
}
```

---

## Next Steps

1. **Run Layer 4 tests** (when ready)
   - Evaluate real survey sessions
   - Identify quality issues
   - Validate fixes

2. **Integrate with CI/CD** (optional)
   - Run on sample surveys after algorithm changes
   - Fail builds if quality drops below threshold

3. **Production Monitoring** (future)
   - Periodic quality audits
   - Track quality trends over time
   - Alert on quality degradation

---

**Last Updated:** 2025-01-XX  
**Status:** ✅ Implementation Complete (Ready to Run)  
**Cost:** ~$0.0001-0.0002 per evaluation


