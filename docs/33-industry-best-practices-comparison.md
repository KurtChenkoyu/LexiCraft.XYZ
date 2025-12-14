# Industry Best Practices vs. Current ASRS Design

**Date:** 2024-12  
**Purpose:** Compare our Adaptive Spaced Repetition System (ASRS) against industry standards

---

## Executive Summary

| Aspect | Industry Standard | Our Design | Gap Analysis |
|--------|------------------|------------|--------------|
| **Algorithm** | FSRS (modern) or SM-2 (legacy) | SM-2+ (modified) | ⚠️ Should consider FSRS |
| **Max Interval** | 365+ days (Anki), unlimited (SuperMemo) | 365 days | ✅ Aligned |
| **Difficulty Tracking** | Per-item ease factor | Per-word ease factor | ✅ Aligned |
| **Leech Detection** | Standard in Anki/SuperMemo | Implemented | ✅ Aligned |
| **Mastery Detection** | Graduation system | 5-level mastery | ✅ Aligned |
| **Response Time** | Tracked in modern systems | Tracked | ✅ Aligned |
| **Active Recall** | Core principle | MCQ format | ✅ Aligned |
| **Personalization** | Per-user adaptation | Per-user ease factor | ✅ Aligned |

**Overall Assessment:** Our design is **well-aligned** with industry best practices, but we should consider upgrading to **FSRS algorithm** for better performance.

---

## 1. Algorithm Comparison

### 1.1 Industry Standards

#### SM-2 (SuperMemo 2) - Legacy but Proven
- **Used by:** SuperMemo (original), Anki (legacy mode)
- **Characteristics:**
  - Ease factor: 1.3 - 2.5 (default 2.5)
  - Simple multiplication: `interval = previous_interval * ease_factor`
  - Performance-based ease factor adjustment
  - **Pros:** Simple, proven, widely understood
  - **Cons:** Can be too aggressive for some users, doesn't account for forgetting curve well

#### FSRS (Free Spaced Repetition Scheduler) - Modern Standard
- **Used by:** Anki (default since 2023), modern SRS apps
- **Characteristics:**
  - Neural network-based prediction
  - Considers multiple factors: stability, difficulty, retention
  - Better handles forgetting curve
  - **Pros:** More accurate, better retention prediction, handles edge cases
  - **Cons:** More complex, requires more data to train

#### SM-4, SM-5, SM-6 (SuperMemo Evolution)
- **Used by:** SuperMemo (paid versions)
- **Characteristics:**
  - Progressive improvements over SM-2
  - Better difficulty estimation
  - More sophisticated interval calculation
  - **Pros:** Highly optimized, research-backed
  - **Cons:** Proprietary, complex

### 1.2 Our Design: SM-2+

**What we have:**
```python
# Modified SM-2 with:
- Ease factor: 1.3 - 3.0 (wider range than SM-2)
- Performance scale: 0-5 (more granular than SM-2's binary)
- Consecutive correct tracking
- Max interval: 365 days
```

**Comparison:**

| Feature | SM-2 (Industry) | FSRS (Industry) | Our SM-2+ |
|---------|-----------------|-----------------|-----------|
| Ease Factor Range | 1.3 - 2.5 | N/A (uses stability) | 1.3 - 3.0 ✅ |
| Performance Granularity | Binary (pass/fail) | Continuous | 0-5 scale ✅ |
| Forgetting Curve | Basic | Advanced | Basic ⚠️ |
| Max Interval | Unlimited | Unlimited | 365 days ⚠️ |
| Difficulty Tracking | Per-item | Per-item | Per-word ✅ |
| Complexity | Low | High | Medium ✅ |

**Recommendation:**
- ✅ **Short-term:** Keep SM-2+ (it's good enough, simpler to implement)
- ⚠️ **Long-term:** Consider FSRS for better accuracy (after MVP)

---

## 2. Interval Progression Comparison

### 2.1 Industry Standards

#### Anki (FSRS)
```
Easy word: 1 → 4 → 10 → 25 → 60 → 150 → 365 → 1000+ days
Hard word: 1 → 1 → 3 → 7 → 15 → 30 → 60 → 120 → 240 → 365+ days
```

#### SuperMemo (SM-6)
```
Easy word: 1 → 4 → 10 → 20 → 50 → 120 → 300 → 800+ days
Hard word: 1 → 1 → 2 → 5 → 10 → 20 → 40 → 80 → 160 → 320+ days
```

#### Duolingo (Simplified)
```
Fixed progression: 1 → 6 hours → 1 day → 2 days → 7 days → 14 days → 30 days
(Then stops - no mastery concept)
```

### 2.2 Our Design

**Easy word (EF = 2.8):**
```
1 → 3 → 7 → 20 → 56 → 157 → 365 days
```

**Average word (EF = 2.5):**
```
1 → 3 → 7 → 18 → 45 → 112 → 280 → 365 days
```

**Hard word (EF = 1.8):**
```
1 → 3 → 7 → 13 → 23 → 41 → 74 → 133 → 239 → 365 days
```

**Comparison:**

| Word Type | Anki (FSRS) | SuperMemo | Our Design | Assessment |
|-----------|-------------|-----------|------------|------------|
| Easy | 1→4→10→25→60→150→365+ | 1→4→10→20→50→120→300+ | 1→3→7→20→56→157→365 | ⚠️ Slower progression |
| Average | 1→3→7→15→30→60→120+ | 1→2→5→10→20→40→80+ | 1→3→7→18→45→112→280→365 | ✅ Similar |
| Hard | 1→1→3→7→15→30→60→120+ | 1→1→2→5→10→20→40→80+ | 1→3→7→13→23→41→74→133+ | ⚠️ Faster initial, slower later |

**Gap Analysis:**
- ⚠️ **Easy words:** Our progression is slower (more conservative). Industry goes faster.
- ✅ **Hard words:** Our progression is similar to industry.
- ⚠️ **Max interval:** Industry allows unlimited (1000+ days), we cap at 365.

**Recommendation:**
- Consider allowing intervals > 365 days for truly mastered words
- Consider faster progression for easy words (EF > 2.7)

---

## 3. Difficulty Detection & Tracking

### 3.1 Industry Standards

#### Anki
- **Ease factor** per card (1.3 - 2.5)
- **Leech threshold:** 8 lapses → flagged
- **Difficulty rating:** User can mark "again", "hard", "good", "easy"
- **Response time:** Not tracked by default (addon available)

#### SuperMemo
- **Ease factor** per item
- **Difficulty rating:** User provides 0-5 scale
- **Response time:** Tracked and used in calculations
- **Leech detection:** Automatic after repeated failures

#### Memrise
- **Difficulty score:** Based on error rate
- **Response time:** Tracked
- **User feedback:** "I know this" / "I don't know this"
- **Adaptive difficulty:** Adjusts based on performance

### 3.2 Our Design

**Signals tracked:**
- Response time (0.2 weight)
- Hesitation patterns (0.1 weight)
- Global error rate (0.2 weight)
- User error rate (0.3 weight)
- Ease factor (0.2 weight)

**Comparison:**

| Signal | Anki | SuperMemo | Memrise | Our Design |
|--------|------|-----------|---------|------------|
| Ease Factor | ✅ | ✅ | ❌ | ✅ |
| Response Time | ⚠️ (addon) | ✅ | ✅ | ✅ |
| Error Rate | ✅ | ✅ | ✅ | ✅ |
| Hesitation | ❌ | ❌ | ❌ | ✅ (unique!) |
| Global Stats | ❌ | ❌ | ✅ | ✅ |

**Assessment:**
- ✅ **Better than Anki:** We track response time natively
- ✅ **Better than SuperMemo:** We track hesitation patterns
- ✅ **Better than Memrise:** We have ease factor
- ✅ **Unique feature:** Hesitation tracking (changed answers)

**Recommendation:**
- ✅ Keep our multi-signal approach (it's more comprehensive)

---

## 4. Leech Detection & Handling

### 4.1 Industry Standards

#### Anki
- **Detection:** 8 lapses (failures) → flagged as leech
- **Handling:**
  - Suspend card (stop showing)
  - User can unsuspend manually
  - No automatic help provided
- **User control:** Can mark as leech manually

#### SuperMemo
- **Detection:** Automatic based on ease factor drop
- **Handling:**
  - Reset to beginning
  - Show more frequently
  - Provide additional context
- **User control:** Can mark as "buried" (skip temporarily)

#### Memrise
- **Detection:** Based on repeated failures
- **Handling:**
  - Show more frequently
  - Provide hints
  - Suggest related words
- **User control:** Can "skip" or "mark as known"

### 4.2 Our Design

**Detection:**
- 3 consecutive failures OR
- Ease factor < 1.5 OR
- Total time > 15 min without success

**Handling:**
- Mnemonics suggested
- Visual aids shown
- Related words linked
- Can "skip for now"
- Special learning interface

**Comparison:**

| Feature | Anki | SuperMemo | Memrise | Our Design |
|---------|------|-----------|---------|------------|
| Detection Threshold | 8 lapses | Automatic | Automatic | 3 lapses ✅ |
| Automatic Help | ❌ | ⚠️ (basic) | ✅ | ✅ |
| Mnemonics | ❌ | ❌ | ⚠️ (limited) | ✅ |
| Visual Aids | ❌ | ❌ | ⚠️ | ✅ |
| Skip Option | ⚠️ (suspend) | ⚠️ (bury) | ✅ | ✅ |
| Special UI | ❌ | ❌ | ❌ | ✅ (unique!) |

**Assessment:**
- ✅ **More proactive:** We detect leeches earlier (3 vs 8)
- ✅ **More helpful:** We provide multiple support strategies
- ✅ **Better UX:** Special interface for leeches

**Recommendation:**
- ✅ Keep our leech handling (it's more user-friendly)

---

## 5. Mastery Detection

### 5.1 Industry Standards

#### Anki
- **Graduation:** Card moves to "graduated" after X reviews
- **Ease factor:** High ease factor (2.5) = easier
- **No permanent mastery:** Cards always come back
- **Max interval:** Unlimited (can be years)

#### SuperMemo
- **Final interval:** When interval > 1 year, considered "final"
- **Mastery levels:** Not explicitly tracked
- **Re-testing:** Still happens, but very rarely

#### Duolingo
- **Skill levels:** 1-5 levels per skill
- **"Legendary" status:** Highest level, but still tested
- **No permanent mastery:** Skills decay over time

#### Memrise
- **"Learned" status:** After passing all tests
- **Re-testing:** Periodic re-tests to maintain status
- **No permanent mastery:** Words can be "unlearned"

### 5.2 Our Design

**Mastery levels:**
1. **Learning:** < 3 correct in a row
2. **Familiar:** 3-4 correct in a row
3. **Known:** 5+ correct, EF > 2.5
4. **Mastered:** 5+ correct, EF > 2.8, interval > 180 days
5. **Permanent:** Mastered for 2+ years

**Testing frequency:**
- Learning: Every 1-7 days
- Familiar: Every 2-4 weeks
- Known: Every 1-3 months
- Mastered: Once per year
- Permanent: Almost never

**Comparison:**

| Feature | Anki | SuperMemo | Duolingo | Memrise | Our Design |
|---------|------|-----------|----------|---------|------------|
| Explicit Mastery Levels | ❌ | ❌ | ✅ (5 levels) | ⚠️ (2 levels) | ✅ (5 levels) |
| Permanent Mastery | ❌ | ⚠️ (rare testing) | ❌ | ❌ | ✅ |
| Testing Frequency Reduction | ⚠️ (graduation) | ✅ | ❌ | ⚠️ | ✅ |
| User Feedback | ❌ | ❌ | ✅ | ✅ | ✅ |

**Assessment:**
- ✅ **More explicit:** We have clear mastery levels
- ✅ **Better UX:** Users see progress clearly
- ✅ **Permanent mastery:** Unique feature (others keep testing)

**Recommendation:**
- ✅ Keep our mastery system (it's more user-friendly)

---

## 6. Maximum Interval

### 6.1 Industry Standards

| Platform | Max Interval | Rationale |
|----------|--------------|-----------|
| **Anki** | Unlimited (1000+ days) | Let algorithm decide |
| **SuperMemo** | Unlimited | Research shows long intervals work |
| **Duolingo** | 30 days (stops) | Simplified, no mastery concept |
| **Memrise** | ~90 days | Then re-test |
| **Quizlet** | ~60 days | Then re-test |

### 6.2 Our Design

**Max interval:** 365 days (1 year)

**Rationale:**
- Conservative approach
- Ensures words don't disappear forever
- Still allows for long-term retention

**Gap Analysis:**

| Aspect | Industry | Our Design | Recommendation |
|--------|----------|------------|---------------|
| Max Interval | Unlimited | 365 days | ⚠️ Consider 730 days (2 years) |
| Mastered Words | Still tested | Once/year | ✅ Good |
| Permanent Words | N/A | Almost never | ✅ Unique feature |

**Recommendation:**
- ⚠️ **Consider increasing max interval to 730 days** (2 years) for mastered words
- ✅ **Keep permanent mastery** (unique feature, good UX)

---

## 7. Response Time Tracking

### 7.1 Industry Standards

| Platform | Tracks Response Time? | Uses in Algorithm? |
|----------|----------------------|-------------------|
| **Anki** | ⚠️ (addon only) | ❌ |
| **SuperMemo** | ✅ | ✅ |
| **Memrise** | ✅ | ✅ |
| **Duolingo** | ✅ | ⚠️ (for analytics) |
| **Quizlet** | ✅ | ❌ |

### 7.2 Our Design

**Tracks:** ✅ Yes  
**Uses in algorithm:** ✅ Yes (difficulty score, performance rating)

**Assessment:**
- ✅ **Better than Anki:** Native tracking
- ✅ **Aligned with SuperMemo/Memrise:** Industry standard
- ✅ **Used in calculations:** More sophisticated than most

**Recommendation:**
- ✅ Keep response time tracking (it's a best practice)

---

## 8. Active Recall

### 8.1 Industry Standards

All major platforms use active recall:
- **Anki:** Flashcards (recall before reveal)
- **SuperMemo:** Question-answer format
- **Duolingo:** Multiple choice + typing
- **Memrise:** Multiple choice + typing
- **Quizlet:** Flashcards + games

### 8.2 Our Design

**Format:** MCQ (6-option multiple choice)

**Comparison:**

| Format | Industry | Our Design | Assessment |
|--------|----------|------------|------------|
| Active Recall | ✅ All platforms | ✅ MCQ | ✅ Aligned |
| Multiple Choice | ✅ Common | ✅ 6 options | ✅ Good |
| Typing | ✅ Common | ❌ Not yet | ⚠️ Consider adding |
| Context | ✅ Important | ✅ Yes | ✅ Aligned |

**Recommendation:**
- ✅ Keep MCQ format (it's industry standard)
- ⚠️ **Consider adding typing exercises** for advanced users (like Duolingo/Memrise)

---

## 9. Personalization

### 9.1 Industry Standards

| Platform | Personalization Level |
|----------|---------------------|
| **Anki** | Per-card ease factor, deck settings |
| **SuperMemo** | Per-item difficulty, user preferences |
| **Duolingo** | Adaptive path, personalized practice |
| **Memrise** | Per-word difficulty, learning speed |
| **Quizlet** | Basic (no personalization) |

### 9.2 Our Design

**Personalization:**
- Per-word ease factor per user
- Learning profile (best time, session length)
- Difficulty patterns (struggles with idioms, etc.)
- Optimal review time detection

**Comparison:**

| Feature | Industry | Our Design | Assessment |
|---------|----------|------------|------------|
| Per-item difficulty | ✅ | ✅ | ✅ Aligned |
| Learning profile | ⚠️ (limited) | ✅ | ✅ Better |
| Time optimization | ❌ | ✅ | ✅ Unique |
| Pattern detection | ❌ | ✅ | ✅ Unique |

**Assessment:**
- ✅ **More personalized:** We track more signals
- ✅ **Unique features:** Time optimization, pattern detection

**Recommendation:**
- ✅ Keep our personalization (it's more advanced)

---

## 10. Key Gaps & Recommendations

### 10.1 Critical Gaps

| Gap | Impact | Priority | Recommendation |
|-----|--------|----------|----------------|
| **Algorithm:** SM-2+ vs FSRS | Medium | Low (post-MVP) | Consider FSRS for v2 |
| **Max Interval:** 365 vs unlimited | Low | Medium | Increase to 730 days |
| **Easy word progression:** Slower | Low | Low | Consider faster for EF > 2.7 |
| **Typing exercises:** Missing | Medium | Medium | Add for advanced users |

### 10.2 Strengths (Better than Industry)

| Feature | Why It's Better |
|---------|----------------|
| **Hesitation tracking** | Unique signal, not in other platforms |
| **Leech handling** | More proactive (3 vs 8 failures) + better support |
| **Mastery levels** | More explicit than Anki/SuperMemo |
| **Permanent mastery** | Unique feature (others keep testing) |
| **Learning profile** | More comprehensive than industry |
| **Time optimization** | Unique feature (best time of day) |

### 10.3 Industry Best Practices We're Missing

1. **FSRS Algorithm** (Low priority - post-MVP)
   - More accurate than SM-2+
   - Better handles edge cases
   - Used by modern Anki

2. **Interleaving** (Medium priority)
   - Mix different word types in same session
   - Industry research shows it helps
   - We could add this easily

3. **Elaboration prompts** (Low priority)
   - "Explain in your own words"
   - Industry research shows it helps
   - Could add as optional feature

---

## 11. Final Recommendations

### 11.1 Keep (Already Good)

✅ **SM-2+ algorithm** - Good enough for MVP, simpler than FSRS  
✅ **Multi-signal difficulty tracking** - More comprehensive than industry  
✅ **Proactive leech detection** - Better UX than Anki  
✅ **5-level mastery system** - More explicit than industry  
✅ **Permanent mastery** - Unique feature, good UX  
✅ **Response time tracking** - Industry best practice  
✅ **Learning profile** - More advanced than industry  

### 11.2 Improve (Post-MVP)

⚠️ **Consider FSRS algorithm** - More accurate, but complex  
⚠️ **Increase max interval to 730 days** - Align with industry  
⚠️ **Add typing exercises** - Like Duolingo/Memrise  
⚠️ **Add interleaving** - Mix word types in sessions  

### 11.3 Unique Strengths to Highlight

🎯 **Hesitation tracking** - Not in other platforms  
🎯 **Comprehensive leech support** - Better than industry  
🎯 **Permanent mastery** - Others keep testing forever  
🎯 **Time optimization** - Best time of day detection  

---

## 12. Conclusion

**Overall Assessment:** Our ASRS design is **well-aligned with industry best practices** and in some areas **exceeds industry standards**.

**Key Strengths:**
- More comprehensive difficulty tracking
- Better leech handling
- More explicit mastery system
- Unique features (hesitation, time optimization)

**Minor Gaps:**
- Algorithm could be FSRS (but SM-2+ is fine for MVP)
- Max interval could be longer (but 365 days is reasonable)
- Could add typing exercises (but MCQ is standard)

**Recommendation:** Proceed with current design. Consider FSRS and extended intervals for v2.

