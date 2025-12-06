# Economic Model: Hypotheses & Design

**Last Updated:** December 2024  
**Status:** Hypotheses - Requires Real-World Validation

---

## Overview

LexiCraft operates on a **dual economy model** that separates intrinsic game motivation (XP) from extrinsic real-world rewards (money). This document outlines the design hypotheses that need validation through user testing.

---

## Core Hypothesis

> **The dual economy model allows kids to explore freely while parents control monetary incentives, creating a sustainable learning ecosystem.**

**Status:** Hypothesis - Not yet proven with real user data.

---

## The Two Economies

### Internal Economy (Always Active)

**Purpose:** Intrinsic motivation through game mechanics

**Components:**
- **Block XP** - Earned by forging blocks (base + connection bonus)
- **Crystals** - Earned by achievements, streaks, patterns
- **Levels** - Based on total XP accumulated
- **Achievements** - Unlocked by milestones
- **Streaks** - Daily learning continuity

**Characteristics:**
- Always available (no funding required)
- Pure game experience
- Intrinsic motivation
- No real-world value

**Example:**
```
Kid discovers "break" → Earns 220 XP → Levels up → Unlocks achievement
(No money involved, pure game progression)
```

---

### External Economy (Requires Funding)

**Purpose:** Extrinsic motivation through real-world rewards

**Components:**
- **Funded Blocks** - Blocks labeled with 💰 by parent funding
- **Conversion Rights** - Ability to withdraw money when blocks are mastered
- **Withdrawal System** - Convert mastered funded blocks to real money
- **Package Pricing** - Parent purchases set of blocks for conversion

**Characteristics:**
- Requires parent funding to activate
- Extrinsic motivation
- Real-world value (NT$)
- Visible badges (💰) on funded blocks

**Example:**
```
Parent funds "Essential 2000" package (NT$2,000)
→ 2,000 blocks get 💰 badge
→ Kid masters "break" (funded block)
→ Can withdraw NT$1.00 (if conversion rate is NT$1/block)
```

---

## The Connection Between Economies

### How They Interact

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    BLOCK LIFECYCLE (Unified)                             │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  DISCOVERY → FORGING → MASTERY                                         │
│  ─────────   ───────   ───────                                         │
│                                                                         │
│  🪨 Raw Block                                                           │
│  • Discovered via mining                                                │
│  • 0 XP earned                                                          │
│  • If funded: Shows 💰 badge                                           │
│                                                                         │
│  🧱 Hollow Block                                                       │
│  • In forging process                                                   │
│  • Earning XP (same for funded/unfunded)                               │
│  • If funded: Shows 💰 badge + "Worth NT$X"                            │
│                                                                         │
│  🟨 Solid Block                                                         │
│  • Fully mastered (FSRS stable)                                        │
│  • Full XP earned                                                       │
│  • If funded: Can convert to money                                     │
│  • If unfunded: Still valuable (XP, achievements)                      │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

**Key Insight:** The gaming experience is IDENTICAL for funded and unfunded blocks. The only difference is the 💰 badge and conversion ability.

---

## Hypotheses to Test

### H1: XP Alone Provides Sufficient Motivation

**Hypothesis:** Kids will engage with the game even without money attached to blocks.

**Test:** Run a cohort with XP-only, no funding option.

**Metrics:**
- Daily active users
- Blocks forged per session
- Retention rate (D1, D7, D30)
- Time spent in app

**Success Criteria:** >40% D7 retention, >5 min avg session

---

### H2: Money Badges Increase Engagement

**Hypothesis:** Visible 💰 badges on funded blocks increase completion rates vs unfunded blocks.

**Test:** A/B test - same blocks, some with 💰 badge, some without.

**Metrics:**
- Completion rate (funded vs unfunded)
- Time to mastery
- Return rate (do they come back to funded blocks first?)

**Success Criteria:** Funded blocks have 20%+ higher completion rate

---

### H3: Kids Understand Dual Economy

**Hypothesis:** Kids can distinguish between XP value and money value without confusion.

**Test:** User testing - ask kids to explain the difference.

**Metrics:**
- Comprehension rate (can explain difference)
- Confusion incidents
- Support tickets about economy

**Success Criteria:** >80% can explain difference, <5% confusion rate

---

### H4: Free-to-Play → Conversion Works

**Hypothesis:** Kids who start without funding will convert to funded accounts.

**Test:** Track unfunded users who later get funding.

**Metrics:**
- Conversion rate (unfunded → funded)
- Time to conversion
- Blocks forged before conversion

**Success Criteria:** >20% conversion rate within 30 days

---

### H5: Parents Prefer "Funding" Framing

**Hypothesis:** Parents prefer "funding conversion rights" over "paying per word."

**Test:** A/B test messaging in parent onboarding.

**Metrics:**
- Sign-up rate
- Package purchase rate
- Parent satisfaction scores

**Success Criteria:** "Funding" messaging has 15%+ higher conversion

---

## Package Design (Hypotheses)

### Package Structure

| Package | Price (NT$) | Blocks | $/Block | Hypothesis |
|---------|-------------|--------|---------|------------|
| **Starter 500** | $500 | 500 | $1.00 | Low barrier to entry |
| **Essential 2000** | $2,000 | 2,000 | $1.00 | Core vocabulary |
| **Academic 5000** | $4,500 | 5,000 | $0.90 | School success focus |
| **Complete 10000** | $8,000 | 10,000 | $0.80 | Full mastery |
| **Elite (All)** | $15,000 | All | Variable | Premium option |

**Hypothesis:** Bulk pricing (lower $/block) increases package size preference.

**Test:** A/B test package presentation (emphasize value vs. emphasize quantity).

---

## Conversion Mechanics (Hypotheses)

### Conversion Rate Options

**Option A: Fixed Rate**
```
Package Price ÷ Number of Blocks = Fixed Rate per Block
Example: NT$2,000 ÷ 2,000 = NT$1.00 per block
```

**Option B: Variable Rate**
```
Different blocks have different values based on:
- Tier (Basic = $0.50, Idiom = $2.00)
- Connections (more connections = higher value)
- Difficulty (harder = higher value)
```

**Hypothesis:** Variable rate feels more fair but is harder to understand.

**Test:** A/B test fixed vs variable, measure:
- Parent comprehension
- Purchase rate
- Satisfaction

---

## What We Don't Know Yet

### Critical Unknowns

1. **Will kids play without funding?**
   - Or will they feel "why bother if there's no money?"
   - Need to test pure XP motivation

2. **Is visible money required for motivation?**
   - Or is XP enough?
   - Does 💰 badge actually increase engagement?

3. **Will dual economy confuse users?**
   - Can kids understand XP vs money?
   - Will parents understand "funding conversion rights"?

4. **What's the optimal $/block ratio?**
   - Too low = not motivating
   - Too high = unsustainable
   - Need to find sweet spot

5. **Do parents want packages or per-word pricing?**
   - Packages = simpler, predictable
   - Per-word = more flexible, complex

6. **Does free-to-play → conversion work?**
   - Will unfunded kids stick around?
   - Will they ask parents for funding?

---

## Implementation Flexibility

Since we don't know what works, the system should support multiple models:

### Model A: All Funded
- Every block has money attached
- Simple, high motivation
- No free exploration

### Model B: Dual Economy (Current Hypothesis)
- XP always, money optional
- Free-to-play conversion
- Complex but flexible

### Model C: Tiered Funding
- Base blocks free, premium funded
- Freemium model
- Clear upgrade path

### Model D: XP-to-Money Exchange
- Earn XP, convert at rate
- Parent sets budget, not blocks
- Most flexible

**Recommendation:** Start with Model B (dual economy), but build system to support all models for A/B testing.

---

## Success Metrics

### Engagement Metrics
- Daily active users (target: >60% of funded users)
- Blocks forged per session (target: >5)
- Session length (target: >5 min)
- Retention D7 (target: >40%)

### Economic Metrics
- Package purchase rate (target: >30% of parents)
- Average package size (target: >2,000 blocks)
- Withdrawal rate (target: >20% monthly)
- Conversion rate (unfunded → funded) (target: >20%)

### Learning Metrics
- Blocks mastered per month (target: >50)
- Connection discoveries (target: >10 per session)
- Pattern recognition (target: >5 patterns per month)

---

## Next Steps

1. **Build MVP with dual economy** (Model B)
2. **Run user tests** with small cohort
3. **Measure all hypotheses** (H1-H5)
4. **Iterate based on data**
5. **A/B test alternative models** if needed

---

## Related Documents

- [Terminology Glossary](./00-TERMINOLOGY.md) - Economic terms defined
- [UX Vision](./30-ux-vision-game-design.md) - How economy appears in UI
- [Learning Point Integration](./02-learning-point-integration.md) - Technical implementation

---

**Status:** This model is a hypothesis. All claims need validation through real user data.

