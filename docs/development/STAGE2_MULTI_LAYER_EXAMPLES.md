# Stage 2: Multi-Layer Example Enrichment

**Status:** 🟡 Design Complete, Implementation In Progress  
**Date:** January 2025  
**Related:** Phase 2 (Content Enrichment)

---

## Decision Summary

After Stage 1 enrichment (basic definitions, single examples, translations), we identified that **one example sentence is often insufficient** to fully illustrate a word sense. Learners need multiple layers of contextual support to truly understand vocabulary.

### The Problem

- Single examples can be ambiguous
- Learners need to see words in different contexts
- Contrast with opposites helps clarify meaning
- Comparison with synonyms shows subtle differences
- Addressing confusion points prevents common errors

### The Solution: 4-Layer Example System

A second enrichment stage that generates multiple example sentences organized into four pedagogical layers, leveraging existing graph relationships.

---

## Architecture Overview

### Layer 1: Contextual Support (Tiered by Usage)
**Purpose:** Provide contextual examples tiered by sense usage frequency.

**Tiered Approach:**
- **PRIMARY senses (>50% usage):** 15-20 examples - learners encounter constantly
- **COMMON senses (20-50% usage):** 8-12 examples - regular exposure
- **RARE senses (<20% usage):** 5-8 examples - occasional use

**Source:** Generated directly by Gemini (no graph relationships needed)

**Rationale:** Primary senses need MORE examples to:
- Prevent pattern memorization during spaced repetition
- Provide unique MCQs across multiple review cycles
- Support adaptive difficulty with variety

**Example for "bank" (financial institution) - PRIMARY sense:**
15-20 examples covering: formal/casual, written/spoken, school/work/daily life contexts

### Layer 2: Opposite Examples (Contrast)
**Purpose:** Show antonyms in context to highlight what the word is NOT.

**Source:** `(:Word)-[:OPPOSITE_TO]->(:Word)` relationships (489 existing)

**Example for "brave":**
- Target: "She was brave enough to speak up."
- Opposite: "He was too **cowardly** to face the challenge." (from OPPOSITE_TO relationship)

### Layer 3: Similar Examples (Nuance)
**Purpose:** Show synonyms in context to illustrate subtle differences.

**Source:** `(:Word)-[:RELATED_TO]->(:Word)` relationships (3,956 existing)

**Example for "happy":**
- Target: "I'm happy with the results."
- Similar: "She felt **joyful** after the good news." (from RELATED_TO relationship)
- Similar: "They were **pleased** with the service." (shows subtle difference)

### Layer 4: Confused Examples (Clarification)
**Purpose:** Address common confusion points, especially for Taiwan EFL learners.

**Source:** `(:Word)-[:CONFUSED_WITH]->(:Word)` relationships (1,234 existing)

**Example for "affect":**
- Target: "The weather will affect our plans."
- Confused: "The **effect** of the storm was severe." (from CONFUSED_WITH relationship, reason: "Sound")
- Clarification: Shows the difference between verb (affect) and noun (effect)

---

## Data Model

### Updated EnrichedSense Schema

```python
class ExamplePair(BaseModel):
    """A single example sentence pair (English + Chinese)."""
    example_en: str = Field(description="English example sentence")
    example_zh: str = Field(description="Traditional Chinese translation")
    context_label: Optional[str] = Field(
        default=None, 
        description="Context tag: 'formal', 'casual', 'written', 'spoken', etc."
    )
    relationship_word: Optional[str] = Field(
        default=None,
        description="The related word used in this example (for Layers 2-4)"
    )
    relationship_type: Optional[str] = Field(
        default=None,
        description="'opposite', 'similar', 'confused' (for Layers 2-4)"
    )

class EnrichedSense(BaseModel):
    """Enriched data for a specific sense (Stage 1)."""
    sense_id: str
    definition_en: str
    definition_zh: str
    example_en: str  # Single example (Stage 1 - kept for backward compatibility)
    example_zh: str
    
    # Validation Engine (Stage 1)
    quiz: VerificationQ
    mapped_phrases: List[str]

class MultiLayerExamples(BaseModel):
    """Stage 2: Multi-layer example enrichment (Tiered by usage frequency)."""
    sense_id: str
    
    # Layer 1: Contextual Support (tiered: 15-20 primary, 8-12 common, 5-8 rare)
    examples_contextual: List[ExamplePair] = Field(
        min_items=5,
        max_items=25,  # Allow up to 25 for primary senses
        description="Tiered examples: PRIMARY (15-20), COMMON (8-12), RARE (5-8)"
    )
    
    # Layer 2: Opposites (2-3 per relationship from OPPOSITE_TO)
    examples_opposite: List[ExamplePair] = Field(
        default_factory=list,
        description="Examples using antonyms to contrast meaning (2-3 per relationship)"
    )
    
    # Layer 3: Similar (2-3 per relationship from RELATED_TO)
    examples_similar: List[ExamplePair] = Field(
        default_factory=list,
        description="Examples using synonyms to show subtle differences (2-3 per relationship)"
    )
    
    # Layer 4: Confused (2-3 per relationship from CONFUSED_WITH)
    examples_confused: List[ExamplePair] = Field(
        default_factory=list,
        description="Examples showing commonly confused words in context (2-3 per relationship)"
    )
```

### Neo4j Schema Extension

**New Node Type (Optional):**
```cypher
(:Example {
    id: String,              // e.g., "bank.n.01_contextual_1"
    example_en: String,
    example_zh: String,
    layer: String,           // "contextual", "opposite", "similar", "confused"
    context_label: String,   // Optional: "formal", "casual", etc.
    relationship_word: String,  // For Layers 2-4: the related word
    relationship_type: String   // For Layers 2-4: "opposite", "similar", "confused"
})
```

**New Relationships:**
```cypher
(:Sense)-[:HAS_EXAMPLE]->(:Example)
(:Example)-[:ILLUSTRATES]->(:Word)  // For Layers 2-4: links to related word
```

**Alternative (Simpler):** Store as properties on Sense node:
```cypher
(:Sense {
    // ... existing properties ...
    examples_contextual: List[Map],  // [{example_en, example_zh, context_label}]
    examples_opposite: List[Map],     // [{example_en, example_zh, relationship_word}]
    examples_similar: List[Map],     // [{example_en, example_zh, relationship_word}]
    examples_confused: List[Map]      // [{example_en, example_zh, relationship_word, reason}]
})
```

**Decision:** Use properties on Sense node (simpler, no new node types needed).

---

## Implementation Plan

### Stage 2 Enrichment Agent

**File:** `backend/src/agent_stage2.py`

**Process:**
1. Query Neo4j for senses that have Stage 1 enrichment but not Stage 2
2. For each sense:
   - Fetch the word and sense data
   - Query relationships: `OPPOSITE_TO`, `RELATED_TO`, `CONFUSED_WITH`
   - Generate examples using Gemini with relationship context
   - Store results in Neo4j

**Gemini Prompt Structure (Tiered by Usage Frequency):**
```
You are an expert EFL curriculum developer for Taiwan.

Target Sense: {sense_id}
Definition: {definition_en} / {definition_zh}
Usage Ratio: {usage_ratio} ({tier} priority)

Generate examples in 4 layers:

1. CONTEXTUAL (TIERED - REQUIRED for MCQ variety):
   - PRIMARY senses (>50% usage): Provide 15-20 natural examples
   - COMMON senses (20-50%): Provide 8-12 natural examples
   - RARE senses (<20%): Provide 5-8 natural examples
   - Show DIVERSE contexts: formal, casual, school, work, daily life
   - Each example should be DISTINCT (different sentence structure)
   - More examples = more MEANING MCQs for verification

2. OPPOSITE (2-3 examples per antonym if antonyms exist):
   - Related words: {opposite_words}
   - Generate 2-3 examples per antonym showing contrast
   - Each example should show a different aspect of the contrast

3. SIMILAR (2-3 examples per synonym if synonyms exist):
   - Related words: {similar_words}
   - Generate 2-3 examples per synonym showing subtle differences
   - Help learners understand nuance through multiple contexts

4. CONFUSED (2-3 examples per confused word if confused words exist):
   - Confused words: {confused_words} (reasons: {reasons})
   - Generate 2-3 examples per confused word that clarify the distinction
   - Address common errors for Taiwan EFL learners

Return JSON matching MultiLayerExamples schema.
```

### Pipeline Integration

**Updated Factory Flow:**
```
Phase 0: Data Prep
Phase 1: Structure Miner (WordNet skeletons)
Phase 2a: Agent Stage 1 (Basic enrichment)
Phase 3: Adversary Miner (Relationships)
Phase 2b: Agent Stage 2 (Multi-layer examples) ⭐ NEW
Phase 4: Loader
```

**Dependencies:**
- Stage 2 requires Stage 1 to be complete (needs definitions)
- Stage 2 requires Phase 3 to be complete (needs relationships)

---

## Validation Strategy

### Validation Scripts

#### 1. `verify_example_relationships.py`
**Purpose:** Verify that Layer 2-4 examples correctly use relationship words.

**Checks:**
- Layer 2 examples contain words from `OPPOSITE_TO` relationships
- Layer 3 examples contain words from `RELATED_TO` relationships
- Layer 4 examples contain words from `CONFUSED_WITH` relationships
- Relationship words are actually used in the examples (not just mentioned)

#### 2. `verify_example_quality.py`
**Purpose:** Verify naturalness and clarity of examples.

**Checks:**
- Examples are natural and modern (not awkward/outdated)
- Examples clearly illustrate the target sense
- Layer 2 examples show appropriate contrast
- Layer 3 examples show meaningful differences
- Layer 4 examples actually clarify confusion

#### 3. `verify_layer_completeness.py`
**Purpose:** Verify that all layers are generated where appropriate.

**Checks:**
- Layer 1 has 2-3 examples (required)
- Layers 2-4 have examples if relationships exist
- Missing layers flagged for manual review
- Statistics: % of senses with complete 4-layer coverage

#### 4. `evaluate_example_pedagogy.py`
**Purpose:** LLM-based evaluation of pedagogical effectiveness.

**Checks:**
- Do examples actually help learners understand the sense?
- Are contrastive examples clear enough?
- Do synonym examples show meaningful differences?
- Do confusion examples actually clarify distinctions?

**Similar to:** `test_holistic_quality.py` (uses Gemini for evaluation)

---

## Industry Alignment

This approach aligns with established vocabulary instruction practices:

1. **Semantic Networks:** Showing relationships (synonyms, antonyms, hyponyms)
2. **Contrastive Examples:** Highlighting differences through opposites
3. **Confusion Mapping:** Addressing common errors (especially L1 interference)
4. **Multiple Contexts:** Providing varied examples to solidify meaning

**Research Support:**
- Nation (2013): Vocabulary learning benefits from seeing words in multiple contexts
- Schmitt (2010): Contrastive examples help learners distinguish similar words
- Laufer (1997): Addressing confusion points reduces fossilized errors

---

## Success Metrics

### Coverage Metrics
- % of enriched senses with Layer 1 examples (target: 100%)
- % of senses with Layer 2 examples (target: 80%+ where antonyms exist)
- % of senses with Layer 3 examples (target: 90%+ where synonyms exist)
- % of senses with Layer 4 examples (target: 70%+ where confused words exist)

### Quality Metrics
- Average example naturalness score (LLM evaluation, target: ≥0.8)
- Relationship accuracy (target: 100% - examples use correct relationship words)
- Pedagogical effectiveness score (LLM evaluation, target: ≥0.75)

### Validation Metrics
- Validation script pass rate (target: ≥95%)
- Manual review required (target: <5% of senses)

---

## Implementation Status

- [x] Design and documentation
- [ ] Data model updates
- [ ] Stage 2 enrichment agent
- [ ] Validation scripts
- [ ] Pipeline integration
- [ ] Testing and quality assurance

---

## Related Documents

- `backend/DATA_QUALITY_ENRICHMENT_PROMPT.md` - Stage 1 enrichment prompt
- `backend/src/agent.py` - Stage 1 enrichment agent
- `backend/src/adversary_miner.py` - Relationship mining
- `backend/src/verify_content_quality.py` - Stage 1 validation
- `docs/development/LEARNING_POINT_CLOUD_CONSTRUCTION_PLAN.md` - Overall architecture

