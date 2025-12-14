# ADR-002: Minecraft Game Model

**Status:** Accepted  
**Date:** December 2024  
**Supersedes:** Traditional RPG level/XP model

---

## Context

LexiCraft initially used a traditional RPG gamification model:
- XP earned → Level increases → Features unlock
- Word proficiency tracked separately via FSRS
- XP was a "score" to hoard, not a currency to spend

This model has several problems:
1. **"Why am I learning this?"** - No clear purpose beyond abstract numbers
2. **Prior knowledge ignored** - A well-read student starts at Level 1 like everyone else
3. **XP conflated with learning** - High XP ≠ actually knowing words
4. **No emotional stakes** - Forgetting a word has no visible consequence

## Decision

Adopt the **Minecraft game model** where:

1. **Your vocabulary IS your power** (inventory, not level)
2. **XP is spendable currency** (like gold for enchanting)
3. **Words become building materials** (mine → smelt → build)
4. **Forgetting damages your structures** (creeper mechanic)
5. **Prior knowledge = starting inventory** (from survey/proving)

### Core Loop

```
MINE (MCQ) → SMELT (Review) → BUILD (Blueprints)
```

### Key Principles

| Principle | Implementation |
|-----------|---------------|
| Inventory over Level | Power Rating = √(Words × Effort) |
| XP is Currency | Spend on tools, cosmetics, features |
| Tangible Progress | Visual structures, filled inventory |
| Stakes for Forgetting | Blocks crack, structures damaged |
| Prior Knowledge Valued | Fast-track proving, starting inventory |

## Consequences

### Positive
- **Clear purpose**: "I need 5 more diamonds for my castle"
- **Fair to all**: Readers have advantage, grinders can catch up
- **Emotional engagement**: Protect your creations
- **Natural retention**: Come back to prevent decay
- **Semantic learning**: Villager quests cluster related words

### Negative
- **Major refactor**: Current XP/level system needs rework
- **New UI required**: Inventory, blueprints, structures
- **Complexity**: More systems to explain to new users
- **Database changes**: New tables for inventory, structures, quests

### Neutral
- FSRS algorithm remains (becomes "the furnace")
- MCQ system remains (becomes "the pickaxe")
- Points/cash economy remains separate (external economy)

## Implementation

See [35-minecraft-game-design.md](../35-minecraft-game-design.md) for full design spec.

### Phase Priority

1. Inventory system (materials from tiers)
2. Blueprint system (goals with requirements)
3. Decay visualization (FSRS → block health)
4. XP shop (spend, don't hoard)
5. Advanced mechanics (enchanting, villagers, nether)

## Alternatives Considered

### Alternative A: Enhanced RPG Model
Keep levels but add more unlocks and achievements.
- Rejected: Doesn't solve "why am I learning?" problem

### Alternative B: Tycoon Model
Treat words as business assets generating revenue.
- Rejected: Accumulating money is less compelling than building creations

### Alternative C: Minecraft Model (Selected)
Words as building materials, structures as goals.
- Selected: Answers "why?", values prior knowledge, creates emotional stakes

## References

- [35-minecraft-game-design.md](../35-minecraft-game-design.md) - Full design document
- [30-ux-vision-game-design.md](../30-ux-vision-game-design.md) - Original vision (foundation)
- Minecraft game design analysis

