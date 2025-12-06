# Vocabulary Assessment Research & LexiSurvey Redesign Proposal

## Executive Summary

After researching established vocabulary assessment methodologies (Nation's VLT, CAT/IRT, IVST, TestYourVocab), I've identified several fundamental issues with our current 3-phase binary search approach. This document outlines the problems and proposes a redesign based on research best practices.

---

## Part 1: Research Findings

### 1.1 Established Vocabulary Assessment Methodologies

#### Nation's Vocabulary Levels Test (VLT)
- **Approach**: Tests words at specific frequency bands (2K, 3K, 5K, 10K words)
- **Key Insight**: Score at each level extrapolates to total knowledge
- **Formula**: If learner scores 80% at 5000-word level → knows ~4000 words at that level
- **Total estimate**: Sum across all frequency bands

#### TestYourVocab.com
- **Approach**: Self-report on word recognition across frequency bands
- **Sample size**: ~40 words per band, sampled randomly
- **Extrapolation**: `(words_known / words_tested) × band_size`
- **Accuracy**: ±10% margin of error

#### Intelligent Vocabulary Size Test (IVST)
- **Approach**: Neural network-based adaptive testing
- **Convergence**: ~60 questions to reach stable estimate
- **Key Feature**: Dynamically adjusts difficulty based on responses
- **Stopping rule**: Continues until estimate stabilizes

#### Computer Adaptive Testing (CAT) with IRT
- **Approach**: Item Response Theory models probability of correct response
- **Stopping rules**:
  - Minimum questions (e.g., 10-20)
  - Standard Error < threshold (typically 0.25-0.30)
  - Maximum questions (safety limit, e.g., 50-100)
- **Efficiency**: Can achieve same precision as 50-item fixed test with 15-20 adaptive items

### 1.2 Key Concepts from Research

#### Breadth vs Depth
- **Breadth**: Number of words known (what we call "Volume")
- **Depth**: How well each word is known (multiple meanings, usage, collocations)
- **Our focus**: Primarily breadth (receptive vocabulary size)

#### Vocabulary Acquisition is Probabilistic
**Critical insight**: Learners don't have a sharp cutoff at rank X!

Reality:
- Know ~95% of words in top 1000
- Know ~85% of words in 1000-2000
- Know ~60% of words in 2000-3000
- Know ~30% of words in 3000-5000
- Know ~10% of words in 5000+

This is a **probability curve**, not a binary boundary!

#### Confidence-Based Stopping
Research consensus: Stop testing when:
1. Minimum questions answered (10-20)
2. Standard Error of estimate < threshold (0.25-0.30)
3. OR maximum questions reached (50-100)

---

## Part 2: Problems with Our Current Approach

### 2.1 Fixed 3-Phase Design is Arbitrary

```
Phase 1 (Q1-Q5): Coarse sweep ±1500
Phase 2 (Q6-Q12): Fine tuning ±200  
Phase 3 (Q13-Q15): Verification ±100
```

**Problems**:
- Doesn't adapt to learner level
- Beginner might need more questions to find boundary
- Advanced learner might need fewer
- Phase transitions are arbitrary, not based on confidence

### 2.2 Binary Search Model is Fundamentally Wrong

Our model assumes: "User knows ALL words below rank X, NONE above"

**Reality**: Vocabulary acquisition is probabilistic!
- User knows 95% at rank 1000, 70% at 2000, 30% at 4000
- Binary search tries to find a boundary that doesn't exist
- This explains why bounds keep getting "inverted" (low > high)

**Evidence from tests**:
```
User "knows" 2000 words:
- Bounds converge to 2200 (ABOVE true boundary)
- Why? User got some words correct above 2000 (common high-rank words like "worry", "soap")
- Binary search interprets this as "boundary is higher"
```

### 2.3 Volume Calculation Makes No Statistical Sense

Current formula:
```python
for hist in history:
    volume += rank * weight * position_weight
volume = volume // len(history)
```

This is **averaging weighted ranks**, not estimating vocabulary size!

**What it should be**: Extrapolate from frequency band performance
```python
# Correct approach:
# If user got 80% correct at 2000-word level:
# Estimated words known at that level = 0.80 × 2000 = 1600
# Total = sum across all tested bands
```

### 2.4 Reach Calculation is Unreliable

Current: `reach = max(correct_ranks)` with 0.8 penalty

**Problems**:
- One lucky guess at high rank inflates reach
- 0.8 penalty is arbitrary
- Doesn't account for probability distribution

**Should be**: Highest band where performance > 50% (or other threshold)

### 2.5 Density Concept is Good but Disconnected

Our monotonicity-based density is measuring the right thing (consistency), but:
- It's disconnected from the vocabulary model
- Doesn't leverage the probability curve insight

---

## Part 3: Proposed Redesign

### 3.1 Core Philosophy Change

**FROM**: Binary search for a sharp boundary  
**TO**: Probability estimation across frequency bands

### 3.2 New Algorithm: Adaptive Frequency Band Sampling

```
ALGORITHM: AdaptiveVocabEstimation

1. INITIALIZATION
   - Define frequency bands: [0-1K, 1K-2K, 2K-3K, 3K-4K, 4K-5K, 5K-6K, 6K-8K]
   - Start with middle bands (2K-3K, 3K-4K)
   - Initialize: confidence = 0, estimate = 0

2. ADAPTIVE SAMPLING
   WHILE confidence < THRESHOLD and questions < MAX_QUESTIONS:
       a. Select next band based on information gain
       b. Sample random word from that band
       c. Ask question, record result
       d. Update band performance estimates
       e. Calculate new vocabulary estimate
       f. Calculate confidence (inverse of standard error)

3. BAND SELECTION STRATEGY
   Priority:
   - Bands near estimated boundary (high information)
   - Bands with few samples (reduce uncertainty)
   - Avoid over-sampling any single band

4. STOPPING CRITERIA
   Stop when ANY of:
   - confidence >= 0.85 (SE < 0.20)
   - questions >= 30 (enough data)
   - bounds_converged AND questions >= 15

5. METRIC CALCULATION
   Volume = Σ (band_accuracy × band_size) for all bands
   Reach = highest band where accuracy > 50%
   Density = consistency metric (monotonicity)
```

### 3.3 New Metric Definitions

#### Volume (Vocabulary Size Estimate)
```python
def calculate_volume(band_performance):
    """
    Estimate total vocabulary size from band performance.
    
    band_performance = {
        1000: {"tested": 3, "correct": 3},   # 100% at 1K
        2000: {"tested": 4, "correct": 3},   # 75% at 2K  
        3000: {"tested": 5, "correct": 2},   # 40% at 3K
        4000: {"tested": 3, "correct": 0},   # 0% at 4K
    }
    """
    total = 0
    for band, perf in band_performance.items():
        accuracy = perf["correct"] / perf["tested"] if perf["tested"] > 0 else 0
        # Each band represents ~1000 words
        band_contribution = accuracy * 1000
        total += band_contribution
    return int(total)

# Example: 1000 + 750 + 400 + 0 = 2150 words
```

#### Reach (Vocabulary Horizon)
```python
def calculate_reach(band_performance, threshold=0.5):
    """
    Find highest frequency band where accuracy > threshold.
    """
    bands_sorted = sorted(band_performance.keys(), reverse=True)
    for band in bands_sorted:
        perf = band_performance[band]
        if perf["tested"] >= 2:  # Need minimum samples
            accuracy = perf["correct"] / perf["tested"]
            if accuracy >= threshold:
                return band
    return min(band_performance.keys())  # Fallback to lowest band
```

#### Density (Knowledge Consistency)
Keep monotonicity-based approach, but also consider:
```python
def calculate_density(band_performance, history):
    """
    Measure consistency of knowledge across bands.
    
    High density = sharp transition (knows most below boundary, few above)
    Low density = gradual/inconsistent transition
    """
    # Method 1: Monotonicity (current - keep this)
    monotonicity = calculate_monotonicity(history)
    
    # Method 2: Transition sharpness
    # How quickly does accuracy drop across bands?
    accuracies = []
    for band in sorted(band_performance.keys()):
        perf = band_performance[band]
        if perf["tested"] > 0:
            accuracies.append(perf["correct"] / perf["tested"])
    
    if len(accuracies) >= 2:
        # Sharp transition = high variance in accuracies
        # Gradual transition = low variance
        sharpness = max(accuracies) - min(accuracies)
    else:
        sharpness = 0.5
    
    # Combine: density = monotonicity weighted by sharpness
    density = monotonicity * (0.5 + 0.5 * sharpness)
    return density
```

### 3.4 Confidence Calculation

```python
def calculate_confidence(band_performance, history):
    """
    Calculate confidence in vocabulary estimate.
    Based on:
    - Number of questions answered
    - Coverage of frequency bands
    - Consistency of responses
    """
    n_questions = len(history)
    n_bands_tested = sum(1 for b in band_performance.values() if b["tested"] >= 2)
    total_bands = len(band_performance)
    
    # Question factor: more questions = more confidence
    question_factor = min(n_questions / 20, 1.0)  # Saturates at 20 questions
    
    # Coverage factor: testing more bands = more confidence  
    coverage_factor = n_bands_tested / total_bands
    
    # Consistency factor: monotonic responses = more confidence
    monotonicity = calculate_monotonicity(history)
    
    # Combine
    confidence = (
        0.4 * question_factor +
        0.3 * coverage_factor +
        0.3 * monotonicity
    )
    
    return confidence
```

### 3.5 Stopping Criteria

```python
def should_stop(state, confidence):
    """
    Determine if survey should stop.
    
    Stop when ANY of:
    1. High confidence achieved (>= 0.85)
    2. Maximum questions reached (30)
    3. Bounds converged AND minimum questions (15)
    """
    n_questions = len(state.history)
    
    # Always stop at max
    if n_questions >= 30:
        return True
    
    # Stop early if very confident
    if confidence >= 0.85 and n_questions >= 10:
        return True
    
    # Stop if bounds converged and enough questions
    bounds_range = state.high_bound - state.low_bound
    if bounds_range < 500 and n_questions >= 15:
        return True
    
    return False
```

---

## Part 4: Implementation Roadmap

### Phase 1: Core Algorithm Refactor (Priority: HIGH)
1. Add frequency band tracking to SurveyState
2. Implement band-based word selection
3. Update volume calculation to use band extrapolation
4. Update reach calculation to use band thresholds

### Phase 2: Adaptive Stopping (Priority: HIGH)
1. Replace fixed phase structure with confidence-based stopping
2. Implement proper confidence calculation
3. Remove MIN_QUESTIONS=15 hard limit, use dynamic stopping

### Phase 3: Improved Word Selection (Priority: MEDIUM)
1. Implement information-gain based band selection
2. Ensure adequate sampling across bands
3. Avoid over-testing any single band

### Phase 4: Validation (Priority: HIGH)
1. Update Layer 2 tests for new algorithm
2. Update Layer 3 simulations with realistic probability curves
3. Run Layer 4 holistic review

---

## Part 5: Quick Wins (Can Implement Now)

### 5.1 Fix Volume Formula
Change from weighted-rank averaging to band-based estimation.

### 5.2 Fix Reach Formula  
Change from max-correct-rank to threshold-based band finding.

### 5.3 Add Band Tracking
Track performance by frequency band even within current algorithm.

### 5.4 Dynamic Question Limit
Remove fixed 15-20 questions, use confidence threshold.

---

## Appendix: Comparison Table

| Aspect | Current Approach | Research Best Practice | Gap |
|--------|-----------------|----------------------|-----|
| **Model** | Binary boundary | Probability curve | MAJOR |
| **Question Selection** | Binary search | Information-gain adaptive | MAJOR |
| **Stopping Rule** | Fixed 15-20 questions | Confidence threshold | MEDIUM |
| **Volume Calculation** | Weighted rank average | Band extrapolation | MAJOR |
| **Reach Calculation** | Max correct rank | Threshold-based band | MEDIUM |
| **Density** | Monotonicity | Monotonicity | ✅ GOOD |

---

## References

1. Nation, P. (2001). Vocabulary Levels Test
2. TestYourVocab.com methodology
3. IVST: Intelligent Vocabulary Size Test (Language Testing Asia, 2023)
4. CAT/IRT: Computerized Adaptive Testing literature
5. Polish Vocabulary Size Test (PVST) - arXiv:2507.19869

