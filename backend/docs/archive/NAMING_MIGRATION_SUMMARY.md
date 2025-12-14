# Naming Convention Migration - Quick Summary

**Status:** 🟡 Planning Complete, Ready to Execute  
**Created:** January 2025

---

## New Naming System

| Old Term | New Term | Notes |
|----------|----------|-------|
| Pipeline Phase 0-6 | Pipeline Step 0-7 | Clearer, no overlap |
| Stage 1/2 | Content Level 1/2 | Clearer distinction |
| Relationship Phase 1-5 | Relationship Milestone 1-5 | No confusion with pipeline |
| Enrichment Stage | Content Level | More accurate |
| Layer 1-4 | Layer 1-4 | ✅ Keep as-is |

---

## Migration Scope

- **56 markdown files** to review
- **207+ references** to "Phase" terminology
- **Multiple "Stage" references** to update
- **Code comments/docstrings** to update

---

## Quick Start

1. **Run audit script:**
   ```bash
   python3 scripts/audit_naming_conventions.py
   ```

2. **Start with Priority 1 files:**
   - `QUICK_STATUS.md`
   - `STAGE2_IMPLEMENTATION_STATUS.md`
   - `RELATIONSHIP_IMPROVEMENT_PLAN.md`
   - `NEXT_STEPS_PLAN.md`

3. **Verify incrementally:**
   ```bash
   grep -r "Pipeline Phase" backend/ --include="*.md" | wc -l
   ```

---

## Full Details

See `NAMING_MIGRATION_PLAN.md` for complete migration plan.


