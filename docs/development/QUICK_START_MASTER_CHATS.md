# Quick Start: Master Chats for MVP Build

This is your quick reference for setting up master chats to build the LexiCraft MVP.

---

## Overview

We're using a **multi-chat workflow** to build the MVP in parallel. Each chat focuses on one component and reports back to the master planning chat.

**Master Chats (Coordinators/Verifiers)**:
- Assign work to implementation chats
- Track progress and status
- Verify completion reports
- Ensure quality and alignment
- Make decisions
- **Do NOT write code or create files**

**Implementation Chats (Doers)**:
- Receive assignments from master chats
- Read handoff documents
- Write code and create files
- Implement features
- Report back to master chats

---

## Step 1: Start Master Planning Chat

**Create a new chat** and paste this:

```
You are the master planning chat for LexiCraft MVP. You coordinate all implementation work and verify completion reports.

Read: docs/development/MASTER_CHAT_PLAN.md

Your role (Coordinator/Verifier):
- Assign work to implementation chats
- Track work status for all phases
- Verify completion reports from implementation chats
- Ensure quality and alignment
- Update MASTER_CHAT_PLAN.md with progress
- Make decisions about next steps

You do NOT write code or create files - you coordinate and verify.

Current status: Phase 1 starting (Database, Word List, Landing Page)
```

---

## Step 2: Start Master Schema Planner Chat

**Database Schema is complex enough to warrant its own coordinator.**

**Create a new chat** and paste this:

```
You are the Master Schema Planner for LexiCraft MVP. You coordinate all database schema work (Neo4j + PostgreSQL).

Read: docs/development/MASTER_SCHEMA_PLANNER.md

Your role (Coordinator/Verifier):
- Assign database setup tasks to implementation chats
- Coordinate Neo4j setup (assign to implementation chat)
- Coordinate PostgreSQL setup (assign to implementation chat)
- Verify completion reports
- Ensure schemas align with requirements
- Report back to Master Planning Chat when complete

You do NOT write code or create files - you coordinate and verify. Assign work to implementation chats.

Current status: Starting database schema coordination
```

---

## Step 3: Start Other Phase 1 Chats

### Landing Page (Can run in parallel with Database Schema)

**Chat: Landing Page**
```
[Copy prompt from MASTER_CHAT_PROMPTS.md - Phase 1 - Landing Page]
```

**Why parallel**: Independent of database work

### Word List (Wait for Database Schema)

**Chat: Word List**
```
[Copy prompt from MASTER_CHAT_PROMPTS.md - Phase 1 - Word List Compilation]
```

**Why wait**: Needs database to populate learning points

---

## Step 3: Report Back to Master Planning Chat

When an implementation chat completes work, ask it to create a completion report:

```
Please create a structured report of the work we just completed. Format it as follows:

**What was done:**
[Brief description]

**Decisions made:**
[Key decisions]

**Files changed:**
[List of files]

**Status:**
[✅ Complete / 🚧 In Progress / ⚠️ Blocked]

**Next steps:**
[What's next]
```

Then paste the report into the **Master Planning Chat** and update `MASTER_CHAT_PLAN.md`.

---

## File Structure

```
docs/development/
├── MASTER_CHAT_PLAN.md          # Master planning document (tracking)
├── MASTER_CHAT_PROMPTS.md       # Copy-paste prompts for each phase
├── QUICK_START_MASTER_CHATS.md  # This file
└── handoffs/
    ├── HANDOFF_PHASE1_DATABASE.md
    ├── HANDOFF_PHASE1_WORDLIST.md
    ├── HANDOFF_PHASE1_LANDING.md
    └── [More handoff docs...]
```

---

## Workflow Example

1. **Master Planning Chat** assigns "Phase 1 - Database Schema"
2. **Implementation Chat** receives prompt, reads handoff doc, implements
3. **Implementation Chat** creates completion report
4. **Master Planning Chat** receives report, updates `MASTER_CHAT_PLAN.md`
5. **Master Planning Chat** assigns next task

---

## Tips

- **Name your chats**: Use format "Phase X - [Component Name]" for easy tracking
- **Stay in thread**: Don't switch chats mid-task (preserves context)
- **Report often**: Report back when you hit milestones, not just at the end
- **Ask questions**: If blocked, ask the master planning chat

---

## Next Steps

1. Read `MASTER_CHAT_PLAN.md` to understand the full plan
2. Read `MASTER_CHAT_PROMPTS.md` for copy-paste prompts
3. Start with Phase 1 (Database, Word List, Landing Page)
4. Report back to master planning chat when done

---

**Ready to start? Copy a prompt from `MASTER_CHAT_PROMPTS.md` into a new chat!**

