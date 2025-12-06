# LexiCraft Terminology Glossary

**Last Updated:** December 2024  
**Purpose:** Single source of truth for all terminology used across LexiCraft documentation and codebase.

---

## Core Concepts

### Block (字塊)

**Definition:** The fundamental unit of learning in LexiCraft. A block can be:
- A word sense (e.g., "bank" as financial institution)
- A phrase (e.g., "make a decision")
- An idiom (e.g., "beat around the bush")
- A morphological pattern (e.g., "in-" prefix)

**Key Properties:**
- Has a unique identifier (e.g., `bank.n.01`)
- Has a base XP value (determined by tier)
- Has dynamic value (increases with connections)
- Can be in various states (Raw, Hollow, Solid)

**Related Terms:** Learning Point (deprecated), Word Block, Vocabulary Block

---

### Mining (挖礦)

**Definition:** The act of discovering new blocks through exploration of the vocabulary universe.

**Process:**
1. Explore the Block Mine (vocabulary graph)
2. Find connections between blocks
3. Discover new blocks through relationships
4. Unlock phrases/idioms when component blocks are known

**Not to be confused with:** Forging (mastering), which happens after discovery.

**Example:** "I mined the connection between 'direct' and 'indirect' and discovered the 'in-' prefix pattern."

---

### Forging (鍛造)

**Definition:** The process of solidifying a block through spaced repetition and verification.

**Process:**
1. Start with a Hollow Block (discovered but not mastered)
2. Complete verification quizzes (Pickaxe)
3. Gain XP through correct answers
4. Progress through FSRS spaced repetition schedule
5. Achieve Solid Block status (fully mastered)

**Metaphor:** Like forging metal - applying heat (reviews) and pressure (quizzes) to transform raw material into a solid, permanent structure.

**Related Terms:** Verification, Mastery, Solidification

---

### The Mine (礦區)

**Definition:** The vocabulary universe - the complete knowledge graph of all blocks and their connections.

**Structure:**
- Blocks are nodes
- Relationships are edges
- Pre-populated in Neo4j
- Personalized view shows user's progress

**Visualization:** A graph/map showing:
- Blocks you've mastered (Solid/Gold)
- Blocks you're learning (Hollow/Cracked)
- Blocks you can discover (Raw/Gray)
- Connections between blocks

**Related Terms:** Vocabulary Universe, Block Graph, Knowledge Graph

---

### Pickaxe (十字鎬)

**Definition:** The verification tool - the MCQ quiz that tests understanding of a block.

**Function:**
- Tests context understanding
- Uses distractors from related blocks
- Measures comprehension depth
- Determines if block can progress to next stage

**Metaphor:** Like a pickaxe in mining - the tool you use to extract value from blocks.

**Related Terms:** Quiz, MCQ, Verification Test

---

## Block States

### Raw Block (原始字塊)

**Definition:** A block that has been discovered but not yet attempted.

**Visual:** Gray/unlocked block
**XP:** 0
**Status:** Available to start learning

---

### Hollow Block (空心磚)

**Definition:** A block that has been attempted but not yet mastered. The learner has "seen" it but doesn't truly understand it.

**Visual:** Cracked/partially filled block
**XP:** Partial (earning in progress)
**Status:** In learning phase
**Metaphor:** Like a hollow brick - looks solid from outside but collapses under pressure (like in high school exams)

---

### Solid Block (實心磚)

**Definition:** A block that has been fully mastered through verification and spaced repetition.

**Visual:** Gold/solid block
**XP:** Full value earned
**Status:** Mastered, FSRS stable
**Metaphor:** Like a solid brick - permanent, reliable, won't collapse

---

### Gold Block (金磚)

**Definition:** A Solid Block that has been mastered for 30+ days (long-term retention).

**Visual:** Shimmering gold block
**XP:** Full value + retention bonus
**Status:** Long-term mastered
**Special:** May unlock special achievements or decorations

---

## Block Types & Tiers

### Tier 1: Basic Block (⭐)

**Value:** Base XP (e.g., 100 XP)
**Type:** Single meaning word
**Example:** "apple" = fruit
**Complexity:** Low

---

### Tier 2: Multi-Block (⭐⭐)

**Value:** Base XP × 2.5
**Type:** Word with multiple distinct meanings
**Example:** "bank" = financial institution AND river edge
**Complexity:** Medium

---

### Tier 3: Phrase Block (⭐⭐⭐)

**Value:** Base XP × 5
**Type:** Common collocation
**Example:** "make a decision"
**Complexity:** Medium-High
**Requirement:** Must know component words first

---

### Tier 4: Idiom Block (⭐⭐⭐⭐)

**Value:** Base XP × 10
**Type:** Idiomatic expression
**Example:** "beat around the bush"
**Complexity:** High
**Requirement:** Must know component words first

---

### Tier 5: Pattern Block (🔗)

**Value:** Base XP × 3
**Type:** Morphological pattern (prefix/suffix)
**Example:** "in-" negation prefix (direct → indirect)
**Complexity:** Medium
**Special:** Unlocks multiple words when recognized

---

### Tier 6: Register Block (📝)

**Value:** Base XP × 4
**Type:** Formal/informal variant
**Example:** "utilize" (formal) vs "use" (informal)
**Complexity:** Medium

---

### Tier 7: Context Block (🎯)

**Value:** Base XP × 7.5
**Type:** Context-specific meaning
**Example:** "bush" in "beat around the bush" vs literal plant
**Complexity:** High

---

## Dynamic Value System

### Connection Bonus

**Formula:**
```
Block Value = Base XP + (Connection Count × Connection Bonus)
```

**Connection Bonuses:**
- Related word: +10 XP per connection
- Opposite word: +10 XP per connection
- Part of phrase: +20 XP per phrase
- Part of idiom: +30 XP per idiom
- Morphological: +10 XP per pattern
- Register variant: +10 XP per variant

**Example:**
- "break" base: 250 XP (Multi-Block)
- 12 connections: +120 XP
- **Total: 370 XP**

---

## Economic Terms

### Internal Economy

**Definition:** The XP-based game economy that always operates.

**Components:**
- Block XP (earned by forging)
- Crystals (earned by achievements)
- Levels (based on total XP)
- Achievements (unlocked by milestones)

**Status:** Always active, no funding required

---

### External Economy

**Definition:** The real-world money economy that requires parent funding.

**Components:**
- Funded blocks (labeled with 💰)
- Conversion rights (ability to withdraw)
- Withdrawal amounts (XP → money conversion)

**Status:** Requires parent funding to activate

---

### Funded Block

**Definition:** A block that has been labeled as convertible to real money by parent funding.

**Visual:** Shows 💰 badge
**Function:** Can be converted to money when mastered
**Note:** Still earns same XP as unfunded blocks

---

### Block Trust (字塊信託)

**Definition:** Parent's deposit that funds a set of blocks for conversion.

**Example:** "Essential 2000" package funds 2,000 blocks
**Function:** Labels those blocks as convertible
**Status:** Money held in escrow until blocks are mastered

---

## Relationship Types

### PREREQUISITE_OF

**Definition:** Block A must be learned before Block B
**Direction:** A → B
**Example:** "make" is prerequisite for "make a decision"

---

### COLLOCATES_WITH

**Definition:** Blocks often used together
**Direction:** A ↔ B
**Example:** "make" collocates with "decision"

---

### RELATED_TO

**Definition:** Blocks with similar meanings
**Direction:** A ↔ B
**Example:** "break" related to "opportunity"

---

### OPPOSITE_OF

**Definition:** Blocks with opposite meanings
**Direction:** A ↔ B
**Example:** "direct" opposite of "indirect"

---

### PART_OF

**Definition:** Block A is a component of Block B (phrase/idiom)
**Direction:** A → B
**Example:** "beat" is part of "beat around the bush"

---

### MORPHOLOGICAL

**Definition:** Block A is a prefix/suffix of Block B
**Direction:** A → B
**Example:** "in-" is morphological component of "indirect"

---

### REGISTER_VARIANT

**Definition:** Block A is formal/informal variant of Block B
**Direction:** A ↔ B
**Example:** "utilize" is formal variant of "use"

---

### FREQUENCY_RANK

**Definition:** Block A is more common than Block B
**Direction:** A → B
**Example:** "use" is more frequent than "utilize"

---

## Deprecated Terms

| Old Term | New Term | Reason |
|----------|----------|--------|
| Learning Point | Block | Aligns with brand vocabulary |
| Learning Point Cloud | The Mine | More intuitive, game-like |
| Word | Block | More accurate (includes phrases/idioms) |
| Sense | Block | More user-friendly |
| Verification | Forging | More engaging metaphor |
| Discovery | Mining | More game-like |

---

## Usage Guidelines

1. **Always use "Block"** instead of "Learning Point" in user-facing content
2. **Use "Mining"** for discovery actions
3. **Use "Forging"** for mastery actions
4. **Use "The Mine"** for the vocabulary universe
5. **Use Chinese terms** (字塊, 挖礦, 鍛造) when appropriate for Taiwan market

---

**Related Documents:**
- [Brand Definition](./16-brand-definition-lexicraft.md) - Source of terminology
- [UX Vision](./30-ux-vision-game-design.md) - Game design using this terminology
- [Economic Model](./31-economic-model-hypotheses.md) - Dual economy concepts

