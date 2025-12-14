# LexiCraft 2.0: The Minecraft Game Design

**Date:** December 8, 2025  
**Status:** MVP Implementation  
**Supersedes:** [30-ux-vision-game-design.md](./30-ux-vision-game-design.md) (partial - this expands the vision)

---

## Executive Summary

This document defines LexiCraft's core game loop based on **Minecraft's design principles**. The key insight: **Your vocabulary IS your power, not some abstract XP number.**

> **Before:** "Add gamification to education"  
> **After:** "Build Minecraft where vocabulary is the building material"

---

## Three-Currency Economy (MVP)

LexiCraft uses three distinct currencies, each representing a different aspect of learning:

| Currency | Symbol | What It Represents | How Earned | How Used |
|----------|--------|-------------------|------------|----------|
| **Sparks** | ✨ | Effort & Activity | Any activity (even wrong answers) | Levels up → Converts to Energy |
| **Essence** | 💧 | Skill & Knowledge | Correct MCQ answers only | Required for building |
| **Blocks** | 🧱 | Vocabulary Assets | Mastered words (solid) | Building materials |

### Sparks → Energy Conversion

Sparks accumulate and level you up. **On each level up**, Sparks convert to Energy (⚡):

| Level Up | Energy Received |
|----------|-----------------|
| → Level 2 | 30 ⚡ |
| → Level 3 | 50 ⚡ |
| → Level 4 | 75 ⚡ |
| → Level 5 | 100 ⚡ |
| → Level 6+ | 125 ⚡ |

**Key insight:** Your Level reflects total lifetime effort (never decreases). Energy is the spendable form for building.

### Earning Currencies

| Activity | Sparks ✨ | Essence 💧 | Blocks 🧱 |
|----------|----------|-----------|----------|
| View new word | +1 | - | - |
| Start MCQ | +2 | - | - |
| Wrong answer | +1 | - | - |
| Correct answer | +5 | +1 | - |
| Fast + Correct | +8 | +2 | - |
| Review word | +2 | - | - |
| Pass review | +3 | +1 | - |
| Word → Hollow | +5 | - | - |
| Word → Solid | +10 | - | +1 Block |

### Building Recipe Example

**"Popcorn Phase" (First Session):**
```
Repair Desk Level 0 → Level 1:  FREE (Tutorial)
Upgrade Desk Level 1 → Level 2: 5⚡ + 2💧 + 0🧱 (Instant hook!)
```

**Mid-Game:**
```
Upgrade Desk Level 2 → Level 3:
├── 20 ⚡ Energy
├── 10 💧 Essence
└── 1 🧱 Block (first mastered word required)
```

**Late-Game:**
```
Upgrade Desk Level 4 → Level 5:
├── 70 ⚡ Energy
├── 45 💧 Essence
└── 6 🧱 Blocks (requires ~2 weeks of SRS)
```

### Starter Pack (New User Experience)

New users DON'T start with an empty room. They start with:
- 📦 Broken Desk (Level 0 - "Cardboard Box")
- 💡 Broken Lamp (Level 0 - "Bare Bulb")

**Tutorial:** "Your study space is a mess! Let's fix it up."
- Step 1: Repair Desk (L0→L1) = FREE
- Step 2: Repair Lamp (L0→L1) = FREE
- Step 3: "Now earn currencies to upgrade!"

**Why this works:**
- "Fixing" feels better than "buying from nothing"
- User immediately sees cause-and-effect
- No empty room depression

### Three Currencies Create Balance

This creates meaningful gameplay:
- You might have Energy but not enough Essence (need to get more answers RIGHT)
- You might have Essence but not enough Blocks (need to MASTER more words)
- All three required = balanced learning

**The Anti-Speedrun:** High-level furniture requires T3+ Blocks, which take 7-10 real days to generate through SRS. A rich parent CANNOT buy their kid the "Royal Desk" - the kid must have been consistent.

---

## Part 1: The Paradigm Shift

### From RPG to Minecraft

| RPG Model (Old) | Minecraft Model (New) |
|-----------------|----------------------|
| XP → Level → Power | Inventory → Power |
| Level gates content | Tools improve efficiency |
| "I'm level 30" | "I have 500 mastered blocks" |
| XP is hoarded | XP is spent |
| Abstract numbers | Tangible inventory |

### The Core Question Changes

> ❌ Old: "What level are you?"  
> ✅ New: "How big is your Mine? What have you built?"

---

## Part 2: The Two Separate Systems

### Word Knowledge (Actual Learning)
- **What it is:** The blocks you've mined and refined
- **Where it comes from:** School, reading, life, AND the app
- **How it's tracked:** FSRS algorithm, mastery levels
- **What it represents:** Your actual vocabulary
- **Can you lose it?** Yes (forgetting/decay)

### XP (Effort Currency)
- **What it is:** Spendable currency earned through effort
- **Where it comes from:** In-app activities only
- **How it's used:** Spent on tools, cosmetics, boosts
- **What it represents:** Time and dedication invested
- **Can you lose it?** Only when spent

### Why This Matters

A student who reads a lot:
- Has a large vocabulary (big inventory)
- Can prove knowledge quickly (fast mining)
- May have low XP (doesn't need to grind)

A dedicated app user:
- Builds vocabulary through practice
- Has high XP (can buy tools)
- Catches up through effort

**Both paths are valid. Neither alone wins.**

---

## Part 3: The Core Loop - Mine → Smelt → Build

### Phase 1: MINE (The Learning Session)

The MCQ engine is your **Pickaxe**. Every question is a block you're trying to break.

```
┌─────────────────────────────────────────────────────────────┐
│  ⛏️ MINING SESSION                                          │
│                                                             │
│  What does "ubiquitous" mean?                              │
│                                                             │
│  ○ A) Rare and hard to find                                │
│  ● B) Found everywhere, omnipresent ✓                      │
│                                                             │
│  💎 RARE ORE FOUND!                                         │
│  +1 Diamond Ore added to inventory                         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Ore Types by Vocabulary Tier:**

| Tier | Block Type | Ore/Material | Visual |
|------|-----------|--------------|--------|
| 1: Basic | Single meaning | 🪨 Stone | Common, essential |
| 2: Multi-meaning | Polysemous | 🪵 Oak Wood | Versatile |
| 3: Phrases | Collocations | 🧱 Brick | Structural |
| 4: Idioms | Fixed expressions | 🔶 Gold | Prestige |
| 5: Patterns | Morphological | ⛓️ Iron | Functional |
| 6: Register | Formal/informal | 💜 Amethyst | Specialized |
| 7: Context | Nuanced meaning | 💎 Diamond | Rare, valuable |

### Phase 2: SMELT (The Review/SRS)

In Minecraft, raw Iron Ore is useless. You must **smelt** it to get Iron Bars.

```
┌─────────────────────────────────────────────────────────────┐
│  🔥 THE FURNACE (Reviews Due)                               │
│                                                             │
│  RAW ORE → [FURNACE] → REFINED BLOCKS                      │
│                                                             │
│  Ready to smelt:                                           │
│  💎 ubiquitous (learned yesterday)                         │
│  🪨 determine (learned 3 days ago)                         │
│  🧱 make sense (learned 1 week ago)                        │
│                                                             │
│  [🔥 Start Smelting Session]                               │
│                                                             │
│  ⚠️ 2 ores will expire if not smelted by tomorrow!        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**The Mechanic:**
- Newly learned word = **Raw Ore** (unstable, can't use for building)
- Pass the review = **Ore smelts into Refined Block**
- This forces users to return: "I have 20 Gold Ores but can't build until I smelt them tomorrow!"

### Phase 3: BUILD (Blueprints)

Blueprints give PURPOSE to learning. "Why am I learning this?" → "Because I need 5 more Diamond blocks to finish my Castle!"

```
┌─────────────────────────────────────────────────────────────┐
│  🏰 CASTLE TOWER                          65% Complete     │
│  ████████████████░░░░░░░░                                  │
│                                                             │
│  Materials Needed:                                          │
│  🪨 Stone:     85/100  ████████░░                          │
│  🧱 Brick:     42/50   ████████░░                          │
│  🔶 Gold:      3/5     ██████░░░░                          │
│  💎 Diamond:   0/2     ░░░░░░░░░░  ← Need 2 more!          │
│                                                             │
│  Reward: 🎖️ "Castle Builder" title                         │
│          🔓 Unlocks: Guild features                        │
│                                                             │
│  ⚠️ 3 blocks cracking! (words overdue)                     │
│  [Repair Now]                                               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Part 4: The Survival Mechanic (Decay/Creeper)

Minecraft isn't just building—it's **surviving the night**. This gamifies spaced repetition decay.

### The Creeper Mechanic

```
┌─────────────────────────────────────────────────────────────┐
│  YOUR CASTLE                                                │
│                                                             │
│     🧱🧱🧱🧱🧱🧱🧱🧱🧱🧱                                    │
│     🧱🧱💥🧱🧱🧱🧱🧱🧱🧱   ← CRACKING! "analyze" overdue   │
│     🧱🧱🧱🧱🧱🧱💥🧱🧱🧱   ← CRACKING! "determine" overdue │
│     🪨🪨🪨🪨🪨🪨🪨🪨🪨🪨                                    │
│                                                             │
│  ⚠️ 2 blocks need repair!                                  │
│                                                             │
│  If ignored:                                                │
│  - Block cracks more each day                              │
│  - After 7 days: Block BREAKS (hole in your castle!)       │
│  - Must re-mine and re-smelt to repair                     │
│                                                             │
│  [🔧 Repair Now - Review These Words]                       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Why It Works:** Children are OBSESSED with protecting their creations. They will log in just to "fix the roof."

### Health System

Each block in a structure has health tied to FSRS retention:

```
Block Health = retention_probability × 100

100% = Solid (perfect recall)
70%  = Stable (due for review soon)
50%  = Cracking (review overdue)
30%  = Critical (about to break)
0%   = Broken (needs re-learning)
```

---

## Part 5: Advanced Mechanics

### 5.1 The Enchanting Table (Deep Mastery)

In Minecraft, an Iron Sword is okay, but an **Enchanted** Iron Sword is god-tier.

In LexiCraft, "knowing the definition" is the base item. We want users to learn **nuance, collocations, and usage**.

```
┌─────────────────────────────────────────────────────────────┐
│  🔮 ENCHANTING TABLE                                        │
│                                                             │
│  Base Item: 🗡️ "RUN" (Stone Sword)                         │
│  Status: Definition known ✓                                │
│                                                             │
│  Available Enchantments:                                    │
│                                                             │
│  ✨ Collocation I (30 Lapis)                               │
│     "Which fits? Run _____ (rapidly / dull)"               │
│     Reward: +1 Durability, Purple glow                     │
│                                                             │
│  ✨ Usage Mastery (50 Lapis)                               │
│     "Use 'run' correctly in context"                       │
│     Reward: +2 Durability, 2x points in battles            │
│                                                             │
│  ✨ Pronunciation (20 Lapis)                               │
│     "Record yourself saying this word"                     │
│     Reward: Audio badge                                    │
│                                                             │
│  Your Lapis: 💎 145 (earned from streaks)                  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Pedagogy:** This incentivizes **Deep Processing**. Users won't just skim definitions; they'll grind to understand USAGE so their gear looks cool.

**Enchantment Types:**
- **Collocation** - Learn which words go together
- **Usage** - Apply in sentences
- **Pronunciation** - Audio practice
- **Etymology** - Word origins
- **Register** - Formal vs informal usage

### 5.2 Crafting Recipes (Grammar & Syntax)

Minecraft is about combining simple things to make complex things: `Stick + Coal = Torch`.

LexiCraft uses this to teach **sentence structure** without boring grammar lessons.

```
┌─────────────────────────────────────────────────────────────┐
│  🛠️ CRAFTING TABLE                                          │
│                                                             │
│  Blueprint: 🏠 LIGHTHOUSE                                   │
│  Requires: Syntax combination                              │
│                                                             │
│  Recipe: [Article] + [Adjective] + [Noun] + [Verb]         │
│                                                             │
│  Your Inventory:                                           │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐              │
│  │  The   │ │ Bright │ │ Light  │ │ Shines │              │
│  │Article │ │  Adj   │ │  Noun  │ │  Verb  │              │
│  └────────┘ └────────┘ └────────┘ └────────┘              │
│                                                             │
│  Drag blocks into slots:                                   │
│  [____] + [____] + [____] + [____]                         │
│                                                             │
│  [Craft Sentence]                                          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Result:** "The bright light shines" → Lighthouse crafted!

**Pedagogy:** Creates a mental model of grammar as **modular slots**. "I can't build this sentence because I'm missing a Transitive Verb block."

**Recipe Types:**
- **Simple Sentence:** Subject + Verb
- **Descriptive:** Article + Adjective + Noun + Verb
- **Complex:** Clause + Conjunction + Clause
- **Questions:** Aux + Subject + Verb + Object

### 5.3 Villager Trading (Dynamic Quests)

In Minecraft, Villagers offer random trades: "I'll give you an Emerald for 20 Wheat."

In LexiCraft, this solves **"What should I learn today?"** paralysis.

```
┌─────────────────────────────────────────────────────────────┐
│  🏘️ VILLAGE - Today's Traders                               │
│                                                             │
│  👨‍🍳 THE BAKER                                              │
│  "I need 5 food-related words to bake bread!"              │
│  Words needed: ingredient, recipe, dough, flour, yeast     │
│  Reward: 🥖 Baker's Hat (cosmetic) + 50 Emeralds           │
│  Time left: 23:45:12                                       │
│  [Accept Quest]                                            │
│                                                             │
│  📚 THE LIBRARIAN                                          │
│  "I need 3 adjectives about intelligence"                  │
│  Words needed: clever, brilliant, wise                     │
│  Reward: 📖 Scholar's Robe + 30 Emeralds                   │
│  Time left: 23:45:12                                       │
│  [Accept Quest]                                            │
│                                                             │
│  🗡️ THE BLACKSMITH                                         │
│  "I need 4 action verbs for battle"                        │
│  Words needed: strike, defend, dodge, attack               │
│  Reward: ⚔️ Warrior's Blade + 40 Emeralds                  │
│  Time left: 23:45:12                                       │
│  [Accept Quest]                                            │
│                                                             │
│  Your Emeralds: 💚 234                                     │
│  (Use for: Streak Freeze, Premium Blueprints)              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Pedagogy:** Forces users to explore **Semantic Clusters**. They stop learning random words and start learning *related* words to fulfill trades.

### 5.4 The Nether Portal (Hardcore Immersion)

The Nether is scary, dangerous, high risk, high reward.

In LexiCraft, the "Nether" is **Real World Content**.

```
┌─────────────────────────────────────────────────────────────┐
│  🌋 THE NETHER                                              │
│                                                             │
│  ⚠️ WARNING: This is HARDCORE mode                         │
│  - No multiple choice - Type your answers                  │
│  - Real videos and articles                                │
│  - Wrong answers cost HEALTH (blocks can break)            │
│  - Unique rewards ONLY available here                      │
│                                                             │
│  Requirements: Level 10+, 50 Obsidian blocks               │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  🎬 Video Challenge: TED Talk Clip                  │   │
│  │                                                      │   │
│  │  "The speaker says innovation requires _____"       │   │
│  │  Type your answer: [____________]                   │   │
│  │                                                      │   │
│  │  ❤️❤️❤️🖤🖤 Health: 3/5                              │   │
│  │  🔥 Ghast approaching in 0:15...                    │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  Rewards: Nether Quartz (for Modern Tech buildings)        │
│           Exclusive titles and cosmetics                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Pedagogy:** Bridge from "Learning" to "Acquisition." Pushes advanced users out of the comfort zone of flashcards into real-world application.

---

## Part 6: The Biome System

Vocabulary sets map to visual biomes, giving variety to the learning journey.

| Vocabulary Set | Minecraft Biome | Materials | Structures |
|----------------|-----------------|-----------|------------|
| Foundation (A1) | Plains/Forest | Wood, Dirt, Stone | Basic Hut, Farm |
| Daily Life (A2) | Village | Bricks, Glass, Wool | Shops, Houses |
| Academic (B1/B2) | Stronghold | Stone Brick, Obsidian | Castles, Libraries |
| Professional (C1) | Nether | Nether Brick, Quartz | Towers, Labs |
| Nuance/Idioms (C2) | The End | End Stone, Purpur | Space Station, Magic Tower |

---

## Part 7: Sparks, Energy & The Building Economy

### How Sparks Work

Sparks (✨) represent effort. **ANY activity** earns Sparks. Your **Level** is derived from lifetime Sparks and never decreases.

```
┌─────────────────────────────────────────────────────────────┐
│  ⚡ XP SHOP                                                  │
│                                                             │
│  Your XP: 2,450 ⚡                                          │
│                                                             │
│  TOOLS                                                     │
│  ⛏️ Iron Pickaxe (200 XP)                                   │
│     Mine 20% faster for 7 days                             │
│                                                             │
│  🔥 Furnace Upgrade (300 XP)                               │
│     Smelt 2 ores at once                                   │
│                                                             │
│  BOOSTS                                                    │
│  🧊 Streak Freeze (50 XP)                                  │
│     Protect your streak for 1 day                          │
│                                                             │
│  ⚡ Fast Track (100 XP per word)                           │
│     Skip a word to next mastery level                      │
│                                                             │
│  COSMETICS                                                 │
│  👑 Gold Crown (500 XP)                                    │
│  🎨 Rainbow Frame (300 XP)                                 │
│  🏷️ "Dedicated Miner" Title (150 XP)                       │
│                                                             │
│  FEATURES                                                  │
│  🔮 Enchanting Table Access (1000 XP)                      │
│  🏘️ Village Trading (500 XP)                               │
│  🌋 Nether Portal (2000 XP)                                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Sparks Sources

| Activity | Sparks ✨ | Notes |
|----------|----------|-------|
| View new word | +1 | Just looking counts |
| Start MCQ question | +2 | Trying counts |
| Wrong answer | +1 | Effort, not skill |
| Correct answer | +5 | Bonus for success |
| Fast + Correct | +8 | Bonus for mastery |
| Review word | +2 | Maintenance counts |
| Pass review | +3 | Extra for success |
| Word → Hollow | +5 | Progress milestone |
| Word → Solid | +10 | Mastery milestone |
| Daily login | +10 | Consistency bonus |
| 7-day streak | +50 | Streak reward |

### Energy: The Building Currency

Energy (⚡) is ONLY obtained by leveling up. You cannot buy it or grind it directly.

| Level | Sparks Needed | Energy Reward |
|-------|--------------|---------------|
| 1 → 2 | 100 | 30 ⚡ |
| 2 → 3 | 150 | 50 ⚡ |
| 3 → 4 | 225 | 75 ⚡ |
| 4 → 5 | 337 | 100 ⚡ |
| 5 → 6 | 506 | 125 ⚡ |
| 6+ | +50% each | 125 ⚡ |

**Why Energy-on-Level-Up works:**
- Forces consistent play (can't speed-run to max energy)
- Level-up moments feel rewarding (tangible reward, not just a number)
- Creates natural pacing

---

## Part 8: Power Rating System

Instead of "Level 30," users have a **Power Rating** based on their actual vocabulary.

### Formula

```
Power Rating = √(Vocabulary Score × Effort Multiplier)

Vocabulary Score = 
    (Mastered × 1.0) + 
    (Known × 0.7) + 
    (Familiar × 0.4) + 
    (Learning × 0.1)

Effort Multiplier = 1 + (Total XP Spent / 10000)
```

### Example Comparisons

| Player | Mastered | Known | XP Spent | Power |
|--------|----------|-------|----------|-------|
| Bookworm | 400 | 200 | 500 | ~25 |
| Grinder | 100 | 150 | 5000 | ~22 |
| Balanced | 200 | 200 | 2000 | ~24 |

**The grinder can catch up, but prior knowledge has real advantage.**

### Mine Tiers (Replaces Levels)

| Power Rating | Mine Tier | Title |
|--------------|-----------|-------|
| 0-25 | Novice Mine | Apprentice Miner |
| 25-100 | Bronze Mine | Journeyman Miner |
| 100-400 | Silver Mine | Expert Miner |
| 400-1000 | Gold Mine | Master Miner |
| 1000+ | Diamond Mine | Legendary Miner |

---

## Part 9: Database Schema

### New Tables

```sql
-- Materials inventory (replaces simple XP tracking)
CREATE TABLE user_inventory (
    user_id UUID REFERENCES auth.users(id),
    material_type VARCHAR(30),  -- 'stone', 'wood', 'brick', 'gold', 'iron', 'amethyst', 'diamond'
    raw_quantity INT DEFAULT 0,     -- Unprocessed (learned but not reviewed)
    refined_quantity INT DEFAULT 0,  -- Smelted (passed review)
    PRIMARY KEY (user_id, material_type)
);

-- Blueprint definitions  
CREATE TABLE blueprints (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(50) UNIQUE NOT NULL,
    name_en VARCHAR(100) NOT NULL,
    name_zh VARCHAR(100),
    category VARCHAR(30),  -- 'starter', 'village', 'castle', 'nether', 'legendary'
    biome VARCHAR(30),     -- 'plains', 'village', 'stronghold', 'nether', 'end'
    -- Material requirements (refined blocks only)
    req_stone INT DEFAULT 0,
    req_wood INT DEFAULT 0,
    req_brick INT DEFAULT 0,
    req_gold INT DEFAULT 0,
    req_iron INT DEFAULT 0,
    req_amethyst INT DEFAULT 0,
    req_diamond INT DEFAULT 0,
    -- Unlock conditions
    prerequisite_blueprint VARCHAR(50),  -- Must complete this first
    min_power_rating INT DEFAULT 0,
    -- Rewards
    reward_title VARCHAR(50),
    reward_cosmetic VARCHAR(50),
    reward_feature VARCHAR(50),
    xp_reward INT DEFAULT 0
);

-- User's structures (what they're building)
CREATE TABLE user_structures (
    user_id UUID REFERENCES auth.users(id),
    blueprint_id UUID REFERENCES blueprints(id),
    status VARCHAR(20) DEFAULT 'building',  -- 'locked', 'building', 'complete', 'damaged'
    completion_pct DECIMAL(5,2) DEFAULT 0,
    damage_pct DECIMAL(5,2) DEFAULT 0,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    PRIMARY KEY (user_id, blueprint_id)
);

-- Links words to structure blocks (which word is which block)
CREATE TABLE structure_blocks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    blueprint_id UUID NOT NULL,
    learning_progress_id INT REFERENCES learning_progress(id),
    material_type VARCHAR(30),
    block_position INT,  -- Which slot in the structure
    health DECIMAL(3,2) DEFAULT 1.0,  -- 1.0 = solid, 0.0 = broken
    FOREIGN KEY (user_id, blueprint_id) REFERENCES user_structures(user_id, blueprint_id)
);

-- Enchantments on words
CREATE TABLE word_enchantments (
    user_id UUID REFERENCES auth.users(id),
    learning_progress_id INT REFERENCES learning_progress(id),
    enchant_type VARCHAR(30),  -- 'collocation', 'usage', 'pronunciation', 'etymology'
    enchant_level INT DEFAULT 1,
    unlocked_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (user_id, learning_progress_id, enchant_type)
);

-- Villager quests (daily rotating)
CREATE TABLE villager_quests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    villager_type VARCHAR(30),  -- 'baker', 'librarian', 'blacksmith', 'merchant'
    theme VARCHAR(50),  -- 'food', 'emotions', 'actions', etc.
    required_words TEXT[],  -- Array of sense_ids needed
    reward_emeralds INT,
    reward_cosmetic VARCHAR(50),
    active_date DATE,
    expires_at TIMESTAMPTZ
);

-- User quest progress
CREATE TABLE user_quests (
    user_id UUID REFERENCES auth.users(id),
    quest_id UUID REFERENCES villager_quests(id),
    status VARCHAR(20) DEFAULT 'active',  -- 'active', 'completed', 'expired'
    words_completed TEXT[],
    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    PRIMARY KEY (user_id, quest_id)
);

-- Crafting recipes (sentence patterns)
CREATE TABLE crafting_recipes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100),
    pattern TEXT[],  -- ['article', 'adjective', 'noun', 'verb']
    result_structure VARCHAR(50),  -- What structure this unlocks
    difficulty VARCHAR(20)  -- 'basic', 'intermediate', 'advanced'
);

-- XP as spendable currency (rename/repurpose)
-- Keep user_xp but add spending tracking
ALTER TABLE user_xp ADD COLUMN IF NOT EXISTS xp_spent INT DEFAULT 0;
ALTER TABLE user_xp ADD COLUMN IF NOT EXISTS xp_available INT GENERATED ALWAYS AS (total_xp - xp_spent) STORED;
```

### Migration from Current System

```sql
-- Map current mastery levels to materials
-- When a word reaches FAMILIAR → award raw ore
-- When a word reaches MASTERED → convert to refined block

-- Tier 1 words → Stone
-- Tier 2 words → Wood  
-- Tier 3 words → Brick
-- Tier 4 words → Gold
-- Tier 5 words → Iron
-- Tier 6 words → Amethyst
-- Tier 7 words → Diamond
```

---

## Part 10: Implementation Phases

### Phase 1: Foundation (Week 1-2)
- [ ] Add `user_inventory` table
- [ ] Map vocabulary tiers to material types
- [ ] Award raw materials on word learning
- [ ] Convert to refined on review pass
- [ ] Basic inventory UI

### Phase 2: Blueprints (Week 3-4)
- [ ] Add `blueprints` and `user_structures` tables
- [ ] Seed 10-15 starter blueprints
- [ ] Blueprint selection UI
- [ ] Structure progress visualization
- [ ] Material consumption on building

### Phase 3: Decay/Creeper (Week 5)
- [ ] Add `structure_blocks` table
- [ ] Link words to structure blocks
- [ ] Health calculation from FSRS retention
- [ ] Cracking visualization
- [ ] Repair mechanic (review to fix)

### Phase 4: XP Shop (Week 6)
- [ ] Repurpose XP as spendable currency
- [ ] XP shop UI
- [ ] Tool effects (faster learning, etc.)
- [ ] Cosmetic purchases
- [ ] Feature unlocks

### Phase 5: Enchanting (Week 7-8)
- [ ] Add `word_enchantments` table
- [ ] Design enchantment challenges
- [ ] Enchanting UI
- [ ] Durability bonuses

### Phase 6: Villagers (Week 9-10)
- [ ] Add quest tables
- [ ] Daily quest generation (semantic clustering)
- [ ] Quest UI
- [ ] Emerald currency

### Phase 7: Crafting (Week 11-12)
- [ ] Add `crafting_recipes` table
- [ ] Grammar pattern challenges
- [ ] Drag-and-drop crafting UI
- [ ] Sentence construction mechanics

### Phase 8: Nether (Week 13+)
- [ ] Real-world content integration
- [ ] Hardcore mode mechanics
- [ ] Nether-exclusive rewards

---

## Part 10.1: Asset Strategy

### Phased Approach

**Phase 0 - MVP (Ship Today):**
- Emoji + CSS only
- Test mechanic before investing in visuals
- If users don't care about leveling up the desk, pretty art won't save it

```tsx
const DeskVisual = ({ level }) => {
  const styles = [
    { bg: 'bg-amber-700', emoji: '📦', name: 'Cardboard Box' },
    { bg: 'bg-amber-600', emoji: '🪑', name: 'Folding Table' },
    { bg: 'bg-yellow-800', emoji: '📚', name: 'Wooden Desk' },
    { bg: 'bg-red-900', emoji: '💼', name: 'Mahogany Desk' },
    { bg: 'bg-blue-600', emoji: '🚀', glow: true, name: 'Hover Desk' },
  ][level - 1]
  return <div className={styles.bg}>{styles.emoji}</div>
}
```

**Phase 1 - Free Assets:**
- [Kenny Assets](https://kenney.nl/assets) - CC0 license, isometric city kits
- OpenGameArt.org - Various free assets
- Cost: $0 (donation encouraged)

**Phase 2 - AI Generated (if needed):**
- Midjourney/DALL-E for custom style
- ~$10-30/month subscription
- Prompt: "isometric pixel art desk, game asset, 64x64, transparent background"

**Phase 3 - Custom Art (if validated):**
- Commission artist on Fiverr/Upwork
- ~$50-200 for full asset set
- Only after mechanic is validated

### Two Rooms MVP

The MVP includes **2 rooms** to demonstrate the concept isn't "just one item":

#### Study Room (書房)
| Item | Emoji | Levels | Focus |
|------|-------|--------|-------|
| Desk | 📦→🚀 | 5 | Main progression |
| Lamp | 💡 | 4 | Secondary |
| Chair | 🪑 | 3 | Starter |
| Bookshelf | 📚 | 4 | Mid-game |

#### Living Room (客廳)
| Item | Emoji | Levels | Focus |
|------|-------|--------|-------|
| Plant | 🌱→🌳 | 4 | Low barrier |
| Coffee Table | 🫖 | 3 | Starter |
| TV | 📺 | 4 | Mid-game |
| Sofa | 🛋️ | 4 | Comfort goal |

#### Fast Progression Design

Each item level requires a mix of currencies:

```
Desk Upgrade Cost (Level → Level)
Level 1→2:  20⚡  +  5💧  + 0🧱  (just energy and essence)
Level 2→3:  35⚡  + 15💧  + 2🧱  (need first mastered words)
Level 3→4:  50⚡  + 25💧  + 4🧱  (mid commitment)
Level 4→5:  75⚡  + 40💧  + 8🧱  (significant achievement)
```

Lighter items (Chair, Plant) cost less. Heavier items (Sofa, Bookshelf) cost more.

**Success Metric:** Does the user ask "Where is my money?" or "How do I upgrade my desk?"
- If money → Overjustification problem (pivot needed)
- If desk → Winner (proceed to full city)

---

## Part 11: Summary Comparison

| Minecraft Concept | LexiCraft Mechanic | Educational Goal |
|-------------------|-------------------|------------------|
| **Mining** | Answering MCQs | Acquisition & Recognition |
| **Smelting** | Spaced Repetition Reviews | Retention & Memory |
| **Building** | Blueprint Completion | Goal-Oriented Learning |
| **Durability/Decay** | Block Health (FSRS) | Consistency & Review |
| **Crafting** | Sentence Construction | Grammar & Syntax |
| **Enchanting** | Deep Word Mastery | Nuance & Proficiency |
| **Villagers** | Themed Daily Quests | Semantic Clustering |
| **The Nether** | Real-World Immersion | Application & Fluency |
| **Inventory** | Word Collection | Tangible Progress |
| **Power Rating** | Vocabulary + Effort | Fair Competition |

---

## Part 12: Why This Works

### 1. Answers "Why Am I Learning This?"
- ❌ Old: "To pass a test"
- ✅ New: "I need 5 more Diamond blocks for my Castle"

### 2. Prior Knowledge is Valued
- Students who read a lot start with an advantage
- Their existing vocabulary counts as "starting inventory"
- But effort (XP) can close the gap

### 3. Learning Feels Like Progress
- Not abstract numbers going up
- Visible inventory filling
- Structures physically being built

### 4. Forgetting Has Stakes
- Your castle starts cracking
- Emotional attachment to creations
- "I need to log in to fix my tower!"

### 5. Multiple Paths to Success
- Grind XP → Buy tools → Learn faster
- Already know words → Prove them → Big inventory
- Mix of both → Optimal path

---

## Related Documents

- [30-ux-vision-game-design.md](./30-ux-vision-game-design.md) - Original UX vision (foundation)
- [31-economic-model-hypotheses.md](./31-economic-model-hypotheses.md) - Dual economy (XP + Points)
- [06-spaced-repetition-strategy.md](./06-spaced-repetition-strategy.md) - FSRS algorithm (the furnace)
- [00-TERMINOLOGY.md](./00-TERMINOLOGY.md) - Block terminology

---

*This isn't vocabulary memorization.*
*This is Minecraft where words are the building blocks.*

