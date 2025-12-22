# LexiCraft UX Vision: The Block Miner Game

**Date:** December 2024  
**Status:** Planning

---

## Overview

This document defines LexiCraft's UX vision as a **game-first vocabulary learning experience**, leveraging our unique assets: The Mine (knowledge graph) and Connection Pathway Engine.

**Terminology:** This document uses unified Block terminology. See [Terminology Glossary](./00-TERMINOLOGY.md) for definitions.

**Related Documents:**
- [Terminology Glossary](./00-TERMINOLOGY.md) - Unified vocabulary
- [Economic Model Hypotheses](./31-economic-model-hypotheses.md) - Dual economy design
- [02-learning-point-integration.md](./02-learning-point-integration.md) - Technical integration
- [Brand Definition](./16-brand-definition-lexicraft.md) - Source of terminology

---

## Part 1: Our Unique Competitive Advantages

### 1.1 The Mine (Neo4j Knowledge Graph)

A pre-populated graph with **8,873 blocks** (word senses) connected by 8 relationship types:

| Relationship | Purpose |
|--------------|---------|
| `PREREQUISITE_OF` | A → B: need A before B |
| `COLLOCATES_WITH` | A ↔ B: often used together |
| `RELATED_TO` | A ↔ B: similar concepts |
| `PART_OF` | A → B: A is part of phrase B |
| `OPPOSITE_OF` | A ↔ B: antonyms |
| `MORPHOLOGICAL` | A → B: A is prefix/suffix of B |
| `FREQUENCY_RANK` | A → B: rarity |
| `REGISTER_VARIANT` | A → B: formal/informal |

**Competitive Insight:** Blocks aren't isolated flashcards. They're **connected nodes in a discovery graph** (The Mine).

### 1.2 Connection Pathway Engine

Every word sense has:
- **Literal translation** → Shows English structure
- **Explanation** → Identifies nuances learners would miss
- **Connection pathway** → literal meaning → metaphor → idiomatic meaning

**Example for "break" (opportunity):**
> "原本你被困住，前面有一道牆擋著你 (literal break)。這道牆突然出現一個缺口 (metaphorical break)，讓你可以通過，繼續前進。所以「a break」就像是打破了阻礙你前進的困境，給你帶來一個新的開始和更好的機會 (idiomatic meaning)。"

**Competitive Insight:** Learning isn't memorization. It's **understanding how meaning flows**.

### 1.3 Dual Economy System

Unlike any competitor:
- **Internal economy**: XP, levels, achievements (always active)
- **External economy**: Real money rewards (requires parent funding)
- **Dynamic block values**: Value increases with connections
- Discovery bonuses for finding connections

**Status:** Economic model is hypothesis - see [Economic Model Hypotheses](./31-economic-model-hypotheses.md) for details.

---

## Part 2: Core Design Philosophy

### The Mindset Shift

| ❌ DON'T | ✅ DO |
|----------|------|
| "Add gamification to education" | "Build a game where vocabulary is the skill you level up" |
| "Show word definitions" | "Guide players through meaning discovery" |
| "Track progress in a dashboard" | "Visualize your growing vocabulary universe" |
| "Award virtual points" | "Pay real treasure for real knowledge" |

### The Core Fantasy

> **"You're a Block Miner discovering connections in The Mine, forging solid blocks and earning treasure for every discovery."**

The key concepts are **MINING** (discovery) and **FORGING** (mastery). Players are:
- **Mining** The Mine (exploring the connected knowledge graph)
- **Discovering** how blocks relate to each other
- **Unlocking** phrases/idioms when component blocks are known
- **Finding** patterns that unlock dozens of blocks
- **Understanding** WHY blocks mean what they mean (connection pathways)
- **Forging** blocks from hollow to solid through spaced repetition

---

## Part 3: Block Types & Dynamic Value System

### Block Tiers

From [02-learning-point-integration.md](./02-learning-point-integration.md):

| Tier | Type | Base XP | Example |
|------|------|---------|---------|
| ⭐ | Basic Block | 100 XP | "apple" = fruit |
| ⭐⭐ | Multi-Block | 250 XP | "bank" = finance AND river edge |
| ⭐⭐⭐ | Phrase Block | 500 XP | "make a decision" |
| ⭐⭐⭐⭐ | Idiom Block | 1,000 XP | "beat around the bush" |
| 🔗 | Pattern Block | 300 XP | "direct" → "indirect" (in- prefix) |
| 📝 | Register Block | 400 XP | "utilize" (formal) vs "use" (informal) |
| 🎯 | Context Block | 750 XP | "bush" (literal plant vs. idiom) |

### Dynamic Block Value Formula

**Block value increases with connections:**

```
Block Value = Base XP + (Connection Count × Connection Bonus)
```

**Connection Bonuses:**
- Related word: +10 XP per connection
- Opposite word: +10 XP per connection
- Part of phrase: +20 XP per phrase
- Part of idiom: +30 XP per idiom
- Morphological: +10 XP per pattern
- Register variant: +10 XP per variant

**Example:**
- "break" (Multi-Block): 250 XP base
- 12 connections: +120 XP
- **Total: 370 XP**

**Why This Matters:** Hub blocks (highly connected) are more valuable, encouraging exploration of central vocabulary.

### Discovery Bonuses

```
Mine "direct"                    → 100 XP
  └─ Discover "indirect" exists   → +50 XP DISCOVERY BONUS
       └─ Forge "indirect"        → 100 XP
            └─ Pattern recognized → +100 XP PATTERN BONUS

TOTAL: 350 XP (vs 200 XP without discovery)
```

---

## Part 4: Key UI Components

### 4.1 The Block Mine Map (Core Feature)

Instead of a flat block list, show a **visual graph** of The Mine (player's vocabulary universe):

```
                    ┌──────────┐
                    │  break   │ 🟨 SOLID (370 XP)
                    │ (chance) │
                    └────┬─────┘
                         │ RELATED_TO
         ┌───────────────┼───────────────┐
         │               │               │
    ┌────┴────┐    ┌─────┴─────┐    ┌────┴────┐
    │ fortune │    │opportunity│    │  lucky  │
    │  🪨 RAW │    │ 🧱 HOLLOW │    │  🪨 RAW │
    └─────────┘    └───────────┘    └─────────┘
         │
         │ UNLOCKS
    ┌────┴─────────────┐
    │ 🔒 "fortune      │
    │    favors the    │
    │    bold" 1000 XP │
    └──────────────────┘
```

### 4.2 Game Header (Always Visible)

```
┌────────────────────────────────────────────────────────────────────┐
│ 🔥 23    [Lv.12 ████████░░]    💰 $47.50    🔔    👤               │
└────────────────────────────────────────────────────────────────────┘
   ↑              ↑                 ↑          ↑       ↑
 Streak    Level + XP Progress   Balance   Notifs   Avatar
```

**Instantly communicates:**
- Streak (don't break it!)
- Level + progress to next
- XP earned (internal economy)
- Money earned (if funded blocks - external economy)
- Avatar identity

### 4.3 Block Detail View

Shows connections + explanation:

```
┌─────────────────────────────────────────────────────────────┐
│                        BREAK                                │
│                     ⭐⭐ Multi-Block                        │
│                    370 XP (250 base + 120 connections)      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  🎯 SENSE: A fortunate opportunity                         │
│                                                             │
│  📝 EXAMPLE                                                 │
│  "Getting that job was a real break for him."               │
│                                                             │
│  🔤 LITERAL TRANSLATION                                     │
│  "得到那份工作對他來說真是一個真正的突破"                    │
│                                                             │
│  💡 WHAT IT REALLY MEANS                   [Tap to reveal] │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ 「a real break」在這裡是說得到這個工作是個非常幸運的    │  │
│  │ 事情，讓他的人生有了很大的轉變。                        │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  🔗 CONNECTION PATHWAY                     [Tap to reveal] │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ 原本你被困住，前面有一道牆擋著你 (literal break)。      │  │
│  │ 這道牆突然出現一個缺口 (metaphorical break)，讓你      │  │
│  │ 可以通過，繼續前進。所以「a break」就像是打破了阻礙    │  │
│  │ 你前進的困境，給你帶來一個新的開始和更好的機會。        │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  🔗 CONNECTED BLOCKS                                        │
│  ┌─────────┐ ┌─────────────┐ ┌─────────┐                  │
│  │ fortune │ │ opportunity │ │  lucky  │                  │
│  │  🪨 RAW │ │ 🧱 HOLLOW   │ │  🪨 RAW │                  │
│  └─────────┘ └─────────────┘ └─────────┘                  │
│                                                             │
│  🔓 UNLOCKS                                                 │
│  • "big break" (phrase, 500 XP)                            │
│  • "break a leg" (idiom, 1000 XP) - need "leg" first        │
│                                                             │
│  💰 FUNDING STATUS (if funded)                              │
│  This block is funded - can convert to money when mastered  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 4.4 Discovery Moments

**Connection Discovery:**
```
┌─────────────────────────────────────────────────────────────┐
│                    ✨ DISCOVERY! ✨                         │
│                                                             │
│         You found a connection between words!               │
│                                                             │
│              direct ←──OPPOSITE──→ indirect                │
│                                                             │
│        These blocks share the "in-" prefix pattern!        │
│                                                             │
│                    +50 XP DISCOVERY BONUS                  │
│                                                             │
│  🔓 This pattern also applies to:                          │
│     • complete → incomplete                                 │
│     • visible → invisible                                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Phrase Unlock:**
```
┌─────────────────────────────────────────────────────────────┐
│                    🔓 PHRASE UNLOCKED!                      │
│                                                             │
│           "beat around the bush"                            │
│                                                             │
│      You know all the component blocks!                     │
│        beat ✓    around ✓    bush ✓                        │
│                                                             │
│      Now forge this idiom for 1000 XP!                     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Part 5: Parent View

Parents see their children's **exploration journey**, not grades:

```
┌─────────────────────────────────────────────────────────────┐
│                   👧 小明的探索旅程                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Level 12 Block Miner • ⚡ 23 Day Streak                    │
│                                                             │
│  TODAY'S MINING                                             │
│  ██████████░░░░░░░░ 8/15 blocks reviewed                   │
│                                                             │
│  RECENT DISCOVERIES                                         │
│  • Unlocked "in-" pattern (+100 XP bonus)                  │
│  • Forged "break" all 4 senses (370 XP each)                │
│  • Discovered 3 new block connections                       │
│                                                             │
│  FUNDING STATUS (if funded)                                 │
│  Deposited: NT$2,000 • Mastered: 847 blocks                │
│  Withdrawable: NT$847                                       │
│                                                             │
│  [ View Full Map ] [ Add Funds ] [ Withdraw ]               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Part 6: Visual Design Principles

### 6.1 Aesthetic Direction

| ❌ Avoid | ✅ Embrace |
|----------|-----------|
| Soft pastels | Bold, high-contrast |
| Rounded "safe" shapes | Gaming aesthetic |
| Educational app blue | Dark mode + neon accents |
| Static displays | Particle effects, animations |

### 6.2 Color Semantics

| Color | CSS Variable | Usage |
|-------|--------------|-------|
| Cyan | `#06b6d4` | XP, progress, primary actions |
| Orange | `#f97316` | Streak, urgency |
| Yellow | `#eab308` | Money, achievements, rare |
| Green | `#22c55e` | Correct, earned, complete |
| Purple | `#a855f7` | Levels, premium, special |
| Slate | `#0f172a` | Dark backgrounds |

### 6.3 Avatar System

- **Base characters**: 8 starter options
- **Level unlocks**: New characters at L5, L10, L20, L50
- **Achievement decorations**: Frames, backgrounds
- **Streak badges**: Visible flame size
- **Wealth indicators**: Gold trim at $50+, diamond at $100+

---

## Part 7: Implementation Phases

### Phase 0: API Foundation (Week 0-1)
- [ ] Expose The Mine (Neo4j) connections to frontend
- [ ] Add tier/XP info to block data
- [ ] Add relationship data to MCQ responses
- [ ] Calculate dynamic block values (base + connections)
- [ ] Bridge Neo4j (blocks) and PostgreSQL (user progress)

### Phase 1: Identity + Map (Week 1-3)
- [ ] GameHeader with streak, level, XP, money (if funded)
- [ ] Block Mine Map MVP (simple graph visualization)
- [ ] Block detail view with connections + explanation
- [ ] Discovery moment animations

### Phase 2: Collection System (Week 4-5)
- [ ] Block collection view
- [ ] Tier badges on blocks (⭐⭐⭐)
- [ ] Dynamic value display (base + connections)
- [ ] Pattern recognition display
- [ ] Phrase/idiom unlock previews

### Phase 3: Discovery Celebrations (Week 6-7)
- [ ] Connection discovery animation
- [ ] Phrase unlock moment
- [ ] Pattern mastery celebration
- [ ] Bonus XP/money animations

### Phase 4: Parent Experience (Week 8)
- [ ] Child mining summary
- [ ] Mini Block Mine map for parents
- [ ] Discovery feed
- [ ] Funding flow improvements
- [ ] Dual economy visualization (XP vs money)

---

## Part 8: Competitive Positioning

| Competitor | Their Approach | LexiCraft Advantage |
|------------|----------------|---------------------|
| **Duolingo** | Generic gamification, virtual XP | Discovery graph, real money, connection understanding |
| **Khan Academy** | Video-based, passive learning | Active exploration, discovery mechanics |
| **ClassDojo** | Behavior points, no learning | Vocabulary mastery, semantic understanding |
| **Quizlet** | Flat flashcards, no connections | Knowledge graph, connection pathways |

---

## Part 9: Success Metrics

| Metric | Target | Why |
|--------|--------|-----|
| D1 Retention | >60% | Come back tomorrow? |
| D7 Retention | >40% | Hooked? |
| D30 Retention | >25% | Habit? |
| DAU/MAU | >40% | Daily engagement |
| Avg Session | >5 min | Meaningful sessions? |
| Streak 7+ days | >50% | Streak working? |
| Withdrawal rate | >20%/mo | Earning and cashing out? |

---

## Part 10: Data Model Status

### What Exists

**Neo4j (The Mine):**
- 3,500 Word nodes
- 8,873 Sense nodes (blocks)
- 13,318 relationships
- Enriched content (definitions, examples, explanations)

**PostgreSQL (User Data):**
- `learning_progress` table (tracks block mastery)
- `mcq_pool` table (stores quizzes)
- `mcq_attempts` table (tracks quiz results)
- References to Neo4j via `sense_id` (TEXT field)

### What's Missing

**API Bridge:**
- Endpoint to combine Neo4j block data + PostgreSQL user progress
- Dynamic value calculation (base + connections)
- Block Mine map queries (connections visualization)

**Frontend Data Model:**
- TypeScript types for unified Block interface
- Block state management (Raw → Hollow → Solid)
- Connection data structure

**See:** [Terminology Glossary](./00-TERMINOLOGY.md) for data model details.

---

## Conclusion

**Our competitors treat blocks as isolated items.**  
**LexiCraft treats vocabulary as The Mine - a connected universe to explore.**

The UX should make every player feel like they're:
1. **Mining** The Mine (exploring a vast map of connected knowledge)
2. **Discovering** how blocks relate to each other
3. **Understanding** WHY blocks mean what they mean (connection pathways)
4. **Forging** blocks from hollow to solid (spaced repetition mastery)
5. **Earning** XP and achievements (internal economy)
6. **Converting** to money when funded (external economy)

---

*This isn't vocabulary memorization.*  
*This is block mining and forging with a knowledge graph engine underneath.*

**Related:**
- [Terminology Glossary](./00-TERMINOLOGY.md) - All terms defined
- [Economic Model](./31-economic-model-hypotheses.md) - Dual economy design

