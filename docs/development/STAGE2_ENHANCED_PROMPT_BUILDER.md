# Stage 2 Enhanced Prompt Builder

**Status:** ✅ Design Complete, Implementation In Progress  
**Date:** January 2025

---

## Overview

The enhanced prompt builder leverages the full data structure available in Neo4j to provide richer context to the LLM, resulting in higher quality, more contextually appropriate examples.

---

## Current vs Enhanced Approach

### Current (Minimal Data)
**Fetches:**
- Word name
- Sense ID
- Definition (EN + ZH)

**Uses in prompt:**
- Basic word/definition context
- Hardcoded "B1/B2" level
- No awareness of part of speech, frequency, or Taiwan context

### Enhanced (Full Data Utilization)
**Fetches:**
- All Word properties: `frequency_rank`, `moe_level`, `cefr`, `is_moe_word`
- All Sense properties: `pos`, `example_en`, `example_zh`, `usage_ratio`
- Related data: `phrases` mapped to sense

**Uses in prompt:**
- Dynamic CEFR level (actual or inferred)
- Part of speech awareness (grammar correctness)
- Taiwan MOE context (exam vocabulary awareness)
- Sense priority (primary vs secondary)
- Existing example reference (avoid duplication)
- Common phrases (natural usage)

---

## Data Structure Utilization

### Word Node Properties

| Property | Usage in Prompt | Benefit |
|----------|----------------|---------|
| `cefr` | Dynamic target level | Use actual difficulty, not hardcoded |
| `moe_level` | Taiwan context | Highlight exam vocabulary |
| `is_moe_word` | Special attention | Emphasize importance for Taiwan learners |
| `frequency_rank` | Difficulty inference | Lower rank = more common = simpler examples |

### Sense Node Properties

| Property | Usage in Prompt | Benefit |
|----------|----------------|---------|
| `pos` | Grammar awareness | Generate grammatically correct examples |
| `example_en` | Reference | Avoid duplicating Stage 1 example |
| `example_zh` | Reference | Ensure variety |
| `usage_ratio` | Priority awareness | Emphasize primary senses, contextualize rare ones |

### Relationships

| Relationship | Usage in Prompt | Benefit |
|--------------|----------------|---------|
| `(:Phrase)-[:MAPS_TO_SENSE]` | Natural phrases | Use common collocations in examples |
| `(:Word)-[:OPPOSITE_TO]` | Contrast examples | With definitions for clarity |
| `(:Word)-[:RELATED_TO]` | Similar examples | With definitions for nuance |
| `(:Word)-[:CONFUSED_WITH]` | Clarification | With reasons for targeted help |

---

## CEFR Level Detection Strategy

### Priority Order:
1. **Use `w.cefr` if available** (most accurate)
2. **Infer from `w.moe_level`** (Taiwan-specific mapping)
3. **Infer from `w.frequency_rank`** (common words = easier)
4. **Default to "B1/B2"** (fallback)

### Mapping Logic:

```python
# MOE Level to CEFR
moe_to_cefr = {
    1: "A1",   # Elementary
    2: "A2",   # Elementary
    3: "B1",   # Intermediate
    4: "B2",   # Intermediate
    5: "C1",   # Advanced
    6: "C2"    # Advanced
}

# Frequency Rank to CEFR (approximate)
if frequency_rank < 500:
    inferred_cefr = "A1/A2"  # Very common words
elif frequency_rank < 2000:
    inferred_cefr = "B1/B2"  # Common words
else:
    inferred_cefr = "C1/C2"  # Less common words
```

---

## Enhanced Prompt Structure

### 1. Context Section (Rich Metadata)
```
Target Sense: bank.n.01
Word: "bank"
Part of Speech: noun
CEFR Level: B1
Taiwan MOE Level: 3
⚠️ This word appears in Taiwan MOE exam vocabulary
Frequency Rank: 150 (lower = more common)
⚠️ This is the PRIMARY sense (usage ratio: 85.0%)

Existing Example (from Stage 1):
  EN: I need to deposit money at the bank.
  ZH: 我需要在銀行存錢。
  → Generate NEW examples that are DIFFERENT from this one

Common Phrases for this sense:
  bank account, bank loan, bank teller, savings bank
  → Consider using these phrases in examples if natural
```

### 2. Language Requirements (Dynamic)
```
CRITICAL LANGUAGE REQUIREMENTS:
- Use SIMPLE, CLEAR English suitable for B1 level learners
- Keep sentences short (10-20 words maximum for B1)
- Pay special attention: This word is in Taiwan MOE exam vocabulary (Level 3)
- This is the PRIMARY sense (85.0% usage) - make examples very clear

GRAMMAR NOTE: This is a NOUN. Examples must use correct noun grammar.
```

### 3. Layer Instructions (Conditional)
- Only include layers that have relationships
- Each layer includes definitions of relationship words
- Explicit contrast/similarity instructions

---

## Hybrid Approach Implementation

### Conditional Layer Generation

**Strategy:**
- Layer 1: Always included (required)
- Layer 2: Only if `OPPOSITE_TO` relationships exist
- Layer 3: Only if `RELATED_TO` relationships exist
- Layer 4: Only if `CONFUSED_WITH` relationships exist

**Benefits:**
- Shorter prompts (no empty sections)
- Lower token usage
- More focused instructions
- Better quality (LLM focuses on relevant layers)

**Implementation:**
```python
prompt_sections = []

# Layer 1: Always
prompt_sections.append(layer1_section)

# Layer 2: Conditional
if has_opposites:
    prompt_sections.append(layer2_section)

# Layer 3: Conditional
if has_similar:
    prompt_sections.append(layer3_section)

# Layer 4: Conditional
if has_confused:
    prompt_sections.append(layer4_section)

prompt = "\n".join(prompt_sections)
```

---

## Relationship Enhancement

### Current: Word Names Only
```
Related antonyms: withdraw, save, invest
```

### Enhanced: With Definitions
```
Related antonyms:
  * "withdraw" (definition: "to take money out of an account")
  * "save" (definition: "to keep money for future use")
  * "invest" (definition: "to put money into something to make profit")
```

**Implementation:**
- Fetch antonyms with their primary sense definitions
- Include in prompt for semantic clarity
- LLM knows what to contrast with what

---

## Simple English Requirements

### Explicit Instructions Added:
1. **Sentence Length:** "Keep sentences short (10-20 words maximum)"
2. **Vocabulary:** "Use common, everyday words"
3. **Grammar:** "Avoid complex grammar structures"
4. **Clarity:** "Make examples immediately understandable"
5. **Level-Appropriate:** "Suitable for {cefr_level} level learners"

### Why Explicit?
- "B1/B2 learners" is implied, but not actionable
- LLM needs concrete constraints
- Prevents overly complex examples
- Ensures accessibility

---

## Example: Full Enhanced Prompt

For word "bank" (financial institution):

```
You are an expert EFL curriculum developer for Taiwan, specializing in vocabulary instruction for B1 learners.

Target Sense: bank.n.01
Word: "bank"
Part of Speech: noun
CEFR Level: B1
Taiwan MOE Level: 3
⚠️ This word appears in Taiwan MOE exam vocabulary
Frequency Rank: 150 (lower = more common)
⚠️ This is the PRIMARY sense (usage ratio: 85.0%)

Existing Example (from Stage 1):
  EN: I need to deposit money at the bank.
  ZH: 我需要在銀行存錢。
  → Generate NEW examples that are DIFFERENT from this one

Common Phrases for this sense:
  bank account, bank loan, bank teller, savings bank
  → Consider using these phrases in examples if natural

Definition (EN): A financial institution that accepts deposits
Definition (ZH): 銀行

CRITICAL LANGUAGE REQUIREMENTS:
- Use SIMPLE, CLEAR English suitable for B1 level learners
- Keep sentences short (10-20 words maximum for B1)
- Use common, everyday words that B1 learners would know
- Avoid complex grammar structures beyond B1 level
- Make examples immediately understandable without explanation
- Pay special attention: This word is in Taiwan MOE exam vocabulary (Level 3)
- This is the PRIMARY sense (85.0% usage) - make examples very clear

GRAMMAR NOTE: This is a NOUN. Examples must use correct noun grammar.

REFERENCE: You already have this example: "I need to deposit money at the bank."
  → Generate DIFFERENT examples that show other contexts/uses

Your task is to generate example sentences organized into pedagogical layers:

1. CONTEXTUAL SUPPORT (REQUIRED - 2-3 examples):
   - Provide 2-3 natural, modern example sentences that clearly illustrate this sense
   - Use SIMPLE English: short sentences, common words, clear structure
   - Show different contexts/registers if appropriate
   - Each example should solidify understanding of this specific sense
   - Examples must be immediately understandable to B1 learners
   - Avoid complex grammar or vocabulary beyond B1 level
   - Consider using phrases like: bank account, bank loan, bank teller

2. OPPOSITE EXAMPLES:
  * "withdraw" (definition: "to take money out of an account")
  * "save" (definition: "to keep money for future use")
   
   - For each antonym listed above, generate 1-2 examples that:
     * Use SIMPLE English: short, clear sentences with common words
     * Use the antonym word in a natural sentence
     * Show clear contrast with the target sense
     * Highlight what aspect of the target sense is being contrasted
     * Make the distinction clear to help learners understand the difference
     * Keep language simple enough for B1 learners to understand immediately
   
   - Example structure:
     Target sense: "I deposited money at the bank." (simple, clear)
     Contrast: "He withdrew money from the bank." (shows opposite action: depositing vs withdrawing)

[... rest of prompt ...]
```

---

## Implementation Checklist

- [x] Document enhanced approach
- [ ] Update data fetching query
- [ ] Add CEFR level detection logic
- [ ] Enhance relationship fetching (with definitions)
- [ ] Implement conditional layer generation
- [ ] Add explicit simple English requirements
- [ ] Update prompt builder with all context
- [ ] Test with sample words

---

## Benefits Summary

1. **Better Quality:** Richer context = better examples
2. **Appropriate Difficulty:** Dynamic CEFR = right complexity
3. **Taiwan Context:** MOE awareness = exam relevance
4. **Grammar Correctness:** POS awareness = proper usage
5. **Variety:** Existing example reference = no duplication
6. **Natural Usage:** Phrase integration = authentic examples
7. **Cost Efficiency:** Hybrid approach = shorter prompts
8. **Clarity:** Explicit instructions = consistent quality

---

## Related Documents

- `docs/development/STAGE2_MULTI_LAYER_EXAMPLES.md` - Original design
- `backend/src/agent_stage2.py` - Implementation
- `backend/STAGE2_IMPLEMENTATION_STATUS.md` - Status tracking

