# Caching Rules - IMMUTABLE

**This document defines the authoritative caching strategy. Do not modify without explicit approval.**

## The Rule

**IndexedDB is the single source of truth for all user data.**

## What Goes Where

| Data Type | Storage | Example |
|-----------|---------|---------|
| User Profile | IndexedDB | `downloadService.getProfile()` |
| Children | IndexedDB | `downloadService.getChildren()` |
| Progress | IndexedDB | `localStore.progress` |
| Achievements | IndexedDB | `downloadService.getAchievements()` |
| Goals | IndexedDB | `downloadService.getGoals()` |
| Notifications | IndexedDB | `downloadService.getNotifications()` |
| Leaderboard | IndexedDB | `downloadService.getLeaderboard()` |
| Role Preference | localStorage (tiny UI pref) | `useRolePreference` hook |
| Language | localStorage (tiny UI pref) | i18n settings |

## Implementation Pattern

```typescript
// ✅ CORRECT: Load from IndexedDB
const profile = await downloadService.getProfile()
await localStore.setCache('user_profile', profile, CACHE_TTL.MEDIUM)

// ❌ WRONG: Using localStorage for user data
const profile = JSON.parse(localStorage.getItem('profile'))
localStorage.setItem('profile', JSON.stringify(profile))
```

## Why This Approach?

Following mobile game pattern (Last War):

- Single cache system = no sync issues
- Pre-load everything on login
- Render instantly from cache
- Sync in background silently
- Works offline perfectly

## Enforcement

Any code using localStorage for user data must be fixed immediately.

## Reference Implementation

See:
- `landing-page/contexts/UserDataContext.tsx` - Correct pattern
- `landing-page/services/downloadService.ts` - Cache management
- `landing-page/lib/local-store.ts` - IndexedDB wrapper

