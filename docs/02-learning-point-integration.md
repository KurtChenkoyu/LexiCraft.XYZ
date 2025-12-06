# The Mine: Block Integration

**Terminology:** This document uses unified Block terminology. See [Terminology Glossary](./00-TERMINOLOGY.md) for definitions.

## Overview

The Mine is a **pre-populated knowledge graph** (Neo4j) that serves as the source of truth for all block relationships. It enables sophisticated, context-aware vocabulary learning that goes far beyond simple word counting.

**Note:** Economic values (NT$) shown are for funded blocks only. See [Economic Model Hypotheses](./31-economic-model-hypotheses.md) for details on dual economy.

## The Mine Architecture

### Structure

```
The Mine (Neo4j Knowledge Graph)

Nodes: Blocks
├── Vocabulary words (senses)
├── Phrases/collocations
├── Grammar patterns
├── Morphological components (prefixes, suffixes)
└── Contexts (formal, informal, technical)

Edges: Relationships (ALL PRE-POPULATED)
├── PREREQUISITE_OF (A → B: need A before B)
├── COLLOCATES_WITH (A ↔ B: often used together)
├── RELATED_TO (A ↔ B: similar/related concepts)
├── PART_OF (A → B: A is part of B)
├── OPPOSITE_OF (A ↔ B: antonyms)
├── MORPHOLOGICAL (A → B: A is prefix/suffix of B)
├── FREQUENCY_RANK (A → B: A is more common than B)
└── REGISTER_VARIANT (A → B: A is formal, B is informal)
```

### Key Features

1. **Context-Aware**: "Bush" (name) vs "bush" (word) tracked separately
2. **Component-Based**: Track prefixes, suffixes, contexts independently
3. **Frequency Data**: Corpus-based frequency rankings (YouTube captions 2024/2025)
4. **Multi-Hop Relationships**: 1-degree, 2-degree, 3-degree connections
5. **Pre-Populated**: All relationships defined upfront, agents query to discover

## Example: "Beat Around the Bush"

### Learning Point Cloud Structure

```cypher
(beat_around_the_bush:Idiom)
  -[:PART_OF]-> (beat:Word)
  -[:PART_OF]-> (around:Word)
  -[:PART_OF]-> (bush:Word {context: "idiomatic"})
  -[:RELATED_TO]-> (direct:Word)
  -[:RELATED_TO]-> (indirect:Word)

(indirect:Word)
  -[:MORPHOLOGICAL {type: "prefix"}]-> (in-:Prefix)
  -[:OPPOSITE_OF]-> (direct:Word)

(bush:Word {context: "literal"})
  -[:REGISTER_VARIANT]-> (shrub:Word {register: "formal"})
```

### Query Example

```cypher
// Find all components related to "beat around the bush" within 3 degrees
MATCH path = (target:Sense {id: "beat_around_the_bush"})-[*1..3]-(component:Sense)
RETURN component.id, length(path) as degrees, relationships(path)
ORDER BY degrees, component.frequency_rank
```

## Block Tiers & Base XP Values

**Note:** Values shown are base XP. Dynamic value (base + connections) is calculated separately. See Dynamic Value System below.

### Tier 1: Basic Block (⭐)
- **Base XP**: 100 XP
- **What**: Learn block in most common context
- **Verification**: Recognition test (multiple choice)
- **Example**: "apple" = fruit
- **Frequency**: Top 1,000 most common blocks
- **Time**: 7-day verification cycle
- **Funded Value**: NT$1.00 (if funded)

### Tier 2: Multi-Block (⭐⭐)
- **Base XP**: 250 XP
- **What**: Learn block with 2+ distinct meanings
- **Verification**: Must demonstrate all meanings
- **Example**: "bank" = financial institution AND river edge
- **Frequency**: Top 5,000 blocks
- **Time**: 14-day verification cycle
- **Funded Value**: NT$2.50 (if funded)

### Tier 3: Phrase Block (⭐⭐⭐)
- **Base XP**: 500 XP
- **What**: Learn blocks in common phrases
- **Verification**: Must use block correctly in phrases
- **Example**: "make a decision" (not "do a decision")
- **Frequency**: Top 10,000 collocations
- **Time**: 21-day verification cycle
- **Funded Value**: NT$5.00 (if funded)

### Tier 4: Idiom Block (⭐⭐⭐⭐)
- **Base XP**: 1,000 XP
- **What**: Learn idiomatic expressions
- **Verification**: Must understand figurative meaning
- **Example**: "beat around the bush" = avoid being direct
- **Frequency**: Top 1,000 idioms
- **Time**: 30-day verification cycle
- **Funded Value**: NT$10.00 (if funded)

### Tier 5: Pattern Block (🔗)
- **Base XP**: 300 XP
- **What**: Learn morphological relationships
- **Verification**: Must understand prefix/suffix relationships
- **Example**: "direct" → "indirect" (knowing "in-" prefix)
- **Frequency**: Top 5,000 morphological relationships
- **Time**: 14-day verification cycle
- **Funded Value**: NT$3.00 (if funded)

### Tier 6: Register Block (📝)
- **Base XP**: 400 XP
- **What**: Learn formal vs. informal variants
- **Verification**: Must use appropriate register
- **Example**: "utilize" (formal) vs. "use" (informal)
- **Frequency**: Top 2,500 register pairs
- **Time**: 21-day verification cycle
- **Funded Value**: NT$4.00 (if funded)

### Tier 7: Context Block (🎯)
- **Base XP**: 750 XP
- **What**: Learn blocks in specialized contexts
- **Verification**: Must understand context-specific meaning
- **Example**: "bush" in "beat around the bush" vs. "bush" as plant
- **Time**: 30-day verification cycle
- **Funded Value**: NT$7.50 (if funded)

## Dynamic Block Value System

**Key Innovation:** Block value increases with connections, making hub blocks more valuable.

### Value Formula

```
Block Value = Base XP + (Connection Count × Connection Bonus)
```

### Connection Bonuses

| Connection Type | Bonus per Connection |
|----------------|---------------------|
| Related word | +10 XP |
| Opposite word | +10 XP |
| Part of phrase | +20 XP |
| Part of idiom | +30 XP |
| Morphological | +10 XP |
| Register variant | +10 XP |

### Examples

**"break" (Multi-Block):**
- Base XP: 250 XP
- Connections: 12 (related words, phrases, idioms)
- Connection Bonus: 12 × 10 XP = 120 XP
- **Total Value: 370 XP**

**"apple" (Basic Block):**
- Base XP: 100 XP
- Connections: 2 (related words)
- Connection Bonus: 2 × 10 XP = 20 XP
- **Total Value: 120 XP**

**"make" (Basic Block, but hub word):**
- Base XP: 100 XP
- Connections: 8 (part of many phrases)
- Connection Bonus: 8 × 20 XP = 160 XP
- **Total Value: 260 XP**

### Why This Matters

- **Hub blocks** (highly connected) are more valuable, encouraging exploration of central vocabulary
- **Discovery rewards** finding connections between blocks
- **Reflects true learning value** - a well-connected block IS more useful
- **Creates treasure hunting** - some blocks are worth way more

## Earning Tiers Based on Complexity (Legacy - For Reference)

**Note:** These dollar amounts are for funded blocks only. See [Economic Model](./31-economic-model-hypotheses.md).

### Tier 1: Basic Word Recognition ($1.00/word)
- **What**: Learn word in most common context
- **Verification**: Recognition test (multiple choice)
- **Example**: "apple" = fruit
- **Frequency**: Top 1,000 most common words
- **Time**: 7-day verification cycle

### Tier 2: Multiple Meanings ($2.50/word)
- **What**: Learn word with 2+ distinct meanings
- **Verification**: Must demonstrate all meanings
- **Example**: "bank" = financial institution AND river edge
- **Frequency**: Top 5,000 words
- **Time**: 14-day verification cycle

### Tier 3: Phrase/Collocation Mastery ($5.00/phrase)
- **What**: Learn words in common phrases
- **Verification**: Must use word correctly in phrases
- **Example**: "make a decision" (not "do a decision")
- **Frequency**: Top 10,000 collocations
- **Time**: 21-day verification cycle

### Tier 4: Idiom/Expression Mastery ($10.00/idiom)
- **What**: Learn idiomatic expressions
- **Verification**: Must understand figurative meaning
- **Example**: "beat around the bush" = avoid being direct
- **Frequency**: Top 1,000 idioms
- **Time**: 30-day verification cycle

### Tier 5: Morphological Mastery ($3.00/relationship)
- **What**: Learn word family relationships
- **Verification**: Must understand prefix/suffix relationships
- **Example**: "direct" → "indirect" (knowing "in-" prefix)
- **Frequency**: Top 5,000 morphological relationships
- **Time**: 14-day verification cycle

### Tier 6: Register Mastery ($4.00/variant)
- **What**: Learn formal vs. informal variants
- **Verification**: Must use appropriate register
- **Example**: "utilize" (formal) vs. "use" (informal)
- **Frequency**: Top 2,500 register pairs
- **Time**: 21-day verification cycle

### Tier 7: Advanced Context Mastery ($7.50/context)
- **What**: Learn words in specialized contexts
- **Verification**: Must understand context-specific meaning
- **Example**: "bush" in "beat around the bush" vs. "bush" as plant
- **Time**: 30-day verification cycle

## Gamification Layers

### 1. Relationship Discovery Bonuses
- Forge "direct" → 100 XP
- Discover "indirect" relationship → +50 XP bonus
- Forge "indirect" → 100 XP
- **Total**: 250 XP (vs. 200 XP without discovery)

### 2. Pattern Recognition Bonuses
- Recognize "in-" prefix pattern → +100 XP bonus
- Apply pattern to 5 blocks → +200 XP mastery bonus

### 3. Phrase Completion Challenges
- Forge "make" → 100 XP
- Forge "decision" → 100 XP
- Forge "make a decision" → +300 XP phrase bonus

### 4. Idiom Unlocking System
- Forge component blocks → 300 XP
- Unlock "beat around the bush" → +700 XP idiom bonus

### 5. Context Mastery Achievements
- Forge "bank" (financial) → 250 XP
- Forge "bank" (river) → 250 XP
- Master both contexts → +200 XP bonus

## Verification: Context-Dependent Testing

### Instead of Simple "Define This Word"

**We test**:
1. **Context understanding**: "In 'I went to the bank,' what does 'bank' mean?"
2. **Relationship knowledge**: "How is 'indirect' related to 'direct'?"
3. **Phrase completion**: "Complete: 'I need to ___ a decision'"
4. **Frequency awareness**: "Is this word common or rare?"
5. **Morphological patterns**: "What's the base word of 'dishonest'?"

### Why This Works

- **Prevents gaming**: Can't just memorize definitions
- **Ensures understanding**: Must demonstrate context awareness
- **Tests relationships**: Must understand word connections
- **Verifies usage**: Must know how to use words correctly

## Revenue Impact (For Funded Blocks)

**Note:** These calculations assume all blocks are funded. See [Economic Model](./31-economic-model-hypotheses.md) for dual economy details.

### Simple Model
- 5,000 blocks × NT$2 = NT$10,000

### Complex Model (The Mine)
- 1,000 basic × NT$1 = NT$1,000
- 2,000 multiple meanings × NT$2.50 = NT$5,000
- 1,000 phrases × NT$5 = NT$5,000
- 500 idioms × NT$10 = NT$5,000
- 500 relationships × NT$3 = NT$1,500
- **Total**: NT$18,500 (**85% increase**)

### With Dynamic Value
- Hub blocks (highly connected) earn more
- Connection bonuses increase total value
- Encourages exploration of central vocabulary

## Implementation

### Phase 1: Basic Integration (Months 1-3)
- Integrate The Mine (Neo4j) API
- Implement Tier 1-2 blocks
- Basic relationship tracking
- Dynamic value calculation
- **Revenue**: +20% vs. simple model (if funded)

### Phase 2: Phrase Integration (Months 4-6)
- Add Tier 3 (phrase blocks)
- Phrase completion challenges
- Connection-based value scaling
- **Revenue**: +50% vs. simple model (if funded)

### Phase 3: Advanced Features (Months 7-12)
- Add Tier 4-7 (idioms, morphology, register, context)
- Full relationship bonuses
- Hub block identification
- **Revenue**: +85% vs. simple model (if funded)

## Key Benefits

1. **Higher Revenue Potential**: 85%+ increase (if all blocks funded)
2. **Better Learning**: Context-aware, relationship-based
3. **Stronger Verification**: Hard to game
4. **Richer Gamification**: Mining, forging, discovery, achievements
5. **Dynamic Value**: Hub blocks more valuable, encourages exploration
6. **Competitive Advantage**: No competitor has this sophistication

## Next Steps

1. Review [Terminology Glossary](./00-TERMINOLOGY.md) for unified vocabulary
2. Review [UX Vision](./30-ux-vision-game-design.md) for game design
3. Review [Economic Model](./31-economic-model-hypotheses.md) for dual economy
4. Review technical architecture: `04-technical-architecture.md`
5. Review API specifications: `05-api-specifications.md`
6. Start implementation: `03-implementation-roadmap.md`

