# LexiCraft.xyz Learning Platform - Project Starter

## Project Overview

**LexiCraft.xyz** is a revolutionary educational platform where parents invest upfront, and children earn money back by mastering vocabulary through a sophisticated Learning Point Cloud system.

**Brand Identity:** LexiCraft.xyz • 字塊所  
**Brand Story:** "xyz" = End of the alphabet = Complete learning journey from A to Z

---

## 🚀 Quick Start (Get to Market Fast)

### Key Decisions Made

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **MVP Reward Model** | Direct cash withdrawal | Simpler, faster, lower legal risk |
| **Game Integration** | Phase 2 (future) | Validate core thesis first |
| **Word List** | 3,000-4,000 words | CEFR + Taiwan + Corpus combined |
| **Learning Points** | ~5,000 (MVP Tier 1-2) | Expandable to ~13,700 (all tiers) |
| **Database** | PostgreSQL + JSONB | Not Neo4j for MVP (faster) |
| **Timeline** | 4 weeks to MVP | Beta launch Week 5 |

### Start Here

1. **📋 Key Decisions**: `docs/15-key-decisions-summary.md` - All decisions consolidated
2. **🚀 MVP Strategy**: `docs/10-mvp-validation-strategy.md` - 4-week plan to launch
3. **💰 Investor One-Pager**: `docs/11-investor-one-pager.md` - Ready-to-share
4. **✅ Week 1 Checklist**: `docs/12-immediate-action-items.md` - Start today
5. **⚖️ Legal (Taiwan)**: `docs/13-legal-analysis-taiwan.md` - Critical legal issues

---

## Project Structure

```
lexicraft-project/
├── README.md                              # This file
├── docs/
│   ├── 01-project-overview.md            # Complete project overview
│   ├── 02-learning-point-integration.md  # Learning Point Cloud integration
│   ├── 03-implementation-roadmap.md      # Step-by-step implementation
│   ├── 04-technical-architecture.md      # Technical design
│   ├── 05-mcq-verification-strategy.md   # MCQ verification with 6 options
│   ├── 06-spaced-repetition-strategy.md  # Spaced repetition intervals
│   ├── 07-partial-unlock-mechanics.md    # Partial unlock & deficit system
│   ├── 08-robux-integration-analysis.md  # Robux integration (Phase 2)
│   ├── 09-multi-game-integration-analysis.md  # Multi-game (Phase 2)
│   ├── 10-mvp-validation-strategy.md     # ⭐ MVP STRATEGY (START HERE)
│   ├── 11-investor-one-pager.md          # ⭐ INVESTOR SUMMARY
│   ├── 12-immediate-action-items.md      # Week 1 checklist
│   ├── 13-legal-analysis-taiwan.md       # Taiwan legal analysis
│   ├── 14-legal-quick-reference-taiwan.md # Legal quick reference
│   ├── 15-key-decisions-summary.md       # ⭐ ALL DECISIONS CONSOLIDATED
│   └── 17-lexisurvey-specification.md     # LexiSurvey feature spec
├── examples/
│   ├── learning-point-examples.md        # Learning Point examples
│   ├── mcq-verification-examples.md      # MCQ verification examples
│   └── partial-unlock-examples.md        # Partial unlock examples
└── specs/
    ├── earning-rules.md                  # Earning tier definitions
    └── verification-rules.md             # Verification requirements
```

---

## Key Concepts

### MVP Model: Direct Cash Withdrawal

For MVP, we use **direct cash withdrawal** instead of game currency:

```
Parent deposits NT$1,000 → Child learns vocabulary → 
Child earns points → Parent withdraws cash → 
Parent decides how to reward (allowance, toys, savings, etc.)
```

**Game integration = Future Phase 2 (NOT MVP)**

### Word List Strategy: Combined Standard

**Phase 1 (MVP): 3,000-4,000 words**
- CEFR A1-B2 (40%) - European standard
- Taiwan MOE Curriculum (30%) - Local relevance
- Corpus Frequency (30%) - Real-world usage

**Phase 2: 8,000-10,000 words**
- CEFR C1-C2 + Taiwan Advanced + Corpus Top 8000

### Learning Points Estimate

| Tier | Points | Description |
|------|--------|-------------|
| Tier 1 | 3,500 | Basic word recognition |
| Tier 2 | 1,500 | Multiple meanings |
| Tier 3 | 6,000 | Phrases/collocations |
| Tier 4 | 500 | Idioms |
| Tier 5 | 1,200 | Morphological relationships |
| Tier 6 | 300 | Register variants |
| Tier 7 | 700 | Advanced contexts |
| **MVP (Tier 1-2)** | **~5,000** | MVP scope |
| **All Tiers** | **~13,700** | Full system |

### Verification System (MVP)

- **6-option MCQ** with 99.54% confidence
- **Day 1, 3, 7** spaced repetition schedule
- **Anti-gaming**: 20 words/day limit (100+ days to game 2000 words)

### Earning Tiers

| Tier | Rate | Description |
|------|------|-------------|
| Tier 1 | 10 pts/word | Basic Recognition |
| Tier 2 | 25 pts/word | Multiple Meanings |
| Tier 3 | 50 pts/phrase | Phrase Mastery |
| Tier 4 | 100 pts/idiom | Idiom Mastery |
| Tier 5 | 30 pts/rel | Morphological |
| Tier 6 | 40 pts/variant | Register |
| Tier 7 | 75 pts/context | Advanced Context |

---

## Roadmap

### Phase 1: MVP (Weeks 1-4)
- ✅ Direct cash withdrawal model
- ✅ 3,000-4,000 words (CEFR + Taiwan + Corpus)
- ✅ Tier 1-2 earning (~5,000 learning points)
- ✅ PostgreSQL + JSONB (fast to build)
- Target: 50-100 beta families

### Phase 2: Expansion (Months 2-4)
- 💰 Game currency integration (if validated - NOT MVP)
- 📚 Expand to 8,000-10,000 words
- 📊 All 7 tiers
- 🔗 See `docs/08-robux-integration-analysis.md` and `docs/09-multi-game-integration-analysis.md` for future game integration plans

### Phase 3: Scale (Months 4-12)
- 🧠 Full Learning Point Cloud (Neo4j)
- 📱 Mobile apps (iOS, Android)
- 🏢 B2B expansion (schools, tutoring centers)
- 🌏 International markets

---

## Taiwan Legal Compliance

**Critical for Taiwan launch:**

1. **Age of Majority = 20** (parent must be account owner)
2. **Direct withdrawal model** (simpler than game currency)
3. **Tax reporting** (rewards ≥NT$1,000)
4. **FTC limits** (NT$150M annual max)
5. **7-day refund right** (Consumer Protection Act)

See: `docs/13-legal-analysis-taiwan.md` for full details

---

## 🛠️ Building the MVP

### Master Chat Workflow

We use a **multi-chat workflow** to build the MVP in parallel:

1. **Master Planning Chat**: Tracks all work, coordinates between chats
2. **Implementation Chats**: Build specific components, report back when done

**Quick Start:**
- Read `docs/development/QUICK_START_MASTER_CHATS.md` - How to set up master chats
- Read `docs/development/MASTER_CHAT_PLAN.md` - Complete build plan
- Use `docs/development/MASTER_CHAT_PROMPTS.md` - Copy-paste prompts for each phase

**Phase 1 (Week 1)**: Database Schema, Word List, Landing Page  
**Phase 2 (Week 2)**: Auth, Learning Interface, MCQ Generator  
**Phase 3 (Week 3)**: Verification, Points, Dashboard  
**Phase 4 (Week 4)**: Withdrawal, Notifications, Launch Prep

---

## Next Steps

1. **Read** `docs/15-key-decisions-summary.md` - All decisions in one place
2. **Follow** `docs/10-mvp-validation-strategy.md` - 4-week build plan
3. **Use** `docs/12-immediate-action-items.md` - Week 1 checklist
4. **Share** `docs/11-investor-one-pager.md` - With investors
5. **Build** `docs/development/QUICK_START_MASTER_CHATS.md` - Set up master chats

---

## Related Documents

See full documentation in `docs/` folder for:
- Technical architecture
- MCQ verification strategy
- Spaced repetition details
- Game integration analysis (Future Phase 2 - NOT MVP)
- Legal compliance
