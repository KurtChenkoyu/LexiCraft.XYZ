# Core Gamification System - Task Checklist
## (Gamification Layer - XP, Achievements, Levels)

**Status:** 📋 Ready to Start  
**Priority:** 🔴 CRITICAL  
**Estimated Time:** 2-3 weeks

---

## Quick Reference

### What We're Building
A functioning core system that automatically:
- ✅ Awards XP when users verify words (10 XP)
- ✅ Awards XP when users complete reviews (15 XP)
- ✅ Awards XP for daily streaks (5 XP)
- ✅ Checks and unlocks achievements automatically
- ✅ Provides immediate feedback via API responses

### Current Problem
- XP system exists but isn't triggered automatically
- Achievements exist but aren't checked automatically
- Users don't see immediate rewards for verification

---

## Phase 1: Core XP Triggers (Week 1)

### Task 1.1: Word Verification XP Trigger
**File:** `backend/src/api/verification.py`  
**Time:** 2 days

- [ ] Locate word verification endpoint
- [ ] Import LevelService
- [ ] Add `level_service.add_xp(user_id, 10, 'word_verified', word_id)` after word verified
- [ ] Test: Verify word → Check XP increased by 10
- [ ] Test: Verify XP history recorded
- [ ] Test: Check level-up detection works

**Code Location:**
```python
# After word is verified
from ..services.levels import LevelService
level_service = LevelService(db)
xp_result = level_service.add_xp(user_id, 10, 'word_verified', word_id)
```

---

### Task 1.2: Review Completion XP Trigger
**File:** `backend/src/api/verification.py`  
**Time:** 2 days

- [ ] Locate review completion endpoint
- [ ] Import LevelService
- [ ] Add `level_service.add_xp(user_id, 15, 'review', review_id)` after review completed
- [ ] Test: Complete review → Check XP increased by 15
- [ ] Test: Complete multiple reviews → Check XP accumulates
- [ ] Test: Check level-up works

**Code Location:**
```python
# After review is recorded
level_service = LevelService(db)
xp_result = level_service.add_xp(user_id, 15, 'review', review_id)
```

---

### Task 1.3: Daily Streak XP Trigger
**File:** `backend/src/services/learning_velocity.py`  
**Time:** 1 day

- [ ] Locate streak update logic
- [ ] Import LevelService
- [ ] Add `level_service.add_xp(user_id, 5, 'streak')` when streak maintained
- [ ] Test: Maintain streak → Check XP increased by 5
- [ ] Test: Check streak XP only awarded once per day
- [ ] Consider: Scheduled job for daily streak check

**Code Location:**
```python
# In update_streak() or similar function
if streak_maintained:
    level_service = LevelService(self.db)
    xp_result = level_service.add_xp(user_id, 5, 'streak')
```

---

## Phase 2: Automatic Achievement Checking (Week 1-2)

### Task 2.1: Achievement Check After Word Learned
**File:** `backend/src/api/verification.py`  
**Time:** 1 day

- [ ] Import AchievementService
- [ ] Add `achievement_service.check_achievements(user_id)` after word learned
- [ ] Test: Learn first word → Check "First Word" achievement unlocks
- [ ] Test: Learn 100th word → Check "100 Words" achievement unlocks
- [ ] Test: Check XP awarded for achievement unlock

**Code Location:**
```python
# After word learned and XP awarded
from ..services.achievements import AchievementService
achievement_service = AchievementService(db)
newly_unlocked = achievement_service.check_achievements(user_id)
```

---

### Task 2.2: Achievement Check After Review
**File:** `backend/src/api/verification.py`  
**Time:** 1 day

- [ ] Add `achievement_service.check_achievements(user_id)` after review completed
- [ ] Test: Complete 100th review → Check "Reviewer" achievement unlocks
- [ ] Test: Complete 500th review → Check "Dedicated Reviewer" achievement unlocks
- [ ] Test: Check notifications created

**Code Location:**
```python
# After review completed and XP awarded
newly_unlocked = achievement_service.check_achievements(user_id)
```

---

### Task 2.3: Achievement Check After Streak
**File:** `backend/src/services/learning_velocity.py`  
**Time:** 1 day

- [ ] Add `achievement_service.check_achievements(user_id)` after streak maintained
- [ ] Test: Reach 3-day streak → Check "Getting Started" achievement unlocks
- [ ] Test: Reach 7-day streak → Check "Week Warrior" achievement unlocks
- [ ] Test: Reach 30-day streak → Check "Monthly Master" achievement unlocks
- [ ] Test: Check notifications created

**Code Location:**
```python
# After streak XP awarded
achievement_service = AchievementService(self.db)
newly_unlocked = achievement_service.check_achievements(user_id)
```

---

### Task 2.4: Optimize Achievement Checking
**File:** `backend/src/services/achievements.py`  
**Time:** 1 day

- [ ] Cache achievement definitions (don't reload every time)
- [ ] Only check relevant categories (e.g., only vocabulary achievements after word learned)
- [ ] Test: Performance < 100ms for achievement check
- [ ] Test: Multiple achievements unlock correctly

---

## Phase 3: Immediate Feedback (Week 2)

### Task 3.1: Enhance API Responses
**File:** `backend/src/api/verification.py`  
**Time:** 2 days

- [ ] Add gamification data to word learning response
- [ ] Add gamification data to review response
- [ ] Include: XP earned, total XP, level, level-up status, new achievements
- [ ] Test: Response includes all gamification data
- [ ] Test: Frontend can parse response

**Response Format:**
```json
{
  "word_verified": true,
  "gamification": {
    "xp_earned": 10,
    "total_xp": 150,
    "current_level": 2,
    "level_up": false,
    "new_achievements": []
  }
}
```

---

### Task 3.2: Level-Up Notifications
**File:** `backend/src/services/levels.py`  
**Time:** 1 day

- [ ] Add notification creation in `add_xp()` when level_up is True
- [ ] Test: Level up → Check notification created
- [ ] Test: Notification content is correct
- [ ] Test: Notification appears in frontend

**Code Location:**
```python
# In LevelService.add_xp() after level calculation
if level_up:
    from .notifications import NotificationService
    notification_service = NotificationService(self.db)
    notification_service.create_notification(
        user_id, 'level_up', 'Level Up!', '恭喜！你升級了！', 
        data={'new_level': new_level}
    )
```

---

### Task 3.3: Achievement Unlock Notifications
**File:** `backend/src/services/achievements.py`  
**Time:** 1 day

- [ ] Verify notifications are created in `_unlock_achievement()`
- [ ] Test: Achievement unlocks → Check notification created
- [ ] Test: Notification content includes achievement info
- [ ] Test: Multiple achievements → Multiple notifications

---

## Phase 4: Progress Visibility (Week 2-3)

### Task 4.1: Achievement Progress Calculation
**File:** `backend/src/services/achievements.py`  
**Time:** 1 day

- [ ] Add `progress_percentage` to `get_user_achievements()`
- [ ] Add `remaining` count (words/actions needed)
- [ ] Test: Progress percentage calculated correctly
- [ ] Test: Frontend receives progress data

**Code:**
```python
# In get_user_achievements()
progress_percentage = min(100, int((current_value / requirement_value) * 100)) if requirement_value > 0 else 0
remaining = max(0, requirement_value - current_value)
```

---

### Task 4.2: XP Summary Endpoint
**File:** `backend/src/api/learner_profile.py`  
**Time:** 1 day

- [ ] Add `GET /api/v1/profile/learner/xp-summary` endpoint
- [ ] Use `LevelService.get_xp_summary()`
- [ ] Test: Endpoint returns XP summary by source
- [ ] Test: Endpoint supports days parameter

**Endpoint:**
```python
@router.get("/xp-summary")
async def get_xp_summary(
    user_id: UUID = Depends(get_current_user_id),
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db_session)
):
    level_service = LevelService(db)
    return level_service.get_xp_summary(user_id, days)
```

---

### Task 4.3: Frontend Integration
**File:** Frontend files  
**Time:** 2 days

- [ ] Update API client to parse gamification data
- [ ] Show XP popup when XP is earned
- [ ] Show level-up celebration modal
- [ ] Show achievement unlock animation
- [ ] Display progress percentages in achievement cards
- [ ] Test: All feedback appears correctly

---

## Phase 5: Testing & Optimization (Week 3)

### Task 5.1: End-to-End Testing
**Time:** 2 days

- [ ] Test: Verify word → Earn XP → Check achievement → Unlock → Notification
- [ ] Test: Complete review → Earn XP → Check achievement → Unlock
- [ ] Test: Maintain streak → Earn XP → Check achievement → Unlock
- [ ] Test: Level up + achievement unlock together
- [ ] Test: Multiple achievements unlock simultaneously
- [ ] Test: Rapid actions (multiple words quickly)

---

### Task 5.2: Performance Optimization
**Time:** 1 day

- [ ] Profile achievement checking (target: < 100ms)
- [ ] Profile XP awarding (target: < 50ms)
- [ ] Optimize database queries if needed
- [ ] Add indexes if needed
- [ ] Test under load

---

### Task 5.3: Documentation
**Time:** 1 day

- [ ] Document new API responses
- [ ] Document XP triggers
- [ ] Update API documentation
- [ ] Create developer guide for adding XP triggers

---

## Testing Checklist

### Unit Tests
- [ ] Word learning XP (10 XP)
- [ ] Review XP (15 XP)
- [ ] Streak XP (5 XP)
- [ ] Level-up detection
- [ ] Achievement unlock
- [ ] Notification creation

### Integration Tests
- [ ] Complete word verification flow
- [ ] Complete review flow
- [ ] Complete streak flow
- [ ] Multiple achievements unlock
- [ ] Level-up + achievement together

### Performance Tests
- [ ] Achievement check < 100ms
- [ ] XP award < 50ms
- [ ] API response time acceptable
- [ ] Database queries optimized

---

## Success Criteria

- [ ] Users earn 10 XP automatically when learning a word
- [ ] Users earn 15 XP automatically when completing a review
- [ ] Users earn 5 XP automatically when maintaining a streak
- [ ] Achievements unlock automatically when requirements are met
- [ ] Level-ups are detected and notifications created
- [ ] API responses include gamification data
- [ ] Progress percentages are calculated correctly
- [ ] All tests pass
- [ ] Performance targets met

---

## Files to Modify

1. `backend/src/api/verification.py` - Add XP triggers, achievement checks, enhance responses
2. `backend/src/services/learning_velocity.py` - Add streak XP trigger
3. `backend/src/services/levels.py` - Add level-up notifications
4. `backend/src/services/achievements.py` - Add progress calculation, optimize
5. `backend/src/api/learner_profile.py` - Add XP summary endpoint
6. Frontend files - Show feedback, progress, celebrations

---

## Notes

- All required services already exist
- No database migrations needed
- No new dependencies needed
- Can start immediately

**Full Details:** See `CORE_SYSTEM_IMPLEMENTATION_PLAN.md`

