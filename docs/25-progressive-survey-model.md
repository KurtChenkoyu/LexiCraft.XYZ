# Progressive Survey Model (PSM) Specification

**Version:** 1.0  
**Date:** 2024-12  
**Status:** Implementation Ready  
**Module ID:** MOD_SURVEY_PSM

---

## 1. Executive Summary

The Progressive Survey Model (PSM) transforms LexiSurvey from a standalone assessment tool into an intelligent, progressively learning system that gets smarter with each interaction.

### Key Insight

> Survey and Learning are not separate systems - they should feed into each other.  
> Survey → calibrates learning. Learning → makes future surveys smarter.

### Benefits

1. **Reduced Assessment Time**: Warm-start surveys need fewer questions
2. **Higher Confidence**: Prior data increases estimation accuracy
3. **Better UX**: Users see the system "remembers" them
4. **Testimonial Data**: Track efficiency improvements over time
5. **Methodology Validation**: Prove that time with platform = better assessments

---

## 2. Survey Modes

### 2.1 Cold Start (Initial Assessment)

**When**: First-time users, no learning history  
**Questions**: 20-35 (adaptive, confidence-based stopping)  
**Prior Data**: None  
**Goal**: Establish baseline vocabulary estimate

```
User Journey:
├── Onboarding → CEFR selection (optional calibration)
├── Survey starts at mapped rank (A1=1000, B1=3500, C1=5500)
├── 20-35 questions across frequency bands
├── Confidence threshold reached or max questions
└── Result: Volume, Reach, Density (baseline)
```

### 2.2 Warm Start (Progress Check)

**When**: User has learning_progress data (verified words)  
**Questions**: 10-20 (reduced due to prior knowledge)  
**Prior Data**: Verified words from learning_progress  
**Goal**: Update vocabulary estimate, focus on uncertainty zones

```
User Journey:
├── System queries learning_progress for verified words
├── Pre-populate band_performance with known words
├── Calculate initial confidence from prior data
├── Focus questions on UNCERTAIN bands (gaps)
├── 10-20 questions (or fewer if high confidence)
└── Result: Updated Volume, Reach, Density
```

### 2.3 Quick Validation (Milestone Check)

**When**: After major learning milestone (e.g., 100 new verifications)  
**Questions**: 5-10 (highly focused)  
**Prior Data**: Recent learning + previous survey results  
**Goal**: Validate recent learning, quick progress indicator

```
User Journey:
├── Triggered by milestone (100 verifications, 30 days, etc.)
├── Only test recently learned bands
├── 5-10 focused questions
└── Result: Delta metrics (+Volume, +Reach since last check)
```

### 2.4 Deep Dive (Thorough Re-assessment)

**When**: User-requested, annual assessment, or doubt about accuracy  
**Questions**: 30-50 (comprehensive)  
**Prior Data**: Optional (can ignore for "clean" assessment)  
**Goal**: Most accurate possible estimate

```
User Journey:
├── User requests full re-assessment
├── Can choose to use or ignore prior data
├── 30-50 questions across ALL bands
├── Highest confidence threshold
└── Result: High-confidence Volume, Reach, Density
```

---

## 3. Warm-Start Algorithm

### 3.1 Prior Knowledge Extraction

```python
def extract_prior_knowledge(user_id: UUID, db: Session) -> PriorKnowledge:
    """
    Extract prior knowledge from learning_progress for warm-start.
    
    Returns:
        PriorKnowledge with band performance from verified words
    """
    # Query verified learning points
    result = db.execute(text("""
        SELECT 
            lp.tier,
            COUNT(*) as count,
            AVG(CASE WHEN vs.passed THEN 1 ELSE 0 END) as avg_pass_rate,
            MAX(lp.learned_at) as last_learned
        FROM learning_progress lp
        LEFT JOIN verification_schedule vs ON vs.learning_progress_id = lp.id
        WHERE lp.user_id = :user_id
        AND lp.status = 'verified'
        GROUP BY lp.tier
        ORDER BY lp.tier
    """), {"user_id": user_id})
    
    # Map tiers to frequency bands
    prior_bands = {}
    for tier, count, pass_rate, last_learned in result:
        band = tier_to_frequency_band(tier)
        prior_bands[band] = {
            "verified_count": count,
            "pass_rate": pass_rate or 1.0,
            "last_learned": last_learned,
            "source": "learning_progress"
        }
    
    return PriorKnowledge(
        bands=prior_bands,
        total_verified=sum(b["verified_count"] for b in prior_bands.values()),
        confidence_boost=calculate_confidence_boost(prior_bands)
    )
```

### 3.2 Band Performance Pre-population

```python
def warm_start_band_performance(prior: PriorKnowledge) -> Dict[int, Dict[str, int]]:
    """
    Pre-populate band_performance with prior knowledge.
    
    Prior knowledge is treated as "pre-tested" with high accuracy.
    """
    BANDS = [1000, 2000, 3000, 4000, 5000, 6000, 7000, 8000]
    band_performance = {band: {"tested": 0, "correct": 0, "prior": 0} for band in BANDS}
    
    for band, data in prior.bands.items():
        if band in band_performance:
            # Verified words count as "correct" with high confidence
            verified = data["verified_count"]
            pass_rate = data["pass_rate"]
            
            # Add prior knowledge to band
            # Use fractional contribution based on pass_rate
            effective_correct = int(verified * pass_rate)
            
            band_performance[band]["prior"] = verified
            band_performance[band]["tested"] += verified
            band_performance[band]["correct"] += effective_correct
    
    return band_performance
```

### 3.3 Initial Confidence Calculation

```python
def calculate_warm_start_confidence(prior: PriorKnowledge) -> float:
    """
    Calculate initial confidence from prior knowledge.
    
    More verified words across more bands = higher initial confidence.
    """
    # Factor 1: Coverage (how many bands have data)
    bands_with_data = sum(1 for b in prior.bands.values() if b["verified_count"] > 0)
    coverage = bands_with_data / 8  # 8 total bands
    
    # Factor 2: Volume (total verified words)
    # Saturates around 500 words (full confidence)
    volume_factor = min(prior.total_verified / 500, 1.0)
    
    # Factor 3: Recency (how recent is the data)
    # Data from last 30 days = 1.0, decays to 0.5 after 180 days
    recency_factor = calculate_recency_factor(prior)
    
    # Combine factors
    initial_confidence = (
        0.4 * coverage +
        0.4 * volume_factor +
        0.2 * recency_factor
    )
    
    # Cap at 0.6 - always need some questions to validate
    return min(0.6, initial_confidence)
```

### 3.4 Focused Band Selection

```python
def select_priority_bands(
    band_performance: Dict[int, Dict], 
    prior: PriorKnowledge
) -> List[int]:
    """
    Identify bands to prioritize for testing.
    
    Priority:
    1. Bands with NO data (complete uncertainty)
    2. Bands near the estimated boundary (high information)
    3. Bands with stale data (old verifications)
    """
    priority_bands = []
    
    # 1. Bands with no prior data
    for band in BANDS:
        if band not in prior.bands or prior.bands[band]["verified_count"] == 0:
            priority_bands.append((band, "no_data", 3))  # High priority
    
    # 2. Bands near estimated boundary
    estimated_reach = estimate_reach_from_prior(prior)
    boundary_bands = [b for b in BANDS if abs(b - estimated_reach) <= 1000]
    for band in boundary_bands:
        if band not in [p[0] for p in priority_bands]:
            priority_bands.append((band, "boundary", 2))
    
    # 3. Bands with stale data (> 60 days)
    for band, data in prior.bands.items():
        if data["last_learned"] and days_since(data["last_learned"]) > 60:
            if band not in [p[0] for p in priority_bands]:
                priority_bands.append((band, "stale", 1))
    
    # Sort by priority (highest first)
    priority_bands.sort(key=lambda x: x[2], reverse=True)
    
    return [band for band, reason, priority in priority_bands]
```

---

## 4. Data Model Extensions

### 4.1 New Table: survey_metadata

Tracks survey efficiency and context for testimonials.

```sql
CREATE TABLE IF NOT EXISTS survey_metadata (
    id SERIAL PRIMARY KEY,
    session_id UUID NOT NULL REFERENCES survey_sessions(id) ON DELETE CASCADE,
    
    -- Survey mode and context
    survey_mode TEXT NOT NULL DEFAULT 'cold_start',  -- 'cold_start', 'warm_start', 'quick_validation', 'deep_dive'
    
    -- Prior knowledge at survey time
    prior_verified_words INTEGER DEFAULT 0,
    prior_bands_with_data INTEGER DEFAULT 0,
    prior_confidence FLOAT DEFAULT 0.0,
    
    -- Survey efficiency metrics
    questions_asked INTEGER NOT NULL,
    questions_from_prior INTEGER DEFAULT 0,  -- Bands skipped due to prior
    time_taken_seconds INTEGER,
    final_confidence FLOAT NOT NULL,
    
    -- Comparison with previous survey
    previous_session_id UUID REFERENCES survey_sessions(id),
    improvement_volume INTEGER,  -- +/- change
    improvement_reach INTEGER,   -- +/- change
    days_since_last_survey INTEGER,
    
    -- Learning efficiency (for testimonials)
    verified_words_between_surveys INTEGER,
    learning_days_between_surveys INTEGER,
    efficiency_score FLOAT,  -- (improvement / verified_words) or similar
    
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_survey_metadata_session ON survey_metadata(session_id);
CREATE INDEX idx_survey_metadata_mode ON survey_metadata(survey_mode);
CREATE INDEX idx_survey_metadata_user ON survey_metadata(session_id); -- Join to get user
```

### 4.2 Updated SurveyState Model

```python
class SurveyState(BaseModel):
    """Extended for Progressive Survey Model."""
    
    # Existing fields...
    session_id: str
    current_rank: int
    history: List[Dict[str, Any]]
    band_performance: Optional[Dict[int, Dict[str, int]]]
    confidence: float
    estimated_vocab: int
    
    # NEW: PSM fields
    survey_mode: str = Field(
        default="cold_start",
        description="Survey mode: cold_start, warm_start, quick_validation, deep_dive"
    )
    prior_knowledge: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Prior knowledge from learning_progress"
    )
    priority_bands: Optional[List[int]] = Field(
        default=None,
        description="Bands to prioritize for testing"
    )
    initial_confidence: float = Field(
        default=0.0,
        description="Confidence from prior knowledge before questions"
    )
```

### 4.3 API Request Extension

```python
class StartSurveyRequest(BaseModel):
    cefr_level: Optional[str] = None
    user_id: Optional[str] = None
    
    # NEW: PSM options
    survey_mode: Optional[str] = Field(
        default=None,  # Auto-detect based on user history
        description="Force survey mode: cold_start, warm_start, quick_validation, deep_dive"
    )
    use_prior_knowledge: bool = Field(
        default=True,
        description="Whether to use learning_progress data (warm-start)"
    )
```

---

## 5. Survey Result Extensions

### 5.1 Extended SurveyResult

```python
class SurveyResult(BaseModel):
    """Extended result with PSM metadata."""
    
    # Existing fields...
    status: str
    session_id: str
    payload: Optional[QuestionPayload]
    metrics: Optional[TriMetricReport]
    
    # NEW: PSM metadata (when status='complete')
    survey_metadata: Optional[SurveyMetadata] = Field(
        default=None,
        description="Survey efficiency and comparison data"
    )

class SurveyMetadata(BaseModel):
    """Metadata for Progressive Survey Model."""
    survey_mode: str
    questions_asked: int
    time_taken_seconds: int
    
    # Prior knowledge impact
    prior_verified_words: int
    prior_confidence: float
    final_confidence: float
    questions_saved: int  # Estimated questions saved by warm-start
    
    # Progress comparison
    previous_survey: Optional[PreviousSurveyComparison]
    efficiency_report: Optional[EfficiencyReport]

class PreviousSurveyComparison(BaseModel):
    """Comparison with last survey."""
    previous_date: datetime
    days_since: int
    volume_change: int
    reach_change: int
    density_change: float

class EfficiencyReport(BaseModel):
    """Learning efficiency for testimonials."""
    verified_words_between: int
    learning_days: int
    efficiency_score: float  # Higher = more efficient learning
    message: str  # "Your vocabulary grew 2x faster with LexiCraft!"
```

---

## 6. Testimonial Queries

### 6.1 User Progress Timeline

```sql
-- Get user's survey history with progress
SELECT 
    ss.start_time,
    sr.volume,
    sr.reach,
    sr.density,
    sm.survey_mode,
    sm.questions_asked,
    sm.prior_verified_words,
    sm.improvement_volume,
    sm.efficiency_score
FROM survey_sessions ss
JOIN survey_results sr ON sr.session_id = ss.id
LEFT JOIN survey_metadata sm ON sm.session_id = ss.id
WHERE ss.user_id = :user_id
ORDER BY ss.start_time;
```

### 6.2 Aggregate Efficiency Stats

```sql
-- Calculate platform-wide efficiency improvements
WITH user_journeys AS (
    SELECT 
        ss.user_id,
        COUNT(*) as survey_count,
        MIN(sr.volume) as first_volume,
        MAX(sr.volume) as latest_volume,
        MAX(sr.volume) - MIN(sr.volume) as total_growth,
        MAX(sm.prior_verified_words) as max_verified,
        AVG(sm.efficiency_score) as avg_efficiency
    FROM survey_sessions ss
    JOIN survey_results sr ON sr.session_id = ss.id
    LEFT JOIN survey_metadata sm ON sm.session_id = ss.id
    GROUP BY ss.user_id
    HAVING COUNT(*) >= 2  -- At least 2 surveys
)
SELECT 
    AVG(total_growth) as avg_vocabulary_growth,
    AVG(avg_efficiency) as avg_learning_efficiency,
    PERCENTILE_CONT(0.9) WITHIN GROUP (ORDER BY total_growth) as top_10_growth
FROM user_journeys;
```

### 6.3 Individual Testimonial Data

```sql
-- Get testimonial data for a specific user
WITH user_surveys AS (
    SELECT 
        ss.start_time,
        sr.volume,
        sr.reach,
        sm.questions_asked,
        sm.prior_verified_words,
        LAG(sr.volume) OVER (ORDER BY ss.start_time) as prev_volume,
        LAG(ss.start_time) OVER (ORDER BY ss.start_time) as prev_date
    FROM survey_sessions ss
    JOIN survey_results sr ON sr.session_id = ss.id
    LEFT JOIN survey_metadata sm ON sm.session_id = ss.id
    WHERE ss.user_id = :user_id
    ORDER BY ss.start_time
)
SELECT 
    start_time,
    volume,
    reach,
    questions_asked,
    prior_verified_words,
    volume - COALESCE(prev_volume, 0) as vocabulary_gained,
    EXTRACT(DAY FROM start_time - prev_date) as days_since_last
FROM user_surveys
ORDER BY start_time;
```

---

## 7. Implementation Roadmap

### Phase 1: Database & Models (Priority: HIGH)

1. Create `survey_metadata` table migration
2. Extend `SurveyState` model with PSM fields
3. Add `SurveyMetadata` response model
4. Update API request model

### Phase 2: Warm-Start Engine (Priority: HIGH)

1. Implement `extract_prior_knowledge()` function
2. Implement `warm_start_band_performance()` function
3. Implement `calculate_warm_start_confidence()` function
4. Implement `select_priority_bands()` function
5. Update `LexiSurveyEngine.process_step()` to use warm-start

### Phase 3: API Updates (Priority: MEDIUM)

1. Update `/api/v1/survey/start` to support warm-start
2. Add survey mode auto-detection
3. Store survey_metadata on completion
4. Add previous survey comparison

### Phase 4: Testimonial Features (Priority: LOW)

1. Add `/api/v1/survey/history` endpoint for user timeline
2. Add `/api/v1/survey/efficiency` endpoint for metrics
3. Frontend dashboard for progress visualization

---

## 8. Configuration

### Stopping Thresholds by Mode

| Mode | Min Questions | Confidence Threshold | Max Questions |
|------|--------------|---------------------|---------------|
| cold_start | 15 | 0.80 | 35 |
| warm_start | 8 | 0.85 | 20 |
| quick_validation | 5 | 0.90 | 10 |
| deep_dive | 25 | 0.90 | 50 |

### Prior Knowledge Weights

```python
PRIOR_WEIGHT_CONFIG = {
    # How much to trust prior knowledge
    "verified_word_weight": 0.9,    # Verified = 90% reliable
    "recency_decay_days": 180,      # Full decay after 6 months
    "min_recency_weight": 0.5,      # Oldest data = 50% weight
    
    # Confidence calculation
    "max_initial_confidence": 0.6,  # Never start above 60%
    "coverage_weight": 0.4,         # Band coverage importance
    "volume_weight": 0.4,           # Total verified words importance
    "recency_weight": 0.2,          # Data freshness importance
}
```

---

## 9. Success Metrics

### User Experience

- **Cold-start questions**: Target 20-25 (currently 20-35)
- **Warm-start questions**: Target 10-15 (50% reduction)
- **Quick validation questions**: Target 5-8
- **User satisfaction**: "The system knows me better"

### Accuracy

- **Correlation with learning_progress**: > 0.8
- **Test-retest reliability**: > 0.85
- **Estimated vs actual vocabulary**: Within 10%

### Testimonial Value

- **Efficiency improvement**: Show 2x faster assessment after 3 months
- **Accuracy improvement**: Higher confidence with more data
- **Vocabulary growth**: Track and visualize over time

---

## 10. References

- Nation's Vocabulary Levels Test (VLT)
- Computer Adaptive Testing (CAT) with IRT
- Bayesian Knowledge Tracing (BKT)
- Spaced Repetition research (Ebbinghaus, Pimsleur)

