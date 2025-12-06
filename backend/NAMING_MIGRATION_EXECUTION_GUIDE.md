# Naming Convention Migration - Execution Guide

**Purpose:** Step-by-step guide for executing the naming convention migration

**Status:** 🟡 Ready to Execute  
**Created:** January 2025

---

## Migration Scope Summary

Based on audit results:

- **163 files** scanned
- **432 Pipeline Phase references** to update
- **299 Enrichment Stage references** to update
- **40 Relationship Phase references** to update
- **576 generic "enrichment" references** (many may be fine as-is)

---

## Execution Strategy

### Approach: Incremental, Priority-Based

1. **Start with core documentation** (highest visibility)
2. **Update in small batches** (verify after each)
3. **Keep database schema unchanged** (status flags stay as-is)
4. **Update comments/docstrings** (code clarity)

---

## Step-by-Step Execution

### Phase 1: Core Documentation (2-3 hours)

**Files to update:**
1. `QUICK_STATUS.md`
2. `STAGE2_IMPLEMENTATION_STATUS.md`
3. `STAGE2_ENHANCED_IMPLEMENTATION.md`
4. `RELATIONSHIP_IMPROVEMENT_PLAN.md`
5. `RELATIONSHIP_IMPROVEMENT_PROMPT.md`
6. `NEXT_STEPS_PLAN.md`
7. `NAMING_CONVENTIONS.md` (update with new system)

**Replacements:**
- "Pipeline Phase 0-6" → "Pipeline Step 0-7"
- "Stage 1/2" → "Content Level 1/2"
- "Relationship Phase 1-5" → "Relationship Milestone 1-5"
- "Enrichment Stage" → "Content Level"

**Verification:**
```bash
# Check remaining old references
grep -r "Pipeline Phase" backend/ --include="*.md" | grep -v "NAMING_MIGRATION\|NAMING_CONVENTIONS" | wc -l
```

---

### Phase 2: Status Reports (1-2 hours)

**Files to update:**
- `V6.1_STATUS_REPORT.md`
- `CURRENT_STATUS.md`
- `COMPREHENSIVE_UPDATE_SUMMARY.md`
- `TEST_RESULTS_REAL_API.md`
- `PROMPT_REFINEMENT_SUMMARY.md`

**Focus:** Update phase/stage references in status descriptions

---

### Phase 3: Code Documentation (2-3 hours)

**Files to update:**
- `backend/src/main_factory.py` (docstrings, comments)
- `backend/src/agent.py` (docstrings, comments)
- `backend/src/agent_stage2.py` (docstrings, comments)
- `backend/src/agent_batched.py` (docstrings, comments)
- `backend/src/structure_miner.py` (comments)
- `backend/src/adversary_miner.py` (comments)
- `backend/src/data_prep.py` (comments)
- `backend/src/db_loader.py` (comments)

**Focus:** Update comments and docstrings, keep code logic unchanged

---

### Phase 4: Scripts (1 hour)

**Files to update:**
- `backend/scripts/check_enrichment_verification.py`
- `backend/scripts/monitor_batch2.py`
- `backend/src/verify_layer_completeness.py`

**Focus:** Update output messages and variable names

---

### Phase 5: Documentation Files (2-3 hours)

**Files to update:**
- `docs/development/STAGE2_MULTI_LAYER_EXAMPLES.md`
- `docs/development/LEARNING_POINT_CLOUD_CONSTRUCTION_PLAN.md`
- Other docs in `docs/` directory

---

## Replacement Patterns

### Pattern 1: Pipeline Phases
```bash
# Find
Pipeline Phase 0
Pipeline Phase 1
Pipeline Phase 2
Pipeline Phase 3
Pipeline Phase 4
Pipeline Phase 5
Pipeline Phase 6
Phase 2b

# Replace with
Pipeline Step 0
Pipeline Step 1
Pipeline Step 2
Pipeline Step 3
Pipeline Step 4
Pipeline Step 5
Pipeline Step 6
Pipeline Step 7
Pipeline Step 4  # (for Phase 2b)
```

### Pattern 2: Enrichment Stages
```bash
# Find
Stage 1
Stage 2
Stage 1 enrichment
Stage 2 enrichment
Enrichment Stage

# Replace with
Content Level 1
Content Level 2
Level 1 content generation
Level 2 content generation
Content Level
```

### Pattern 3: Relationship Phases
```bash
# Find
Relationship Phase 1
Relationship Phase 2
Relationship Phase 3
Relationship Phase 4
Relationship Phase 5

# Replace with
Relationship Milestone 1
Relationship Milestone 2
Relationship Milestone 3
Relationship Milestone 4
Relationship Milestone 5
```

### Pattern 4: Context-Specific
```bash
# When "enrichment" refers to the process:
"enrichment process" → "content generation process"
"enrichment pipeline" → "content generation pipeline"

# When "enrichment" refers to status:
"enriched" → "has Level 1 content" or keep "enriched" (status flag)
"s.enriched" → Keep as-is (database property)
```

---

## What NOT to Change

### Database Schema
- ✅ Keep `s.enriched = true` (database property)
- ✅ Keep `s.stage2_enriched = true` (database property)
- ✅ Keep property names in Neo4j queries

### Code Logic
- ✅ Keep function names (e.g., `get_enrichment()`)
- ✅ Keep variable names in code
- ✅ Keep file names (for now - can rename later)

### API/External
- ✅ Keep any external API references
- ✅ Keep user-facing messages (if any)

---

## Verification Checklist

After each phase:

- [ ] Run audit script: `python3 scripts/audit_naming_conventions.py`
- [ ] Check for remaining old references
- [ ] Verify new terminology is used consistently
- [ ] Test that documentation still makes sense
- [ ] Check that code still works (no logic changes)

---

## Rollback Plan

If issues arise:

1. **Git revert** specific files
2. **No database impact** (schema unchanged)
3. **No code logic changes** (only comments/docs)
4. **Incremental rollback** possible

---

## Success Metrics

✅ **Zero ambiguous "Phase" references**  
✅ **Clear distinction between:**
   - Pipeline Steps (workflow)
   - Content Levels (content depth)
   - Relationship Milestones (roadmap)
   - Example Layers (example organization)  
✅ **All Priority 1 files updated**  
✅ **Code comments/docstrings updated**  
✅ **Documentation is consistent**  

---

## Quick Commands

### Before Migration
```bash
# Run audit
python3 scripts/audit_naming_conventions.py > audit_before.txt

# Count references
grep -r "Pipeline Phase" backend/ --include="*.md" | wc -l
grep -r "Stage [12]" backend/ --include="*.md" | wc -l
```

### During Migration
```bash
# Check progress
grep -r "Pipeline Step" backend/ --include="*.md" | wc -l
grep -r "Content Level" backend/ --include="*.md" | wc -l
```

### After Migration
```bash
# Verify completion
grep -r "Pipeline Phase" backend/ --include="*.md" | grep -v "NAMING_MIGRATION\|NAMING_CONVENTIONS" | wc -l
# Should be 0 or very low

# Run final audit
python3 scripts/audit_naming_conventions.py > audit_after.txt
```

---

## Timeline

- **Phase 1 (Core Docs):** 2-3 hours
- **Phase 2 (Status Reports):** 1-2 hours  
- **Phase 3 (Code Docs):** 2-3 hours
- **Phase 4 (Scripts):** 1 hour
- **Phase 5 (Documentation):** 2-3 hours
- **Verification:** 1 hour

**Total:** ~10-12 hours

---

## Next Steps

1. ✅ Review this execution guide
2. ✅ Run initial audit: `python3 scripts/audit_naming_conventions.py`
3. ⏳ Start with Phase 1 (Core Documentation)
4. ⏳ Verify after each phase
5. ⏳ Complete all phases
6. ⏳ Final verification

---

**Status:** 🟡 Ready to Begin  
**Last Updated:** January 2025


