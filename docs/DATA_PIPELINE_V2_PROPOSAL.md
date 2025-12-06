# Data Pipeline V2: Multi-Authority Hybrid Architecture

## Context

After testing the current pipeline with real users, we discovered:
1. WordNet senses are too academic ("quark color", British spellings)
2. AI-generated examples sometimes don't match senses
3. Missing common senses (verbs for "drop")
4. Over-granular distinctions users can't distinguish

**Key Question**: Should we trust AI more, or add more authoritative sources?

**Answer**: Neither extreme. Use **multiple authorities for facts**, AI for **selection and localization**.

---

## The Hallucination Problem

### What AI Can Hallucinate
- ❌ Definitions (subtle errors)
- ❌ Example sentences (wrong sense)
- ❌ Translations (awkward/wrong)
- ❌ Made-up idioms
- ❌ Grammar patterns

### What AI Cannot Hallucinate If We Anchor
- ✅ Selecting from a list (choice, not generation)
- ✅ Simplifying text (transformation, not creation)
- ✅ Translating verified text (bounded task)
- ✅ Ranking by criteria (judgment, not facts)

**Principle**: AI selects and transforms; authorities provide facts.

---

## Available Open Authoritative Sources

### Currently Implemented ✅

| Source | What It Provides | Quality |
|--------|-----------------|---------|
| **WordNet** | Synsets, relationships | Academic, comprehensive |
| **NGSL** | Frequency rankings | Research-backed |
| **Taiwan MOE 7000** | Word list, levels | Official curriculum |

### Available but Not Used ⚠️

| Source | What It Would Provide | Access |
|--------|----------------------|--------|
| **English Vocabulary Profile (EVP)** | CEFR levels (A1-C2) | Free registration |
| **Wiktionary** | Definitions, translations | Free API |
| **CC-CEDICT** | Chinese translations | Free download |
| **COCA 60k** | Frequency + collocations | Free download |
| **Simple English Wikipedia** | Simple definitions | Free |

### Commercial (Not Recommended for MVP)

| Source | Cost | Value |
|--------|------|-------|
| Oxford API | ~$500-2000/year | High quality |
| Cambridge API | ~$500-2000/year | CEFR levels |

---

## Proposed V2 Architecture: Multi-Authority Hybrid

```
┌─────────────────────────────────────────────────────────────────┐
│                    AUTHORITATIVE DATA LAYER                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Taiwan MOE 7000        NGSL Frequency       CEFR (EVP)         │
│  ───────────────        ──────────────       ──────────         │
│  • Word list            • Frequency rank     • Difficulty level │
│  • MOE levels           • 90% coverage       • A1-C2 mapping    │
│  • Curriculum           • Research-backed    • Learner-focused  │
│                                                                  │
│  WordNet                CC-CEDICT            Wiktionary          │
│  ───────                ─────────            ──────────          │
│  • Synset IDs           • ZH translations    • Simple defs      │
│  • Relationships        • Community vetted   • Modern usage     │
│  • POS structure        • Taiwan Mandarin    • Multiple langs   │
│                                                                  │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    AI INTELLIGENCE LAYER                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. SENSE SELECTION                                              │
│     Input: All WordNet synsets for word                          │
│     AI Task: "Which 2 are most useful for Taiwan B1/B2?"         │
│     Output: Selected synset IDs (not definitions)                │
│                                                                  │
│  2. DEFINITION SIMPLIFICATION                                    │
│     Input: WordNet/Wiktionary definition                         │
│     AI Task: "Rewrite for B1/B2 level in 15 words"              │
│     Output: Simplified English definition                        │
│                                                                  │
│  3. TRANSLATION VALIDATION                                       │
│     Input: CC-CEDICT translation + context                       │
│     AI Task: "Is this natural Taiwan Mandarin? Improve if not"  │
│     Output: Verified/improved translation                        │
│                                                                  │
│  4. EXAMPLE GENERATION                                           │
│     Input: Definition + word + Taiwan context                    │
│     AI Task: "Create relatable example for Taiwan student"       │
│     Output: Example sentence + translation                       │
│                                                                  │
│  5. EXAMPLE VALIDATION                                           │
│     Input: Generated example + target sense                      │
│     AI Task: "Does this example clearly show THIS meaning?"      │
│     Output: PASS/FAIL + reason                                   │
│                                                                  │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    VALIDATION LAYER                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  AUTOMATED CHECKS                                                │
│  ────────────────                                                │
│  • Definition length (≤20 words)                                 │
│  • Example-sense match (AI validation)                           │
│  • Translation character check (繁體, no 简体)                    │
│  • Profanity/sensitivity filter                                  │
│                                                                  │
│  HUMAN REVIEW (Top 500 words only)                               │
│  ────────────────────────────────                                │
│  • Sample 10% of top 500 for manual review                       │
│  • Flag issues for batch correction                              │
│  • Build correction patterns for pipeline improvement            │
│                                                                  │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FINAL DATABASE                                │
│                                                                  │
│  12,000 words × ~2 senses × rich data = ~30-40MB                 │
│  Gzip compressed: ~8-10MB                                        │
│  Load time: ~3-5 seconds (cached after first)                    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Data Flow Example: "drop"

### Step 1: Gather Authorities

```
Taiwan MOE: Level 1 (core vocabulary)
NGSL Rank: 1726
CEFR (EVP): A2/B1

WordNet synsets (20 total):
  drop.n.01: "a shape that is spherical and small"
  drop.n.02: "a small indefinite quantity"  
  drop.n.03: "a sudden sharp decrease"
  drop.v.01: "let fall to the ground"
  drop.v.02: "fall vertically"
  ... (15 more)

CC-CEDICT translations:
  drop (v): 掉, 落下, 滴
  drop (n): 滴, 下降
  
Wiktionary simple def:
  drop (v): "To let something fall"
  drop (n): "A small amount of liquid"
```

### Step 2: AI Selection

```
Prompt: "Select 2 most useful senses for Taiwan B1 student"

AI Output:
{
  "selected": [
    {"id": "drop.v.01", "reason": "Core action verb, daily use"},
    {"id": "drop.n.03", "reason": "Common in news/economy context"}
  ],
  "rejected_notable": [
    {"id": "drop.n.01", "reason": "Too specific, rarely used alone"}
  ]
}
```

### Step 3: AI Simplification & Localization

```
Sense 1: drop.v.01 (verb)

Authoritative inputs:
- WordNet def: "let fall to the ground"
- CC-CEDICT: 掉, 落下
- Wiktionary: "To let something fall"

AI tasks:
1. Simplify: "To let something fall from your hand" ✅
2. Validate translation: "掉落" (more natural than 落下) ✅
3. Generate example: "I dropped my phone on the ground" ✅
4. Translate example: "我把手機掉到地上了" ✅
5. Validate example matches sense: ✅ PASS
```

### Step 4: Final Entry

```json
{
  "sense_id": "drop.v.01",
  "word": "drop",
  "pos": "v",
  "cefr": "A2",
  "moe_level": 1,
  "frequency_rank": 1726,
  
  "definition_en": "To let something fall from your hand or a higher place",
  "definition_zh": "讓某物從手中或高處掉落",
  
  "example_en": "Be careful not to drop your phone!",
  "example_zh": "小心別把手機摔了！",
  
  "authority_sources": ["wordnet", "cc-cedict", "evp"],
  "ai_tasks": ["sense_selection", "simplification", "example_gen"],
  "validated": true
}
```

---

## Implementation Plan

### Phase 1: Add Authority Sources (3 days)

| Source | Task | Effort |
|--------|------|--------|
| CC-CEDICT | Download, parse, index by word | 4 hours |
| EVP/CEFR | Download word list, map levels | 4 hours |
| Wiktionary | Parse dump for simple defs | 8 hours |
| Integration | Merge into pipeline | 8 hours |

### Phase 2: AI Pipeline Refactor (1 week)

| Task | Description | Effort |
|------|-------------|--------|
| Sense Selector | New prompt for useful sense selection | 1 day |
| Definition Simplifier | Transform academic → learner | 1 day |
| Translation Validator | Check CC-CEDICT + improve | 1 day |
| Example Generator | Taiwan-context examples | 1 day |
| Validation Chain | Multi-step verification | 1 day |

### Phase 3: Full Re-enrichment (3-5 days)

| Task | Words | Time |
|------|-------|------|
| Top 1000 (intensive) | 1,000 | 2 days |
| Extended vocabulary | 6,000 | 2 days |
| Advanced vocabulary | 5,000 | 1 day |
| Total | 12,000 | 5 days |

**API Cost Estimate**: ~$20-50 for Gemini (12k words × 5 calls × $0.001)

### Phase 4: Validation (2 days)

| Task | Scope | Method |
|------|-------|--------|
| Auto-validation | All 12k | Script |
| Human review | Top 500 | Manual sample |
| Fixes | Failed entries | Targeted re-gen |

---

## Performance Impact

### Current (3,500 words)
- File size: 7 MB (1.4 MB gzip)
- Load time: ~1 second

### Projected (12,000 words, 2x richer)
- File size: ~40 MB (8 MB gzip)
- Load time: ~3-5 seconds (first load)
- Cached: Instant

### Mitigation Strategies

1. **Progressive Loading**
   ```
   Initial: Core 2,000 words (2 MB)
   Background: Load remaining 10,000
   ```

2. **IndexedDB Caching**
   ```javascript
   // Store in browser after first load
   // Subsequent visits: instant
   ```

3. **CDN + Service Worker**
   ```
   // PWA approach: pre-cache vocabulary
   // Works offline
   ```

**Verdict**: 40MB is NOT a problem for modern web apps.

---

## Why This Is Better Than AI-Only

| Aspect | AI-Only | Multi-Authority Hybrid |
|--------|---------|----------------------|
| Definition accuracy | Risk of subtle errors | Grounded in sources |
| Translation quality | May be awkward | Validated against CC-CEDICT |
| CEFR levels | AI guesses | EVP-backed |
| Relationships | Must generate | WordNet-backed |
| Frequency | Must estimate | NGSL-backed |
| Hallucination risk | High | Minimal (selection only) |
| Consistency | Variable | Source-anchored |

---

## Why This Is Better Than WordNet-Only

| Aspect | WordNet-Only | Multi-Authority Hybrid |
|--------|--------------|----------------------|
| Definition readability | Academic | B1/B2 simplified |
| Sense selection | Top N arbitrary | AI-selected for usefulness |
| Taiwan context | None | Built-in |
| Chinese quality | AI-generated | CC-CEDICT validated |
| CEFR alignment | None | EVP-backed |
| British spelling | Mixed | Normalized |

---

## Decision Summary

### Recommended Approach

1. **Keep WordNet** for structure (synsets, relationships)
2. **Add CC-CEDICT** for Chinese translation anchoring
3. **Add EVP/CEFR** for difficulty levels
4. **Use AI** for selection, simplification, localization
5. **Validate** with multi-step checks

### Not Recommended

- ❌ Full AI generation (hallucination risk)
- ❌ Pure WordNet (academic, not learner-focused)
- ❌ Commercial APIs (cost, dependency)

### Timeline

| Phase | Duration | Outcome |
|-------|----------|---------|
| Authority integration | 3 days | CC-CEDICT + EVP ready |
| Pipeline refactor | 5 days | New AI workflow |
| Re-enrichment | 5 days | 12k words done |
| Validation | 2 days | Quality assured |
| **Total** | **~3 weeks** | **Production-ready 12k dictionary** |

---

## Next Steps

1. **Decision**: Approve this architecture?
2. **Scope**: Full 12k or start with 3.5k?
3. **Priority**: Which authority sources first?
4. **Timeline**: When to start?

---

*Document created: 2025-12-06*
*Status: PROPOSAL - Awaiting approval*

