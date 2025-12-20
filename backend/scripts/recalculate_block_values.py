#!/usr/bin/env python3
"""
Recalculate Block Values Script

Verifies and recalculates all block values in vocabulary.json based on:
- Tier-based base XP
- Connection counts (with type-specific bonuses)

Formula:
  base_xp = TIER_BASE_XP[tier]
  connection_bonus = (related * 10) + (opposite * 10) + (phrases * 20) + (idioms * 30) + (morphological * 10)
  total_xp = base_xp + connection_bonus

Usage:
  python recalculate_block_values.py [--dry-run] [--auto]
  
Options:
  --dry-run    Show what would be changed without updating the file
  --auto       Automatically apply changes without confirmation
"""

import json
import sys
import argparse
from pathlib import Path
from typing import Dict, List, Tuple
from datetime import datetime
from collections import defaultdict

# Tier-based base XP (from LevelService - Frequency-Aligned Design)
TIER_BASE_XP = {
    1: 100,   # Basic Block (High Freq - Baseline)
    2: 120,   # Multi-Block (High Freq - Variant)
    3: 200,   # Phrase Block (Mid Freq - Combinatorial)
    4: 300,   # Idiom Block (Low Freq - Abstract)
    5: 150,   # Pattern Block (Mid Freq - Structural)
    6: 200,   # Register Block (Mid Freq - Social)
    7: 250,   # Context Block (Low Freq - Nuance)
}

# Connection bonuses by type
CONNECTION_BONUSES = {
    'related': 10,
    'opposite': 10,
    'phrases': 20,
    'idioms': 30,
    'morphological': 10,
}


def calculate_block_value(
    tier: int,
    connection_counts: Dict[str, int]
) -> Tuple[int, int, int]:
    """
    Calculate block value components.
    
    Args:
        tier: Block tier (1-7)
        connection_counts: Dictionary with connection type counts
        
    Returns:
        Tuple of (base_xp, connection_bonus, total_xp)
    """
    # Get base XP from tier
    base_xp = TIER_BASE_XP.get(tier, 100)
    
    # Calculate connection bonus
    connection_bonus = 0
    for conn_type, bonus_per_conn in CONNECTION_BONUSES.items():
        count = connection_counts.get(conn_type, 0)
        connection_bonus += count * bonus_per_conn
    
    total_xp = base_xp + connection_bonus
    
    return base_xp, connection_bonus, total_xp


def verify_and_recalculate_sense(
    sense_id: str,
    sense_data: Dict
) -> Tuple[bool, Dict, Dict]:
    """
    Verify and recalculate value for a single sense.
    
    Args:
        sense_id: Sense ID
        sense_data: Sense data from vocabulary.json
        
    Returns:
        Tuple of (needs_update, old_value, new_value)
    """
    # Get tier (default to 1 if missing)
    tier = sense_data.get('tier', 1)
    
    # Get connection counts
    connection_counts = sense_data.get('connection_counts', {})
    if not connection_counts:
        # Fallback: count from connections arrays
        connections = sense_data.get('connections', {})
        connection_counts = {
            'related': len(connections.get('related', [])),
            'opposite': len(connections.get('opposite', [])),
            'phrases': len(connections.get('phrases', [])),
            'idioms': len(connections.get('idioms', [])),
            'morphological': len(connections.get('morphological', [])),
            'total': sum([
                len(connections.get('related', [])),
                len(connections.get('opposite', [])),
                len(connections.get('phrases', [])),
                len(connections.get('idioms', [])),
                len(connections.get('morphological', [])),
            ])
        }
    
    # Calculate correct values
    base_xp, connection_bonus, total_xp = calculate_block_value(tier, connection_counts)
    
    # Get current stored values
    old_value = sense_data.get('value', {})
    old_base_xp = old_value.get('base_xp', 100)
    old_connection_bonus = old_value.get('connection_bonus', 0)
    old_total_xp = old_value.get('total_xp', 100)
    
    # New value object
    new_value = {
        'base_xp': base_xp,
        'connection_bonus': connection_bonus,
        'total_xp': total_xp
    }
    
    # Check if update needed
    needs_update = (
        old_base_xp != base_xp or
        old_connection_bonus != connection_bonus or
        old_total_xp != total_xp
    )
    
    return needs_update, old_value, new_value


def main():
    """Main script execution."""
    # Parse arguments
    parser = argparse.ArgumentParser(
        description='Recalculate block values in vocabulary.json'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be changed without updating the file'
    )
    parser.add_argument(
        '--auto',
        action='store_true',
        help='Automatically apply changes without confirmation'
    )
    args = parser.parse_args()
    
    # Paths
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent  # Go up two levels: scripts -> backend -> root
    vocab_file = project_root / 'landing-page' / 'data' / 'vocabulary.json'
    backup_file = vocab_file.with_suffix('.json.backup')
    
    print("=" * 70)
    print("Block Value Recalculation Script")
    print("=" * 70)
    if args.dry_run:
        print("🔍 DRY RUN MODE - No changes will be made")
    print(f"Vocabulary file: {vocab_file}")
    print()
    
    # Check if file exists
    if not vocab_file.exists():
        print(f"❌ Error: Vocabulary file not found at {vocab_file}")
        sys.exit(1)
    
    # Load vocabulary data
    print("📖 Loading vocabulary.json...")
    try:
        with open(vocab_file, 'r', encoding='utf-8') as f:
            vocab_data = json.load(f)
    except Exception as e:
        print(f"❌ Error loading vocabulary.json: {e}")
        sys.exit(1)
    
    print(f"✅ Loaded {len(vocab_data.get('senses', {}))} senses")
    print()
    
    # Statistics
    stats = {
        'total_senses': 0,
        'needs_update': 0,
        'updates_by_type': defaultdict(int),
        'value_changes': {
            'base_xp_changes': 0,
            'connection_bonus_changes': 0,
            'total_xp_changes': 0,
        },
        'max_increase': 0,
        'max_decrease': 0,
        'examples': []
    }
    
    # Process all senses
    print("🔍 Verifying and recalculating values...")
    senses = vocab_data.get('senses', {})
    
    for sense_id, sense_data in senses.items():
        stats['total_senses'] += 1
        
        needs_update, old_value, new_value = verify_and_recalculate_sense(
            sense_id, sense_data
        )
        
        if needs_update:
            stats['needs_update'] += 1
            
            # Track changes
            if old_value.get('base_xp') != new_value['base_xp']:
                stats['value_changes']['base_xp_changes'] += 1
            if old_value.get('connection_bonus') != new_value['connection_bonus']:
                stats['value_changes']['connection_bonus_changes'] += 1
            if old_value.get('total_xp') != new_value['total_xp']:
                stats['value_changes']['total_xp_changes'] += 1
            
            # Track max changes
            old_total = old_value.get('total_xp', 0)
            new_total = new_value['total_xp']
            diff = new_total - old_total
            
            if diff > stats['max_increase']:
                stats['max_increase'] = diff
            if diff < stats['max_decrease']:
                stats['max_decrease'] = diff
            
            # Store example (first 10)
            if len(stats['examples']) < 10:
                stats['examples'].append({
                    'sense_id': sense_id,
                    'word': sense_data.get('word', 'unknown'),
                    'old': old_value,
                    'new': new_value,
                    'diff': diff
                })
            
            # Update the sense data
            sense_data['value'] = new_value
    
    # Print statistics
    print()
    print("=" * 70)
    print("📊 Statistics")
    print("=" * 70)
    print(f"Total senses processed: {stats['total_senses']}")
    print(f"Senses needing update: {stats['needs_update']}")
    print(f"Percentage: {(stats['needs_update'] / stats['total_senses'] * 100):.2f}%")
    print()
    print("Value changes:")
    print(f"  - Base XP changes: {stats['value_changes']['base_xp_changes']}")
    print(f"  - Connection bonus changes: {stats['value_changes']['connection_bonus_changes']}")
    print(f"  - Total XP changes: {stats['value_changes']['total_xp_changes']}")
    print()
    print(f"Max increase: +{stats['max_increase']} XP")
    print(f"Max decrease: {stats['max_decrease']} XP")
    print()
    
    if stats['examples']:
        print("Example changes (first 10):")
        for ex in stats['examples']:
            diff_str = f"+{ex['diff']}" if ex['diff'] > 0 else str(ex['diff'])
            print(f"  - {ex['word']} ({ex['sense_id']}): "
                  f"{ex['old'].get('total_xp', 0)} → {ex['new']['total_xp']} XP ({diff_str})")
        print()
    
    # Ask for confirmation if updates needed
    if stats['needs_update'] > 0:
        if args.dry_run:
            print("=" * 70)
            print(f"🔍 DRY RUN: Would update {stats['needs_update']} senses")
            print("=" * 70)
            print("Run without --dry-run to apply changes.")
            sys.exit(0)
        
        if not args.auto:
            print("=" * 70)
            print("⚠️  WARNING: Changes will be made to vocabulary.json")
            print("=" * 70)
            response = input(f"Update {stats['needs_update']} senses? (yes/no): ").strip().lower()
            
            if response not in ['yes', 'y']:
                print("❌ Update cancelled.")
                sys.exit(0)
        
        # Create backup
        print()
        print(f"💾 Creating backup: {backup_file}")
        try:
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(vocab_data, f, ensure_ascii=False, indent=2)
            print(f"✅ Backup created successfully")
        except Exception as e:
            print(f"❌ Error creating backup: {e}")
            sys.exit(1)
        
        # Update vocabulary.json
        print()
        print(f"✏️  Updating vocabulary.json...")
        try:
            # Update export timestamp
            vocab_data['exportedAt'] = datetime.now().isoformat()
            
            with open(vocab_file, 'w', encoding='utf-8') as f:
                json.dump(vocab_data, f, ensure_ascii=False, indent=2)
            print(f"✅ Successfully updated {stats['needs_update']} senses")
        except Exception as e:
            print(f"❌ Error updating vocabulary.json: {e}")
            print(f"💡 Backup is available at: {backup_file}")
            sys.exit(1)
    else:
        print("✅ All values are correct! No updates needed.")
    
    print()
    print("=" * 70)
    print("✅ Script completed successfully")
    print("=" * 70)


if __name__ == '__main__':
    main()

