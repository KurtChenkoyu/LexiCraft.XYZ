# LexiCraft MVP Roadmap

**Updated:** December 8, 2025 01:30 AM  
**Target:** 2-3 weeks to testable MVP  
**Goal:** Validate the core hypothesis before building everything

---

## MVP Definition

### The Core Hypothesis
> "If we make vocabulary learning feel like building something you OWN, users will be intrinsically motivated to learn more."

### Success Metric
After 10 users complete 1 week of testing:
- **Win:** Users ask "How do I upgrade my desk?" or show off their progress
- **Lose:** Users ask "Where is my money?" or disengage after initial novelty

### MVP Scope: "Two Rooms" Test
We need **2 rooms with 8 items total** to demonstrate the concept isn't "just one item":

**Study Room (書房):** Desk, Lamp, Chair, Bookshelf  
**Living Room (客廳):** Plant, Coffee Table, TV, Sofa

---

## Three-Currency Economy

The MVP uses three distinct currencies:

| Currency | Symbol | How Earned | How Spent |
|----------|--------|------------|-----------|
| **Sparks** | ✨ | ANY activity (even wrong answers) | Leveling → Energy |
| **Essence** | 💧 | Correct MCQ answers | Building requirement |
| **Blocks** | 🧱 | Mastering words (Solid) | Building materials |

### Sparks → Energy Conversion (Level Up)

| Level | Sparks Needed | Energy Earned |
|-------|--------------|---------------|
| 1 → 2 | 100 | 30 ⚡ |
| 2 → 3 | 150 | 50 ⚡ |
| 3 → 4 | 225 | 75 ⚡ |
| 4 → 5 | 337 | 100 ⚡ |
| 5+ | +50% | 125 ⚡ |

### Activity Rewards

| Activity | Sparks ✨ | Essence 💧 |
|----------|----------|-----------|
| View word | +1 | - |
| Start MCQ | +2 | - |
| Wrong answer | +1 | - |
| Correct answer | +5 | +1 |
| Fast + Correct | +8 | +2 |
| Pass review | +3 | +1 |
| Word → Solid | +10 | +1 Block |

### Item Upgrade Costs (Tuned for "Popcorn Phase")

**Design Principle:** First upgrades are CHEAP to hook users fast, then costs scale up.

| Level | Energy ⚡ | Essence 💧 | Blocks 🧱 | Design Notes |
|-------|---------|-----------|----------|--------------|
| 1 → 2 | 5 | 2 | 0 | "Popcorn" - instant gratification |
| 2 → 3 | 20 | 10 | 1 | First block requirement |
| 3 → 4 | 40 | 25 | 3 | Mid commitment |
| 4 → 5 | 70 | 45 | 6 | Significant achievement |

**Lighter items (Chair, Plant, Coffee Table):** 60% of Desk costs  
**Heavier items (Bookshelf, Sofa, TV):** 120% of Desk costs

### Starter Pack (Pre-Installed)

New users start with **broken/dirty** versions of:
- 🪑 Desk (Level 0 - "Cardboard Box")
- 💡 Lamp (Level 0 - "Bare Bulb")

**First Tutorial:** "Repair your desk!" (L0→L1 costs 0 - free tutorial)

This is psychologically better than empty room → buying. "Fixing" feels rewarding.

### Future Mechanic: Essence Synthesizer

**Problem:** Smart kids may accumulate 5,000 Essence but have no Blocks (SRS is slow).

**Future Solution (Post-MVP):** "Synthesizer" machine
- Convert 100 Essence → 50 Sparks
- Prevents dead currency buildup
- NOT in MVP - just noted for future

**Key insight:** You can't just grind. You need:
- Energy (from leveling → requires activity)
- Essence (from correct answers → requires skill)
- Blocks (from mastering words → requires retention)

---

## Current Status Audit

### Complete (No Work Needed)
| Component | Status | Notes |
|-----------|--------|-------|
| Landing Page | Done | Waitlist working |
| Database (PostgreSQL) | Done | All tables ready |
| User Auth | Done | Supabase integrated |
| MCQ System | Done | Core flow working |
| Spaced Repetition | Done | FSRS + SM-2+ |
| Study Desk Component | Done | 5 levels, animations |
| One-Shot Payload | Done | Instant feedback |

### Needs Work (MVP Critical)
| Component | Current | Needed | Effort |
|-----------|---------|--------|--------|
| Three-Currency Backend | None | Sparks/Essence/Energy tracking | 1.5 days |
| Building Tables | None | Items, blueprints, user_items | 0.5 day |
| Building API | None | GET/POST items, upgrade endpoint | 1 day |
| BaseItem Component | None | Reusable item with levels | 1 day |
| Room Components | None | Study Room + Living Room | 1 day |
| Build Page | None | /build with room switching | 1 day |
| Currency UI | None | Display + level-up modal | 0.5 day |
| Integration | None | Connect MCQ → currencies → items | 1 day |
| Mobile Polish | Partial | Test on phones | 1 day |

### Defer (Post-MVP)
| Component | Why Defer |
|-----------|-----------|
| Withdrawal System | Manual for 10 test users |
| Decay/Creeper | Adds complexity before validation |
| Enchanting/Crafting/Villagers | Post-validation features |
| Parent Dashboard Analytics | Basic stats sufficient |

---

## Two-Week Sprint Plan

### Week 1: Backend + Core Components

#### Day 1-2: Three-Currency Backend
**Goal:** Track Sparks, Essence, Energy, Blocks

**Database additions:**
```sql
-- User currencies (add columns to user_xp or new table)
ALTER TABLE user_xp ADD COLUMN sparks INT DEFAULT 0;
ALTER TABLE user_xp ADD COLUMN essence INT DEFAULT 0;
ALTER TABLE user_xp ADD COLUMN energy INT DEFAULT 0;
ALTER TABLE user_xp ADD COLUMN solid_blocks INT DEFAULT 0;

-- Items and blueprints
CREATE TABLE item_blueprints (
    id UUID PRIMARY KEY,
    code VARCHAR(50) UNIQUE,
    name VARCHAR(100),
    room VARCHAR(50),  -- 'study', 'living'
    max_level INT DEFAULT 5,
    base_emoji TEXT[],  -- Array of emoji per level
    upgrade_energy INT[],
    upgrade_essence INT[],
    upgrade_blocks INT[]
);

CREATE TABLE user_items (
    user_id UUID REFERENCES auth.users(id),
    blueprint_id UUID REFERENCES item_blueprints(id),
    current_level INT DEFAULT 1,
    upgraded_at TIMESTAMPTZ,
    PRIMARY KEY (user_id, blueprint_id)
);
```

**API endpoints:**
```
GET  /api/v1/currencies  → { sparks, level, energy, essence, blocks }
POST /api/v1/items/upgrade → { success, item, currencies_after }
```

**Services to create/modify:**
- `backend/src/services/currencies.py` - New
- `backend/src/services/levels.py` - Add energy on level-up
- `backend/src/api/currencies.py` - New
- `backend/src/api/items.py` - New

#### Day 3: BaseItem Component
**Goal:** Reusable item component for all furniture

```tsx
// landing-page/components/features/building/BaseItem.tsx
interface Props {
  emoji: string
  level: number
  maxLevel: number
  name: string
  colors: { primary: string, secondary: string, glow?: string }
  showProgress?: boolean
  progress?: { current: number, required: number }
  size?: 'sm' | 'md' | 'lg'
}
```

**Items to configure:**
- Desk (existing, refactor)
- Lamp, Chair, Bookshelf (Study Room)
- Plant, CoffeeTable, TV, Sofa (Living Room)

#### Day 4: Room Components
**Goal:** Study Room + Living Room with item placement

```tsx
// StudyRoom.tsx - 4 items in grid layout
// LivingRoom.tsx - 4 items in grid layout
// RoomSwitcher.tsx - Tab to switch between rooms
```

#### Day 5: Build Page + Currency UI
**Goal:** /build page with room switching and currency display

```
/build page:
├── CurrencyBar (top): ✨ Sparks (Lvl X) | ⚡ Energy | 💧 Essence | 🧱 Blocks
├── RoomSwitcher: [Study Room] [Living Room]
├── Current Room: Grid of items
└── Selected Item: Upgrade modal with cost breakdown
```

---

### Week 2: Integration + Polish

#### Day 6: MCQ → Currency Integration
**Goal:** MCQs award Sparks + Essence correctly

**Flow:**
```
1. User answers MCQ
2. Backend calculates: +5 Sparks, +1 Essence (if correct)
3. Check for level-up: If yes, +Energy based on level
4. Check for word mastery: If Solid, +1 Block
5. Return all in One-Shot Payload
```

**Files to modify:**
- `backend/src/api/mcq.py` - Add currency updates
- `landing-page/services/mcqApi.ts` - Handle currency response
- `landing-page/components/features/mcq/MCQCard.tsx` - Show currency feedback

#### Day 7: Level-Up Energy Modal
**Goal:** Celebrate level-up with Energy reward

```tsx
// On level-up, show modal:
// "🎉 Level 5!"
// "You earned 100 ⚡ Energy!"
// [Claim] button → adds to energy balance
```

#### Day 8: Item Upgrade Flow
**Goal:** Complete upgrade flow with currency deduction

```
1. Click item in room
2. Modal shows: Current level, next level preview
3. Cost breakdown: 35⚡ + 15💧 + 2🧱
4. "Upgrade" button (disabled if can't afford)
5. On success: Animation, item upgrades, balances update
```

#### Day 9: Mobile Polish + Testing
**Goal:** Works on phones, full flow tested

**Test script:**
```
1. Create account → Complete survey
2. Do 10 MCQs (track Sparks + Essence)
3. Level up → Check Energy granted
4. Master 2 words → Check Blocks granted
5. Go to /build → Try upgrading Desk
6. Verify currency deduction
7. Test on iPhone + Android
```

#### Day 10: Bug Fixes + Test User Prep
**Goal:** Ready for 10 test users

**Tasks:**
1. Fix any bugs from Day 9
2. Create test accounts with various states
3. Write onboarding doc
4. Set up feedback survey

---

## Detailed Task Breakdown

### Backend: Currency Service

```python
# backend/src/services/currencies.py
class CurrencyService:
    LEVEL_ENERGY_REWARDS = {
        2: 30, 3: 50, 4: 75, 5: 100, 6: 125  # 6+ all get 125
    }
    
    async def get_currencies(self, user_id: str) -> dict:
        """Get all currency balances for user."""
        
    async def add_sparks(self, user_id: str, amount: int, reason: str) -> dict:
        """Add sparks, check for level-up, grant energy if leveled."""
        
    async def add_essence(self, user_id: str, amount: int) -> dict:
        """Add essence (from correct answers)."""
        
    async def add_block(self, user_id: str) -> dict:
        """Add solid block (from mastering a word)."""
        
    async def spend_currencies(self, user_id: str, energy: int, essence: int, blocks: int) -> dict:
        """Attempt to spend currencies. Raise if insufficient."""
```

### Backend: Items Service

```python
# backend/src/services/items.py
class ItemService:
    async def get_user_items(self, user_id: str) -> list[dict]:
        """Get all items and their levels for user."""
        
    async def upgrade_item(self, user_id: str, item_code: str) -> dict:
        """Upgrade item if user can afford it."""
        # 1. Get item blueprint
        # 2. Get upgrade cost for next level
        # 3. Check user currencies
        # 4. Deduct currencies
        # 5. Increment item level
        # 6. Return updated state
```

### Frontend: Component Hierarchy

```
/build page
├── CurrencyBar
│   ├── SparksBadge (level + progress)
│   ├── EnergyBadge
│   ├── EssenceBadge
│   └── BlocksBadge
├── RoomSwitcher
│   ├── Tab: Study Room
│   └── Tab: Living Room
├── Room (current)
│   ├── BaseItem (Desk)
│   ├── BaseItem (Lamp)
│   ├── BaseItem (Chair)
│   └── BaseItem (Bookshelf)
└── UpgradeModal (when item selected)
    ├── Current vs Next preview
    ├── Cost breakdown
    └── Upgrade button
```

### Item Definitions (Seed Data)

```typescript
const ITEMS = {
  study: [
    { code: 'desk', name: 'Study Desk', emoji: ['📦','🪑','📚','💼','🚀'], maxLevel: 5, starter: true },
    { code: 'lamp', name: 'Desk Lamp', emoji: ['💡','🔦','🪔','✨'], maxLevel: 4, starter: true },
    { code: 'chair', name: 'Chair', emoji: ['🪑','🛋️','👑'], maxLevel: 3 },
    { code: 'bookshelf', name: 'Bookshelf', emoji: ['📖','📚','📕','🏛️'], maxLevel: 4 },
  ],
  living: [
    { code: 'plant', name: 'Plant', emoji: ['🌱','🌿','🪴','🌳'], maxLevel: 4 },
    { code: 'coffee_table', name: 'Coffee Table', emoji: ['🫖','☕','🍵'], maxLevel: 3 },
    { code: 'tv', name: 'TV', emoji: ['📺','🖥️','📽️','🎬'], maxLevel: 4 },
    { code: 'sofa', name: 'Sofa', emoji: ['🛋️','🛏️','👑','🏰'], maxLevel: 4 },
  ]
}
```

### Critical UX: Block Mastery Animation

When a user masters a word and earns a Block, this is the **"Diamond Moment"**.

**Must be HUGE:**
- 3D cube spinning animation
- Flying into inventory
- Sound effect (if enabled)
- Screen shake or particle burst
- "+1 🧱 BLOCK!" banner

This is the payoff for 7-10 days of SRS work. Don't undersell it.

### Component Architecture Warning

**DO NOT** create separate files:
- ❌ `Lamp.tsx`, `Chair.tsx`, `Desk.tsx`

**DO** create generic component:
- ✅ `<FurnitureItem config={ITEMS.study.desk} level={3} />`

This prevents maintenance nightmare when adding Kitchen/Bedroom later.

---

## MVP Feature Matrix

| Feature | MVP | v1.1 | v2.0 |
|---------|-----|------|------|
| Three currencies | ✅ Sparks/Essence/Blocks | Emeralds (premium) | Trading |
| Two rooms | ✅ Study + Living | Kitchen + Bedroom | Full house |
| 8 items | ✅ 4 per room | More variants | Custom items |
| Level-up Energy | ✅ Fixed per level | Bonus events | Daily energy |
| MCQ → Currency | ✅ Sparks + Essence | Combo bonuses | Speed bonuses |
| Item upgrades | ✅ Click to upgrade | Craft to unlock | Enchanting |
| Currency UI | ✅ Bar + modal | Animated | Sound effects |
| Word browsing | ✅ Simple grid | Search + filter | Graph viz |
| Streaks | ✅ Display | Freeze purchase | Social |
| Decay | ❌ | Warning only | Visual cracking |
| Parent view | ❌ | Basic stats | Analytics |
| Withdrawal | ❌ | Manual | Automated |

---

## 🧪 Test User Criteria

### Ideal Test Users (10 total)
- **4x** Kids (10-14 years old) with parent supervision
- **3x** High school students (15-18)
- **3x** Adults learning English

### Feedback Questions
1. "What was your favorite part?"
2. "Did you notice your desk changing?"
3. "What would make you want to come back tomorrow?"
4. "Would you show this to a friend?"
5. "What was confusing or frustrating?"

### Success Signals
- ✅ Users mention the desk unprompted
- ✅ Users complete 5+ days in a row
- ✅ Users ask about getting to the next desk level
- ✅ Users show screenshots to others

### Failure Signals
- ❌ Users ask "When do I get paid?"
- ❌ Users quit after day 2-3
- ❌ Users don't notice desk changes
- ❌ Users say "It's just flashcards with extra steps"

---

## Timeline Summary

| Week | Days | Focus | Deliverable |
|------|------|-------|-------------|
| 1 | 1-2 | Backend | Currency + Items services + API |
| 1 | 3 | Components | BaseItem + item configs |
| 1 | 4 | Rooms | StudyRoom + LivingRoom |
| 1 | 5 | Build Page | /build with room switching |
| 2 | 6 | Integration | MCQ → Currencies flow |
| 2 | 7 | Level-up | Energy modal + animations |
| 2 | 8 | Upgrades | Item upgrade flow |
| 2 | 9 | Mobile | Polish + testing |
| 2 | 10 | Prep | Test users ready |

**Total: 10 working days (2 weeks)**

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Currency backend complex | Delays integration | Start here, block everything else |
| Item upgrade feels clunky | Bad UX | Polish animations early |
| Mobile layout breaks | Bad UX for kids | Allocate full day |
| Three currencies confusing | Users overwhelmed | Clear UI labels + tutorial |
| Low test user engagement | Inconclusive | Offer small incentive |

---

## 🚀 Post-MVP Roadmap (If Validated)

### v1.1 (Week 3-4)
- Full blueprint system (build a room)
- Decay warnings (review reminders)
- Basic XP shop
- Parent progress emails

### v1.2 (Week 5-6)
- Multiple structures (desk → bookshelf → room)
- Enchanting (deep word mastery)
- Social sharing

### v2.0 (Month 2+)
- Full Minecraft model
- Crafting (grammar)
- Villager quests
- Nether mode
- Withdrawal system

---

## Definition of Done (MVP)

- [ ] Three currencies tracked in backend (Sparks, Essence, Energy, Blocks)
- [ ] MCQs correctly award Sparks + Essence
- [ ] Level-up grants Energy (fixed amount per level)
- [ ] Mastering words grants Blocks
- [ ] /build page with 2 rooms and 8 items
- [ ] Items can be upgraded by spending currencies
- [ ] Currency UI shows balances and updates in real-time
- [ ] Level-up modal shows Energy reward
- [ ] Works on mobile (iPhone, Android)
- [ ] No critical bugs in core flow
- [ ] 10 test users can be onboarded

---

**Next Action:** Start Day 1 - Create `backend/src/services/currencies.py`

