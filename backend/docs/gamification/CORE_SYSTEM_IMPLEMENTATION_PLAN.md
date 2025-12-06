# Core Gamification System - Implementation Plan
## (Gamification Layer - XP, Achievements, Levels)

**Status:** 📋 Planning Phase  
**Priority:** 🔴 CRITICAL - Foundation for all gamification features  
**Estimated Time:** 2-3 weeks  
**Dependencies:** None (can start immediately)

---

## Executive Summary

Before implementing advanced features (Battle Pass, Daily Quests, etc.), we need a **functioning core system** that automatically awards XP and checks achievements when users perform learning activities. Currently, the system is well-designed but **not automatically triggered**.

**Current State:**
- ✅ XP system designed and implemented
- ✅ Achievement system designed and implemented
- ✅ Level progression working
- ❌ **NO automatic XP triggers** for word learning
- ❌ **NO automatic XP triggers** for reviews
- ❌ **NO automatic achievement checking** after actions
- ❌ **NO immediate feedback** when XP is earned

**Target State:**
- ✅ Automatic XP when words are learned
- ✅ Automatic XP when reviews are completed
- ✅ Automatic XP for daily streaks
- ✅ Automatic achievement checking after significant actions
- ✅ Immediate feedback (API responses, notifications)

---

## Core System Components

### 1. Automatic XP Triggers

#### 1.1 Word Learning XP Trigger

**Location:** `backend/src/api/verification.py` (when word is verified/learned)

**Current Flow:**
```
User verifies word → Word marked as learned → End
```

**Target Flow:**
```
User verifies word → Word marked as learned → Award 10 XP → Check achievements → Return response with XP info
```

**Implementation:**
```python
# In verification endpoint after word is verified
from ..services.levels import LevelService
from ..services.achievements import AchievementService

level_service = LevelService(db)
achievement_service = AchievementService(db)

# Award XP for word verified
xp_result = level_service.add_xp(user_id, 10, 'word_verified', word_id)

# Check for newly unlocked achievements
newly_unlocked = achievement_service.check_achievements(user_id)

# Return response with XP and achievement info
return {
    'word_verified': True,
    'xp_earned': 10,
    'total_xp': xp_result['new_xp'],
    'level_up': xp_result['level_up'],
    'new_level': xp_result['new_level'] if xp_result['level_up'] else None,
    'new_achievements': newly_unlocked
}
```

**Files to Modify:**
- `backend/src/api/verification.py` - Add XP trigger after word verification
- Potentially: `backend/src/services/vocabulary_size.py` - If word verification happens there

**Testing:**
- Verify word → Check XP increased by 10
- Verify word → Check achievement progress updated
- Verify word → Check level-up detection works

---

#### 1.2 Review Completion XP Trigger

**Location:** `backend/src/api/verification.py` (when review is completed)

**Current Flow:**
```
User completes review → Review recorded → End
```

**Target Flow:**
```
User completes review → Review recorded → Award 15 XP → Check achievements → Return response with XP info
```

**Implementation:**
```python
# In review completion endpoint
level_service = LevelService(db)
achievement_service = AchievementService(db)

# Award XP for review
xp_result = level_service.add_xp(user_id, 15, 'review', review_id)

# Check achievements (especially review-based ones)
newly_unlocked = achievement_service.check_achievements(user_id)

# Return response
return {
    'review_completed': True,
    'xp_earned': 15,
    'total_xp': xp_result['new_xp'],
    'level_up': xp_result['level_up'],
    'new_achievements': newly_unlocked
}
```

**Files to Modify:**
- `backend/src/api/verification.py` - Add XP trigger after review completion

**Testing:**
- Complete review → Check XP increased by 15
- Complete multiple reviews → Check review achievement progress
- Complete review → Check level-up works

---

#### 1.3 Daily Streak XP Trigger

**Location:** `backend/src/services/learning_velocity.py` (daily streak calculation)

**Current Flow:**
```
Daily streak calculated → Streak updated → End
```

**Target Flow:**
```
Daily streak calculated → Streak updated → Award 5 XP (if streak maintained) → Check streak achievements → Update leaderboard
```

**Implementation:**
```python
# In learning_velocity.py when streak is maintained
from .levels import LevelService
from .achievements import AchievementService

def update_streak(user_id: UUID):
    # ... existing streak calculation ...
    
    if streak_maintained:
        level_service = LevelService(self.db)
        achievement_service = AchievementService(self.db)
        
        # Award streak XP
        xp_result = level_service.add_xp(user_id, 5, 'streak')
        
        # Check streak achievements (3-day, 7-day, 30-day, 100-day)
        newly_unlocked = achievement_service.check_achievements(user_id)
        
        # Create notification if achievement unlocked
        if newly_unlocked:
            notification_service = NotificationService(self.db)
            for achievement in newly_unlocked:
                notification_service.create_notification(
                    user_id,
                    'achievement',
                    f"Achievement Unlocked: {achievement['name_en']}",
                    f"You unlocked: {achievement['name_zh'] or achievement['name_en']}",
                    data={'achievement_id': achievement['id']}
                )
```

**Files to Modify:**
- `backend/src/services/learning_velocity.py` - Add XP trigger in streak update
- Consider: Create a scheduled job that runs daily to check streaks

**Testing:**
- Maintain streak → Check XP increased by 5
- Reach 7-day streak → Check achievement unlocked
- Reach milestone → Check notification created

---

### 2. Automatic Achievement Checking

#### 2.1 Achievement Check Triggers

**When to Check Achievements:**
1. ✅ After word is learned (vocabulary achievements)
2. ✅ After review is completed (review achievements)
3. ✅ After streak is maintained (streak achievements)
4. ✅ After mastery level changes (mastery achievements)
5. ✅ After goal is completed (goal achievements - already implemented)

**Implementation Pattern:**
```python
# After any significant learning action
achievement_service = AchievementService(db)
newly_unlocked = achievement_service.check_achievements(user_id)

if newly_unlocked:
    # Award XP for achievements (already done in _unlock_achievement)
    # Create notifications
    # Return in API response
```

**Files to Modify:**
- All endpoints where learning actions occur:
  - `backend/src/api/verification.py` - Word learning, reviews
  - `backend/src/services/learning_velocity.py` - Streak updates
  - `backend/src/services/vocabulary_size.py` - Vocabulary milestones

**Optimization:**
- Cache achievement definitions (don't reload every time)
- Only check relevant achievement categories (e.g., only vocabulary achievements after word learned)
- Batch achievement checks if multiple actions occur

---

### 3. Immediate Feedback System

#### 3.1 API Response Enhancement

**Current API Responses:**
```json
{
  "word_verified": true,
  "word_id": "uuid"
}
```

**Enhanced API Responses:**
```json
{
  "word_verified": true,
  "word_id": "uuid",
  "gamification": {
    "xp_earned": 10,
    "total_xp": 150,
    "current_level": 2,
    "xp_to_next_level": 100,
    "xp_in_current_level": 50,
    "progress_percentage": 50,
    "level_up": false,
    "new_achievements": [
      {
        "id": "uuid",
        "name_en": "First Word Learned",
        "name_zh": "學會第一個單字",
        "xp_reward": 25
      }
    ]
  }
}
```

**Files to Modify:**
- `backend/src/api/verification.py` - Enhance all responses
- `backend/src/api/learner_profile.py` - Ensure consistent format

---

#### 3.2 Level-Up Detection & Notifications

**Implementation:**
```python
# In LevelService.add_xp()
level_up = new_level > old_level

if level_up:
    # Create level-up notification
    notification_service = NotificationService(db)
    notification_service.create_notification(
        user_id,
        'level_up',
        f'Level Up!',
        f'恭喜！你升級到 Level {new_level}！',
        data={
            'old_level': old_level,
            'new_level': new_level,
            'total_xp': new_total_xp
        }
    )

return {
    'level_up': level_up,
    'old_level': old_level,
    'new_level': new_level,
    # ... other info
}
```

**Files to Modify:**
- `backend/src/services/levels.py` - Add notification creation on level-up
- `backend/src/services/notifications.py` - Ensure level_up type exists

---

#### 3.3 Achievement Unlock Notifications

**Implementation:**
```python
# In AchievementService._unlock_achievement()
# After unlocking achievement
notification_service = NotificationService(self.db)
notification_service.create_notification(
    user_id,
    'achievement',
    f'Achievement Unlocked: {achievement_name_en}',
    f'成就解鎖：{achievement_name_zh}',
    data={
        'achievement_id': achievement_id,
        'xp_reward': xp_reward,
        'tier': tier
    }
)
```

**Files to Modify:**
- `backend/src/services/achievements.py` - Add notification creation
- Already partially implemented, ensure it's called

---

### 4. Progress Tracking & Visibility

#### 4.1 Achievement Progress Calculation

**Current State:**
- Progress is stored but not calculated as percentage
- Frontend needs progress percentages

**Implementation:**
```python
# In AchievementService.get_user_achievements()
# Calculate progress percentage for each achievement
progress_percentage = min(100, int((current_value / requirement_value) * 100)) if requirement_value > 0 else 0

achievements.append({
    # ... existing fields ...
    'progress': current_value,
    'progress_percentage': progress_percentage,
    'remaining': max(0, requirement_value - current_value)
})
```

**Files to Modify:**
- `backend/src/services/achievements.py` - Add progress calculation
- Already partially implemented in `get_achievement_progress()`, extend to `get_user_achievements()`

---

#### 4.2 XP History & Summary

**Current State:**
- XP history is tracked
- No summary/analytics endpoint

**Implementation:**
```python
# New endpoint: GET /api/v1/profile/learner/xp-summary
@router.get("/xp-summary")
async def get_xp_summary(
    user_id: UUID = Depends(get_current_user_id),
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db_session)
):
    level_service = LevelService(db)
    summary = level_service.get_xp_summary(user_id, days)
    return summary
```

**Files to Create/Modify:**
- `backend/src/api/learner_profile.py` - Add xp-summary endpoint
- `backend/src/services/levels.py` - `get_xp_summary()` already exists, verify it works

---

## Implementation Checklist

### Phase 1: Core XP Triggers (Week 1)

- [ ] **Task 1.1**: Add XP trigger to word learning
  - [ ] Locate word verification endpoint
  - [ ] Add LevelService.add_xp() call
  - [ ] Test XP awarding (10 XP per word)
  - [ ] Verify XP history is recorded

- [ ] **Task 1.2**: Add XP trigger to review completion
  - [ ] Locate review completion endpoint
  - [ ] Add LevelService.add_xp() call
  - [ ] Test XP awarding (15 XP per review)
  - [ ] Verify XP history is recorded

- [ ] **Task 1.3**: Add XP trigger to daily streak
  - [ ] Locate streak update logic
  - [ ] Add LevelService.add_xp() call (5 XP per day)
  - [ ] Test streak XP awarding
  - [ ] Consider: Scheduled job for daily streak check

### Phase 2: Automatic Achievement Checking (Week 1-2)

- [ ] **Task 2.1**: Add achievement check after word learned
  - [ ] Call AchievementService.check_achievements() after word learned
  - [ ] Test vocabulary achievements unlock
  - [ ] Test first word achievement

- [ ] **Task 2.2**: Add achievement check after review completed
  - [ ] Call AchievementService.check_achievements() after review
  - [ ] Test review achievements unlock
  - [ ] Test milestone achievements (100 reviews, 500 reviews)

- [ ] **Task 2.3**: Add achievement check after streak maintained
  - [ ] Call AchievementService.check_achievements() after streak update
  - [ ] Test streak achievements unlock (3-day, 7-day, 30-day)
  - [ ] Test perfect week achievement

- [ ] **Task 2.4**: Optimize achievement checking
  - [ ] Cache achievement definitions
  - [ ] Only check relevant categories
  - [ ] Batch checks if needed

### Phase 3: Immediate Feedback (Week 2)

- [ ] **Task 3.1**: Enhance API responses with gamification data
  - [ ] Add XP info to word learning response
  - [ ] Add XP info to review response
  - [ ] Add level-up status
  - [ ] Add newly unlocked achievements

- [ ] **Task 3.2**: Implement level-up notifications
  - [ ] Create notification on level-up
  - [ ] Test level-up notification creation
  - [ ] Verify notification appears in frontend

- [ ] **Task 3.3**: Implement achievement unlock notifications
  - [ ] Ensure notifications created on unlock
  - [ ] Test notification creation
  - [ ] Verify notification content

### Phase 4: Progress Visibility (Week 2-3)

- [ ] **Task 4.1**: Calculate achievement progress percentages
  - [ ] Add progress_percentage to get_user_achievements()
  - [ ] Add remaining count
  - [ ] Test progress calculation

- [ ] **Task 4.2**: Create XP summary endpoint
  - [ ] Add /xp-summary endpoint
  - [ ] Test XP summary by source
  - [ ] Test XP summary by time period

- [ ] **Task 4.3**: Frontend integration
  - [ ] Update frontend to show XP in responses
  - [ ] Show level-up celebrations
  - [ ] Show achievement unlock animations
  - [ ] Display progress percentages

### Phase 5: Testing & Optimization (Week 3)

- [ ] **Task 5.1**: End-to-end testing
  - [ ] Test complete flow: verify word → earn XP → check achievement → unlock → notification
  - [ ] Test level-up flow
  - [ ] Test streak XP flow
  - [ ] Test edge cases (multiple achievements, level-up + achievement)

- [ ] **Task 5.2**: Performance optimization
  - [ ] Profile achievement checking (ensure it's fast)
  - [ ] Optimize database queries
  - [ ] Add caching if needed
  - [ ] Test under load

- [ ] **Task 5.3**: Documentation
  - [ ] Document new API responses
  - [ ] Document XP triggers
  - [ ] Update API documentation
  - [ ] Create developer guide

---

## File Modification Summary

### Files to Modify

1. **`backend/src/api/verification.py`**
   - Add XP triggers after word verification
   - Add XP triggers after review completion
   - Add achievement checking
   - Enhance API responses

2. **`backend/src/services/learning_velocity.py`**
   - Add XP trigger for daily streak
   - Add achievement checking after streak update

3. **`backend/src/services/levels.py`**
   - Add notification creation on level-up (if not already)
   - Verify get_xp_summary() works correctly

4. **`backend/src/services/achievements.py`**
   - Add progress percentage calculation
   - Ensure notifications are created on unlock
   - Optimize achievement checking

5. **`backend/src/api/learner_profile.py`**
   - Add XP summary endpoint
   - Ensure consistent response format

6. **`backend/src/services/notifications.py`**
   - Ensure level_up notification type exists
   - Verify achievement notification creation

### Files to Create

- None (all functionality exists, just needs to be connected)

---

## Testing Plan

### Unit Tests

1. **XP Trigger Tests**
   - Test word learning XP (10 XP)
   - Test review XP (15 XP)
   - Test streak XP (5 XP)
   - Test level-up detection

2. **Achievement Check Tests**
   - Test vocabulary achievement unlock
   - Test streak achievement unlock
   - Test review achievement unlock
   - Test multiple achievements unlock

3. **Notification Tests**
   - Test level-up notification
   - Test achievement unlock notification
   - Test notification content

### Integration Tests

1. **Complete Flow Tests**
   - Verify word → Earn XP → Check achievement → Unlock → Notification
   - Complete review → Earn XP → Check achievement → Unlock
   - Maintain streak → Earn XP → Check achievement → Unlock

2. **Edge Case Tests**
   - Multiple achievements unlock simultaneously
   - Level-up + achievement unlock together
   - Rapid actions (multiple words in quick succession)

### Performance Tests

1. **Achievement Check Performance**
   - Measure time to check all achievements
   - Test with user who has many achievements
   - Optimize if > 100ms

2. **Database Query Performance**
   - Profile XP history queries
   - Profile achievement queries
   - Add indexes if needed

---

## Success Criteria

### Functional Requirements

- ✅ Users earn 10 XP automatically when learning a word
- ✅ Users earn 15 XP automatically when completing a review
- ✅ Users earn 5 XP automatically when maintaining a streak
- ✅ Achievements unlock automatically when requirements are met
- ✅ Level-ups are detected and notifications created
- ✅ API responses include gamification data
- ✅ Progress percentages are calculated correctly

### Performance Requirements

- ✅ Achievement check completes in < 100ms
- ✅ XP awarding completes in < 50ms
- ✅ API responses include gamification data without significant delay

### User Experience Requirements

- ✅ Users see immediate feedback when XP is earned
- ✅ Users see level-up celebrations
- ✅ Users see achievement unlock notifications
- ✅ Users can see progress toward next achievement

---

## Dependencies & Prerequisites

### Required Services (Already Implemented)

- ✅ `LevelService` - XP and level management
- ✅ `AchievementService` - Achievement checking and unlocking
- ✅ `NotificationService` - Notification creation
- ✅ Database schema - All tables exist

### No External Dependencies

- All required functionality exists
- No new libraries needed
- No database migrations needed

---

## Risk Assessment

### Low Risk

- **XP Triggering**: Simple function calls, low risk of breaking existing functionality
- **Achievement Checking**: Already implemented, just needs to be called
- **Notifications**: Already implemented, just needs to be called

### Medium Risk

- **Performance**: Achievement checking might be slow with many achievements
  - **Mitigation**: Optimize queries, cache definitions, only check relevant categories

- **Edge Cases**: Multiple achievements unlocking simultaneously
  - **Mitigation**: Test thoroughly, handle gracefully

### High Risk

- **None identified** - All components are already implemented and tested

---

## Timeline Estimate

### Week 1: Core Triggers
- Days 1-2: Word learning XP trigger
- Days 3-4: Review XP trigger
- Days 5: Streak XP trigger
- Days 6-7: Testing and bug fixes

### Week 2: Achievement Checking & Feedback
- Days 1-2: Automatic achievement checking
- Days 3-4: Enhanced API responses
- Days 5: Notifications
- Days 6-7: Testing

### Week 3: Progress & Polish
- Days 1-2: Progress calculations
- Days 3-4: XP summary endpoint
- Days 5-7: Testing, optimization, documentation

**Total: 2-3 weeks**

---

## Next Steps After Core System

Once the core system is functioning:

1. **Daily Quests** (1 week) - Builds on XP system
2. **Streak Freezes** (3-5 days) - Enhances streak system
3. **Battle Pass** (2-3 weeks) - Uses XP system
4. **Collection System** (2-3 weeks) - Uses achievement system

All advanced features depend on the core system working first.

---

## Documentation Updates Needed

After implementation:

1. **API Documentation**
   - Update verification endpoints with gamification responses
   - Document XP summary endpoint
   - Document new notification types

2. **Developer Guide**
   - How to add XP triggers to new endpoints
   - How to add achievement checks
   - Best practices for gamification integration

3. **User Documentation**
   - How XP is earned
   - How achievements work
   - How to track progress

---

**Document Version:** 1.0  
**Created:** January 2025  
**Status:** Ready for Implementation  
**Next Review:** After Phase 1 Completion

