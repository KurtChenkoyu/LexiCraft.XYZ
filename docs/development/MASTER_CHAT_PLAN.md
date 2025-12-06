# Master Chat Plan: LexiCraft MVP

This document coordinates multiple implementation chats for building the LexiCraft MVP. Each chat focuses on a specific component and reports back to this master planning document.

**When you complete work in other chats, report back here using the structured format below.**

---

## How to Report Work Completed

When you finish work in another chat, give that chat this prompt to generate a structured report:

```
Please create a structured report of the work we just completed. Format it as follows:

**What was done:**
[Brief description of the work completed]

**Decisions made:**
[Key architectural or design decisions, with rationale if important]

**Files changed:**
[List of files modified/created/deleted]

**Workflow impact:**
[How this changes the MVP - which sections need updates?]

**New issues discovered:**
[Any problems or edge cases found during implementation]

**Status:**
[✅ Complete / 🚧 In Progress / ⚠️ Blocked - and why]

**Next steps (if any):**
[What still needs to be done or what should be tackled next]
```

---

## Recommended Multi-Chat Workflow

Use these chat types to keep context focused:

1. **Master Planning Chat (this thread) - Coordinator/Verifier**
   - Owns the canonical MVP plan
   - Assigns work to implementation chats
   - Receives and verifies structured reports
   - Records decisions
   - Chooses the next focus area
   - **Does NOT write code or create files**

2. **Master Schema Planner Chat - Coordinator/Verifier** (for complex database work)
   - Coordinates Neo4j + PostgreSQL setup
   - Assigns database tasks to implementation chats
   - Verifies completion reports
   - Reports back to Master Planning Chat
   - **Does NOT write code or create files**
   - See `docs/development/MASTER_SCHEMA_PLANNER.md`

3. **Implementation Chats (one per phase/component) - Doers**
   - **Chat Name Format**: `Phase X - [Component Name]` (e.g., "Phase 1 - Landing Page")
   - Receive assignments from master chats
   - Read handoff documents
   - **Write code and create files**
   - Implement features
   - Stay in the same thread until the task ships
   - Report back to master chats when complete

4. **Research/Design Chats**
   - Explore APIs, libraries, or design patterns
   - When a decision emerges, capture it and return here

---

## MVP Build Phases

### Phase 1: Foundation (Week 1)
**Goal**: Database schema, word list, basic infrastructure

| Component | Chat Name | Handoff Doc | Status |
|-----------|-----------|-------------|--------|
| Database Schema | Master Schema Planner Chat | `HANDOFF_PHASE1_DATABASE_NEO4J.md` | ⏳ Not Started |
| Word List Compilation | Phase 1 - Word List | `HANDOFF_PHASE1_WORDLIST.md` | ⏳ Not Started |
| Landing Page | Phase 1 - Landing Page | `HANDOFF_PHASE1_LANDING.md` | ⏳ Not Started |

### Phase 2: Core Features (Week 2)
**Goal**: User auth, learning interface, basic verification

| Component | Chat Name | Handoff Doc | Status |
|-----------|-----------|-------------|--------|
| User Auth & Accounts | Phase 2 - Auth | `HANDOFF_PHASE2_AUTH.md` | ⏳ Not Started |
| Learning Interface | Phase 2 - Learning UI | `HANDOFF_PHASE2_LEARNING.md` | ⏳ Not Started |
| MCQ Generator | Phase 2 - MCQ System | `HANDOFF_PHASE2_MCQ.md` | ⏳ Not Started |

### Phase 3: Verification & Points (Week 3)
**Goal**: Spaced repetition, points calculation, parent dashboard

| Component | Chat Name | Handoff Doc | Status |
|-----------|-----------|-------------|--------|
| Verification Scheduler | Phase 3 - Verification | `HANDOFF_PHASE3_VERIFICATION.md` | ⏳ Not Started |
| Points System | Phase 3 - Points | `HANDOFF_PHASE3_POINTS.md` | ⏳ Not Started |
| Parent Dashboard | Phase 3 - Dashboard | `HANDOFF_PHASE3_DASHBOARD.md` | ⏳ Not Started |

### Phase 4: Withdrawal & Launch (Week 4)
**Goal**: Withdrawal flow, notifications, beta launch prep

| Component | Chat Name | Handoff Doc | Status |
|-----------|-----------|-------------|--------|
| Withdrawal System | Phase 4 - Withdrawal | `HANDOFF_PHASE4_WITHDRAWAL.md` | ⏳ Not Started |
| Notifications | Phase 4 - Notifications | `HANDOFF_PHASE4_NOTIFICATIONS.md` | ⏳ Not Started |
| Beta Launch Prep | Phase 4 - Launch | `HANDOFF_PHASE4_LAUNCH.md` | ⏳ Not Started |

---

## Work Status Tracking

### Phase 1: Foundation

#### Database Schema
- **Status**: ⏳ Not Started
- **Assigned Chat**: Master Schema Planner Chat (coordinates Neo4j + PostgreSQL)
- **Last Update**: [Date]
- **Blockers**: None
- **Notes**: Neo4j for Learning Point Cloud, PostgreSQL for user data (see NEO4J_VS_POSTGRESQL_ANALYSIS.md)
- **Sub-tasks**: Neo4j Setup, PostgreSQL Setup, Schema Integration

#### Word List Compilation
- **Status**: ⏳ Not Started
- **Assigned Chat**: [None yet]
- **Last Update**: [Date]
- **Blockers**: None
- **Notes**: Combine CEFR + Taiwan + Corpus (3,000-4,000 words)

#### Landing Page
- **Status**: ⏳ Not Started
- **Assigned Chat**: [None yet]
- **Last Update**: [Date]
- **Blockers**: None
- **Notes**: Framer/Carrd, waitlist collection

### Phase 2: Core Features

#### User Auth & Accounts
- **Status**: ⏳ Not Started
- **Assigned Chat**: [None yet]
- **Last Update**: [Date]
- **Blockers**: Depends on Phase 1 (Database)
- **Notes**: Supabase auth, parent + child accounts

#### Learning Interface
- **Status**: ⏳ Not Started
- **Assigned Chat**: [None yet]
- **Last Update**: [Date]
- **Blockers**: Depends on Phase 1 (Word List, Database)
- **Notes**: Flashcard UI, word display

#### MCQ Generator
- **Status**: ⏳ Not Started
- **Assigned Chat**: [None yet]
- **Last Update**: [Date]
- **Blockers**: Depends on Phase 1 (Word List, Database)
- **Notes**: 6-option MCQ with distractors

### Phase 3: Verification & Points

#### Verification Scheduler
- **Status**: ⏳ Not Started
- **Assigned Chat**: [None yet]
- **Last Update**: [Date]
- **Blockers**: Depends on Phase 2 (MCQ System)
- **Notes**: Day 1, 3, 7 scheduling

#### Points System
- **Status**: ⏳ Not Started
- **Assigned Chat**: [None yet]
- **Last Update**: [Date]
- **Blockers**: Depends on Phase 2 (Learning Interface)
- **Notes**: Tier 1-2 points calculation

#### Parent Dashboard
- **Status**: ⏳ Not Started
- **Assigned Chat**: [None yet]
- **Last Update**: [Date]
- **Blockers**: Depends on Phase 3 (Points System)
- **Notes**: Progress tracking, withdrawal requests

### Phase 4: Withdrawal & Launch

#### Withdrawal System
- **Status**: ⏳ Not Started
- **Assigned Chat**: [None yet]
- **Last Update**: [Date]
- **Blockers**: Depends on Phase 3 (Points System)
- **Notes**: Stripe Connect or local payment

#### Notifications
- **Status**: ⏳ Not Started
- **Assigned Chat**: [None yet]
- **Last Update**: [Date]
- **Blockers**: Depends on Phase 3 (Verification, Points)
- **Notes**: Email notifications (Resend/SendGrid)

#### Beta Launch Prep
- **Status**: ⏳ Not Started
- **Assigned Chat**: [None yet]
- **Last Update**: [Date]
- **Blockers**: Depends on all previous phases
- **Notes**: Testing, bug fixes, documentation

---

## Key Decisions Log

### Technical Decisions

| Decision | Date | Rationale | Impact |
|----------|------|-----------|--------|
| Direct cash withdrawal (not game currency) | [Date] | Simpler, faster, lower legal risk | MVP scope |
| PostgreSQL + JSONB (not Neo4j) | [Date] | Faster to build, good enough for MVP | Database choice |
| 3,000-4,000 words (Phase 1) | [Date] | CEFR + Taiwan + Corpus combined | Word list size |
| Tier 1-2 only (MVP) | [Date] | Validate core concept first | Learning points scope |

### Business Decisions

| Decision | Date | Rationale | Impact |
|----------|------|-----------|--------|
| 4-week MVP timeline | [Date] | Fast validation | Timeline |
| 50-100 beta families | [Date] | Sufficient for validation | Beta size |
| Direct withdrawal model | [Date] | Parent flexibility | Reward model |

---

## Next Steps

### Immediate (This Week)

1. **Start Master Schema Planner Chat**
   - Assigns database setup tasks to implementation chats
   - Coordinates Neo4j + PostgreSQL work
   - Verifies completion

2. **Start Phase 1 - Word List**
   - Assign to implementation chat
   - Can run in parallel with Database Schema (after database is ready)

3. **Start Phase 1 - Landing Page**
   - Assign to implementation chat
   - Can run in parallel (independent of database)

### Week 2 (After Phase 1 Complete)

1. Phase 2 - User Auth
2. Phase 2 - Learning Interface
3. Phase 2 - MCQ Generator

---

## Handoff Documents Location

All handoff documents will be in:
```
docs/development/handoffs/
├── HANDOFF_PHASE1_DATABASE.md
├── HANDOFF_PHASE1_WORDLIST.md
├── HANDOFF_PHASE1_LANDING.md
├── HANDOFF_PHASE2_AUTH.md
├── HANDOFF_PHASE2_LEARNING.md
├── HANDOFF_PHASE2_MCQ.md
├── HANDOFF_PHASE3_VERIFICATION.md
├── HANDOFF_PHASE3_POINTS.md
├── HANDOFF_PHASE3_DASHBOARD.md
├── HANDOFF_PHASE4_WITHDRAWAL.md
├── HANDOFF_PHASE4_NOTIFICATIONS.md
└── HANDOFF_PHASE4_LAUNCH.md
```

---

## Master Prompts

See `MASTER_CHAT_PROMPTS.md` for copy-paste prompts to start each implementation chat.

---

*Last updated: [Date]*

