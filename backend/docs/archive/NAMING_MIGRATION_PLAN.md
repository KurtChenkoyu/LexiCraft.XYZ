# Naming Convention Migration Plan

**Purpose:** Systematically update all documentation to use the new unified naming convention

**Status:** 🟡 Planning Phase  
**Created:** January 2025

---

## New Naming Convention

### 1. Pipeline Steps (replaces "Pipeline Phases")
- **Step 0:** Data Prep
- **Step 1:** Structure Mining
- **Step 2:** Content Generation Level 1
- **Step 3:** Relationship Mining
- **Step 4:** Content Generation Level 2
- **Step 5:** Graph Loading
- **Step 6:** Schema Optimization
- **Step 7:** Orchestration

### 2. Content Levels (replaces "Enrichment Stages")
- **Level 1:** Basic Content (definitions, single examples)
- **Level 2:** Multi-Layer Content (4 layers of examples)

### 3. Relationship Milestones (replaces "Relationship Phases")
- **Milestone 1:** Quality Relationships
- **Milestone 2:** Morphological Relationships
- **Milestone 3:** Hierarchical Relationships
- **Milestone 4:** Part-Whole Relationships
- **Milestone 5:** Verb Relationships

### 4. Example Layers (unchanged)
- **Layer 1:** Contextual Support
- **Layer 2:** Opposite Examples
- **Layer 3:** Similar Examples
- **Layer 4:** Confused Examples

---

## Migration Mapping

### Old → New Terminology

| Old Term | New Term | Context |
|----------|----------|---------|
| Pipeline Phase 0 | Pipeline Step 0 | Data processing workflow |
| Pipeline Phase 1 | Pipeline Step 1 | Structure mining |
| Pipeline Phase 2 | Pipeline Step 2 | Content generation Level 1 |
| Pipeline Phase 3 | Pipeline Step 3 | Relationship mining |
| Pipeline Phase 2b | Pipeline Step 4 | Content generation Level 2 |
| Pipeline Phase 4 | Pipeline Step 5 | Graph loading |
| Pipeline Phase 5 | Pipeline Step 6 | Schema optimization |
| Pipeline Phase 6 | Pipeline Step 7 | Orchestration |
| Stage 1 | Content Level 1 | Basic content enrichment |
| Stage 2 | Content Level 2 | Multi-layer content enrichment |
| Stage 1 enrichment | Level 1 content generation | Content creation |
| Stage 2 enrichment | Level 2 content generation | Content creation |
| Relationship Phase 1 | Relationship Milestone 1 | Relationship roadmap |
| Relationship Phase 2 | Relationship Milestone 2 | Relationship roadmap |
| Relationship Phase 3 | Relationship Milestone 3 | Relationship roadmap |
| Relationship Phase 4 | Relationship Milestone 4 | Relationship roadmap |
| Relationship Phase 5 | Relationship Milestone 5 | Relationship roadmap |
| Enrichment Stage | Content Level | Content depth |
| Enrichment process | Content generation | Content creation |
| Refinement | Content improvement | Quality enhancement |

---

## Files to Update

### Priority 1: Core Documentation

1. **`backend/NAMING_CONVENTIONS.md`**
   - Update with new naming system
   - Add migration notes

2. **`backend/QUICK_STATUS.md`**
   - Update pipeline phase references
   - Update enrichment status references

3. **`backend/STAGE2_IMPLEMENTATION_STATUS.md`**
   - Rename to `CONTENT_LEVEL_2_IMPLEMENTATION_STATUS.md`
   - Update all references

4. **`backend/STAGE2_ENHANCED_IMPLEMENTATION.md`**
   - Rename to `CONTENT_LEVEL_2_ENHANCED_IMPLEMENTATION.md`
   - Update all references

5. **`backend/RELATIONSHIP_IMPROVEMENT_PLAN.md`**
   - Update "Phase" to "Milestone"
   - Update all phase references

6. **`backend/RELATIONSHIP_IMPROVEMENT_PROMPT.md`**
   - Update phase references to milestones

7. **`backend/NEXT_STEPS_PLAN.md`**
   - Update Stage 1/2 to Level 1/2
   - Update phase references

### Priority 2: Status and Reports

8. **`backend/V6.1_STATUS_REPORT.md`**
   - Update pipeline phase references
   - Update enrichment stage references

9. **`backend/CURRENT_STATUS.md`**
   - Update all naming references

10. **`backend/COMPREHENSIVE_UPDATE_SUMMARY.md`**
    - Update stage references

11. **`backend/PROMPT_REFINEMENT_SUMMARY.md`**
    - Clarify refinement vs content generation

12. **`backend/TEST_RESULTS_REAL_API.md`**
    - Update stage references

### Priority 3: Code Comments and Docstrings

13. **`backend/src/main_factory.py`**
    - Update docstrings
    - Update comments

14. **`backend/src/agent.py`**
    - Update docstrings
    - Update comments

15. **`backend/src/agent_stage2.py`**
    - Update docstrings
    - Update comments
    - Consider renaming to `agent_level2.py`

16. **`backend/src/agent_batched.py`**
    - Update docstrings
    - Update comments

17. **`backend/src/structure_miner.py`**
    - Update phase references

18. **`backend/src/adversary_miner.py`**
    - Update phase references

19. **`backend/src/data_prep.py`**
    - Update phase references

20. **`backend/src/db_loader.py`**
    - Update phase references

21. **`backend/src/relationship_miner.py`**
    - Update milestone references

### Priority 4: Scripts and Tools

22. **`backend/scripts/check_enrichment_verification.py`**
    - Update variable names
    - Update output messages

23. **`backend/scripts/monitor_batch2.py`**
    - Update status messages

24. **`backend/src/verify_layer_completeness.py`**
    - Update layer references (keep as is)
    - Update stage references to level

### Priority 5: Documentation Files

25. **`docs/development/STAGE2_MULTI_LAYER_EXAMPLES.md`**
    - Rename to `CONTENT_LEVEL_2_MULTI_LAYER_EXAMPLES.md`
    - Update all references

26. **`docs/development/LEARNING_POINT_CLOUD_CONSTRUCTION_PLAN.md`**
    - Update phase references

27. **`docs/development/MASTER_CHAT_PLAN.md`**
    - Update phase references

28. **`docs/03-implementation-roadmap.md`**
    - Update phase references

---

## Migration Steps

### Step 1: Update Core Naming Document ✅
- [x] Create `NAMING_CONVENTIONS.md` with new system
- [ ] Update `NAMING_CONVENTIONS.md` with migration notes
- [ ] Add old→new mapping table

### Step 2: Update Priority 1 Files
- [ ] Update `QUICK_STATUS.md`
- [ ] Update `STAGE2_IMPLEMENTATION_STATUS.md` (or rename)
- [ ] Update `STAGE2_ENHANCED_IMPLEMENTATION.md` (or rename)
- [ ] Update `RELATIONSHIP_IMPROVEMENT_PLAN.md`
- [ ] Update `RELATIONSHIP_IMPROVEMENT_PROMPT.md`
- [ ] Update `NEXT_STEPS_PLAN.md`

### Step 3: Update Priority 2 Files
- [ ] Update status reports
- [ ] Update summary documents
- [ ] Update test result documents

### Step 4: Update Code Files
- [ ] Update docstrings in `main_factory.py`
- [ ] Update docstrings in `agent.py`
- [ ] Update docstrings in `agent_stage2.py`
- [ ] Update docstrings in other agent files
- [ ] Update comments in miner files
- [ ] Consider renaming `agent_stage2.py` → `agent_level2.py`

### Step 5: Update Scripts
- [ ] Update verification scripts
- [ ] Update monitoring scripts
- [ ] Update status check scripts

### Step 6: Update Documentation
- [ ] Update docs in `docs/development/`
- [ ] Update roadmap documents
- [ ] Update implementation guides

### Step 7: Verification
- [ ] Search for remaining old terminology
- [ ] Verify all references updated
- [ ] Test that documentation is consistent
- [ ] Update README files

---

## Search Patterns to Find and Replace

### Pattern 1: Pipeline Phases
```bash
# Find all instances
grep -r "Phase [0-6]" backend/ --include="*.md" --include="*.py"

# Replacements:
"Phase 0" → "Pipeline Step 0"
"Phase 1" → "Pipeline Step 1"
"Phase 2" → "Pipeline Step 2"
"Phase 3" → "Pipeline Step 3"
"Phase 4" → "Pipeline Step 4"
"Phase 5" → "Pipeline Step 5"
"Phase 6" → "Pipeline Step 7"
"Phase 2b" → "Pipeline Step 4"
```

### Pattern 2: Enrichment Stages
```bash
# Find all instances
grep -r "Stage [12]" backend/ --include="*.md" --include="*.py"
grep -r "enrichment" backend/ --include="*.md" --include="*.py" -i

# Replacements:
"Stage 1" → "Content Level 1" (when referring to content)
"Stage 2" → "Content Level 2" (when referring to content)
"Stage 1 enrichment" → "Level 1 content generation"
"Stage 2 enrichment" → "Level 2 content generation"
"Enrichment Stage" → "Content Level"
```

### Pattern 3: Relationship Phases
```bash
# Find all instances
grep -r "Relationship Phase" backend/ --include="*.md" --include="*.py"
grep -r "Phase [1-5]" backend/RELATIONSHIP* --include="*.md"

# Replacements:
"Relationship Phase 1" → "Relationship Milestone 1"
"Relationship Phase 2" → "Relationship Milestone 2"
"Relationship Phase 3" → "Relationship Milestone 3"
"Relationship Phase 4" → "Relationship Milestone 4"
"Relationship Phase 5" → "Relationship Milestone 5"
```

### Pattern 4: Status Flags (Keep in Code)
```bash
# These should NOT be changed (database schema):
s.enriched = true  # Keep as is
s.stage2_enriched = true  # Keep as is (or consider migration later)

# But update comments:
# "Stage 1 enrichment" → "Level 1 content generation"
# "Stage 2 enrichment" → "Level 2 content generation"
```

---

## File Renaming Considerations

### Files to Consider Renaming

1. **`agent_stage2.py` → `agent_level2.py`**
   - **Pros:** Clearer naming, matches new convention
   - **Cons:** Breaking change, need to update imports
   - **Decision:** Defer to later migration (separate task)

2. **`STAGE2_*.md` → `CONTENT_LEVEL_2_*.md`**
   - **Pros:** Consistent naming
   - **Cons:** Many references to update
   - **Decision:** Update content first, rename later if needed

3. **Keep Layer files as-is**
   - Layer naming is clear and doesn't conflict
   - No changes needed

---

## Migration Checklist

### Pre-Migration
- [x] Create naming conventions document
- [x] Create migration plan
- [ ] Review and approve new naming system
- [ ] Create backup of all documentation

### Phase 1: Core Documentation (Week 1)
- [ ] Update `NAMING_CONVENTIONS.md`
- [ ] Update `QUICK_STATUS.md`
- [ ] Update `STAGE2_IMPLEMENTATION_STATUS.md`
- [ ] Update `STAGE2_ENHANCED_IMPLEMENTATION.md`
- [ ] Update `RELATIONSHIP_IMPROVEMENT_PLAN.md`
- [ ] Update `NEXT_STEPS_PLAN.md`

### Phase 2: Status Reports (Week 1)
- [ ] Update all status report files
- [ ] Update summary documents
- [ ] Update test result documents

### Phase 3: Code Documentation (Week 2)
- [ ] Update docstrings in core files
- [ ] Update comments in pipeline files
- [ ] Update comments in agent files
- [ ] Update comments in miner files

### Phase 4: Scripts and Tools (Week 2)
- [ ] Update verification scripts
- [ ] Update monitoring scripts
- [ ] Update status check scripts

### Phase 5: Documentation (Week 2)
- [ ] Update docs in `docs/development/`
- [ ] Update roadmap documents
- [ ] Update implementation guides

### Post-Migration
- [ ] Verify all references updated
- [ ] Test documentation consistency
- [ ] Update README files
- [ ] Create migration completion report

---

## Verification Commands

### Check for Remaining Old Terminology

```bash
# Check for old phase references (should be minimal)
grep -r "Pipeline Phase" backend/ --include="*.md" --include="*.py" | grep -v "NAMING_CONVENTIONS\|NAMING_MIGRATION"

# Check for old stage references (should be minimal)
grep -r "Stage [12] enrichment" backend/ --include="*.md" --include="*.py" | grep -v "NAMING_CONVENTIONS\|NAMING_MIGRATION"

# Check for old relationship phase references
grep -r "Relationship Phase" backend/ --include="*.md" --include="*.py" | grep -v "NAMING_CONVENTIONS\|NAMING_MIGRATION"

# Verify new terminology is used
grep -r "Pipeline Step" backend/ --include="*.md" | wc -l
grep -r "Content Level" backend/ --include="*.md" | wc -l
grep -r "Relationship Milestone" backend/ --include="*.md" | wc -l
```

---

## Breaking Changes

### Database Schema
- **Status flags:** `s.enriched`, `s.stage2_enriched` - **KEEP AS IS**
  - These are database properties, changing would require migration
  - Update comments/documentation only

### Code Imports
- **File names:** Consider keeping `agent_stage2.py` name for now
  - Changing would require updating all imports
  - Can be done in separate migration

### API/External References
- **None identified** - This is primarily documentation update

---

## Rollback Plan

If issues arise:

1. **Documentation only:** Easy rollback via git
2. **No database changes:** Schema remains unchanged
3. **No code logic changes:** Only comments/docstrings updated
4. **Incremental approach:** Can rollback individual files if needed

---

## Timeline Estimate

- **Phase 1 (Core Docs):** 2-3 hours
- **Phase 2 (Status Reports):** 1-2 hours
- **Phase 3 (Code Docs):** 2-3 hours
- **Phase 4 (Scripts):** 1 hour
- **Phase 5 (Documentation):** 2-3 hours
- **Verification:** 1 hour

**Total:** ~10-12 hours

---

## Success Criteria

✅ All documentation uses new naming convention  
✅ No ambiguous "Phase" references  
✅ Clear distinction between:
   - Pipeline Steps (workflow)
   - Content Levels (content depth)
   - Relationship Milestones (roadmap)
   - Example Layers (example organization)  
✅ All references are consistent  
✅ Verification commands pass  

---

## Next Steps

1. **Review and approve** this migration plan
2. **Start with Priority 1 files** (core documentation)
3. **Verify incrementally** after each phase
4. **Complete verification** at the end
5. **Update this document** with completion status

---

**Status:** 🟡 Ready for Review  
**Last Updated:** January 2025


