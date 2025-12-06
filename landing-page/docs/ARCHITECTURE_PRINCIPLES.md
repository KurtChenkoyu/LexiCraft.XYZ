# LexiCraft Architecture Principles

## 🎮 Core Principle: "As Snappy as Last War"

**Reference**: Mobile games like Last War load instantly. Users expect immediate feedback. Our app must feel the same.

---

## 1. Instant UI Rendering (No Loading Spinners for Content)

### ❌ WRONG Approach
```
User navigates → Show loading spinner → Wait for API → Show content OR error
```

### ✅ CORRECT Approach  
```
User navigates → Show UI immediately (default/empty state) → Fetch in background → Update silently
```

### Implementation Rules:
1. **Never block rendering** on API calls
2. **Default states are valid** - Level 1 profile, empty leaderboard, "no cards due" are all legitimate UI states
3. **Background fetches only** - API calls happen after initial render
4. **Silent updates** - When data arrives, update UI without transitions or spinners

### Example - Profile Page:
```tsx
// Start with defaults - UI renders INSTANTLY
const [profile, setProfile] = useState<LearnerProfile>(defaultProfile)

useEffect(() => {
  // Background fetch - non-blocking
  fetchProfile().then(data => {
    if (data) setProfile(data)  // Silent update
  }).catch(() => {})  // Silent fail - keep defaults
}, [])

// ALWAYS render UI - never conditional loading
return <ProfileUI profile={profile} />
```

---

## 2. Offline-First, Not Error-First

### ❌ WRONG: Show error pages when API fails
```tsx
if (error) return <ErrorPage message="無法載入" />
```

### ✅ CORRECT: Show subtle offline indicator, keep UI functional
```tsx
return (
  <main>
    {isOffline && <OfflineIndicator />}  {/* Subtle, non-blocking */}
    <NormalUIContent />  {/* Always renders */}
  </main>
)
```

### Offline Indicator Pattern:
```tsx
{isOffline && (
  <div className="flex items-center gap-2 text-amber-400/70 text-sm">
    <span className="w-2 h-2 bg-amber-500 rounded-full animate-pulse" />
    離線模式
  </div>
)}
```

---

## 3. Data Loading Hierarchy

### Priority 1: Bundled Data (Instant)
- `vocabulary.json` - Word definitions, connections
- Static assets, UI components

### Priority 2: IndexedDB Cache (Fast, ~10ms)
- `localStore` - User progress, cached API responses
- Survives app restarts

### Priority 3: API Fetch (Background)
- Server data - leaderboards, notifications
- Always non-blocking, updates silently

### Data Flow:
```
Page Load
    ├─→ Render with bundled data (instant)
    ├─→ Check IndexedDB (async, fast)
    │     └─→ Update UI if found
    └─→ Fetch from API (async, slow)
          └─→ Update UI when complete
              └─→ Cache in IndexedDB
```

---

## 4. Pages That Follow This Pattern

| Page | Bundled/Default | Background Fetch |
|------|-----------------|------------------|
| **Mine** | `vocabulary.json` | User progress from API |
| **Profile** | Default Level 1 profile | Full profile from API |
| **Leaderboards** | Empty list | Rankings from API |
| **Verification** | "No cards due" 🎉 | Due cards from API |

---

## 5. Key Files

- `lib/vocabulary.ts` - Bundled vocabulary data
- `lib/local-store.ts` - IndexedDB for offline cache
- `services/syncService.ts` - Background sync queue
- `services/downloadService.ts` - Pre-download user data

---

## 6. Anti-Patterns to Avoid

### ❌ Conditional rendering based on loading state
```tsx
if (isLoading) return <Spinner />  // WRONG - blocks UI
```

### ❌ Error pages for network failures
```tsx
if (error) return <ErrorPage />  // WRONG - breaks offline
```

### ❌ Sequential data loading
```tsx
const profile = await fetchProfile()  // WRONG - blocks
const stats = await fetchStats()      // WRONG - sequential
```

### ✅ Correct patterns
```tsx
// Parallel, non-blocking
useEffect(() => {
  fetchProfile().then(setProfile).catch(() => {})
  fetchStats().then(setStats).catch(() => {})
}, [])

// Always render
return <UI profile={profile || defaultProfile} stats={stats || defaultStats} />
```

---

## Remember

> "The best loading state is no loading state."

Users should never wait. Empty states, default values, and offline modes are all better than spinners.

