#!/usr/bin/env python3
"""
Add Lemma Field to Vocabulary

This script adds an explicit 'lemma' field to each sense in vocabulary.json.
The lemma is extracted from the sense_id (e.g., 'press.v.01' -> 'press').

This makes frontend lookups faster and more explicit - no need to parse
sense_id at runtime.

Usage:
    python add_lemma_field.py
    
Output:
    Updates vocabulary.json in place (with backup)
"""

import json
import shutil
from pathlib import Path
from datetime import datetime


# Configuration
VOCAB_FILE = Path(__file__).parent.parent / "data" / "vocabulary.json"
BACKUP_DIR = Path(__file__).parent.parent / "data" / "backups"


def extract_lemma(sense_id: str) -> str:
    """Extract lemma from sense_id.
    
    Examples:
        'press.v.01' -> 'press'
        'hot_dog.n.01' -> 'hot_dog'
        'be.v.01' -> 'be'
    """
    parts = sense_id.split('.')
    return parts[0] if parts else sense_id


def main():
    print(f"\n{'='*60}")
    print("📝 Adding Lemma Field to Vocabulary")
    print(f"{'='*60}\n")
    
    # Load vocabulary
    print(f"📖 Loading {VOCAB_FILE}...")
    with open(VOCAB_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    senses = data.get('senses', {})
    print(f"✅ Loaded {len(senses)} senses")
    
    # Count how many already have lemma field
    existing_lemmas = sum(1 for s in senses.values() if 'lemma' in s)
    print(f"📊 Existing lemma fields: {existing_lemmas}")
    
    # Create backup
    BACKUP_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = BACKUP_DIR / f"vocabulary_{timestamp}.json"
    print(f"💾 Creating backup at {backup_path}...")
    shutil.copy(VOCAB_FILE, backup_path)
    
    # Add lemma field to each sense
    added_count = 0
    mismatches = []
    
    for sense_id, sense_data in senses.items():
        lemma = extract_lemma(sense_id)
        word = sense_data.get('word', '')
        
        # Add lemma field
        if 'lemma' not in sense_data:
            sense_data['lemma'] = lemma
            added_count += 1
        
        # Track mismatches (where word != lemma)
        if word.lower() != lemma.lower():
            mismatches.append({
                'sense_id': sense_id,
                'lemma': lemma,
                'word': word
            })
    
    # Save updated vocabulary
    print(f"💾 Saving updated vocabulary...")
    with open(VOCAB_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    # Print summary
    print(f"\n{'='*60}")
    print("✅ Complete!")
    print(f"{'='*60}")
    print(f"📊 Added lemma to {added_count} senses")
    print(f"📊 Word/lemma mismatches: {len(mismatches)}")
    
    if mismatches:
        print(f"\n⚠️  Sample mismatches (word ≠ lemma):")
        for m in mismatches[:10]:
            print(f"   {m['sense_id']}: lemma='{m['lemma']}', word='{m['word']}'")
        if len(mismatches) > 10:
            print(f"   ... and {len(mismatches) - 10} more")
    
    print(f"\n📁 Backup saved to: {backup_path}")
    print(f"📁 Updated: {VOCAB_FILE}")


if __name__ == "__main__":
    main()


