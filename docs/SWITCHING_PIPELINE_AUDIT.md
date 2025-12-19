# Learner Switching Pipeline Audit

**Date:** 2024-12-17  
**Status:** ✅ Verified and Working

## Summary

The learner switching pipeline has been audited and verified. All critical paths correctly use `activeLearner` and pass `learner_id` to backend APIs.

## Audit Results

### Child Learners Data Integrity

| Learner | ID | Progress Items | Status |
|---------|-----|----------------|--------|
| hanjk | `c9b59eae-d7b4-489d-a66c-c8c5799b64c6` | 2 (cat, dog) | ✅ Correct |
| hann | `aac4ea9b-c9fa-4577-b25e-9daf4603f49a` | 0 | ✅ Clean |
| Parent | `e965547f-ca48-4dd3-a728-ca4f568ffe48` | 20 | ✅ Legitimate |

### Switching Entry Points

#### 1. `PlayerSwitcher.tsx` (Primary UI Component)
- **Location:** `components/layout/PlayerSwitcher.tsx:47`
- **Trigger:** User clicks learner in dropdown (top bar switcher)
- **Action:** `await switchLearner(learnerId)`
- **Status:** ✅ Correct - Primary switching mechanism, non-blocking, always available in top bar

#### 2. `parent/children/page.tsx` (After Adding Child)
- **Location:** `app/[locale]/(app)/parent/children/page.tsx:111`
- **Trigger:** After adding a new child learner
- **Action:** `await store.switchLearner(currentLearnerId)` (re-triggers for current learner)
- **Status:** ✅ Correct (refreshes current learner, doesn't auto-switch to new child)

### Critical Data Flow Paths

#### 1. Mining Words (`addToQueue`)
- **Location:** `stores/useAppStore.ts:1129-1227`
- **Flow:**
  1. Gets `activeLearnerId` from `state.activeLearner?.id`
  2. Logs debug info (learner name, ID, is_parent)
  3. Saves to IndexedDB with `learnerId`
  4. Calls `progressApi.startForging(senseId, activeLearnerId)`
- **Status:** ✅ Correct with debug logging

#### 2. Backend API Call (`progressApi.startForging`)
- **Location:** `services/progressApi.ts:123-140`
- **Flow:**
  1. Receives `learnerId` parameter
  2. Creates request body: `{ learner_id: learnerId }`
  3. Logs debug info (senseId, learnerId, body)
  4. POSTs to `/api/v1/mine/blocks/${senseId}/start`
- **Status:** ✅ Correct with debug logging

#### 3. Backend Processing (`start_forging`)
- **Location:** `backend/src/api/mine.py:590-757`
- **Flow:**
  1. Receives `request: Optional[StartForgingRequest]` with `learner_id`
  2. Security check: Verifies user is guardian/owner
  3. Uses `effective_learner_id` to create `learning_progress` row
  4. Creates row with `learner_id = effective_learner_id`
- **Status:** ✅ Correct (verified by database audit)

#### 4. Progress Sync (`downloadService.syncProgress`)
- **Location:** `services/downloadService.ts:481-487`
- **Flow:**
  1. Calls `downloadProgress(learnerId)`
  2. Fetches from `/api/v1/mine/progress?learner_id=${learnerId}`
  3. Imports to IndexedDB (learner-scoped)
  4. Updates Zustand if `activeLearner?.id === learnerId`
- **Status:** ✅ Correct with defensive checks

#### 5. Learner Switch (`switchLearner`)
- **Location:** `stores/useAppStore.ts:457-827`
- **Flow:**
  1. Saves current learner state to `learnerCache`
  2. Restores target learner from cache (if exists) or IndexedDB
  3. Triggers background sync via `downloadService.syncProgress`
  4. Updates Zustand with learner-specific data
- **Status:** ✅ Correct with comprehensive logging

## Debug Logging

### Frontend Debug Points

1. **`addToQueue`** - Logs when mining words:
   ```typescript
   [addToQueue] Mining word: {
     senseId, word, activeLearnerId, activeLearnerName, activeLearnerIsParent
   }
   ```

2. **`progressApi.startForging`** - Logs API request:
   ```typescript
   [progressApi.startForging] Sending request: {
     senseId, learnerId, body, hasLearnerId
   }
   ```

3. **`switchLearner`** - Logs switch completion:
   ```typescript
   ✅ Switched to learner: {learner.display_name} ({learnerId})
   ```

### Backend Debug Points

1. **`start_forging`** - Logs when `DEBUG_LEARNER_PIPELINE=true`:
   - Incoming request details
   - Resolved `learner_id`
   - Created `learning_progress` row

2. **`get_user_progress`** - Logs query details:
   - Target `learner_id`
   - Number of rows found

## Known Issues (Resolved)

### Issue 1: Dog/Cat Saved to Wrong Learner
- **Problem:** Words were saved with parent's `learner_id` instead of hanjk's
- **Root Cause:** `activeLearner` was still parent when mining occurred
- **Fix:** Migrated data from parent to hanjk
- **Prevention:** Added debug logging to catch future issues

## Testing Checklist

- [x] Switch to parent → mine word → verify saved with parent's learner_id
- [x] Switch to hanjk → mine word → verify saved with hanjk's learner_id
- [x] Switch to hann → mine word → verify saved with hann's learner_id
- [x] Switch between learners → verify progress persists correctly
- [x] Refresh page → verify activeLearner persists correctly
- [x] Add new child → verify can switch to new child immediately

## Future Improvements

1. **Add Verification Step:** After `switchLearner` completes, verify `activeLearner.id` matches expected
2. **Add Data Integrity Check:** Periodic check for orphaned progress (learner_id doesn't exist)
3. **Add Migration Tool:** Script to migrate incorrectly assigned progress between learners

## Architecture Notes

### Single Source of Truth
- **Frontend:** `activeLearner` in Zustand store
- **Backend:** `learner_id` in `learning_progress` table
- **Cache:** `learnerCache` in Zustand (in-memory snapshots)

### Data Flow
```
User Action (Mine Word)
  ↓
Zustand Store (activeLearner.id)
  ↓
Backend API (POST with learner_id in body)
  ↓
PostgreSQL (learning_progress.learner_id)
  ↓
Backend API (GET with learner_id query param)
  ↓
IndexedDB (learner-scoped storage)
  ↓
Zustand Store (emojiProgress, emojiSRSLevels)
  ↓
UI Components (EmojiMineGrid, EmojiCollectionShowcase)
```

### UI Component Behavior

#### EmojiMineGrid (Mine Page)
- Shows ALL words from vocabulary pack
- Filters by status in render logic (not in useEffect)
- Works correctly with empty progress (shows all words as "raw")
- Syncs `progress` state from `emojiProgress` Map with null handling
- Includes `activeLearner?.id` in dependency array to react to learner switches

#### EmojiCollectionShowcase (Build/Collect Page)
- Shows ONLY collected words (status !== 'raw')
- Filters words in `useEffect` based on `progress` Map
- **Critical:** Filtering effect must run even when `progress.size === 0` to clear `masteredWords` state for empty learners
- Must include `activeLearner?.id` in dependency array to trigger on learner switch
- Syncs both `progress` and `srsLevels` from Zustand Maps

**Key Fix (2024-12-17):** The filtering effect in `EmojiCollectionShowcase` was only running when `progress.size > 0`, causing empty learners to show stale words from previous learner. Fixed by:
1. Adding early return to clear `masteredWords` when `progress.size === 0`
2. Adding `activeLearner?.id` to dependency array
3. Improving `progress` sync effect to match `EmojiMineGrid` pattern (handles `null` case explicitly)

## Conclusion

The switching pipeline is working correctly. All critical paths:
- ✅ Use `activeLearner` correctly
- ✅ Pass `learner_id` to backend APIs
- ✅ Store data with correct `learner_id` in database
- ✅ Load data per-learner from IndexedDB
- ✅ Update UI correctly when switching

Debug logging is in place to catch any future issues early.

