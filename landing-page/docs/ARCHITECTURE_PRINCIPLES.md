# LexiCraft Architecture Principles

## ⚠️ IMMUTABLE CACHING RULE - DO NOT CHANGE

**This is the authoritative caching strategy. Do not modify without explicit approval.**

### Single Cache System (IndexedDB Only)

- **IndexedDB is the ONLY cache** for all user data (profile, children, progress, achievements, goals, notifications, etc.)
- **localStorage is FORBIDDEN** for user data - only allowed for tiny UI preferences (role preference, language)
- **Load from IndexedDB first** (~10ms async), then sync from API in background
- **Never block UI** - always render immediately from cache, update silently when API responds
- **No dual cache systems** - everything goes through IndexedDB via `downloadService` and `localStore`

### Why This Approach?

Following the "Last War" game pattern:
- Games use ONE persistent cache (IndexedDB)
- Pre-load everything on login
- Render instantly from cache
- Sync in background silently

### Enforcement

Any code that uses localStorage for user data is WRONG and must be fixed.
Check `UserDataContext.tsx` and `downloadService.ts` for the correct pattern.

---

## 🎯 Landing Page vs App Architecture (STRATEGIC DECISION)

**Decision (January 2025): Landing pages and app pages remain in the SAME Next.js app using Route Groups.**

**Status:** This is a strategic decision that may evolve as the product scales. See "When to Separate" section below.

### Route Groups (Not Separate Apps)

- **`(marketing)/`** - Public landing pages (shares AuthProvider for smart CTAs)
- **`(auth)/`** - Auth flow pages (auth only, no user data)
- **`(app)/`** - Authenticated app pages (auth + user data)

### Why Keep Them Together? (Strategic Rationale)

**The "Logged-In Marketing" Advantage:**
- **Smart CTAs**: Landing page can detect logged-in users via shared `AuthContext` and show personalized CTAs ("Welcome Back, Kurt! Continue Building" instead of "Sign Up")
- **Viral Loops**: Pre-fill referral codes, show personalized offers without requiring re-authentication
- **Seamless UX**: Single domain (`lexicraft.xyz`) with no context switching between marketing and app

**Architecture is Already "Future-Proof":**
- Route Groups provide logical separation without physical separation
- `(app)/layout.tsx` acts as security guard (auth required)
- `(marketing)/layout.tsx` keeps lobby open (public access)
- No "Integration Hell" - shared code, shared infrastructure (i18n, analytics, components)

**For MVP/Early Stage:** Keeping together is the right choice. Separation adds complexity without clear benefits at current scale.

### When to Separate (Future Consideration)

Consider separating into different Next.js apps when:
- Marketing needs independent CDN/edge deployment
- Marketing bundle size becomes a significant concern
- Marketing team needs different tech stack or tooling
- Different scaling requirements emerge (e.g., marketing needs global CDN, app needs regional deployment)
- Marketing becomes a separate product/brand with different domain

**Note:** If separation becomes necessary, plan for:
- Shared authentication state (cookies/tokens)
- Cross-app navigation (subdomain routing or query params)
- Code duplication (i18n, analytics, shared components)

### Context Providers Location

**Root Layout** (`app/[locale]/layout.tsx`):
- ✅ `AuthProvider` - Needed for AppTopNav login button AND marketing page smart CTAs
- ❌ `UserDataProvider` - **FORBIDDEN** (privacy issue for visitors)
- ❌ `SidebarProvider` - **FORBIDDEN** (only for app pages)

**App Layout** (`app/[locale]/(app)/layout.tsx`):
- ✅ `UserDataProvider` - Loads user data from IndexedDB
- ✅ `SidebarProvider` - Manages sidebar state

### Why This Context Separation?

1. **Privacy**: Visitors never load cached user data
2. **Performance**: Landing pages are lighter (no UserDataProvider)
3. **Security**: User data only for authenticated users
4. **Strategic**: Marketing pages can check auth state for personalized experience without loading user data

### Common Mistakes

❌ **WRONG**: Putting `UserDataProvider` in root layout
```tsx
// Root layout - WRONG
<UserDataProvider>  // ❌ Visitors would load cached data
  {children}
</UserDataProvider>
```

✅ **CORRECT**: Only in app layout
```tsx
// Root layout - CORRECT
<AuthProvider>  // ✅ Only auth, no user data
  {children}
</AuthProvider>

// App layout - CORRECT
<UserDataProvider>  // ✅ Only for authenticated users
  <SidebarProvider>
    {children}
  </SidebarProvider>
</UserDataProvider>
```

---

## 🎮 Core Principle: "As Snappy as Last War"

**Reference**: Mobile games like Last War load instantly. Users expect immediate feedback. Our app must feel the same.

---

## 👤 Identity Naming: Learner vs Player

- **In code (source of truth):**
  - Use **Learner** terminology for identity: `LearnerProfile`, `learners[]`, `activeLearner`, `switchLearner(learnerId)`.
  - All reads/writes that affect progress, SRS, wallet, achievements, etc. MUST flow through `activeLearner.id`.
- **In UI copy only:**
  - You MAY use “玩家 / Player” in labels, buttons, and headings (e.g. “選擇玩家”) to match the game vibe.
  - These labels must always be derived from `activeLearner` (or the learners list), not from a separate `player` identity.
- **Forbidden patterns:**
  - No separate `activePlayer` identity for backend calls.
  - No API requests or cache keys keyed by a `playerId` that can diverge from `activeLearner.id`.

This keeps the mental model simple: **one canonical identity in code (`activeLearner`), many playful “player” presentations in the UI.**

---

## 🚀 Bootstrap Frontloading Strategy (December 2024)

**This is the implementation of the "Last War" pattern. All pages load instantly after Bootstrap.**

### How It Works

1. **Loading Screen** - User sees a game-style loading screen with progress steps
2. **Bootstrap Service** - Loads ALL page data into Zustand (14 steps)
3. **Page Render** - Pages read from Zustand instantly (no API calls!)

### Bootstrap Steps

```typescript
// services/bootstrap.ts - THE source of truth
const BOOTSTRAP_STEPS = [
  'Loading profile...',
  'Loading children...',
  'Loading children summaries...',
  'Loading wallet...',
  'Loading progress...',
  'Loading achievements...',
  'Loading goals...',
  'Loading currencies...',
  'Loading rooms...',
  'Loading vocabulary...',
  'Preparing mining area...',
  'Loading due cards...',
  'Loading leaderboard...',
  'Finalizing...',
]
```

### Page Component Pattern

```typescript
'use client'
import { useAppStore, selectMyData } from '@/stores/useAppStore'

export default function MyPage() {
  // ⚡ Read from Zustand (pre-loaded by Bootstrap)
  const myData = useAppStore(selectMyData)
  const isBootstrapped = useAppStore((state) => state.isBootstrapped)
  
  // Layout shows loading screen until this is true
  if (!isBootstrapped) return null
  
  // Render instantly with pre-loaded data
  return <div>{myData}</div>
}
```

### ❌ NEVER Do This

```typescript
// WRONG: Fetching in useEffect
useEffect(() => {
  fetch('/api/mydata').then(setData)  // ❌ Causes loading delay
}, [])
```

### ✅ Always Do This

```typescript
// CORRECT: Read from Zustand
const data = useAppStore(selectData)  // ✅ Instant!
```

### Adding New Data to Bootstrap

1. **Add to Zustand** (`stores/useAppStore.ts`):
   ```typescript
   myData: null,
   setMyData: (data) => set({ myData: data }),
   export const selectMyData = (state) => state.myData
   ```

2. **Add to Bootstrap** (`services/bootstrap.ts`):
   ```typescript
   // Step N: Load My Data
   const data = await downloadService.getMyData()
   store.setMyData(data)
   ```

3. **Use in Page**:
   ```typescript
   const myData = useAppStore(selectMyData)
   ```

### Progress & Starter Pack Handling

The Mine page has special logic because its data depends on user progress:

```typescript
// 1. Load from IndexedDB first (instant, offline-first)
const progressMap = new Map<string, string>() // senseId -> status
const srsLevelsMap = new Map<string, string>() // senseId -> mastery_level
const localProgress = await localStore.getAllProgress(learnerId)
const localSRS = await localStore.getSRSLevels(learnerId)
localProgress.forEach((status, senseId) => progressMap.set(senseId, status))
localSRS.forEach((level, senseId) => srsLevelsMap.set(senseId, level))

// 2. Try backend API (with timeout)
try {
  const freshProgress = await Promise.race([
    progressApi.getUserProgress(learnerId),
    timeout(5000)
  ])
  // Update both maps with fresh data
  freshProgress.progress.forEach(p => {
    progressMap.set(p.sense_id, p.status)
    if (p.mastery_level) {
      srsLevelsMap.set(p.sense_id, p.mastery_level)
    }
  })
} catch { /* use IndexedDB data */ }

// 3. Update Zustand store (both maps for parallel state pattern)
// NOTE: emojiProgress and emojiSRSLevels are typed as Map | null, but runtime guards
// ensure they're always Maps (never null) when emoji pack is active
if (store.activePack?.id === 'emoji_core') {
  store.setEmojiProgress(new Map(progressMap))  // Runtime guard converts null to empty Map if needed
  store.setEmojiSRSLevels(new Map(srsLevelsMap))  // Runtime guard converts null to empty Map if needed
}

// 4. Build blocks with correct status
for (const [senseId, status] of progressMap) {
  blocks.push({ ...blockData, status })
}
```

### Emoji Progress State Management

**Type Definition:**
- `emojiProgress: Map<string, string> | null` - Maps `sense_id` → workflow status ('raw', 'hollow', 'solid', 'mastered')
- `emojiSRSLevels: Map<string, string> | null` - Maps `sense_id` → SRS mastery level ('learning', 'familiar', 'known', 'mastered')

**Runtime Guarantees:**
- Initialized as empty Maps (`new Map<string, string>()`) in store initial state
- Runtime guards in `setEmojiProgress` and `setEmojiSRSLevels` convert `null` to empty Map if emoji pack is active
- Empty learners have empty Maps (`size === 0`), not `null`
- All code paths (bootstrap, switchLearner, downloadService) ensure Maps are always initialized

**UI Component Requirements:**
- Components must handle both `null` (when pack not active) and empty Maps (when pack active but no progress)
- Filtering effects must run even when `progress.size === 0` to clear stale state for empty learners
- Include `activeLearner?.id` in `useEffect` dependency arrays to react to learner switches
- Example: `EmojiCollectionShowcase` clears `masteredWords` when `progress.size === 0`

### Reference Files

- `services/bootstrap.ts` - Bootstrap logic
- `stores/useAppStore.ts` - Zustand store
- `app/[locale]/(app)/layout.tsx` - Loading screen
- `lib/local-store.ts` - IndexedDB operations

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

### Vocabulary Data Model
- **Lemma-based indexing**: `byLemma` index built at load time from sense_ids
- **Lemma extraction**: `be.v.01` → `be` (first segment of sense_id)
- **Why**: The `word` field may contain inflected forms (`were`), but lookups need lemmas (`be`)
- **Result**: `getSensesForWord("be")` correctly returns `["be.v.01", "be.v.02", ...]`

### Priority 2: IndexedDB Cache (Fast, ~10ms)
- **IndexedDB is the ONLY cache** for all user data
- `localStore.progress` - User block progress
- `localStore.verificationBundles` - Pre-cached MCQs for instant verification
- `downloadService` - User profile, children, achievements, goals, notifications, etc.
- Survives app restarts
- **localStorage is FORBIDDEN for user data** - only allowed for tiny UI preferences

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
| **Mine** | `vocabulary.json` | User progress + pre-cache verification bundles |
| **Profile** | Default Level 1 profile | Full profile from API |
| **Leaderboards** | Empty list | Rankings from API |
| **Verification** | Cached MCQs from bundles | Submit results (background) |

---

## 5. Key Files

- `lib/vocabulary.ts` - Bundled vocabulary data
- `lib/local-store.ts` - IndexedDB for offline cache (progress + verification bundles + user data)
- `services/syncService.ts` - Background sync queue
- `services/bundleCacheService.ts` - Pre-cache verification bundles for entire inventory
- `services/downloadService.ts` - Pre-download user data (uses IndexedDB only)
- `contexts/UserDataContext.tsx` - User data context (uses IndexedDB via downloadService, NOT localStorage)

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

