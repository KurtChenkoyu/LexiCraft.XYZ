# XP & Achievement System - Quick Reference

## Current System Status

### ✅ What's Working
- Level progression formula: `100 + (N-1) × 50` XP per level
- Achievement categories: Streak, Vocabulary, Mastery, Special
- Tier system: Bronze, Silver, Gold, Platinum
- XP history tracking
- Goal completion XP (50 XP)

### ✅ What's Working
- Verification step XP (10 XP per correct answer)
- Tier-based mastery XP (when words are verified)
- Achievement & goal XP

### ⏳ Partial Implementation
- Word learned XP (15 XP) - May overlap with verification step XP
- Tier values need updating (Tier 4 currently 1000 XP, should be 300 XP)

### ❌ Critical Gaps
- **NO XP for words in progress** (should be 5 XP)
- **NO automatic XP for streaks** (should be 5 XP/day)
- **NO automatic achievement checking** after actions
- **NO immediate feedback** when XP is earned

---

## XP Rewards (Dual System: Effort + Mastery)

### Effort-Based XP (Participation Rewards)

| Source | XP Amount | Status |
|--------|-----------|--------|
| Correct answer in verification | 10 XP | ✅ Implemented |
| Word enters "in progress" | 5 XP | ⏳ To Implement |
| Streak Day | 5 XP | ⏳ To Implement |
| Review session started | 5 XP | ⏳ Future |

### Mastery-Based XP (Tier-Based Rewards)

| Tier | Type | Base XP | Status |
|------|------|--------|--------|
| 1 | Basic Block | 100 XP | ✅ Implemented |
| 2 | Multi-Block | 120 XP | 🔄 Needs Update |
| 3 | Phrase Block | 200 XP | 🔄 Needs Update |
| 4 | Idiom Block | 300 XP | 🔄 Needs Update (currently 1000) |
| 5 | Pattern Block | 150 XP | 🔄 Needs Update |
| 6 | Register Block | 200 XP | 🔄 Needs Update |
| 7 | Context Block | 250 XP | 🔄 Needs Update |

### Activity-Based XP

| Source | XP Amount | Status |
|--------|-----------|--------|
| Daily Review Completed | 20 XP | ⏳ To Implement |
| Achievement Unlocked | 25-500 XP | ✅ Working |
| Goal Completed | 50 XP | ✅ Working |

**See:** `XP_SYSTEM_DESIGN.md` for complete specification

---

## Achievement Categories

### Streak Achievements
- 3 days: 25 XP, Bronze
- 7 days: 50 XP + 10 points, Silver
- 30 days: 150 XP + 50 points, Gold
- 100 days: 500 XP + 200 points, Platinum

### Vocabulary Milestones
- 100 words: 50 XP + 20 points, Bronze
- 500 words: 150 XP + 75 points, Silver
- 1,000 words: 300 XP + 150 points, Gold
- 2,500 words: 500 XP + 300 points, Platinum

### Mastery Achievements
- 1 mastered: 25 XP, Bronze
- 10 mastered: 75 XP + 30 points, Silver
- 50 mastered: 200 XP + 100 points, Gold
- 100 mastered: 400 XP + 200 points, Platinum

---

## Industry Comparison

### Duolingo
- ✅ Immediate XP after lessons
- ✅ Auto-checks achievements
- ✅ Streak multipliers (2x on day 7)
- ✅ Daily XP goals

### Our System
- ❌ No immediate XP
- ❌ Manual achievement checking
- ❌ No streak multipliers
- ❌ No daily goals

---

## Priority Actions

### 🔴 CRITICAL (Do First)
1. **Add automatic XP triggers** in verification/review systems
2. **Add automatic achievement checking** after learning actions
3. **Add immediate feedback** (XP popups, level-up notifications)

### 🟠 HIGH (Do Soon)
1. **Add effort-based rewards** (attempts, participation)
2. **Add progress visibility** (progress bars, "X away" messages)
3. **Add streak multipliers** (1.5x at day 7, 2x at day 30)

### 🟡 MEDIUM (Do Later)
1. **Add milestone celebrations** (level-up animations)
2. **Add daily XP goals**
3. **Add achievement chains** visualization

---

## Implementation Checklist

### Phase 1: Automation
- [ ] Hook XP into word verification (10 XP per word)
- [ ] Hook XP into review system (15 XP per review)
- [ ] Hook XP into streak system (5 XP per day)
- [ ] Auto-check achievements after word verified
- [ ] Auto-check achievements after review completed
- [ ] Auto-check achievements after streak maintained

### Phase 2: Feedback
- [ ] Add XP popup in frontend
- [ ] Add level-up detection
- [ ] Add level-up celebration modal
- [ ] Add achievement unlock animation
- [ ] Return progress data in API responses

### Phase 3: Enhancements
- [ ] Add streak multipliers
- [ ] Add effort-based achievements
- [ ] Add progress percentages
- [ ] Add daily XP goals
- [ ] Add milestone bonuses

---

## Code Locations

### XP System
- **Service**: `backend/src/services/levels.py`
- **API**: `backend/src/api/learner_profile.py`
- **Migration**: `backend/migrations/013_gamification_schema.sql`

### Achievement System
- **Service**: `backend/src/services/achievements.py`
- **API**: `backend/src/api/learner_profile.py`
- **Seed**: `backend/scripts/seed_achievements.py`

### Where to Add Hooks
- **Word Verification**: `backend/src/api/verification.py` (when word verified)
- **Reviews**: `backend/src/api/verification.py` (when review completed)
- **Streaks**: `backend/src/services/learning_velocity.py` (daily streak check)

---

## Expected Impact

### Engagement
- **DAU**: +30-50% increase
- **Session Length**: +20-30% increase
- **Retention**: +20-30% improvement

### Motivation
- **XP Earned**: 3-5x increase (from automation)
- **Achievement Unlocks**: 2-3x increase (from auto-checking)
- **User Satisfaction**: +15-25% improvement

---

**Last Updated**: December 20th, 2025  
**Full Analysis**: See `XP_ACHIEVEMENT_SYSTEM_ANALYSIS.md`

