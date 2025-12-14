# Recalculate Block Values Script

## Purpose

Verifies and recalculates all block values in `vocabulary.json` based on:
- **Tier-based base XP** (from `LevelService.TIER_BASE_XP`)
- **Connection counts** with type-specific bonuses

## Formula

```
base_xp = TIER_BASE_XP[tier]
connection_bonus = (related × 10) + (opposite × 10) + (phrases × 20) + (idioms × 30) + (morphological × 10)
total_xp = base_xp + connection_bonus
```

## Connection Bonuses

| Connection Type | Bonus per Connection |
|----------------|---------------------|
| Related | +10 XP |
| Opposite | +10 XP |
| Phrases | +20 XP |
| Idioms | +30 XP |
| Morphological | +10 XP |

## Tier Base XP

| Tier | Type | Base XP |
|------|------|---------|
| 1 | Basic Block | 100 |
| 2 | Multi-Block | 250 |
| 3 | Phrase Block | 500 |
| 4 | Idiom Block | 1,000 |
| 5 | Pattern Block | 300 |
| 6 | Register Block | 400 |
| 7 | Context Block | 750 |

## Usage

### Dry Run (Recommended First)
```bash
cd backend/scripts
python recalculate_block_values.py --dry-run
```

This will show you:
- How many senses need updates
- Example changes
- Statistics without modifying the file

### Apply Changes (Interactive)
```bash
python recalculate_block_values.py
```

The script will:
1. Analyze all senses
2. Show statistics
3. Ask for confirmation
4. Create a backup (`vocabulary.json.backup`)
5. Update `vocabulary.json`

### Auto-Apply (No Confirmation)
```bash
python recalculate_block_values.py --auto
```

Automatically applies changes without asking for confirmation.

## Output

The script provides:
- Total senses processed
- Number of senses needing updates
- Breakdown of value changes (base_xp, connection_bonus, total_xp)
- Max increase/decrease examples
- Sample changes (first 10)

## Safety

- **Automatic backup**: Creates `vocabulary.json.backup` before any changes
- **Dry-run mode**: Test without modifying files
- **Confirmation prompt**: Asks before applying changes (unless `--auto`)

## Example Output

```
======================================================================
Block Value Recalculation Script
======================================================================
Vocabulary file: /path/to/vocabulary.json

📖 Loading vocabulary.json...
✅ Loaded 10470 senses

🔍 Verifying and recalculating values...

======================================================================
📊 Statistics
======================================================================
Total senses processed: 10470
Senses needing update: 234
Percentage: 2.23%

Value changes:
  - Base XP changes: 12
  - Connection bonus changes: 234
  - Total XP changes: 234

Max increase: +150 XP
Max decrease: -20 XP

Example changes (first 10):
  - break (break.v.01): 250 → 370 XP (+120)
  - drop (drop.v.01): 100 → 120 XP (+20)
  ...
```

## When to Run

Run this script when:
- Connection counts have been updated in Neo4j
- Tier assignments have changed
- You want to verify all values are correct
- After major vocabulary enrichment updates

