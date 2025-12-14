# Documentation Index
## LexiCraft Documentation

**Last Updated:** December 8, 2025

---

## 🚀 Quick Start

**New to the project?** Start here:
1. [Quick Start Guide](./29-quick-start-guide.md) - Get running locally
2. [Migration Execution Guide](./24-migration-execution-guide.md) - Run database migrations
3. [Testing Guide](./25-testing-guide.md) - Test everything

---

## 📚 Documentation by Category

### Terminology & Foundation

0. **[Terminology Glossary](./00-TERMINOLOGY.md)** 🆕
   - Unified Block vocabulary
   - Mining, Forging, The Mine concepts
   - Block states and types
   - Relationship types
   - Single source of truth for all terms

### Product & UX Vision

0. **[MVP Roadmap](./36-mvp-roadmap.md)** 🆕 **START HERE**
   - 2-week sprint plan
   - Core hypothesis to test
   - Task breakdown by day
   - Success/failure criteria
   - Post-MVP roadmap

1. **[Taiwan Bilingual Nation Proposal](./37-taiwan-bilingual-nation-proposal.md)** 🆕 **GOVERNMENT PROPOSAL**
   - Cost analysis for 30% population (7.05M people)
   - 14.1 billion TWD investment breakdown
   - Phased rollout strategies (3-5 years)
   - Implementation considerations
   - Risk analysis and success metrics

2. **[Minecraft Game Design](./35-minecraft-game-design.md)** **CORE**
   - **Mine → Smelt → Build** core loop
   - Inventory system (words as materials)
   - Blueprint system (structures to build)
   - Decay/Creeper mechanic (stakes for forgetting)
   - XP as spendable currency
   - Enchanting, Crafting, Villagers, Nether
   - Implementation phases & database schema

3. **[The Mine: Block Integration](./02-learning-point-integration.md)**
   - Knowledge graph architecture (The Mine)
   - Block tiers and base XP values
   - Dynamic value system (connections increase value)
   - Discovery bonuses

4. **[UX Vision: Game Design](./30-ux-vision-game-design.md)**
   - Original game-first design philosophy (foundation)
   - Block Mine Map visualization
   - Mining and forging mechanics
   - Parent/child experiences

5. **[Economic Model Hypotheses](./31-economic-model-hypotheses.md)**
   - Dual economy design (XP vs money)
   - Internal economy (always active)
   - External economy (requires funding)
   - Testable hypotheses

### Architecture Decision Records

- **[ADR-001: One-Shot Payload](./decisions/ADR-001-one-shot-payload.md)** - Instant gamification feedback
- **[ADR-002: Minecraft Game Model](./decisions/ADR-002-minecraft-game-model.md)** 🆕 - Core game design paradigm

### Design & Architecture

6. **[Signup Flow Design](./18-signup-flow-design.md)**
   - User onboarding flow
   - Progressive disclosure
   - Industry best practices

7. **[Relationship Ecosystem Design](./19-relationship-ecosystem-design.md)**
   - All relationship types
   - Roles & permissions
   - Age & legal considerations
   - Use cases

8. **[Session Summary](./20-session-summary.md)**
   - Key decisions made
   - Current state
   - Architecture decisions

### Implementation

9. **[Implementation Status](./21-implementation-status.md)**
   - What's completed
   - What's pending
   - Next steps

10. **[API Updates Summary](./22-api-updates-summary.md)**
    - All API endpoint changes
    - Breaking changes
    - Migration guide for frontend

11. **[Frontend Updates Summary](./23-frontend-updates-summary.md)**
    - Component changes
    - API integration
    - User flow updates

12. **[Complete Implementation Summary](./26-complete-implementation-summary.md)**
    - Full overview
    - Statistics
    - Success criteria

### Execution & Deployment

13. **[Migration Execution Guide](./24-migration-execution-guide.md)**
    - Step-by-step migration
    - Verification queries
    - Troubleshooting

14. **[Testing Guide](./25-testing-guide.md)**
    - Complete test suites
    - Test cases
    - Edge cases

15. **[Deployment Checklist](./28-deployment-checklist.md)**
    - Pre-deployment checklist
    - Post-deployment verification
    - Common issues

16. **[Quick Start Guide](./29-quick-start-guide.md)**
    - Local development setup
    - Environment variables
    - Common issues

### Reference

17. **[Adding User Attributes](./27-adding-user-attributes.md)**
    - How to add columns later
    - Best practices
    - Examples

---

## 📋 Common Tasks

### I want to...

**...run the migrations**
→ See [Migration Execution Guide](./24-migration-execution-guide.md)

**...test the system**
→ See [Testing Guide](./25-testing-guide.md)

**...deploy to production**
→ See [Deployment Checklist](./28-deployment-checklist.md)

**...add a new user attribute**
→ See [Adding User Attributes](./27-adding-user-attributes.md)

**...understand the design**
→ See [Relationship Ecosystem Design](./19-relationship-ecosystem-design.md)

**...understand the game design (Minecraft model)**
→ See [Minecraft Game Design](./35-minecraft-game-design.md)

**...understand the original UX vision**
→ See [UX Vision: Game Design](./30-ux-vision-game-design.md)

**...understand terminology**
→ See [Terminology Glossary](./00-TERMINOLOGY.md)

**...understand the economic model**
→ See [Economic Model Hypotheses](./31-economic-model-hypotheses.md)

**...see what changed**
→ See [Complete Implementation Summary](./26-complete-implementation-summary.md)

**...set up locally**
→ See [Quick Start Guide](./29-quick-start-guide.md)

---

## 🔍 Find Information By Topic

### Database
- Schema: [Migration Execution Guide](./24-migration-execution-guide.md)
- Adding columns: [Adding User Attributes](./27-adding-user-attributes.md)
- Relationships: [Relationship Ecosystem Design](./19-relationship-ecosystem-design.md)

### API
- Endpoints: [API Updates Summary](./22-api-updates-summary.md)
- Changes: [Implementation Status](./21-implementation-status.md)
- Testing: [Testing Guide](./25-testing-guide.md)

### Frontend
- Terminology: [Terminology Glossary](./00-TERMINOLOGY.md)
- UX Vision: [UX Vision: Game Design](./30-ux-vision-game-design.md)
- Economic Model: [Economic Model Hypotheses](./31-economic-model-hypotheses.md)
- Components: [Frontend Updates Summary](./23-frontend-updates-summary.md)
- Integration: [API Updates Summary](./22-api-updates-summary.md)
- Setup: [Quick Start Guide](./29-quick-start-guide.md)

### Deployment
- Checklist: [Deployment Checklist](./28-deployment-checklist.md)
- Migrations: [Migration Execution Guide](./24-migration-execution-guide.md)
- Testing: [Testing Guide](./25-testing-guide.md)

---

## 📊 Implementation Status

### ✅ Completed
- Database schema & migrations (including gamification tables)
- Backend models & CRUD
- API endpoints (MCQ, words, gamification)
- Frontend components (MCQ, achievements, gamification feedback)
- Onboarding flow
- Gamification v1 (XP, levels, achievements, streaks, crystals)
- One-shot payload (instant feedback)
- FSRS/SM-2+ spaced repetition
- Test account seeding

### 🎮 Minecraft Model (Design Complete, Implementation Pending)
- [ ] Inventory system (materials by tier)
- [ ] Blueprint system (structures to build)
- [ ] Decay visualization
- [ ] XP shop
- [ ] Asset strategy: Emoji → Kenny → Custom

### ⏳ Pending
- End-to-end testing
- Word Explorer interface
- Survey → Verification flow connection

---

## 🗂️ File Structure

```
docs/
├── 00-INDEX.md (this file)
├── 00-TERMINOLOGY.md                  ← Unified vocabulary
├── 01-project-overview.md
├── 02-learning-point-integration.md    ← The Mine & block tiers
├── ...
├── 30-ux-vision-game-design.md        ← Original UX vision
├── 31-economic-model-hypotheses.md    ← Dual economy design
├── 35-minecraft-game-design.md        ← 🆕 CORE GAME DESIGN
├── 36-mvp-roadmap.md                  ← 🆕 MVP SPRINT PLAN
├── 37-taiwan-bilingual-nation-proposal.md ← 🆕 GOVERNMENT PROPOSAL
└── decisions/
    ├── ADR-001-one-shot-payload.md
    └── ADR-002-minecraft-game-model.md  ← 🆕
```

---

## 🎯 Next Steps

1. **Read:** [Quick Start Guide](./29-quick-start-guide.md)
2. **Run:** [Migration Execution Guide](./24-migration-execution-guide.md)
3. **Test:** [Testing Guide](./25-testing-guide.md)
4. **Deploy:** [Deployment Checklist](./28-deployment-checklist.md)

---

## 💡 Tips

- **Start with Quick Start Guide** if you're new
- **Check Implementation Status** to see what's done
- **Use Testing Guide** before deploying
- **Reference Adding User Attributes** when extending schema

---

**Status:** All documentation complete and ready to use! 📚

