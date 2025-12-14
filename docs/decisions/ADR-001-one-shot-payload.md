# ADR-001: One-Shot Payload Pattern

**Status**: Accepted  
**Date**: 2025-12-07 (Extended: 2025-12-08)  
**Deciders**: Core team

## Context

Gamification effectiveness depends on instant dopamine feedback. When a user completes an action (answers MCQ, learns a word), they need to see XP gains, level-ups, and achievement unlocks **immediately** - within the same visual frame as the action result.

Traditional architectures often do this:

```
POST /submit → Returns { correct: true }
Frontend animates checkmark
Frontend calls GET /user/xp to check level
Frontend calls GET /user/achievements to check unlocks
```

This multi-call pattern introduces latency that breaks the dopamine loop. By the time XP appears, the moment has passed.

## Decision

**Every API endpoint that triggers gamification MUST return the complete game state update in a single response.**

### Required Response Structure

Any endpoint that awards XP, points, or achievements must include a `gamification` field:

```json
{
  "outcome": "success",
  "gamification": {
    "xp_gained": 10,
    "total_xp": 1250,
    "current_level": 5,
    "xp_to_next_level": 150,
    "xp_in_current_level": 50,
    "progress_percentage": 33,
    "streak_extended": true,
    "streak_days": 7,
    "streak_multiplier": 1.5,
    "level_up": {
      "old_level": 4,
      "new_level": 5,
      "rewards": ["Badge: Word Smith"]
    },
    "achievements_unlocked": [
      {
        "code": "first_word",
        "name_en": "First Step",
        "icon": "🎯",
        "xp_reward": 50
      }
    ]
  }
}
```

### Endpoints That Must Follow This Pattern

| Endpoint | Gamification Triggers |
|----------|----------------------|
| `POST /api/v1/mcq/submit` | XP for review, streak, achievements |
| `POST /api/v1/words/start-verification` | XP for learning new word, streak |
| Future: any action that awards XP | Must include `gamification` field |

### Frontend Behavior

1. Parse `gamification` from response immediately
2. Animate XP bar using `xp_gained` and `progress_percentage`
3. If `level_up` is not null, show celebration overlay
4. If `achievements_unlocked` is not empty, queue achievement toasts
5. If `streak_extended`, show streak indicator

**No additional API calls for gamification state.**

## Consequences

### Positive

- **Instant feedback**: XP animations fire the millisecond response arrives
- **Simpler frontend**: No need to poll or refetch user state
- **Atomic updates**: Game state is always consistent
- **Better offline support**: Single response can be cached/queued

### Negative

- **Larger payloads**: ~200-500 bytes extra per response (acceptable)
- **Backend complexity**: Must calculate all gamification in same request
- **Coupling**: Frontend depends on specific response shape

### Exceptions

- `POST /api/v1/sync` (batch sync endpoint) does NOT return gamification per-action. This is intentional - it's a background offline fallback, not the primary feedback path. Users should see immediate feedback from direct API calls when online.

## Implementation Notes

- Use shared `GamificationResult` Pydantic model across endpoints
- Frontend should have reusable toast/celebration components
- All gamification services (LevelService, AchievementService, LearningVelocityService) must be called within the same request handler

## Extension: Verification Bundle Pre-Cache (December 2025)

The One-Shot Payload principle has been extended to enable **instant local feedback** through pre-caching.

### The Problem

Even with One-Shot Payload, API calls still take 200-500ms. For MCQ verification, users wait for the network before seeing correct/incorrect feedback.

### The Solution: Verification Bundles

When the user visits the Mine page, we pre-cache **verification bundles** for their entire inventory in IndexedDB:

```json
{
  "senseId": "run.v.01",
  "word": "run",
  "mcqs": [
    {
      "mcq_id": "uuid",
      "question": "What does 'run' mean?",
      "options": [...],
      "correct_index": 0,  // Enables instant feedback!
      "mcq_type": "meaning"
    }
  ],
  "cachedAt": 1702012800000
}
```

### How It Works

1. **Mine page loads** → `bundleCacheService.preCacheBundles()` fetches bundles for all inventory blocks
2. **User starts verification** → `MCQSession` loads MCQs from IndexedDB (~10ms)
3. **User answers** → `MCQCard` shows instant feedback using cached `correct_index`
4. **Background** → API submission for gamification (One-Shot Payload still applies)

### Storage

~2.5KB per sense. 500 senses = 1.25MB (minimal for IndexedDB).

### Key Files

- `POST /api/v1/mcq/bundles` - Batch bundle endpoint
- `landing-page/services/bundleCacheService.ts` - Pre-cache service
- `landing-page/lib/local-store.ts` - IndexedDB `verificationBundles` store

This extends One-Shot Payload from "instant after API" to "instant before API".

## Related

- `backend/src/api/mcq.py` - Reference implementation (includes `/bundles` endpoint)
- `backend/src/api/words.py` - Reference implementation
- `landing-page/components/features/mcq/MCQCard.tsx` - Frontend feedback UI
- `landing-page/docs/ARCHITECTURE_PRINCIPLES.md` - Data loading hierarchy

