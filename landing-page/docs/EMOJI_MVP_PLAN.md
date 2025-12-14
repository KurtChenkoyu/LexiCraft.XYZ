# 🎯 Emoji Pack MVP - Implementation Plan

> **Last Updated:** December 2024
> **Status:** Planning → Implementation

## Overview

**Goal:** Skin the existing app for emoji pack mode, NOT build a new app.

**Key Principle:** Same backend, same data flow, different UI based on `activePack`.

---

## 1. Architecture Decision

```
┌─────────────────────────────────────────────────────────┐
│                    SHARED INFRASTRUCTURE                │
│  • SRS (verification_schedule)                          │
│  • Progress (learning_progress)                         │
│  • XP/Currency system (Delta Strategy)                  │
│  • Achievements                                         │
│  • Per-child profiles (learner_id)                      │
│  • Bootstrap frontloading                               │
│  • IndexedDB caching ("Last War" pattern)               │
└─────────────────────────────────────────────────────────┘
              │                           │
              ▼                           ▼
    ┌─────────────────┐         ┌─────────────────┐
    │   LEGACY MODE   │         │   EMOJI MODE    │
    │  (Full vocab)   │         │  (200 emojis)   │
    ├─────────────────┤         ├─────────────────┤
    │ Complex Mine    │         │ Emoji Grid      │
    │ Room Builder    │         │ Collection View │
    │ Full MCQ        │         │ Matching Game   │
    │ Individual Rank │         │ Family Rank     │
    └─────────────────┘         └─────────────────┘
```

---

## 2. Data Strategy (CRITICAL)

### Follow "Last War" Pattern

All emoji progress MUST follow the established caching strategy:

```
1. CACHE FIRST
   └─> Read from IndexedDB instantly
   
2. OPTIMISTIC UPDATE  
   └─> Apply delta to local state immediately
   └─> User sees instant feedback
   
3. BACKGROUND SYNC
   └─> Batch sync to backend
   └─> Reconcile on next session
```

### Delta Strategy for Emoji Progress

```typescript
// On correct answer:
applyDelta({
  delta_xp: 5,
  delta_sparks: 2,
  // Progress update queued for batch sync
})

// Progress saved to IndexedDB immediately
// Backend sync happens in background
```

---

## 3. Player Context System

### Who Can Play?

| Player | Can Play | Notes |
|--------|----------|-------|
| Parent | ✅ Yes | Parent can learn too! |
| Child (added) | ✅ Yes | Primary use case |
| Child (not added) | ⚠️ Prompt | "Ask your parent to add you!" |

### New State: `activePlayer`

```typescript
// In useAppStore.ts
activePlayer: {
  id: string           // learner_id (child OR parent)
  name: string
  avatar?: string
  type: 'parent' | 'child'
} | null

setActivePlayer: (player) => void
clearActivePlayer: () => void
```

### Flow:

```
Parent logs in
    │
    ├─> Has children? 
    │       │
    │       ├─> Yes: Show player selector
    │       │       "Who's playing today?"
    │       │       [👧 Amy] [👦 Ben] [👨 Me (Parent)]
    │       │
    │       └─> No: Show prompt
    │               "Add your children to track their progress!"
    │               [Add Child] [Play as Parent]
    │
    └─> Player selected → activePlayer set → App shows that player's data
```

### No Children Added - UX

If a child is using a parent's device but not added:

```
┌─────────────────────────────────────────┐
│  👋 Hi there!                           │
│                                         │
│  Want to save your progress?            │
│  Ask your parent to add you!            │
│                                         │
│  [▶️ Play as Guest]  [👨‍👩‍👧 Add Me!]        │
└─────────────────────────────────────────┘
```

- "Play as Guest" → Uses parent's profile (progress saved to parent)
- "Add Me!" → Opens child creation flow for parent

---

## 4. Pack Selector (IMPORTANT)

Even though additional packs are out of scope, the **pack selector infrastructure** is critical for:
- Switching between emoji and legacy mode
- Future pack expansion
- Per-child pack preferences

### Pack Selector Location

**Global (Top Nav)** - Available on all pages

```
┌──────────────────────────────────────────────────────┐
│ [🎯 ▼]  [👧 Amy ▼]            ⭐156  🔥5  💰1250   │
└──────────────────────────────────────────────────────┘
     │         │
     │         └─> Player Switcher
     │
     └─> Pack Selector Dropdown
         ┌────────────────────┐
         │ 🎯 Core Emoji  ✓   │
         │ 📚 Full Vocab      │
         │ ─────────────────  │
         │ 🔒 More packs...   │
         └────────────────────┘
```

### Pack Selection Logic

```typescript
// When pack changes:
1. Save preference to activePlayer's profile
2. Clear pack-specific cached data
3. Reload appropriate vocabulary
4. Re-render tabs with correct skin
```

---

## 5. Tab Behavior by Mode

| Tab | Legacy Mode | Emoji Mode |
|-----|-------------|------------|
| 礦區 (Mine) | `<MinePage />` | `<EmojiCollectionGrid />` |
| 建造 (Build) | `<BuildPage />` | `<EmojiShowcase />` |
| 驗證 (Verify) | `<MCQSession />` | `<EmojiMCQSession />` |
| 排行 (Rank) | `<Leaderboard />` | `<FamilyLeaderboard />` |
| 家庭 (Family) | `<FamilyPage />` | Same (manage kids) |
| 我的 (Profile) | `<ProfilePage />` | Same (pack-relevant stats) |

### Conditional Rendering Pattern

```typescript
// In each tab page:
const activePack = useAppStore(selectActivePack)
const isEmojiPack = activePack?.id === 'emoji_core'

if (isEmojiPack) {
  return <EmojiVersionComponent />
}
return <LegacyVersionComponent />
```

---

## 6. New Components

### 6.1 `PlayerSwitcher`
**File:** `components/layout/PlayerSwitcher.tsx`

- Dropdown showing all family members
- Current player highlighted
- Player stats display (XP, streak, coins)
- "Add Child" option at bottom

### 6.2 `EmojiCollectionGrid`
**File:** `components/features/emoji/EmojiCollectionGrid.tsx`

- 200 emoji grid with status indicators
- Status: 📦 new → 🔥 learning → ✨ reviewing → 💎 mastered
- Tap to quiz functionality
- Category filters
- Progress bar

### 6.3 `EmojiShowcase`
**File:** `components/features/emoji/EmojiShowcase.tsx`

- Animated collected emojis
- Mastered = sparkle animation (user-provided assets)
- Trophy room feel
- Category shelves

### 6.4 `FamilyLeaderboard`
**File:** `components/features/emoji/FamilyLeaderboard.tsx`

- Family combined/average score
- Per-child breakdown
- Sibling competition
- Weekly/monthly views

---

## 7. File Changes Summary

### Store (`stores/useAppStore.ts`)
```typescript
// ADD:
activePlayer: { id, name, type } | null
setActivePlayer: (player) => void
clearActivePlayer: () => void

// EXISTING (keep):
activePack
setActivePack
```

### Top Nav (`components/layout/LearnerTopBar.tsx`)
- Add `<PlayerSwitcher />`
- Show `activePlayer` stats

### Tab Pages
Each tab checks `isEmojiPack` and renders appropriate component.

---

## 8. Implementation Phases

### Phase 1: Player Context ⬅️ START HERE
- [ ] Add `activePlayer` to store
- [ ] Create `PlayerSwitcher` component  
- [ ] Player selection on app entry
- [ ] Pass `activePlayer.id` to data fetches

### Phase 2: Pack Selector Enhancement
- [ ] Move pack selector to top nav
- [ ] Per-player pack preference
- [ ] Pack switching clears/reloads data

### Phase 3: Mine Tab (Collection Grid)
- [ ] Create `EmojiCollectionGrid`
- [ ] Conditional render in Mine page
- [ ] Load progress for `activePlayer`
- [ ] Tap-to-quiz

### Phase 4: Verification Integration  
- [ ] `EmojiMCQSession` uses `activePlayer.id`
- [ ] Progress saves to correct profile
- [ ] Delta strategy for updates

### Phase 5: Build Tab (Showcase)
- [ ] Create `EmojiShowcase`
- [ ] Integrate animated assets
- [ ] Category display

### Phase 6: Ranking (Family)
- [ ] Create `FamilyLeaderboard`
- [ ] Aggregate scores
- [ ] Per-child view

---

## 9. SRS Integration

Emoji pack uses the SAME SRS system:

```
Backend Tables (existing):
- learning_progress (sense_id, learner_id, status, mastery_level)
- verification_schedule (next_review_date, interval)

Emoji words just have sense_ids like: "apple.emoji.01"
SRS treats them exactly like regular vocabulary.
```

### Due Cards for Emoji

```typescript
// Bootstrap already loads due cards
// Just filter for emoji pack sense_ids
const emojiDueCards = dueCards.filter(card => 
  card.sense_id.includes('.emoji.')
)
```

---

## 10. Audio Integration

Audio files already exist at `/audio/emoji/{word}_{voice}.mp3`

```typescript
// On correct answer:
audioService.playCorrect()  // Beep sound
audioService.playWord(word, 'emoji')  // Word pronunciation

// Speaker button in quiz:
<button onClick={() => audioService.playWord(word, 'emoji')}>🔊</button>
```

---

## 11. Offline Support

Following Last War pattern:

```
IndexedDB stores:
- Emoji pack vocabulary (200 words)
- Player's progress per word
- Pending delta updates

On reconnect:
- Batch sync pending updates
- Reconcile with server truth
```

---

## 12. Questions Resolved

| Question | Answer |
|----------|--------|
| Can parent play? | ✅ Yes, parent is a valid player |
| No children added? | Prompt: "Ask parent to add you!" with guest option |
| Progress persistence? | Delta strategy (optimistic + batch sync) |
| Offline? | Last War pattern (cache first, sync later) |

---

## 13. Out of Scope (Future)

- Additional emoji packs (Food, Nature, Emotions)
- Cross-device push notifications
- Social sharing
- Parent analytics deep-dive
- Pack marketplace

---

## 14. Success Metrics

- [ ] Player can switch between family members
- [ ] Progress is tracked per-player
- [ ] SRS works for emoji words
- [ ] Audio plays on quiz
- [ ] Collection view shows mastery status
- [ ] Works offline
- [ ] Syncs on reconnect

---

## Related Documentation

- `DELTA_STRATEGY.md` - **CRITICAL:** Complete guide to optimistic updates, batch sync, and reconciliation
- `ARCHITECTURE_PRINCIPLES.md` - Caching strategy
- `CACHING_RULES.md` - Last War pattern
- `.cursorrules` - Bootstrap frontloading
- `AUDIO_HANDOFF.md` - Audio file specs

