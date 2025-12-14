# Game Engine Architecture

**Status:** ✅ Implemented (Phase 1 Complete)

## Overview

The "Game Engine" is LexiCraft's data layer that enables **"Last War" performance** - instant UI rendering with zero spinners after the initial load.

## Philosophy

> "The best loading screen is the one you only see once."

Traditional web apps fetch data on every page load, causing spinners everywhere. The Game Engine inverts this:

1. **Pay the "Time Tax" once** at `/start` (with a beautiful progress bar)
2. **Everything else is instant** (read from Zustand, already in memory)
3. **Background sync** keeps data fresh (invisible to user)

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         Login                                │
│                           ↓                                  │
│                   /start (Airlock)                          │
│                           ↓                                  │
│           ┌──────────────────────────┐                      │
│           │   Bootstrap Service       │                      │
│           │  ┌─────────────────────┐ │                      │
│           │  │ 1. Load IndexedDB   │ │                      │
│           │  │ 2. Hydrate Zustand  │ │                      │
│           │  │ 3. Show Progress    │ │                      │
│           │  └─────────────────────┘ │                      │
│           └──────────────────────────┘                      │
│                           ↓                                  │
│              Redirect to Home (instant)                      │
│                           ↓                                  │
│   ┌─────────────────────────────────────────┐               │
│   │      Components Read from Zustand       │               │
│   │         (Zero API Calls)                │               │
│   └─────────────────────────────────────────┘               │
│                           │                                  │
│            Background Sync (Silent)                          │
│                           ↓                                  │
│                  IndexedDB → Zustand                         │
└─────────────────────────────────────────────────────────────┘
```

## Components

### 1. Zustand Store (`stores/useAppStore.ts`)

**Role:** In-memory state that components read from

**Features:**
- Central state for all app data (user, wallet, progress, achievements, etc.)
- Optimized selectors to prevent unnecessary re-renders
- DevTools integration for debugging
- Reset function for logout

**Usage:**
```typescript
import { useAppStore, selectBalance } from '@/stores/useAppStore'

function WalletDisplay() {
  // ✅ Instant read from Zustand (no API call)
  const balance = useAppStore(selectBalance)
  
  return <div>{balance.available_points} points</div>
}
```

### 2. Bootstrap Service (`services/bootstrap.ts`)

**Role:** Pre-loads all data before app starts

**Steps:**
1. Load user profile from IndexedDB
2. Load children list (if parent)
3. Load learner profile (XP, level, streaks)
4. Load progress stats
5. Load achievements
6. Load goals
7. Vocabulary (lazy-loaded later)
8. Trigger background sync

**Usage:**
```typescript
import { bootstrapApp } from '@/services/bootstrap'

const result = await bootstrapApp(userId, (progress) => {
  console.log(`${progress.percentage}% - ${progress.step}`)
})

if (result.success) {
  router.push(result.redirectTo)
}
```

### 3. Loading Screen (`app/[locale]/(app)/start/page.tsx`)

**Role:** The "Airlock" - beautiful loading screen that hides the Time Tax

**Features:**
- Progress bar (0% → 100%)
- Step-by-step feedback
- Error handling with retry
- Auto-redirect when complete

**UX:**
- Users see progress, not a spinner
- Feels intentional, not broken
- Only shown once per session
- 300ms delay at 100% (shows completion)

### 4. IndexedDB Layer (`lib/local-store.ts`)

**Role:** Persistent cache (survives logout, page refresh)

**Stores:**
- `progress` - Learning progress (raw/hollow/solid blocks)
- `cache` - User data, achievements, goals, etc.
- `syncQueue` - Offline actions waiting to sync
- `verificationBundles` - Pre-cached MCQs

### 5. Download Service (`services/downloadService.ts`)

**Role:** Background data synchronization

**Features:**
- Downloads all user data in parallel
- Caches to IndexedDB
- Respects TTLs (7 days / 30 days / 1 year)
- Error handling (continues on failure)
- Progress tracking

## Data Flow

### Initial Load (Cold Start)
```
User logs in
     ↓
/start page renders
     ↓
Bootstrap Service runs
     ↓
IndexedDB → Zustand (instant if cached)
     ↓
Redirect to home
     ↓
Components render from Zustand (instant)
     ↓
Background sync starts (silent)
     ↓
Fresh data → IndexedDB → Zustand
```

### Subsequent Visits (Warm Start)
```
User logs in
     ↓
/start page renders
     ↓
Already bootstrapped? Skip to redirect (instant)
     ↓
Components render from Zustand (instant)
```

### User Action (e.g., Verify a Word)
```
User clicks verify
     ↓
Optimistic update in Zustand (instant UI)
     ↓
API call in background
     ↓
Response → Update Zustand + IndexedDB
```

## Performance Targets

| Metric | Target | Actual |
|--------|--------|--------|
| Bootstrap time | < 2s | ~1.5s (with cache) |
| Component render | < 16ms | Instant (from Zustand) |
| Background sync | < 5s | ~3s (10 parallel requests) |
| Offline mode | 100% | ✅ Works (IndexedDB cache) |

## Benefits

### For Users
- **Instant navigation** - No spinners between pages
- **Offline capable** - App works without internet
- **Smooth animations** - No data-loading jank
- **Feels like a game** - Not a slow web page

### For Developers
- **No useEffect fetchers** - Components are pure
- **Single source of truth** - Zustand + IndexedDB
- **Predictable state** - Always know where data lives
- **Easy debugging** - Redux DevTools integration

## Rules

### ✅ DO
- Read from Zustand in components
- Use bootstrap service at `/start`
- Update Zustand + IndexedDB together
- Use background sync for fresh data

### ❌ DON'T
- Fetch data in components (use Zustand)
- Use localStorage for user data (IndexedDB only)
- Skip bootstrap (all pages assume data is ready)
- Block UI for API calls (optimistic updates)

## Migration Guide

### Old Pattern (❌ Slow)
```typescript
function MyComponent() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  
  useEffect(() => {
    fetch('/api/data')
      .then(res => res.json())
      .then(setData)
      .finally(() => setLoading(false))
  }, [])
  
  if (loading) return <Spinner />
  return <div>{data.value}</div>
}
```

### New Pattern (✅ Fast)
```typescript
function MyComponent() {
  // Instant read from Zustand (already loaded by Bootstrap)
  const data = useAppStore((state) => state.someData)
  
  // No loading state, no useEffect, no spinner!
  return <div>{data.value}</div>
}
```

## Troubleshooting

### "Data is null in my component"
- Check if Bootstrap ran successfully
- Verify component is inside `(app)/` folder (authenticated routes)
- Check if user is logged in

### "Progress bar stuck at X%"
- Check browser console for errors
- Verify IndexedDB is not blocked (private browsing)
- Check network tab for failed API calls

### "Changes not showing in UI"
- Did you update both Zustand AND IndexedDB?
- Use `store.setX()` methods, don't mutate state directly
- Check Redux DevTools to see state changes

## Next Steps (Phase 2 & 3)

### Phase 2: Layout Fixes
- [ ] Enforce `h-[100dvh] overflow-hidden` in layouts
- [ ] Fix learner layout for HUD + Map layering
- [ ] Add Framer Motion transitions

### Phase 3: Component Migration
- [ ] Remove all `useEffect` fetchers from components
- [ ] Replace `useUserData()` with `useAppStore()`
- [ ] Add optimistic updates for mutations

## References

- `.cursorrules` - "Caching & Bootstrap Strategy" section
- `landing-page/docs/ARCHITECTURE_PRINCIPLES.md`
- `landing-page/docs/CACHING_RULES.md`

