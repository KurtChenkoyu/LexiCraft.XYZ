# Learner Profile Research: Industry Standards & Scientific Findings

**Date:** January 2025  
**Purpose:** Comprehensive analysis of what data should be tracked about learners based on industry standards and scientific research

---

## Executive Summary

Based on deep research into industry standards (Duolingo, Memrise, Anki, adaptive learning platforms) and scientific literature (knowledge tracing, vocabulary learning research, self-regulated learning theory), we have identified **6 core dimensions** that should be tracked for a complete learner profile.

**Current Status:** We have a **strong foundation** (learning progress, spaced repetition, performance metrics) but are missing **critical dimensions** that research shows significantly improve learning outcomes.

---

## Industry Standards: What Successful Platforms Track

### 1. Cognitive Dimensions (Knowledge State) ✅ Partially Covered

**What Industry Tracks:**
- Current vocabulary size (estimated)
- Known words/senses (verified)
- Learning words (in progress)
- Mastery levels per word
- Knowledge gaps
- Prerequisite knowledge
- Learning velocity (words learned per week)

**Our Status:**
- ✅ We track: learning progress, verification schedules, mastery levels
- ❌ Missing: vocabulary size estimation, learning velocity metrics, prerequisite tracking

**Examples:**
- **Duolingo:** Shows "You know ~2,500 words" and "You've learned 50 words this month"
- **Memrise:** Tracks vocabulary size and learning streaks
- **Anki:** Shows cards by difficulty and mastery level

---

### 2. Behavioral Dimensions (Engagement & Activity) ⚠️ Partially Covered

**What Industry Tracks:**
- Daily/weekly activity patterns
- Session frequency and duration
- Time spent per word/sense
- Response times (fast/slow indicators)
- Completion rates
- Drop-off points
- Learning streaks

**Our Status:**
- ✅ We track: review history, response times, total reviews
- ❌ Missing: session-level data, streaks, activity patterns, time-on-task

**Research Finding:**
> "Real-time data collection enables educators to monitor learner progress continuously, allowing for timely interventions." - Brookings Institute

---

### 3. Affective Dimensions (Motivation & Emotion) ❌ Missing

**What Industry Tracks:**
- Self-reported confidence levels
- Difficulty ratings per word
- Frustration indicators (leeches)
- Motivation scores
- Learning goals
- Preferred learning styles

**Our Status:**
- ✅ We track: leech detection (indirect frustration indicator)
- ❌ Missing: explicit confidence, difficulty ratings, motivation, goals

**Research Finding:**
> "Self-reporting actively involves learners in their educational journey, enhancing self-awareness and motivation." - TrekLearn Research

---

### 4. Metacognitive Dimensions (Self-Awareness) ❌ Missing

**What Industry Tracks:**
- Self-assessment accuracy
- Calibration (predicted vs actual performance)
- Reflection prompts
- Goal setting and tracking
- Learning strategy awareness

**Our Status:**
- ✅ We track: performance data
- ❌ Missing: self-assessment, calibration metrics, goal tracking

**Research Finding:**
> "Combining self-reported insights with system data enhances the accuracy of progress tracking." - TrekLearn Research

---

### 5. Social Dimensions (Relationships) ✅ Covered

**What Industry Tracks:**
- Coach/mentor relationships
- Peer learning groups
- Collaborative progress
- Social motivation

**Our Status:**
- ✅ We track: user relationships (coach_student, friend, classmate, sibling)

**Research Finding:**
> "LRM systems focus on student-centric designs that facilitate personalized learning paths and provide a central point for analytics data." - Wikipedia

---

### 6. Temporal Dimensions (Learning Trajectory) ⚠️ Partially Covered

**What Industry Tracks:**
- Learning history timeline
- Progress velocity
- Retention curves
- Forgetting patterns
- Improvement trends

**Our Status:**
- ✅ We track: survey history, review history
- ❌ Missing: velocity metrics, retention curves, trend analysis

**Research Finding:**
> "Predictive analytics utilize historical data to forecast future outcomes, enabling timely interventions." - DataCalculus Research

---

## Scientific Research Findings

### 1. Knowledge Tracing Models (BKT, DKT)

**Research:** Bayesian Knowledge Tracing (BKT) and Deep Knowledge Tracing (DKT) are state-of-the-art models for tracking learner knowledge.

**Key Findings:**
- Effective systems track **probability of knowing each concept** (0-1)
- Learning rate per concept
- Guess/slip probabilities
- Prior knowledge estimates

**Our Status:**
- ✅ We have mastery levels (learning → permanent)
- ❌ Missing: Probabilistic knowledge states

**Implication:** We should track confidence/probability, not just binary "known/unknown"

---

### 2. Vocabulary Learning Research (Nation, Laufer)

**Research:** Nation's Vocabulary Levels Test and Laufer's frequency-based assessment are gold standards.

**Key Metrics:**
- **Vocabulary size** (total known words)
- **Frequency band coverage** (1K, 2K, 3K, etc.)
- **Receptive vs productive knowledge**
- **Word family knowledge**
- **Collocation knowledge**

**Our Status:**
- ✅ We track: Individual words via learning_progress
- ✅ We have: Survey system that estimates vocabulary size
- ❌ Missing: Continuous vocabulary size tracking (not just survey snapshots)
- ❌ Missing: Frequency band coverage tracking

**Implication:** We should calculate vocabulary size from verified learning_progress entries and track frequency band coverage.

---

### 3. Adaptive Learning Systems

**Research:** Adaptive learning systems use Item Response Theory (IRT) and ability estimation.

**Key Components:**
- Ability estimates (IRT models)
- Difficulty calibration
- Personalized learning paths
- Prerequisite relationships

**Our Status:**
- ✅ We have: MCQ ability estimates (in MCQ adaptive service)
- ❌ Missing: Unified ability model across all learning

**Implication:** We should integrate ability estimates into the learner profile.

---

### 4. Self-Regulated Learning (Zimmerman)

**Research:** Self-regulated learning theory emphasizes learner agency.

**Key Components:**
- Goal setting
- Strategy selection
- Self-monitoring
- Self-evaluation
- Self-reflection

**Our Status:**
- ❌ Missing: All components

**Implication:** We should add goal setting and self-assessment features.

---

### 5. Engagement and Motivation (Deci & Ryan, Self-Determination Theory)

**Research:** Self-Determination Theory identifies three psychological needs.

**Key Components:**
- **Autonomy** (choice in learning)
- **Competence** (progress feedback)
- **Relatedness** (social connections)
- Intrinsic vs extrinsic motivation

**Our Status:**
- ✅ We have: Points system (extrinsic motivation)
- ✅ We have: Social relationships (relatedness)
- ❌ Missing: Autonomy tracking, intrinsic motivation indicators

**Implication:** We should track learning choices and intrinsic motivation.

---

## What We Currently Have ✅

### Strong Foundation

1. **Learning Progress Tracking**
   - Words in learning/verified/failed states
   - Tier-based organization
   - Timeline (learned_at)

2. **Spaced Repetition State**
   - Mastery levels (learning → permanent)
   - Algorithm state (SM-2+, FSRS)
   - Review history
   - Leech detection

3. **Performance Metrics**
   - Review statistics
   - Retention rates
   - MCQ performance
   - Response times

4. **Financial Tracking**
   - Points earned/locked/withdrawn
   - Transaction history

5. **Survey Data**
   - Vocabulary size estimates (Volume)
   - Frequency band coverage (Reach)
   - Knowledge density (Density)
   - Efficiency metrics

6. **Social Structure**
   - User relationships
   - Role-based access

---

## Critical Gaps Identified ❌

### 1. Vocabulary Size Estimation (HIGH PRIORITY)

**Research:** Nation's Vocabulary Levels Test, Laufer's frequency-based assessment

**Missing:**
- Current vocabulary size (not just survey snapshots)
- Frequency band coverage (1K, 2K, 3K words known)
- Growth trajectory

**Impact:** Cannot show "You know ~2,500 words" or "You've learned 50 words this month"

**Effort:** Low (can calculate from existing learning_progress data)

---

### 2. Learning Velocity and Trends (HIGH PRIORITY)

**Research:** Learning analytics emphasizes trend analysis

**Missing:**
- Words learned per week/month
- Learning rate changes
- Activity streaks
- Session frequency

**Impact:** Cannot show "You're learning faster!" or "You've been active 7 days in a row"

**Effort:** Low (can calculate from existing timestamps)

---

### 3. Self-Assessment and Calibration (MEDIUM PRIORITY)

**Research:** Self-regulated learning shows calibration improves outcomes

**Missing:**
- Pre-test confidence ratings
- Post-test reflection
- Calibration accuracy (predicted vs actual)

**Impact:** Cannot help learners become more self-aware

**Effort:** Medium (requires new UI and data collection)

---

### 4. Goal Setting and Tracking (MEDIUM PRIORITY)

**Research:** Goal-setting theory shows goals improve motivation

**Missing:**
- Learning goals (e.g., "Learn 100 words this month")
- Daily targets
- Progress toward goals

**Impact:** Cannot support goal-oriented learning

**Effort:** Medium (requires new tables and UI)

---

### 5. Engagement Patterns (MEDIUM PRIORITY)

**Research:** Engagement metrics predict retention

**Missing:**
- Session duration
- Time-on-task per word
- Activity heatmaps
- Drop-off analysis

**Impact:** Cannot identify at-risk learners early

**Effort:** Medium (requires session tracking)

---

### 6. Difficulty and Confidence Tracking (LOW PRIORITY)

**Research:** Difficulty ratings improve personalization

**Missing:**
- User-reported difficulty per word
- Confidence levels
- Frustration indicators (beyond leeches)

**Impact:** Less personalized difficulty adjustment

**Effort:** Low (can add to existing review flow)

---

## Recommended Learner Profile Model

### Core Dimensions to Track

```python
class LearnerProfile:
    # 1. IDENTITY (Current ✅)
    user_id: UUID
    name, age, roles
    
    # 2. VOCABULARY KNOWLEDGE (Partially ✅)
    vocabulary_size: int  # Current estimated size
    frequency_bands: Dict[str, int]  # {1K: 850, 2K: 420, ...}
    known_words: List[str]  # Verified learning points
    learning_words: List[str]  # In progress
    mastery_distribution: Dict[str, int]  # {learning: 15, mastered: 42}
    
    # 3. LEARNING VELOCITY (Missing ❌)
    words_learned_this_week: int
    words_learned_this_month: int
    learning_rate: float  # Words per week
    activity_streak: int  # Days active
    
    # 4. PERFORMANCE METRICS (Partially ✅)
    retention_rate: float
    avg_response_time_ms: int
    leech_count: int
    algorithm_type: str
    
    # 5. ENGAGEMENT (Missing ❌)
    sessions_this_week: int
    avg_session_duration_minutes: int
    last_active_date: date
    total_time_learned_hours: float
    
    # 6. GOALS & MOTIVATION (Missing ❌)
    learning_goals: List[Goal]  # {target: 100, deadline: "2024-02-01", type: "words"}
    daily_target: int
    motivation_level: str  # "high", "medium", "low"
    
    # 7. SELF-ASSESSMENT (Missing ❌)
    self_assessment_accuracy: float  # How well they predict performance
    confidence_levels: Dict[str, float]  # Per word/sense
    
    # 8. TEMPORAL TRENDS (Partially ✅)
    progress_timeline: List[ProgressPoint]
    survey_history: List[SurveyResult]
    improvement_rate: float  # % improvement over time
```

---

## Priority Recommendations

### Phase 1: Essential Learner Visibility (1-2 weeks) 🎯 START HERE

**Goal:** Provide complete learner status in a single API call

1. **Vocabulary Size Estimation**
   - Calculate from verified learning_progress
   - Track frequency band coverage
   - Show growth over time

2. **Learning Velocity Metrics**
   - Words learned per week/month
   - Activity streaks
   - Learning rate trends

3. **Combined Dashboard Endpoint**
   - Single API call for complete learner status
   - Include all existing data + new metrics

**Impact:** High (complete learner picture)  
**Effort:** Low (leverages existing data)

---

### Phase 2: Enhanced Personalization (2-3 weeks)

4. **Goal Setting System**
   - Allow users to set learning goals
   - Track progress toward goals
   - Show goal completion

5. **Engagement Tracking**
   - Session-level data
   - Time-on-task
   - Activity patterns

**Impact:** Medium (improves motivation)  
**Effort:** Medium (requires new tables)

---

### Phase 3: Advanced Features (3-4 weeks)

6. **Self-Assessment Integration**
   - Pre-test confidence
   - Calibration metrics
   - Reflection prompts

7. **Difficulty and Confidence Tracking**
   - User-reported difficulty
   - Confidence levels
   - Personalized difficulty adjustment

**Impact:** Medium (improves self-awareness)  
**Effort:** Medium (requires UI changes)

---

## Implementation Plan: Phase 1

### Step 1: Vocabulary Size Calculation Service

**File:** `backend/src/services/vocabulary_size.py`

**Functions:**
- `calculate_vocabulary_size(user_id)` - Count verified learning points
- `get_frequency_band_coverage(user_id)` - Group by frequency bands
- `get_vocabulary_growth_timeline(user_id, days=90)` - Growth over time

**Data Source:** `learning_progress` table (status='verified')

---

### Step 2: Learning Velocity Service

**File:** `backend/src/services/learning_velocity.py`

**Functions:**
- `get_words_learned_period(user_id, start_date, end_date)` - Count verified in period
- `calculate_activity_streak(user_id)` - Consecutive days with activity
- `get_learning_rate(user_id, days=30)` - Words per week

**Data Source:** `learning_progress` table (learned_at timestamps)

---

### Step 3: Combined Dashboard API

**File:** `backend/src/api/dashboard.py` (NEW)

**Endpoint:** `GET /api/v1/dashboard`

**Response:**
```json
{
  "learner_profile": {
    "vocabulary_size": 2500,
    "frequency_bands": {"1K": 850, "2K": 420, "3K": 380},
    "words_learned_this_week": 25,
    "words_learned_this_month": 100,
    "activity_streak": 7,
    "learning_rate": 12.5
  },
  "performance": {
    "retention_rate": 0.85,
    "total_reviews": 500,
    "cards_learning": 15,
    "cards_mastered": 42
  },
  "engagement": {
    "reviews_today": 10,
    "last_active": "2025-01-15"
  },
  "points": {
    "total_earned": 1250,
    "available_points": 1000
  }
}
```

---

## Conclusion

We have a **solid foundation** for learning progress and performance tracking, but we're missing several dimensions that research shows significantly improve learning outcomes:

1. ✅ **Vocabulary size estimation** (high impact, low effort)
2. ✅ **Learning velocity metrics** (high impact, low effort)
3. ⏳ **Goal tracking** (medium impact, medium effort)
4. ⏳ **Engagement patterns** (medium impact, medium effort)

**Recommendation:** Start with **Phase 1** (vocabulary size + velocity metrics) to provide a complete learner picture with minimal effort.

---

## References

1. **Learning Analytics Research:**
   - Brookings Institute: "Digital Tools for Real-Time Data Collection in Education"
   - TrekLearn: "Tracking Learner Progress"
   - DataCalculus: "Tracking and Reporting Learner Progress"

2. **Vocabulary Learning Research:**
   - Nation, I.S.P. (2001). "Learning Vocabulary in Another Language"
   - Laufer, B. (1998). "The Development of Passive and Active Vocabulary"

3. **Knowledge Tracing:**
   - Corbett, A.T. & Anderson, J.R. (1995). "Knowledge Tracing: Modeling the Acquisition of Procedural Knowledge"
   - Piech, C. et al. (2015). "Deep Knowledge Tracing"

4. **Self-Regulated Learning:**
   - Zimmerman, B.J. (2002). "Becoming a Self-Regulated Learner: An Overview"

5. **Motivation Theory:**
   - Deci, E.L. & Ryan, R.M. (2000). "Self-Determination Theory and the Facilitation of Intrinsic Motivation"

---

**Next Steps:** Implement Phase 1 (vocabulary size + velocity metrics + dashboard endpoint)

