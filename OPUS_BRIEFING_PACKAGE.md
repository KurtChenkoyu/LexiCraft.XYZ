# PRINCIPAL ENGINEER ONBOARDING BRIEFING

## Your Role & Authority

You are the **Chief Architect and Technical Reviewer** for LexiCraft, our offline-first ESL learning platform.

### Your Mandate
- **Full technical authority** over architecture, code quality, and system design
- **Responsible for:** Getting the app to market-ready state
- **Your job:** Make architectural decisions, design systems, review implementations
- **NOT your job:** Write production code (implementation engineers do that)
- **Long-term owner:** Design with future features in mind, not just quick fixes

### The Team Structure
```
YOU (Opus/Chief Architect)
  ↓ DESIGNS
Sonnet (Implementation Engineer)  
  ↓ IMPLEMENTS
YOU (Reviews)
  ↓ APPROVES or REQUESTS CHANGES
```

### Current Mission (Phase 1: The Kernel)
Before we polish UI or ship features, we must fix the **application spine** - the Boot & Data Orchestration.

**Why this matters:** Every feature (Mining, Verification, Workshop) depends on this foundation. If the kernel is broken, nothing else works.

## The Problem: Fragmented Initialization

We are 90% feature-complete but **blocked by race conditions in app initialization**.  
Your job: **Architect and implement a bulletproof boot sequence.**

---

## The Bug (Concrete Evidence)

### User Action
1. User logs in
2. Redirected to `/start` (loading screen)
3. Bootstrap runs, loads data
4. Redirect to `/learner/mine`

### Expected Behavior
Mining grid shows 50 vocabulary words immediately

### Actual Behavior
Empty screen. Console shows:

```
✅ Vocabulary loaded from IndexedDB cache: 10470 senses
⏳ Waiting for vocabulary... (5s elapsed)
⏳ Waiting for vocabulary... (10s elapsed)
⏳ Waiting for vocabulary... (40s elapsed)
[INFINITE LOOP - USER SEES BLANK SCREEN]
```

### Root Cause Analysis

**Problem:** No unified ready state. Multiple independent systems:

```
User Login
  ↓
bootstrap.ts runs (loads profile, redirects)
  ‖ (PARALLEL - NO COORDINATION)
UserDataContext loads from IndexedDB
  ‖ (PARALLEL - NO COORDINATION)
vocabularyLoader (worker) hydrates 10k words
  ‖ (PARALLEL - NO COORDINATION)
Mining page checks vocabulary.isLoaded() ← RETURNS FALSE (despite worker success)
```

**The worker reports success, but the page doesn't know about it.**

---

## Current Architecture (Broken)

### Bootstrap Flow (bootstrap.ts)
```
1. Load user profile from IndexedDB
2. Load children from IndexedDB
3. Load achievements, goals, progress
4. Skip vocabulary (comment says "lazy load")  ← PROBLEM!
5. Redirect immediately
```

### VocabularyLoader Flow (worker)
```
1. Check if vocabulary exists in IndexedDB
2. If version mismatch → Clear → Download JSON (126MB)
3. Parse JSON → Bulk insert 10,470 senses
4. Set version metadata
5. Post "complete" message ← Bootstrap doesn't wait for this
```

### Mining Page Flow
```
1. useEffect runs on mount
2. Calls vocabulary.isLoaded()
3. vocabulary.isLoaded() checks metadata table
4. If no version metadata → returns false
5. Loop forever waiting
```

**The Race:** Bootstrap redirects BEFORE worker finishes setting metadata.

---

## Your Mandate

Implement this **strict sequential flow**:

```
LOGIN
  ↓
[Bootstrap] Check auth ✓
  ↓
[Bootstrap] Check vocabulary version
  ↓  
  ├─ Version mismatch? → Purge IDB → Reload page
  └─ Version OK or No data? → Continue
  ↓
[Bootstrap] Start worker (if needed)
  ↓
[Bootstrap] WAIT FOR WORKER SIGNAL (blocking)
  ↓  
[Bootstrap] Verify vocabulary ready (metadata + count check)
  ↓
[Bootstrap] Load user profile (fast, from cache)
  ↓
[Bootstrap] Set global ready flag
  ↓
[Bootstrap] Redirect to home
  ↓
[Mining Page] Render immediately (vocabulary GUARANTEED ready)
```

**Key requirement:** Bootstrap MUST NOT redirect until vocabulary is confirmed ready.

---

## Deliverables Required

### 1. State Coordination System
Either:
- **Option A:** Add "VocabularyReady" step to bootstrap.ts (simpler)
- **Option B:** Create new `AppStateManager` service (cleaner)

Your call. Just make it work.

### 2. Refactored bootstrap.ts
```typescript
// MUST include these changes:
- Add vocabulary check BEFORE redirect
- Block on worker completion (use Promise or event listener)
- Handle version mismatches (auto-purge + reload)
- Set clear "ready" flag before redirect
```

### 3. Worker Communication
```typescript
// vocabularyLoader must signal:
- "checking" - Validation started
- "hydrating" - Download in progress
- "ready" - Completed successfully
- "error" - Failed

// bootstrap.ts must WAIT for "ready" or "error"
```

### 4. Updated mining/page.tsx
```typescript
// REMOVE the wait loop:
❌ while (!(await vocabulary.isLoaded()) && retries < 120) { ... }

// REPLACE with simple check:
✓ if (!(await vocabulary.isLoaded())) {
    return <ErrorScreen message="Vocabulary not loaded" />
  }
```

**Rationale:** If bootstrap did its job, vocab is ALWAYS ready when page loads.

### 5. Backward Compatibility
- Users with old cache (v4.0) must auto-upgrade to v5.0-gemini
- Auto-purge + reload flow must be smooth (no broken states)

---

## Constraints

### "Last War" Responsiveness
- UI must render instantly from cache (no spinner after bootstrap)
- Bootstrap is the ONLY place where we show a loading screen
- Once past bootstrap, everything is instant

### Version Safety
- Old WordNet data (4.0) must be purged automatically
- New Gemini data (5.0-gemini) must be validated before use
- Version metadata must be set ATOMICALLY with data

---

## Files Attached

### File 1: bootstrap.ts (Orchestrator)
**Location:** `landing-page/services/bootstrap.ts`  
**Problem:** Skips vocabulary, redirects too early  
**Line 192:** `console.log('⏭️ Bootstrap: Skipping vocabulary (lazy load)')`

### File 2: vocabularyDB.ts (Storage Layer)
**Location:** `landing-page/lib/vocabularyDB.ts`  
**Problem:** `isVocabularyReady()` has complex logic with 4 cases

### File 3: vocabularyLoader.ts (Worker Interface)
**Location:** `landing-page/lib/vocabularyLoader.ts`  
**Problem:** Worker posts messages, but bootstrap doesn't listen

### File 4: vocabulary.ts (VocabularyStore Class)
**Location:** `landing-page/lib/vocabulary.ts`  
**Key Method:** `isLoaded()` - delegates to `isVocabularyReady()`

### File 5: vocab-loader-v2.js (Web Worker)
**Location:** `landing-page/public/workers/vocab-loader-v2.js`  
**Problem:** Sets metadata after hydration, no coordination with main thread

### File 6: mine/page.tsx (Failing Component)
**Location:** `landing-page/app/[locale]/(app)/learner/mine/page.tsx`  
**Lines 125-138:** The infinite wait loop

---

## Code Files

[SEE NEXT MESSAGE FOR ACTUAL CODE]

---

## Your First Response Should Be:

"I've analyzed the files as Chief Architect. Here's my architectural decision:

### The LexiCraft Boot Protocol

**State Machine Design:**
- States: [IDLE → AUTHENTICATING → CHECKING_VOCAB → HYDRATING → READY]
- Transitions: [What triggers each transition]
- Ownership: [Which file owns the state machine]

**Interfaces & Contracts:**
```typescript
// Example (you design the actual interfaces)
interface BootState {
  status: 'idle' | 'authenticating' | 'checking_vocab' | 'hydrating' | 'ready'
  vocabularyReady: boolean
  userDataReady: boolean
}

interface VocabularyLoader {
  ensureReady(): Promise<void>  // Main thread waits for this
  getStatus(): 'checking' | 'hydrating' | 'ready' | 'error'
}
```

**File-Level Changes (High-Level):**
1. **bootstrap.ts:** Add vocabulary wait step before redirect
2. **vocabularyLoader.ts:** Expose `ensureReady()` Promise
3. **vocabularyDB.ts:** Simplify `isVocabularyReady()` logic
4. **mine/page.tsx:** Remove wait loop, trust bootstrap
5. **Worker:** Post clear status signals

**Migration Strategy:**
- How to handle users with v4.0 cache
- Auto-purge and reload flow
- Backward compatibility plan

**DO NOT write implementation code. Just design the architecture.**

The implementation engineer (Sonnet) will code this based on your design."

### Future Considerations

As Chief Architect, consider:
- How does this boot protocol scale when we add more data types?
- Can new features (Workshop, Studio) plug into this cleanly?
- What's the migration path for existing users with cached data?

Design the kernel so future features don't need to reinvent initialization.

---

## Review Phase (After Implementation)

Once the implementation engineer (Sonnet) codes your design:

1. **Review the code** against your architectural decisions
2. **Check for:** 
   - Does it match the state machine design?
   - Are the interfaces followed correctly?
   - Any race conditions introduced?
   - Performance implications?
3. **Provide feedback:**
   - "Approved" or
   - "Change X because Y violates the design"

Your job is to ensure **architectural integrity**, not to write the code.

---

## Success Criteria

After your refactor:
1. ✅ User logs in → sees loading screen (0-30s depending on cache)
2. ✅ Loading completes → redirects to mine
3. ✅ Mine page renders 50 words INSTANTLY (no wait loop)
4. ✅ Console shows clean logs (no "waiting for vocabulary" messages)
5. ✅ Works on first install (no cache)
6. ✅ Works on version upgrade (4.0 → 5.0, auto-purges)
7. ✅ Works on repeat visits (instant, uses cache)

**Let's ship this. Show me the code.**

