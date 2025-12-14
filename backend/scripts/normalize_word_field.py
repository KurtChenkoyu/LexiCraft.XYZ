#!/usr/bin/env python3
"""
Normalize Word Field to Lemma

This script fixes vocabulary data quality issues:
1. Sets word = lemma for all senses (so "be.v.01" has word="be", not "were")
2. Stores inflected forms in a new "variants" array
3. Recalculates CEFR based on lemma's actual difficulty

The problem: During WordNet → Taiwan MOE mapping, inflected forms like "were"
got assigned as the primary word for "be.v.01", and given wrong CEFR levels.

Usage:
    python normalize_word_field.py
    
Output:
    backend/data/vocabulary.json (in-place with backup)
"""

import json
import shutil
from pathlib import Path
from datetime import datetime
from collections import defaultdict


# Configuration
VOCAB_FILE = Path(__file__).parent.parent / "data" / "vocabulary.json"
BACKUP_DIR = Path(__file__).parent.parent / "data" / "backups"

# Base CEFR levels for common lemmas (manually curated core vocabulary)
# These override AI-assigned levels for the most fundamental words
BASE_CEFR = {
    # A1 - Most basic
    'be': 'A1', 'have': 'A1', 'do': 'A1', 'say': 'A1', 'get': 'A1',
    'make': 'A1', 'go': 'A1', 'know': 'A1', 'take': 'A1', 'see': 'A1',
    'come': 'A1', 'think': 'A1', 'look': 'A1', 'want': 'A1', 'give': 'A1',
    'use': 'A1', 'find': 'A1', 'tell': 'A1', 'ask': 'A1', 'work': 'A1',
    'seem': 'A1', 'feel': 'A1', 'try': 'A1', 'leave': 'A1', 'call': 'A1',
    'good': 'A1', 'new': 'A1', 'first': 'A1', 'last': 'A1', 'long': 'A1',
    'great': 'A1', 'little': 'A1', 'own': 'A1', 'other': 'A1', 'old': 'A1',
    'right': 'A1', 'big': 'A1', 'high': 'A1', 'small': 'A1', 'large': 'A1',
    'not': 'A1', 'in': 'A1', 'on': 'A1', 'at': 'A1', 'by': 'A1',
    'i': 'A1', 'you': 'A1', 'he': 'A1', 'she': 'A1', 'it': 'A1',
    'we': 'A1', 'they': 'A1', 'this': 'A1', 'that': 'A1', 'what': 'A1',
    
    # A2 - Elementary
    'need': 'A2', 'keep': 'A2', 'let': 'A2', 'begin': 'A2', 'put': 'A2',
    'run': 'A2', 'read': 'A2', 'write': 'A2', 'learn': 'A2', 'grow': 'A2',
    'turn': 'A2', 'move': 'A2', 'live': 'A2', 'believe': 'A2', 'hold': 'A2',
    'bring': 'A2', 'happen': 'A2', 'must': 'A2', 'should': 'A2', 'might': 'A2',
}


def extract_lemma(sense_id: str) -> str:
    """Extract lemma from sense_id (e.g., 'be.v.01' -> 'be')."""
    return sense_id.split('.')[0] if '.' in sense_id else sense_id


def get_best_cefr(lemma: str, current_cefr: str) -> str:
    """Get the best CEFR level for a lemma.
    
    Priority:
    1. Manually curated BASE_CEFR for core vocabulary
    2. Keep current CEFR if reasonable
    """
    lemma_lower = lemma.lower().replace('_', ' ')
    
    # Check base CEFR first
    if lemma_lower in BASE_CEFR:
        return BASE_CEFR[lemma_lower]
    
    # Keep current CEFR if it exists
    return current_cefr or 'B1'


def main():
    print(f"\n{'='*60}")
    print("🔧 Normalizing Word Field to Lemma")
    print(f"{'='*60}\n")
    
    # Load vocabulary
    print(f"📖 Loading {VOCAB_FILE}...")
    with open(VOCAB_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    senses = data.get('senses', {})
    print(f"✅ Loaded {len(senses)} senses")
    
    # Create backup
    BACKUP_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = BACKUP_DIR / f"vocabulary_{timestamp}_prenorm.json"
    print(f"💾 Creating backup at {backup_path}...")
    shutil.copy(VOCAB_FILE, backup_path)
    
    # Statistics
    stats = {
        'word_normalized': 0,
        'variants_added': 0,
        'cefr_fixed': 0,
    }
    
    # Track all variants for each lemma
    lemma_variants = defaultdict(set)
    
    # First pass: collect all unique word forms per lemma
    for sense_id, sense_data in senses.items():
        lemma = extract_lemma(sense_id)
        word = sense_data.get('word', lemma)
        if word.lower() != lemma.lower():
            lemma_variants[lemma.lower()].add(word.lower())
    
    # Second pass: normalize
    for sense_id, sense_data in senses.items():
        lemma = extract_lemma(sense_id)
        old_word = sense_data.get('word', lemma)
        old_cefr = sense_data.get('cefr', '')
        
        # 1. Normalize word to lemma
        if old_word.lower() != lemma.lower():
            sense_data['word'] = lemma
            stats['word_normalized'] += 1
            
            # Store old word as variant if it's a valid inflection
            if 'variants' not in sense_data:
                sense_data['variants'] = []
            if old_word.lower() not in [v.lower() for v in sense_data['variants']]:
                sense_data['variants'].append(old_word)
                stats['variants_added'] += 1
        
        # 2. Fix CEFR based on lemma
        new_cefr = get_best_cefr(lemma, old_cefr)
        if new_cefr != old_cefr:
            sense_data['cefr'] = new_cefr
            stats['cefr_fixed'] += 1
        
        # 3. Add all known variants for this lemma
        all_variants = lemma_variants.get(lemma.lower(), set())
        existing_variants = set(v.lower() for v in sense_data.get('variants', []))
        for var in all_variants:
            if var not in existing_variants and var != lemma.lower():
                if 'variants' not in sense_data:
                    sense_data['variants'] = []
                sense_data['variants'].append(var)
    
    # Save updated vocabulary
    print(f"💾 Saving normalized vocabulary...")
    with open(VOCAB_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    # Print summary
    print(f"\n{'='*60}")
    print("✅ Normalization Complete!")
    print(f"{'='*60}")
    print(f"📊 Words normalized (word → lemma): {stats['word_normalized']}")
    print(f"📊 Variants stored: {stats['variants_added']}")
    print(f"📊 CEFR levels fixed: {stats['cefr_fixed']}")
    
    # Show examples
    print(f"\n📋 Sample normalized senses:")
    sample_ids = ['be.v.01', 'be.v.02', 'be.v.03', 'press.v.01', 'have.v.01']
    for sid in sample_ids:
        if sid in senses:
            s = senses[sid]
            print(f"   {sid}: word='{s.get('word')}', cefr={s.get('cefr')}, variants={s.get('variants', [])}")
    
    print(f"\n📁 Backup: {backup_path}")
    print(f"📁 Updated: {VOCAB_FILE}")


if __name__ == "__main__":
    main()


