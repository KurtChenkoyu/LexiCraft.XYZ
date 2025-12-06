# FSRS vs SM-2+ Technical Comparison

**Date:** 2024-12  
**Purpose:** Understand the fundamental differences between FSRS and SM-2+ algorithms

---

## Executive Summary

| Aspect | SM-2+ (Our Design) | FSRS (Modern Standard) |
|--------|-------------------|------------------------|
| **Type** | Rule-based formula | Machine learning (neural network) |
| **Complexity** | Simple (50 lines) | Complex (requires training) |
| **Personalization** | Per-word ease factor | Per-user forgetting curve |
| **Efficiency** | Good | Better (20-30% fewer reviews) |
| **Data Needed** | Minimal | Needs history to train |
| **Cold Start** | Works immediately | Needs 100+ reviews to optimize |
| **Maintenance** | None | Periodic retraining |

**TL;DR:** FSRS is more accurate but complex. SM-2+ is simpler and works immediately. Both are valid choices.

---

## 1. Core Philosophy

### SM-2+ (Rule-Based)

**Approach:** Fixed mathematical formula that adjusts based on performance

```
IF performance is good:
    interval = previous_interval × ease_factor
ELSE:
    interval = 1 (reset)
    
ease_factor adjusts based on performance
```

**Key Concept:** "Ease Factor" - how easy this word is for this user
- Starts at 2.5 (average)
- Increases if user performs well
- Decreases if user struggles
- Range: 1.3 - 3.0

### FSRS (Machine Learning)

**Approach:** Neural network that learns your personal forgetting curve

```
Predict retention probability = f(stability, difficulty, elapsed_time)

IF retention_probability < threshold:
    schedule review
ELSE:
    don't review yet
```

**Key Concepts:**
- **Stability:** How well you know this word (like ease factor, but more nuanced)
- **Difficulty:** How hard this word is (learned from all users)
- **Retention:** Probability you'll remember it at review time

---

## 2. How They Work

### SM-2+ Algorithm (Our Design)

```python
# Simplified version
def sm2_plus(current_interval, ease_factor, performance, consecutive_correct):
    # 1. Update ease factor based on performance
    if performance >= 3:  # Passed
        new_ef = ease_factor + 0.1  # Increase ease
    else:  # Failed
        new_ef = ease_factor - 0.2  # Decrease ease
    
    new_ef = clamp(new_ef, 1.3, 3.0)
    
    # 2. Calculate next interval
    if performance < 3:
        next_interval = 1  # Reset
    elif consecutive_correct < 3:
        # Fixed progression: 1 → 3 → 7
        next_interval = [1, 3, 7][consecutive_correct]
    else:
        # Multiply by ease factor
        next_interval = int(current_interval * new_ef)
    
    return next_interval, new_ef
```

**Characteristics:**
- ✅ Simple: ~50 lines of code
- ✅ Deterministic: Same inputs = same outputs
- ✅ Works immediately: No training needed
- ⚠️ One-size-fits-all: Same formula for everyone
- ⚠️ Can be inefficient: May review too often or too rarely

### FSRS Algorithm (Modern Standard)

```python
# Simplified conceptual version
class FSRS:
    def __init__(self):
        self.neural_network = load_trained_model()
        # Model has learned from millions of review sessions
    
    def predict_retention(self, stability, difficulty, elapsed_days):
        """
        Predict probability user will remember this word.
        
        Uses neural network trained on:
        - User's historical performance
        - Word difficulty (from all users)
        - Time since last review
        - Other factors (time of day, fatigue, etc.)
        """
        features = [
            stability,
            difficulty,
            elapsed_days,
            # ... 20+ other features
        ]
        retention_prob = self.neural_network.predict(features)
        return retention_prob
    
    def schedule_review(self, word, user):
        stability = word.stability_for_user(user)
        difficulty = word.global_difficulty
        elapsed_days = (today - word.last_review).days
        
        retention = self.predict_retention(stability, difficulty, elapsed_days)
        
        if retention < 0.9:  # Less than 90% chance of remembering
            schedule_review()
        else:
            extend_interval()
    
    def update_after_review(self, word, user, performance):
        """
        Update stability and difficulty based on actual performance.
        """
        # Update stability (how well user knows this word)
        if performance == "correct":
            word.stability *= 1.5  # Increase stability
        else:
            word.stability *= 0.8  # Decrease stability
        
        # Update difficulty (how hard this word is globally)
        word.difficulty = update_global_difficulty(word, performance)
```

**Characteristics:**
- ✅ Personalized: Learns your forgetting curve
- ✅ Efficient: 20-30% fewer reviews needed
- ✅ Accurate: Better retention prediction
- ⚠️ Complex: Requires neural network
- ⚠️ Needs data: Requires 100+ reviews to optimize
- ⚠️ Maintenance: Periodic retraining recommended

---

## 3. Key Differences

### 3.1 Personalization

**SM-2+:**
- Personalizes per **word** (ease factor per word per user)
- Formula is the same for everyone
- Example: "apple" has EF=2.8 for you, EF=2.3 for me

**FSRS:**
- Personalizes per **user** (learns your forgetting curve)
- Also tracks word difficulty (global)
- Example: Your forgetting curve is different from mine, and "apple" is easier than "ephemeral" for everyone

**Impact:**
- FSRS adapts to **how you learn** (fast learner vs slow learner)
- SM-2+ adapts to **what you learn** (easy words vs hard words)

### 3.2 Interval Calculation

**SM-2+:**
```
Interval = Previous_Interval × Ease_Factor

Example:
  Day 1: interval = 1
  Day 3: interval = 3 (1 × 3, but clamped to fixed progression)
  Day 7: interval = 7
  Day 20: interval = 7 × 2.8 = 19.6 → 20 days
  Day 56: interval = 20 × 2.8 = 56 days
```

**FSRS:**
```
Retention = Neural_Network(stability, difficulty, elapsed_time)

IF retention < 0.9:
    Schedule review (interval calculated to hit 0.9 retention)
ELSE:
    Extend interval (calculate when retention will drop to 0.9)

Example:
  Day 1: retention = 0.95 → extend
  Day 3: retention = 0.92 → extend
  Day 7: retention = 0.88 → schedule review
  Day 20: retention = 0.91 → extend
  Day 60: retention = 0.89 → schedule review
```

**Impact:**
- FSRS schedules based on **predicted forgetting**
- SM-2+ schedules based on **fixed multiplication**

### 3.3 Efficiency

**Research Findings:**
- FSRS: **20-30% fewer reviews** needed vs SM-2
- FSRS: **Same or better retention** rates
- FSRS: **Less user fatigue** (fewer unnecessary reviews)

**Why FSRS is more efficient:**
- SM-2+ might review too early (you still remember it)
- SM-2+ might review too late (you already forgot)
- FSRS predicts when you'll forget and reviews just before

**Example:**
```
Word: "apple" (easy for you)

SM-2+ schedule:
  Day 1, 3, 7, 20, 56, 157, 365
  (7 reviews in first year)

FSRS schedule:
  Day 1, 4, 12, 35, 120, 400
  (6 reviews in first year, but better retention)
```

### 3.4 Complexity

**SM-2+ Implementation:**
```python
# ~50 lines of code
def calculate_interval(ef, performance, consecutive):
    if performance < 3:
        return 1, ef - 0.2
    new_ef = ef + 0.1
    if consecutive < 3:
        return [1, 3, 7][consecutive], new_ef
    return int(prev_interval * new_ef), new_ef
```

**FSRS Implementation:**
```python
# Requires:
# 1. Neural network model (pre-trained, ~10MB)
# 2. Feature engineering (20+ features)
# 3. Training pipeline (for personalization)
# 4. Retraining logic (periodic updates)
# ~1000+ lines of code + model files
```

**Impact:**
- SM-2+: Easy to implement, debug, understand
- FSRS: Complex, requires ML expertise, harder to debug

### 3.5 Cold Start Problem

**SM-2+:**
- ✅ Works immediately
- ✅ No data needed
- ✅ Predictable behavior

**FSRS:**
- ⚠️ Needs 100+ reviews to personalize
- ⚠️ Uses default model until enough data
- ⚠️ Gets better over time

**Impact:**
- New users: SM-2+ works better initially
- Experienced users: FSRS works better after 100+ reviews

---

## 4. Real-World Example

### Scenario: Learning "ephemeral" (hard word)

**SM-2+ Behavior:**
```
Review 1 (Day 1): Performance = 3 (correct but slow)
  → EF = 2.5 - 0.1 = 2.4
  → Next: Day 3

Review 2 (Day 3): Performance = 2 (incorrect)
  → EF = 2.4 - 0.2 = 2.2
  → Next: Day 1 (reset)

Review 3 (Day 4): Performance = 3 (correct)
  → EF = 2.2 + 0.1 = 2.3
  → Next: Day 3

Review 4 (Day 7): Performance = 3 (correct)
  → EF = 2.3 + 0.1 = 2.4
  → Next: Day 7

Review 5 (Day 14): Performance = 4 (good)
  → EF = 2.4 + 0.1 = 2.5
  → Next: Day 7 × 2.5 = 17.5 → 18 days

Total: 5 reviews in first month
```

**FSRS Behavior:**
```
Review 1 (Day 1): Performance = 3
  → Stability = 1.5 (low, because hard word)
  → Difficulty = 0.8 (high difficulty)
  → Retention prediction: 0.85 (will forget soon)
  → Next: Day 2 (schedule early)

Review 2 (Day 2): Performance = 2
  → Stability = 1.2 (decreased)
  → Retention prediction: 0.75
  → Next: Day 1 (reset, review tomorrow)

Review 3 (Day 3): Performance = 3
  → Stability = 1.5
  → Retention prediction: 0.82
  → Next: Day 2

Review 4 (Day 5): Performance = 3
  → Stability = 2.0
  → Retention prediction: 0.88
  → Next: Day 4

Review 5 (Day 9): Performance = 4
  → Stability = 3.0
  → Retention prediction: 0.91
  → Next: Day 8

Total: 5 reviews in first month (similar, but better timing)
```

**Key Difference:**
- SM-2+: Fixed progression (1→3→7→multiply)
- FSRS: Dynamic timing (reviews when retention drops to 90%)

---

## 5. When to Use Which?

### Use SM-2+ (Our Current Design) If:

✅ **MVP/Launch:** Need something that works immediately  
✅ **Simplicity:** Want easy-to-understand, debuggable code  
✅ **Small Team:** Don't have ML expertise  
✅ **New Users:** Works well from day 1  
✅ **Predictable:** Need deterministic behavior  
✅ **Low Resources:** Don't want to maintain ML model  

### Use FSRS If:

✅ **Post-MVP:** Have time to implement complex system  
✅ **ML Expertise:** Have team that can maintain neural network  
✅ **Large User Base:** Have enough data to train models  
✅ **Efficiency Critical:** Need to minimize reviews  
✅ **Long-term:** Planning to scale and optimize  

---

## 6. Hybrid Approach (Best of Both)

**Option: Start with SM-2+, migrate to FSRS**

```
Phase 1 (MVP): SM-2+
  - Simple, works immediately
  - Collect user data

Phase 2 (v2): FSRS
  - Use collected data to train FSRS
  - Migrate users gradually
  - A/B test: SM-2+ vs FSRS

Phase 3 (v3): Full FSRS
  - All users on FSRS
  - Continuous model improvement
```

**Benefits:**
- ✅ Launch faster (SM-2+)
- ✅ Collect data (for FSRS training)
- ✅ Improve over time (FSRS)
- ✅ Best of both worlds

---

## 7. Technical Implementation Comparison

### SM-2+ Database Schema

```sql
CREATE TABLE verification_schedule (
    id SERIAL PRIMARY KEY,
    user_id UUID,
    word_id TEXT,
    current_interval INTEGER,      -- days
    ease_factor FLOAT,             -- 1.3 - 3.0
    consecutive_correct INTEGER,
    next_review_date DATE
);
```

**Simple:** 6 columns, straightforward queries

### FSRS Database Schema

```sql
CREATE TABLE verification_schedule (
    id SERIAL PRIMARY KEY,
    user_id UUID,
    word_id TEXT,
    stability FLOAT,               -- Learned from neural network
    difficulty FLOAT,              -- Global word difficulty
    last_review_date DATE,
    next_review_date DATE,
    retention_probability FLOAT    -- Predicted retention
);

CREATE TABLE fsrs_model (
    id SERIAL PRIMARY KEY,
    user_id UUID,
    model_weights JSONB,           -- Neural network weights
    trained_at TIMESTAMP,
    performance_metrics JSONB
);
```

**Complex:** More columns, requires model storage, periodic retraining

---

## 8. Performance Comparison

| Metric | SM-2+ | FSRS | Winner |
|--------|-------|------|--------|
| **Reviews needed** | 100% baseline | 70-80% | FSRS ✅ |
| **Retention rate** | 85-90% | 90-95% | FSRS ✅ |
| **Implementation time** | 1 week | 1-2 months | SM-2+ ✅ |
| **Maintenance** | None | Periodic | SM-2+ ✅ |
| **Cold start** | Immediate | Needs data | SM-2+ ✅ |
| **Personalization** | Per-word | Per-user + per-word | FSRS ✅ |
| **Accuracy** | Good | Better | FSRS ✅ |
| **Predictability** | High | Medium | SM-2+ ✅ |

---

## 9. Code Complexity

### SM-2+ Implementation

```python
# ~50 lines, easy to understand
def calculate_next_interval(current_interval, ease_factor, performance, consecutive):
    # Update ease factor
    if performance >= 3:
        new_ef = min(3.0, ease_factor + 0.1)
    else:
        new_ef = max(1.3, ease_factor - 0.2)
    
    # Calculate interval
    if performance < 3:
        return 1, new_ef
    elif consecutive < 3:
        intervals = [1, 3, 7]
        return intervals[consecutive], new_ef
    else:
        return int(current_interval * new_ef), new_ef
```

### FSRS Implementation

```python
# Requires:
# 1. Neural network library (PyTorch/TensorFlow)
# 2. Model loading
# 3. Feature engineering
# 4. Prediction logic
# 5. Model updating
# ~500+ lines + model files

import torch
from fsrs import FSRS

class FSRSModel:
    def __init__(self):
        self.model = FSRS.load_pretrained()
    
    def predict_retention(self, stability, difficulty, elapsed_days):
        features = self._extract_features(stability, difficulty, elapsed_days)
        return self.model.predict(features)
    
    def update_model(self, review_history):
        # Retrain model periodically
        self.model.retrain(review_history)
    
    # ... 20+ more methods
```

---

## 10. Recommendation

### For LexiCraft MVP:

**✅ Use SM-2+ (Current Design)**

**Reasons:**
1. **Faster to implement:** 1 week vs 1-2 months
2. **Works immediately:** No cold start problem
3. **Easier to debug:** Simple, predictable
4. **Good enough:** 85-90% retention is excellent
5. **Collect data:** Can use data later for FSRS

### For LexiCraft v2:

**⚠️ Consider FSRS Migration**

**When:**
- Have 1000+ users with 100+ reviews each
- Have ML expertise on team
- Want to optimize efficiency
- Have time for complex implementation

**How:**
- A/B test: 50% SM-2+, 50% FSRS
- Measure: Reviews needed, retention rate
- Migrate if FSRS shows 20%+ improvement

---

## 11. Summary

| Question | SM-2+ | FSRS |
|----------|-------|------|
| **What is it?** | Rule-based formula | Machine learning model |
| **How complex?** | Simple (50 lines) | Complex (500+ lines + model) |
| **Personalization?** | Per-word ease factor | Per-user forgetting curve |
| **Efficiency?** | Good (100% baseline) | Better (70-80% of baseline) |
| **Works immediately?** | ✅ Yes | ⚠️ Needs data |
| **Maintenance?** | None | Periodic retraining |
| **Best for MVP?** | ✅ Yes | ❌ No |
| **Best for scale?** | ⚠️ Good enough | ✅ Better |

**Bottom Line:** SM-2+ is perfect for MVP. FSRS is better long-term, but can wait until v2.

