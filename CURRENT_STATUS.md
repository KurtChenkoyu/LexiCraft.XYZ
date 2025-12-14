# LexiCraft Project Status

**Last Updated:** December 14, 2025  
**Status:** 🟢 Active Development - Emoji MVP Implementation

---

## 🎯 Emoji MVP (In Progress)

**Goal:** Simplified emoji matching game for young learners (ages 4-10)

### Current State
- ✅ 200 emoji vocabulary pack created (`emoji-core.json`)
- ✅ 1,908 audio files generated (9 voices × 200+ words)
- ✅ `EmojiMCQSession` component working
- ✅ Audio playback working (word pronunciations + SFX)
- ✅ Marketing landing page (`/emoji-fun`)
- ✅ Stripe payment integration (NT$99 family pack)
- 🔄 Player switcher (multi-child support) - **NEXT**
- ⏳ Tab skinning (emoji vs legacy mode)
- ⏳ Collection view
- ⏳ Family leaderboard

### Architecture Decision
**Same engine, different skin** - NOT a new app!
- Uses existing SRS, progress tracking, XP system
- UI conditionally renders based on `activePack`
- All children share one family subscription

### Documentation
See `landing-page/docs/EMOJI_MVP_PLAN.md` for full implementation plan

---

## 🚀 Bootstrap Frontloading Complete (December 14, 2025)

All pages now render **instantly** with zero loading spinners after the initial load!

### What Was Achieved

- ✅ **14-Step Bootstrap Service** - Pre-loads ALL page data into Zustand during loading screen
- ✅ **Mine Page** - Uses `mineBlocks` from Zustand (instant on tab switch)
- ✅ **Build Page** - Uses `currencies` + `rooms` from Zustand
- ✅ **Verification Page** - Uses `dueCards` from Zustand
- ✅ **Leaderboards Page** - Uses `leaderboardData` from Zustand + in-memory cache
- ✅ **Profile Page** - Uses `learnerProfile`, `achievements`, `goals` from Zustand
- ✅ **Family Page** - Uses `children`, `childrenSummaries` from Zustand
- ✅ **Progress Persistence** - Mine page correctly shows user's worked words across devices

### Technical Implementation

**Data Flow:**
```
Login → Loading Screen → Bootstrap (14 steps) → Zustand Store → Pages Render (instant!)
              ↓
        IndexedDB (offline cache)
```

**Bootstrap Steps:**
1. User Profile → `user`
2. Children → `children`
3. Children Summaries → `childrenSummaries`
4. Learner Profile → `learnerProfile`
5. Progress Stats → `progress`
6. Achievements → `achievements`
7. Goals → `goals`
8. Currencies → `currencies`
9. Rooms → `rooms`
10. Vocabulary → IndexedDB (29,738 senses)
11. Mine Blocks → `mineBlocks` (with progress status)
12. Due Cards → `dueCards`
13. Leaderboard → `leaderboardData`
14. Finalize → `isBootstrapped: true`

**Progress Handling (Critical for Persistence):**
- IndexedDB-first: Load local progress instantly (~10ms)
- Backend sync: Fetch fresh data with 5s timeout
- Starter pack: Regenerates if cached IDs don't match user's progress
- Status applied: Each block gets correct `hollow`/`solid`/`raw` status

**Page Pattern:**
```typescript
// ✅ CORRECT: Read from Zustand (instant!)
const data = useAppStore(selectData)
if (!isBootstrapped) return null // Layout shows loading screen
return <div>{data}</div> // Renders instantly!

// ❌ WRONG: Don't fetch in useEffect
useEffect(() => { fetch('/api/data')... }, []) // NEVER DO THIS
```

### Documentation

- `.cursorrules` - "Bootstrap Frontloading Strategy" section (full implementation guide)
- `landing-page/README.md` - High-level overview
- `landing-page/services/bootstrap.ts` - Source of truth for Bootstrap logic

### Performance Results

| Metric | Before | After |
|--------|--------|-------|
| Page switch delay | 1-5 seconds | **<100ms** |
| Loading spinners | On every page | **Loading screen only** |
| Tab switching | Re-fetches API | **Instant from Zustand** |
| Offline support | Broken | **Full offline** |

---

## 🎯 Phase 5: Layered Grid Mining Complete (December 10, 2025)

Mining is now a focused extraction experience with full persistence!

### Frontend Features (Phase 5a)

- ✅ **Colored Grid** - 6x6 mobile, 10x10 desktop status squares
- ✅ **Multi-select** - Batch mine with "Select All"
- ✅ **Detail Panel** - Slide-up info + drill down
- ✅ **Layer Navigation** - Explore 1-hop connections
- ✅ **Visual Feedback** - Particle effects on mine

### Backend Persistence (Phase 5b)

- ✅ **MineService.process_mining_batch()** - Batch processing in service layer
- ✅ **POST /api/v1/mine/batch** - API endpoint for mining
- ✅ **Database writes** - Creates `learning_progress` entries
- ✅ **Wallet updates** - Awards 10 XP per word, server-side validation
- ✅ **Optimistic sync** - Frontend updates instantly, backend reconciles

### The Complete Mining Flow

```
Survey → Layer 0 → Tap → Detail → Drill → Layer 1 → Mine
  ↓        ↓        ↓       ↓       ↓        ↓        ↓
Wrong   Grid     Panel   Info   Expand  Connections Store
                                                       ↓
                                                  Backend API
                                                       ↓
                                                  PostgreSQL
```

### Technical Implementation

**Frontend:**
- Grid renders instantly from Zustand (Layer 0 from starter pack)
- Colored squares show user status (raw/hollow/solid)
- Tap opens detail panel (mobile: slide-up, desktop: sidebar)
- Drill Down loads 1-hop connections using `vocabulary.getHopConnections()`
- Multi-select with checkboxes + "Select All" button
- Mine action updates Zustand instantly (+10 XP per word)
- Particle feedback animations on successful mining

**Backend:**
- `MineService.process_mining_batch()` creates `learning_progress` entries
- Validates no duplicates (idempotent)
- Awards points via `PointsTransaction` table
- Updates `PointsAccount` atomically
- Returns reconciled wallet balance

**Data Flow:**
1. User clicks "Mine Selected" → Zustand updates (instant)
2. Background: `gameService.mineBatch()` calls API
3. Backend: Creates DB entries + awards XP
4. Frontend: Reconciles wallet with server truth
5. If fails: User sees toast, eventual consistency maintained

**Performance:** All actions < 100ms (instant feel)

---

## 📚 Stage 3 Vocabulary Enrichment Complete (December 12, 2025)

The vocabulary data is now production-ready with comprehensive relationships, morphological forms, and collocations!

### What Was Added

- ✅ **Deep WordNet Extraction** - 15,358 derivations, 13,678 morphological forms, 5,503 similar relationships
- ✅ **Free Dictionary API Integration** - 716 synonyms, 191 antonyms added for common usage
- ✅ **Cascading Collocations** - 35,701 phrases (78.4% coverage via Datamuse API)
- ✅ **Broken Reference Fixer** - 4,314 broken references automatically fixed
- ✅ **Parallel Processing** - 5x speedup (44 minutes vs 5+ hours sequential)

### Final Statistics

- **Senses Processed:** 10,470 (100%)
- **Total Connections Added:** 37,951
- **Total Collocations Added:** 35,701
- **API Calls Made:** 10,178 (Free Dictionary) + 8,213 (Datamuse)
- **Zero API Errors:** 100% success rate

### Impact

Users can now:
- Drill down into complete word families (derivations, morphological forms)
- See comprehensive relationships (synonyms, antonyms, similar words, attributes)
- Discover common phrases and collocations for every word
- Navigate connections without encountering broken references

**See:** `backend/docs/STAGE3_ENRICHMENT.md` for full documentation.

---

## 🏗️ Workshop Enhancement Complete (December 10, 2025)

Added progression-based unlocking and customization to the Workshop!

### New Features

- ✅ **Locked Slot System** - Items unlock as you level up
- ✅ **Edit Mode** - Rearrange furniture layout
- ✅ **Progression Gates** - Level 1/3/5 unlock tiers
- ✅ **Visual Polish** - Locked states, swap feedback

### The Enhanced Loop

```
Mine (⛏️) → Verify (✅) → Build (🏗️) + Customize
  ↓            ↓             ↓        ↓
Instant      Instant       Instant  Instant
                                      └─ Edit Mode!
```

**See:** `WORKSHOP_ENHANCEMENT_COMPLETE.md` for details.

---

## 🎮 Batch 1 Migration: Core Loop Complete (December 10, 2025)

The main gameplay loop is now fully instant! All core pages migrated to Zustand architecture.

### What Was Completed (Batch 1)

- ✅ `/learner/verification` - Cache-first due cards display
- ✅ `/learner/build` - Instant level/XP from Zustand

### The Core Loop

```
Mine (⛏️) → Verify (✅) → Build (🏗️)
  ↓            ↓             ↓
Instant      Instant       Instant
```

**Performance:** Core loop is **30x faster** (1.5s → 50ms)

**See:** `BATCH1_COMPLETE_SUMMARY.md` for migration details.

---

## ⚡ Phase 3: The Live Wire Complete (December 10, 2025)

Components are now connected to the engine with smooth animations!

### What Was Built (Phase 3)

- ✅ **Page Transitions** (`learner/template.tsx`) - Framer Motion slide animations
- ✅ **Bottom Nav Enhancement** - Badge counts from Zustand
- ✅ **Home Page Migration** - Zero-latency reads from Zustand
- ✅ **Mine Page Optimization** - Instant progress stats from Zustand
- ✅ **UserDataContext Deprecation** - Marked for backward compatibility

### The Transformation

**Before:** Each component fetches data → spinners, no transitions  
**After:** Components read from Zustand → instant render, smooth slides

### Performance Wins

- Home page: **30x faster** (< 16ms vs 500ms)
- Mine page: **16x faster** (~50ms vs 800ms)
- Navigation: Native app feel (smooth spring animations)

**See:** `PHASE3_COMPLETE_SUMMARY.md` for migration patterns and testing guide.

---

## 🎨 Phase 2: Game Frame Complete (December 10, 2025)

The viewport is now locked! LexiCraft feels like a mobile game, not a scrolling webpage.

### What Was Built (Phase 2)

- ✅ **Global CSS Reset** - Locked viewport to `100dvh`, killed body scroll, disabled web defaults
- ✅ **Learner Top Bar** (`components/layout/LearnerTopBar.tsx`) - Persistent HUD showing wallet/streak
- ✅ **Game Frame Layout** (`learner/layout.tsx`) - Fixed viewport with Z-index layering
- ✅ **Conditional Navigation** - Learners get custom HUD, parents keep AppTopNav

### The Transformation

**Before:** Scrolling webpage with navigation that reloads  
**After:** Fixed game viewport with persistent HUD (z-40) over scrollable content (z-0)

### Architecture: Engine + Chassis

- ✅ **Phase 1 (Engine):** Zustand + Bootstrap + IndexedDB = Instant data
- ✅ **Phase 2 (Chassis):** Fixed viewport + HUD layering = Game feel

**See:** `PHASE2_COMPLETE_SUMMARY.md` for implementation details.

---

## 🎮 Phase 1: Game Engine Complete (December 10, 2025)

The "Last War" performance architecture is implemented! All critical data is pre-loaded at `/start` and stored in Zustand + IndexedDB for instant rendering.

### What Was Built (Phase 1)

- ✅ **Zustand Store** (`landing-page/stores/useAppStore.ts`) - Centralized state management
- ✅ **Bootstrap Service** (`landing-page/services/bootstrap.ts`) - Pre-loads all data before routing
- ✅ **Loading Screen** (`app/[locale]/(app)/start/page.tsx`) - Beautiful progress bar (0-100%)
- ✅ **Documentation** (`landing-page/docs/GAME_ENGINE.md`) - Complete architecture guide

### Performance Targets (✅ All Met)

| Metric | Target | Actual |
|--------|--------|--------|
| Bootstrap (cached) | < 2s | ~1.5s |
| Component render | < 16ms | Instant |
| Background sync | < 5s | ~3s |
| Offline mode | 100% | Works |

### Next Steps

**Phase 3:** Migrate existing components to use `useAppStore()` instead of `useEffect` fetchers

**See:** `PHASE1_COMPLETE_SUMMARY.md` for full details and testing guide.

---

## Major Architecture Update: Role-Based Route Groups (December 9, 2025)

The app structure has been refactored to separate Parent and Learner "worlds" using Next.js folder-based routing. See `.cursorrules` for the authoritative "Architecture Bible".

### New URL Structure

| Old URL | New URL | Notes |
|---------|---------|-------|
| /dashboard | /parent/dashboard | Tabbed: Overview, Analytics, Finance |
| /coach-dashboard | /parent/dashboard/analytics | Merged into dashboard tabs |
| /children | /parent/children | |
| /goals | /parent/goals | |
| /achievements | /parent/achievements | |
| /settings | /parent/settings | |
| /mine | /learner/mine | |
| /build | /learner/build | |
| /verification | /learner/verification | |
| /leaderboards | /learner/leaderboards | |
| /profile | /learner/profile | |
| /onboarding | /onboarding | Shared (no prefix) |
| /notifications | /notifications | Shared (no prefix) |
| N/A | /start | Traffic Cop - redirects by role |
| N/A | /learner/home | New learner landing page |

### Key Patterns Introduced

1. **Traffic Cop**: `/start` route checks user role and redirects to appropriate home
2. **Tabbed Dashboard**: Parent dashboard uses nested routes for tabs (Overview | Analytics | Finance)
3. **Role-specific Layouts**: `parent/layout.tsx` wraps ParentSidebar, `learner/layout.tsx` wraps BottomNav
4. **Middleware Redirects**: Old URLs are 301 redirected to new locations

### Reference Files

- `.cursorrules` - Architecture Bible (IMMUTABLE)
- `landing-page/app/[locale]/(app)/start/page.tsx` - Traffic Cop
- `landing-page/components/layout/DashboardTabs.tsx` - Tab navigation

---

## Major Design Update: Three-Currency Economy

A three-currency system has been finalized for the MVP:

| Currency | Symbol | Represents | Earned From | Used For |
|----------|--------|------------|-------------|----------|
| **Sparks** | ✨ | Effort | Any activity | Leveling → Energy |
| **Essence** | 💧 | Skill | Correct answers | Building requirement |
| **Blocks** | 🧱 | Vocabulary | Mastered words | Building materials |
| **Energy** | ⚡ | (Derived) | Level-up only | Powering builds |

**Key Design Decision:** Sparks → Energy conversion happens ONLY on level-up (fixed amount per level).

**Why Three Currencies:**
- You can't just grind (need Essence = skill)
- You can't just be smart (need Energy = effort)
- You can't skip mastery (need Blocks = retention)

**Level-Up Energy Rewards:**
| Level | Sparks Needed | Energy |
|-------|--------------|--------|
| 1→2 | 100 | 30⚡ |
| 2→3 | 150 | 50⚡ |
| 3→4 | 225 | 75⚡ |
| 4→5 | 337 | 100⚡ |
| 5+ | +50% | 125⚡ |

---

## MVP Scope: Two Rooms

**Study Room (書房):** Desk (5 lvl), Lamp (4), Chair (3), Bookshelf (4)  
**Living Room (客廳):** Plant (4), Coffee Table (3), TV (4), Sofa (4)

**Upgrade Cost Example (Desk) - "Popcorn Phase" tuned:**
| Level | Energy | Essence | Blocks | Notes |
|-------|--------|---------|--------|-------|
| 0→1 | FREE | FREE | - | Tutorial (repair) |
| 1→2 | 5⚡ | 2💧 | 0🧱 | Instant hook |
| 2→3 | 20⚡ | 10💧 | 1🧱 | First block gate |
| 3→4 | 40⚡ | 25💧 | 3🧱 | Mid game |
| 4→5 | 70⚡ | 45💧 | 6🧱 | ~2 weeks SRS |

**Documentation:**
- [35-minecraft-game-design.md](docs/35-minecraft-game-design.md) - Full design spec
- [36-mvp-roadmap.md](docs/36-mvp-roadmap.md) - Implementation plan
- [ADR-002-minecraft-game-model.md](docs/decisions/ADR-002-minecraft-game-model.md) - Decision record

---

## ✅ Completed Components

### 1. Landing Page
- **Status:** ✅ **DEPLOYED**
- **Location:** Vercel
- **Features:**
  - Multi-language support (English/Traditional Chinese)
  - Waitlist form
  - Survey integration ready
  - Professional design

### 2. Database Infrastructure
- **Neo4j:** ✅ Complete (Optional - used for enrichment only)
  - 3,500+ Word nodes loaded
  - 7,590+ Sense nodes (enriched with quiz data)
  - Relationships (synonyms, antonyms, confused_with)
  - Schema: V6.1 Frequency-Aware Architecture
- **VocabularyStore (JSON):** ✅ Complete (V3 - Primary runtime data source)
  - 10,470 senses in denormalized V3 format
  - Embedded connections (related, opposite, confused)
  - **Lemma-based indexing** (rebuilt from sense_ids at load time)
  - 8,792 unique lemmas indexed for instant lookup
  - 4,535 senses with CONFUSED_WITH relationships
  - No Neo4j dependency for MCQ generation
  - **December 2025 Fix:** `byWord` index now uses lemmas from sense_id, not `word` field
- **PostgreSQL (Supabase):** ✅ Complete
  - Unified user model
  - Learning progress tables
  - Verification schedule tables
  - MCQ pool and statistics
  - Gamification tables (XP, achievements, streaks)

### 3. Word Enrichment Pipeline
- **Status:** ✅ **Stage 3 Complete** (December 12, 2025)
- **Level 1 Content:** 35.2% (1,231/3,500 words)
- **Level 2 Content:** 100% complete (7,674 senses)
- **Stage 3 Enrichment:** ✅ **Complete** (10,470 senses enriched)
  - Deep WordNet extraction: 15,358 derivations, 13,678 morphological forms, 5,503 similar relationships
  - Free Dictionary API: 716 synonyms, 191 antonyms added
  - Collocations: 35,701 phrases (78.4% coverage via Datamuse)
  - Broken references fixed: 4,314
  - Total connections added: 37,951
- **Pipeline Status:** All phases working, production-ready vocabulary data

### 4. User Authentication
- **Status:** ✅ **Complete**
- **Features:**
  - Supabase Auth integration
  - JWT token verification
  - Auth middleware for API endpoints
  - Parent/child account management

### 5. LexiSurvey System
- **Backend:** ✅ Complete
- **Frontend:** ✅ Complete
- **Engine:** LexiSurvey V7.1 implemented

### 6. MCQ Verification System
- **Status:** ✅ **~95% Complete** (Enhanced December 2025)
- **Backend:** ✅ Complete
  - `backend/src/api/mcq.py` - Full API (1,100+ lines)
  - `POST /bundles` - Batch verification bundle endpoint for pre-caching
  - `backend/src/mcq_adaptive.py` - Adaptive selection service
  - `backend/src/mcq_assembler.py` - MCQ generation (V3: Enhanced for 8-15 MCQs per sense)
  - **20-30 distractor pool** with unique subsets per MCQ (expanded from 8)
  - 4-option and 6-option MCQ formats
  - Adaptive difficulty matching
  - Quality metrics (discrimination, difficulty index)
- **Frontend:** ✅ Complete
  - `MCQSession.tsx` - Cache-first loading (IndexedDB → API fallback)
  - `MCQCard.tsx` - Instant answer feedback using cached correct_index
  - Real-time gamification feedback
  - `bundleCacheService.ts` - Pre-cache verification bundles on Mine page load
- **Verification Bundle Pre-Cache:** ✅ Complete
  - Pre-caches MCQs for entire inventory in background (~2.5KB/sense)
  - Instant MCQ loading from IndexedDB (~10ms)
  - Optimistic answer feedback (no API wait for correct/incorrect)
  - Server submission in background for gamification
- **Integration:** ✅ Complete
  - FSRS/SM-2+ spaced repetition
  - Anti-gaming speed trap (< 1.5s = 0 XP)
  - One-shot payload for instant feedback
- **Enhancement Plan (December 2025):**
  - ✅ MCQ assembler enhanced for tiered MCQs (9-26 per sense based on usage)
  - ✅ Level 2 enrichment prompt updated with tiered examples
  - ✅ Verification bundle pre-caching for snappy experience
  - ✅ **Level 2 enrichment complete:** 7,447 senses with V3 tiered data
  - ✅ **MCQ generation complete:** 72,235 MCQs for 10,448 senses
    - MEANING: 55,772 | USAGE: 10,694 | DISCRIMINATION: 5,769
    - Senses with V3 data achieve 15-24 MCQs each
    - Average: 6.9 MCQs/sense (overall), higher for enriched senses

### 7. Spaced Repetition (FSRS/SM-2+)
- **Status:** ✅ **100% Complete**
- **Implementation:**
  - `backend/src/spaced_repetition/fsrs_service.py` - FSRS library wrapper (372 lines)
  - `backend/src/spaced_repetition/algorithm_interface.py` - Abstract interface for both algorithms
  - `backend/src/spaced_repetition/assignment_service.py` - A/B testing assignment (392 lines)
  - `backend/migrations/011_fsrs_support.sql` - Database schema (384 lines)
- **Features:**
  - ✅ FSRS algorithm (machine learning-based, 20-30% fewer reviews)
  - ✅ SM-2+ algorithm (rule-based fallback)
  - ✅ A/B testing: Random 50/50 assignment for new users
  - ✅ Migration support: Users with 100+ reviews can migrate to FSRS
  - ✅ Algorithm comparison analytics
  - ✅ Review history tracking (`fsrs_review_history` table)
  - ✅ Mastery progression tracking
  - ✅ CardState abstraction (works with both algorithms)

### 8. Gamification System
- **Status:** 🟡 **Implementing Three-Currency MVP**
- **Completed (v1 - Legacy):**
  - XP and leveling system ✅
  - Daily streaks with multipliers ✅
  - Achievement system ✅
  - StudyDesk component ✅
- **MVP (v2 - In Progress):**
  - [ ] Sparks tracking (effort currency)
  - [ ] Essence tracking (skill currency)
  - [ ] Energy tracking (from level-ups)
  - [ ] Blocks tracking (mastered words)
  - [ ] Item blueprints table
  - [ ] User items table
  - [ ] /build page with 2 rooms
  - [ ] Item upgrade flow
- **Post-MVP (Planned):**
  - [ ] Decay visualization (cracking blocks)
  - [ ] Enchanting system (word mastery depth)
  - [ ] Villager quests (semantic clustering)
  - [ ] Crafting recipes (grammar/syntax)
  - [ ] Nether mode (real-world content)

---

## 🟡 In Progress

### Word Enrichment (Background)
- **Level 1:** 35.2% complete (1,231/3,500 words)
- Can continue in background

### Verification Flow Integration
- Survey → Verification flow needs connection
- Word explorer/discovery interface

---

## ❌ Not Started / Pending

### 1. Withdrawal System
- **Status:** ❌ Not implemented
- **Needed For:** Financial flow
- **Priority:** Medium (can be manual for MVP)

### 2. Parent Dashboard Analytics
- **Status:** ⚠️ Basic exists, needs enhancement
- **Needed For:** Parent engagement

### 3. Word Explorer Interface
- **Status:** ❌ Not implemented
- **Needed For:** Word discovery/selection

---

## Progress Summary

| Component | Status | Progress |
|-----------|--------|----------|
| Landing Page | ✅ Deployed | 100% |
| Database (Neo4j) | ✅ Complete | 100% |
| Database (PostgreSQL) | ✅ Complete | 100% |
| Word Enrichment L1 | 🟡 In Progress | 35% |
| Word Enrichment L2 | ✅ Complete | 100% |
| Word Enrichment Stage 3 | ✅ Complete | 100% |
| User Auth | ✅ Complete | 100% |
| LexiSurvey | ✅ Complete | 100% |
| MCQ System | ✅ Complete | 95% |
| Spaced Repetition | ✅ Complete | 100% |
| Gamification (v1) | ✅ Complete | 100% |
| **Three-Currency System** | ✅ Backend + API | 80% |
| **Two Rooms MVP** | ✅ Components + Page | 80% |
| Withdrawal System | ❌ Deferred | 0% |

**Foundation Complete:** ~90%  
**MVP Sprint:** Day 8/10 - Mobile testing remaining

### What's Complete (This Session)
- Migration file `017_three_currency_system.sql`
- `CurrencyService` with Sparks → Energy level-up logic
- `/api/v1/currencies` and `/api/v1/items` endpoints
- `FurnitureItem.tsx` (generic reusable component)
- `Room.tsx`, `RoomSwitcher.tsx`, `CurrencyBar.tsx`
- `UpgradeModal.tsx`, `LevelUpModal.tsx`, `BlockMasteryAnimation.tsx`
- `/build` page with room switching
- MCQ submit now awards Sparks + Essence

---

## Recommended Next Steps

### IMMEDIATE: Execute MVP Sprint (2 weeks)
See [36-mvp-roadmap.md](docs/36-mvp-roadmap.md) for detailed plan.

**Day 1-2 (NOW):** Create currency backend
1. Add Sparks/Essence/Energy/Blocks columns to user_xp
2. Create `backend/src/services/currencies.py`
3. Create `backend/src/api/currencies.py`
4. Update MCQ submit to award currencies

**Day 3-5:** Frontend components
1. BaseItem component (reusable)
2. Room components (Study + Living)
3. /build page

**Day 6-10:** Integration + Polish
1. MCQ → Currency flow
2. Item upgrade flow
3. Mobile testing

### Post-MVP
- Decay visualization
- More rooms/items
- Enchanting system

---

## 📚 Key Documentation

### Game Design (NEW)
- `/docs/35-minecraft-game-design.md` - **Core game design spec**
- `/docs/decisions/ADR-002-minecraft-game-model.md` - Design decision record
- `/docs/30-ux-vision-game-design.md` - Original UX vision (foundation)

### Architecture
- `/docs/04-technical-architecture.md`
- `/backend/docs/core-verification-system/` - MCQ & verification docs

### Gamification
- `/backend/docs/gamification/` - XP, achievements, streaks

### Development
- `/docs/development/` - Development guides and handoffs

### API Reference
- Backend runs on FastAPI with auto-docs at `/docs`

---

## 🗂️ Project Organization

Per `.cursorrules`, documentation is organized as:
- `/docs/` - Project-wide documentation
- `/backend/docs/` - Backend-specific implementation notes
- `/landing-page/docs/` - Frontend-specific notes
- `/docs/archive/` - Archived/superseded documentation

---

**Next Action:** Execute MVP Roadmap - See [36-mvp-roadmap.md](docs/36-mvp-roadmap.md)

---

## MVP Roadmap (2 Weeks)

**Goal:** Test core hypothesis with 10 users - "Do users care about building/owning, or just want money?"

### Week 1: Backend + Components
| Day | Task | Status |
|-----|------|--------|
| 1-2 | Currency backend (Sparks/Essence/Energy/Blocks) | ✅ Complete |
| 3 | BaseItem component + item configs | ✅ Complete |
| 4 | Room components (Study + Living) | ✅ Complete |
| 5 | /build page with room switching | ✅ Complete |

### Week 2: Integration + Polish
| Day | Task | Status |
|-----|------|--------|
| 6 | MCQ → Currency integration | ✅ Complete |
| 7 | Level-up Energy modal | ✅ Complete |
| 8 | Item upgrade flow | ✅ Complete |
| 9 | Mobile polish + testing | 🟡 In Progress |
| 10 | Test user preparation | ❌ |

**Full details:** [MVP Roadmap](docs/36-mvp-roadmap.md)
