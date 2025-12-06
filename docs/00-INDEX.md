# Documentation Index
## LexiCraft Documentation

**Last Updated:** December 2024

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

1. **[The Mine: Block Integration](./02-learning-point-integration.md)**
   - Knowledge graph architecture (The Mine)
   - Block tiers and base XP values
   - Dynamic value system (connections increase value)
   - Discovery bonuses
   - Gamification layers

2. **[UX Vision: Game Design](./30-ux-vision-game-design.md)**
   - Game-first design philosophy
   - Block Mine Map visualization
   - Mining and forging mechanics
   - Parent/child experiences
   - Implementation phases
   - Data model status

3. **[Economic Model Hypotheses](./31-economic-model-hypotheses.md)** 🆕
   - Dual economy design (XP vs money)
   - Internal economy (always active)
   - External economy (requires funding)
   - Testable hypotheses
   - Package design options

### Design & Architecture

3. **[Signup Flow Design](./18-signup-flow-design.md)**
   - User onboarding flow
   - Progressive disclosure
   - Industry best practices

4. **[Relationship Ecosystem Design](./19-relationship-ecosystem-design.md)**
   - All relationship types
   - Roles & permissions
   - Age & legal considerations
   - Use cases

5. **[Session Summary](./20-session-summary.md)**
   - Key decisions made
   - Current state
   - Architecture decisions

### Implementation

4. **[Implementation Status](./21-implementation-status.md)**
   - What's completed
   - What's pending
   - Next steps

5. **[API Updates Summary](./22-api-updates-summary.md)**
   - All API endpoint changes
   - Breaking changes
   - Migration guide for frontend

6. **[Frontend Updates Summary](./23-frontend-updates-summary.md)**
   - Component changes
   - API integration
   - User flow updates

7. **[Complete Implementation Summary](./26-complete-implementation-summary.md)**
   - Full overview
   - Statistics
   - Success criteria

### Execution & Deployment

8. **[Migration Execution Guide](./24-migration-execution-guide.md)**
   - Step-by-step migration
   - Verification queries
   - Troubleshooting

9. **[Testing Guide](./25-testing-guide.md)**
   - Complete test suites
   - Test cases
   - Edge cases

10. **[Deployment Checklist](./28-deployment-checklist.md)**
    - Pre-deployment checklist
    - Post-deployment verification
    - Common issues

11. **[Quick Start Guide](./29-quick-start-guide.md)**
    - Local development setup
    - Environment variables
    - Common issues

### Reference

12. **[Adding User Attributes](./27-adding-user-attributes.md)**
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

**...understand the UX vision**
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
- Database schema & migrations
- Backend models & CRUD
- API endpoints
- Frontend components
- Onboarding flow
- Documentation

### ⏳ Pending
- Run migrations in Supabase
- End-to-end testing
- Auth middleware (JWT extraction)
- Production deployment

---

## 🗂️ File Structure

```
docs/
├── 00-INDEX.md (this file)
├── 00-TERMINOLOGY.md                  ← Unified vocabulary
├── 01-project-overview.md
├── 02-learning-point-integration.md    ← The Mine & block tiers
├── ...
├── 18-signup-flow-design.md
├── 19-relationship-ecosystem-design.md
├── 20-session-summary.md
├── 21-implementation-status.md
├── 22-api-updates-summary.md
├── 23-frontend-updates-summary.md
├── 24-migration-execution-guide.md
├── 25-testing-guide.md
├── 26-complete-implementation-summary.md
├── 27-adding-user-attributes.md
├── 28-deployment-checklist.md
├── 29-quick-start-guide.md
├── 30-ux-vision-game-design.md        ← UX/Game design vision
└── 31-economic-model-hypotheses.md    ← Dual economy design
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

