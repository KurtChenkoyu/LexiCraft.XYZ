# Data Pipeline Architecture Review

## The Fundamental Question

> Is WordNet the right backbone for a B1/B2 learner-focused vocabulary app targeting Taiwan students?

---

## Current Architecture Assessment

### What We Built
```
Source Data (NGSL + MOE)
         ↓
    WordNet Mining
    (Top 3 senses)
         ↓
    Gemini Enrichment
    (Chinese, Examples)
         ↓
    Relationship Mining
    (Synonyms/Antonyms)
         ↓
      Neo4j Graph
```

### Problems Discovered Through Usage

| Issue | Root Cause | Impact |
|-------|-----------|--------|
| British spellings ("colour") | WordNet + source data | Confuses learners |
| Academic senses (quark color) | WordNet is academic | Useless content |
| Over-granular senses | WordNet's comprehensiveness | Near-duplicate content |
| Missing common senses | Top 3 limit + bad ranking | Incomplete coverage |
| Example mismatch | AI can't distinguish fine senses | Wrong examples |
| No verb senses for "drop" | POS-blind top 3 selection | Missing core meanings |

### The Core Problem

**WordNet was designed for computational linguists, not language learners.**

It optimizes for:
- ✅ Comprehensive coverage
- ✅ Academic precision  
- ✅ Semantic relationships
- ❌ Learner-appropriate definitions
- ❌ Practical usage frequency
- ❌ Clear sense distinctions

---

## Alternative Backbone Options

### Option 1: Pure WordNet (Current)
**Approach**: Use WordNet as source of truth, post-process heavily

| Pros | Cons |
|------|------|
| Free | Academic orientation |
| Comprehensive | Heavy post-processing needed |
| Structured | British spellings |
| Relationships built-in | No frequency data |
| | Over-granular senses |

**Effort to Fix**: 🔴 High - Need filters, normalization, dedup, validation
**Risk**: Death by a thousand cuts - constant data quality issues

---

### Option 2: Learner Dictionary APIs
**Approach**: Use Oxford/Cambridge/Longman learner dictionaries

| Pros | Cons |
|------|------|
| Designed for learners | Proprietary ($$) |
| B1/B2 level definitions | API rate limits |
| Frequency-tagged | License restrictions |
| Quality examples | Limited customization |

**Examples**:
- Oxford Learner's Dictionary API: ~$500-2000/year
- Cambridge API: Similar pricing
- Longman LDOCE: Academic licensing

**Effort**: 🟡 Medium - Integration work, licensing
**Risk**: Cost, vendor dependency, legal constraints

---

### Option 3: Wiktionary
**Approach**: Use Wiktionary structured data

| Pros | Cons |
|------|------|
| Free, open | Quality varies by entry |
| Modern usage | No consistent structure |
| Multiple languages | No learner levels |
| Active community | Parsing complexity |

**Effort**: 🟡 Medium - Parsing, quality filtering
**Risk**: Inconsistent quality, maintenance burden

---

### Option 4: AI-First Generation
**Approach**: Use word list only, AI generates everything

```
Word List (NGSL + MOE)
         ↓
    Gemini generates:
    - Senses (learner-appropriate)
    - Definitions (B1/B2 level)
    - Examples (modern, relatable)
    - Chinese translations
         ↓
    Human validation (top 1000)
         ↓
      Database
```

| Pros | Cons |
|------|------|
| Full control over quality | Hallucination risk |
| Learner-focused from start | Consistency challenges |
| No legacy constraints | No semantic relationships |
| Modern, natural examples | Higher API costs |
| Perfect for Taiwan context | Needs validation layer |

**Effort**: 🟡 Medium - New prompts, validation pipeline
**Risk**: Hallucination, but controllable with validation

---

### Option 5: Hybrid Architecture (RECOMMENDED)
**Approach**: Light skeleton from WordNet, AI for content, human for validation

```
Word List (NGSL + MOE) ──────────────────────────┐
         ↓                                       │
    Spelling Normalization                       │
    (British → American)                         │
         ↓                                       │
┌────────┴────────┐                              │
│  WordNet Query  │ ← Only for structure         │
│  (1-2 key POS)  │   Not content                │
└────────┬────────┘                              │
         ↓                                       │
    AI Sense Selection                           │
    "Which senses are useful                     │
     for B1/B2 Taiwan students?"                 │
         ↓                                       │
    AI Content Generation         ←──────────────┘
    - Learner-level definitions    (word context)
    - Taiwan-appropriate examples
    - Chinese with explanation
         ↓
    Relationship Extraction
    (WordNet synonyms/antonyms)
         ↓
    Validation Layer
    - Auto: Example-sense match check
    - Human: Top 500 words review
         ↓
      Final Database
```

| Pros | Cons |
|------|------|
| Best of both worlds | More complex pipeline |
| Learner-focused content | Still some WordNet issues |
| Semantic relationships | Needs validation |
| Full control | Initial setup effort |
| Scalable | |

**Effort**: 🟡 Medium - Refactor existing pipeline
**Risk**: Low - Incremental improvement on existing

---

## Decision Matrix

| Criteria | WordNet | Learner Dict | Wiktionary | AI-First | Hybrid |
|----------|---------|--------------|------------|----------|--------|
| Cost | ✅ Free | ❌ $$$ | ✅ Free | ✅ API only | ✅ Free + API |
| Learner-focused | ❌ | ✅ | 🟡 | ✅ | ✅ |
| Quality control | ❌ | ✅ | ❌ | 🟡 | ✅ |
| Relationships | ✅ | 🟡 | 🟡 | ❌ | ✅ |
| Taiwan context | ❌ | ❌ | ❌ | ✅ | ✅ |
| Effort to MVP | 🔴 High | 🟡 Medium | 🟡 Medium | 🟡 Medium | 🟡 Medium |
| Long-term maintainability | ❌ | 🟡 | ❌ | 🟡 | ✅ |

---

## Recommended: Hybrid Architecture

### Core Principles

1. **WordNet is a SKELETON, not the source of truth**
   - Use for: POS categories, synset IDs, relationships
   - Don't use for: Definitions, sense granularity

2. **AI is the CONTENT generator**
   - Gemini decides which senses are useful
   - Gemini creates learner-appropriate definitions
   - Gemini generates Taiwan-context examples

3. **Human validation for HIGH-IMPACT words**
   - Top 500 words get human review
   - Flag and fix issues systematically

4. **Frequency drives priority**
   - High-frequency words get more senses
   - Low-frequency words get 1 sense

### Proposed Sense Strategy

| Frequency Band | Words | Senses Per Word | Validation |
|----------------|-------|-----------------|------------|
| 1-500 | Core vocabulary | 2-3 (AI selected) | Human review |
| 501-1500 | Common | 1-2 | Auto validation |
| 1501-3500 | Extended | 1 | Spot check |

### Example: "drop" Reimagined

**Current (WordNet-first)**:
```
drop.n.01: "a shape that is spherical and small"
drop.n.02: "a small indefinite quantity of liquid"
drop.n.03: "a sudden sharp decrease"
```
→ Missing verb senses, academic definitions

**Proposed (Hybrid)**:
```
Prompt to AI:
"For the word 'drop', identify the 2 most useful 
meanings for a Taiwan B1/B2 student. Include at 
least one verb usage if applicable."

AI Response:
1. (v) 掉落 - To fall or let something fall
   Example: "I dropped my phone and the screen cracked."
   
2. (n) 下降 - A decrease in amount or level  
   Example: "There was a big drop in temperature today."
```

---

## Implementation Roadmap

### Phase 1: Foundation Fix (1 week)
- [ ] Create spelling normalization map
- [ ] Add POS-aware sense selection
- [ ] Filter academic/rare senses
- [ ] Re-export vocabulary.json

### Phase 2: AI-First Content (2 weeks)
- [ ] New Gemini prompt for sense selection
- [ ] Generate learner-appropriate definitions
- [ ] Taiwan-context examples
- [ ] Sense-example validation

### Phase 3: Validation Layer (1 week)
- [ ] Auto-validation for sense-example match
- [ ] Human review interface for top 500
- [ ] Feedback loop for corrections

### Phase 4: Relationship Enhancement (1 week)
- [ ] Clean synonym/antonym extraction
- [ ] Remove duplicate relationships
- [ ] Add frequency-based filtering

---

## Questions for Decision

1. **Budget**: Can we afford learner dictionary API licensing?
   - If yes → Consider hybrid with Oxford API for top 1000
   - If no → Full hybrid with AI

2. **Timeline**: When is MVP needed?
   - Urgent → Quick fixes to current pipeline
   - Flexible → Full hybrid rebuild

3. **Quality bar**: What's acceptable for launch?
   - Perfect → Human review all top 1000
   - Good enough → AI + spot checks

4. **Scale**: How many words for MVP?
   - 1000 words → Can do intensive curation
   - 3500 words → Need automation

---

## Recommendation

**Go with Hybrid Architecture** because:

1. ✅ Preserves existing investment (Neo4j, pipeline code)
2. ✅ Fixes root causes, not symptoms
3. ✅ Learner-focused from content layer
4. ✅ Taiwan context built-in
5. ✅ Scalable with validation layer
6. ✅ No licensing costs

**First Step**: Rebuild the enrichment pipeline with AI-first sense selection, keeping WordNet only for structure and relationships.

---

*Document created: 2025-12-06*
*Status: PROPOSAL - Awaiting decision*

