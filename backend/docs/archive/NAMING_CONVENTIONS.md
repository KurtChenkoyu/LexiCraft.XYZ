# LexiCraft Naming Conventions

**Purpose:** Clarify the different naming systems used throughout the codebase to avoid confusion.

**Last Updated:** January 2025

---

## Overview

The LexiCraft codebase uses **four distinct naming systems** that operate at different levels:

1. **Pipeline Phases** - Data processing workflow (0-6)
2. **Enrichment Stages** - Content enrichment levels (1-2)
3. **Relationship Roadmap Steps** - Relationship improvement plan (1-5)
4. **Example Layers** - Multi-layer example system (1-4)

---

## 1. Pipeline Phases (Data Processing Workflow)

**Scope:** Overall data processing pipeline from raw data to enriched graph

**Naming:** `Phase 0`, `Phase 1`, `Phase 2`, etc.

**Purpose:** Describe the sequential steps in the data processing pipeline

### Phase 0: Data Prep
- **File:** `backend/src/data_prep.py`
- **Purpose:** Prepare and validate input data
- **Output:** Validated word list with unified rank calculation

### Phase 1: Structure Miner
- **File:** `backend/src/structure_miner.py`
- **Purpose:** Extract WordNet skeletons (senses, definitions, examples)
- **Output:** Sense nodes with basic structure

### Phase 2: Agent Stage 1 (Basic Enrichment)
- **File:** `backend/src/agent.py`, `backend/src/agent_batched.py`
- **Purpose:** Enrich senses with definitions, examples, translations
- **Output:** Enriched senses (`s.enriched = true`)
- **Note:** This is "Stage 1" enrichment, but it's "Phase 2" in the pipeline

### Phase 3: Adversary Miner (Relationships)
- **File:** `backend/src/adversary_miner.py`
- **Purpose:** Create semantic relationships (OPPOSITE_TO, RELATED_TO, CONFUSED_WITH)
- **Output:** Relationship edges between Word nodes

### Phase 2b: Agent Stage 2 (Multi-Layer Examples) ⭐ Proposed
- **File:** `backend/src/agent_stage2.py`
- **Purpose:** Generate multi-layer example sentences
- **Output:** Multi-layer examples (`s.stage2_enriched = true`)
- **Note:** Runs after Phase 3 (needs relationships), but logically part of Phase 2

### Phase 4: Loader
- **File:** `backend/src/db_loader.py`
- **Purpose:** Inject data into Neo4j graph
- **Output:** Complete graph structure

### Phase 5: Schema
- **File:** `backend/src/optimize_db.py`
- **Purpose:** Add constraints, indexes, performance optimizations
- **Output:** Optimized database schema

### Phase 6: Factory (Orchestrator)
- **File:** `backend/src/main_factory.py`
- **Purpose:** Orchestrate all phases in sequence
- **Output:** Complete enriched graph

**Current Pipeline Flow:**
```
Phase 0 → Phase 1 → Phase 2 → Phase 3 → Phase 4 → Phase 5 → Phase 6
```

**Proposed Pipeline Flow:**
```
Phase 0 → Phase 1 → Phase 2 → Phase 3 → Phase 2b → Phase 4 → Phase 5 → Phase 6
```

---

## 2. Enrichment Stages (Content Enrichment Levels)

**Scope:** Content enrichment for individual senses

**Naming:** `Stage 1`, `Stage 2`

**Purpose:** Describe the level of content enrichment for a sense

### Stage 1: Basic Enrichment
- **Status Flag:** `s.enriched = true`
- **Content:**
  - English definition (simplified, B1/B2 level)
  - Chinese definition (translation + explanation)
  - Single example sentence (English + Chinese translation + explanation)
  - Quiz question
  - Phrases/collocations
- **Agent:** `agent.py`, `agent_batched.py`
- **Pipeline Phase:** Phase 2

### Stage 2: Multi-Layer Examples
- **Status Flag:** `s.stage2_enriched = true`
- **Content:**
  - Layer 1: 2-3 contextual examples
  - Layer 2: Opposite examples (if OPPOSITE_TO relationships exist)
  - Layer 3: Similar examples (if RELATED_TO relationships exist)
  - Layer 4: Confused examples (if CONFUSED_WITH relationships exist)
- **Agent:** `agent_stage2.py`
- **Pipeline Phase:** Phase 2b (proposed)
- **Prerequisite:** Stage 1 must be complete

**Stage Relationship:**
```
Stage 1 (Basic) → Stage 2 (Multi-Layer)
```

---

## 3. Relationship Roadmap Steps (Relationship Improvement Plan)

**Scope:** Planned improvements to relationship mining

**Naming:** `Phase 1`, `Phase 2`, `Phase 3`, `Phase 4`, `Phase 5`

**Purpose:** Roadmap for enhancing relationship quality and types

**Document:** `backend/RELATIONSHIP_IMPROVEMENT_PLAN.md`

### Relationship Phase 1: Fix RELATED_TO Relationships ✅
- **Status:** Complete
- **File:** `backend/src/relationship_miner.py`
- **Purpose:** Create sense-specific relationships with quality scoring
- **Output:** SYNONYM_OF, CLOSE_SYNONYM, RELATED_TO (sense-level)

### Relationship Phase 2: Add Morphological Relationships ⏳
- **Status:** Planned
- **File:** `backend/src/morphological_miner.py` (to be created)
- **Purpose:** Add word family relationships (prefixes, suffixes, derivations)
- **Output:** DERIVED_FROM, HAS_PREFIX, HAS_SUFFIX relationships

### Relationship Phase 3: Add Conceptual Hierarchies ⏳
- **Status:** Planned
- **Purpose:** Add hypernym/hyponym relationships
- **Output:** HYPERNYM_OF, HYPONYM_OF relationships

### Relationship Phase 4: Add Part-Whole Relationships ⏳
- **Status:** Planned
- **Purpose:** Add meronym/holonym relationships
- **Output:** HAS_PART, PART_OF relationships

### Relationship Phase 5: Add Verb Relationships ⏳
- **Status:** Planned
- **Purpose:** Add entailment relationships
- **Output:** ENTAILS relationships

**Note:** These are **NOT** the same as Pipeline Phases. They are a separate roadmap for relationship improvements.

---

## 4. Example Layers (Multi-Layer Example System)

**Scope:** Example sentences within Stage 2 enrichment

**Naming:** `Layer 1`, `Layer 2`, `Layer 3`, `Layer 4`

**Purpose:** Organize example sentences by pedagogical purpose

**Document:** `docs/development/STAGE2_MULTI_LAYER_EXAMPLES.md`

### Layer 1: Contextual Support
- **Required:** Yes (always generated)
- **Count:** 2-3 examples
- **Purpose:** Solidify understanding through multiple contexts
- **Source:** Generated by LLM (no relationships needed)
- **Storage:** `s.examples_contextual` (JSON string)

### Layer 2: Opposite Examples
- **Required:** No (conditional - only if relationships exist)
- **Count:** 1-3 examples
- **Purpose:** Show contrast with antonyms
- **Source:** `(:Word)-[:OPPOSITE_TO]->(:Word)` relationships
- **Storage:** `s.examples_opposite` (JSON string)

### Layer 3: Similar Examples
- **Required:** No (conditional - only if relationships exist)
- **Count:** 1-3 examples
- **Purpose:** Show subtle differences with synonyms
- **Source:** `(:Word)-[:RELATED_TO]->(:Word)` relationships
- **Storage:** `s.examples_similar` (JSON string)

### Layer 4: Confused Examples
- **Required:** No (conditional - only if relationships exist)
- **Count:** 1-3 examples
- **Purpose:** Prevent common errors with confused words
- **Source:** `(:Word)-[:CONFUSED_WITH]->(:Word)` relationships
- **Storage:** `s.examples_confused` (JSON string)

**Layer Relationship:**
```
Layer 1 (always) → Layer 2 (if opposites) → Layer 3 (if similar) → Layer 4 (if confused)
```

---

## Naming Convention Summary

| System | Naming | Scope | Example |
|--------|--------|-------|---------|
| **Pipeline Phases** | Phase 0-6 | Data processing workflow | "Phase 2: Agent Stage 1" |
| **Enrichment Stages** | Stage 1-2 | Content enrichment levels | "Stage 1: Basic enrichment" |
| **Relationship Steps** | Phase 1-5 | Relationship roadmap | "Relationship Phase 2: Morphological" |
| **Example Layers** | Layer 1-4 | Example organization | "Layer 2: Opposite examples" |

---

## Best Practices

### When to Use Each Naming System

1. **Pipeline Phases (0-6)**
   - Use when describing the overall data processing workflow
   - Use in factory/orchestrator code
   - Use in pipeline documentation

2. **Enrichment Stages (1-2)**
   - Use when describing content enrichment for senses
   - Use in agent code (`agent.py`, `agent_stage2.py`)
   - Use in status checks (`s.enriched`, `s.stage2_enriched`)

3. **Relationship Roadmap Steps (1-5)**
   - Use when describing relationship improvements
   - Use in relationship miner code
   - Use in relationship improvement documentation
   - **Always prefix with "Relationship"** to avoid confusion: "Relationship Phase 2"

4. **Example Layers (1-4)**
   - Use when describing multi-layer examples
   - Use in Stage 2 agent code
   - Use in example verification scripts

### Avoiding Confusion

**❌ DON'T:**
- Say "Phase 2" without context (could mean Pipeline Phase 2 or Relationship Phase 2)
- Mix Pipeline Phases with Relationship Phases

**✅ DO:**
- Say "Pipeline Phase 2" or "Relationship Phase 2"
- Say "Stage 1" or "Stage 2" for enrichment
- Say "Layer 1-4" for examples
- Use full context: "Pipeline Phase 2 runs Stage 1 enrichment"

### Code Examples

```python
# ✅ GOOD: Clear context
def run_pipeline_phase_2():
    """Pipeline Phase 2: Agent Stage 1 enrichment"""
    pass

def run_stage_1_enrichment():
    """Stage 1: Basic enrichment"""
    pass

def run_relationship_phase_2():
    """Relationship Phase 2: Morphological miner"""
    pass

def generate_layer_2_examples():
    """Layer 2: Opposite examples"""
    pass
```

```python
# ❌ BAD: Ambiguous
def run_phase_2():
    """Which Phase 2?"""
    pass
```

---

## Quick Reference

### For Data Processing
- Use **Pipeline Phases (0-6)**

### For Content Enrichment
- Use **Enrichment Stages (1-2)**
- Use **Example Layers (1-4)** within Stage 2

### For Relationship Improvements
- Use **Relationship Roadmap Steps (1-5)**
- Always prefix with "Relationship" to avoid confusion

### Status Flags in Database
- `s.enriched = true` → Stage 1 complete
- `s.stage2_enriched = true` → Stage 2 complete
- `s.examples_contextual` → Layer 1 data
- `s.examples_opposite` → Layer 2 data
- `s.examples_similar` → Layer 3 data
- `s.examples_confused` → Layer 4 data

---

## Future Considerations

### Potential Improvements

1. **Rename Relationship Phases**
   - Consider renaming to "Relationship Roadmap Steps" or "Relationship Enhancement Steps"
   - Or use "Step 1-5" instead of "Phase 1-5"

2. **Pipeline Phase 2b**
   - Consider renaming to "Phase 2.5" or "Phase 2b" for Stage 2
   - Or create separate "Phase 7" for Stage 2

3. **Documentation**
   - Always specify which naming system you're using
   - Use full names in documentation: "Pipeline Phase 2" not just "Phase 2"

---

## Related Documents

- `backend/STAGE2_IMPLEMENTATION_STATUS.md` - Stage 2 status
- `backend/RELATIONSHIP_IMPROVEMENT_PLAN.md` - Relationship roadmap
- `docs/development/STAGE2_MULTI_LAYER_EXAMPLES.md` - Layer system design
- `backend/QUICK_STATUS.md` - Current pipeline status

---

**Last Updated:** January 2025  
**Maintained By:** Development Team


