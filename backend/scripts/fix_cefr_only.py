#!/usr/bin/env python3
"""
Fix CEFR Levels Only

This script only fixes CEFR levels for common words without changing the word field.
The word field keeps the inflected form (like "were") while lemma field has base form.

Usage:
    python fix_cefr_only.py
"""

import json
from pathlib import Path


VOCAB_FILE = Path(__file__).parent.parent / "data" / "vocabulary.json"

# Base CEFR levels for common lemmas
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
    
    # A2 - Elementary
    'need': 'A2', 'keep': 'A2', 'let': 'A2', 'begin': 'A2', 'put': 'A2',
    'run': 'A2', 'read': 'A2', 'write': 'A2', 'learn': 'A2', 'grow': 'A2',
    'turn': 'A2', 'move': 'A2', 'live': 'A2', 'believe': 'A2', 'hold': 'A2',
    'bring': 'A2', 'happen': 'A2',
    
    # B1 - Intermediate
    'press': 'B1', 'push': 'B1', 'pull': 'B1', 'squeeze': 'B1',
}


def extract_lemma(sense_id: str) -> str:
    return sense_id.split('.')[0] if '.' in sense_id else sense_id


def main():
    print(f"📖 Loading {VOCAB_FILE}...")
    with open(VOCAB_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    senses = data.get('senses', {})
    fixed = 0
    
    for sense_id, sense_data in senses.items():
        lemma = extract_lemma(sense_id).lower()
        
        if lemma in BASE_CEFR:
            old_cefr = sense_data.get('cefr', '')
            new_cefr = BASE_CEFR[lemma]
            if old_cefr != new_cefr:
                sense_data['cefr'] = new_cefr
                fixed += 1
    
    print(f"💾 Saving...")
    with open(VOCAB_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Fixed {fixed} CEFR levels")
    
    # Show samples
    print("\n📋 Samples:")
    for sid in ['be.v.01', 'be.v.02', 'press.v.01', 'have.v.01']:
        if sid in senses:
            s = senses[sid]
            print(f"   {sid}: word='{s.get('word')}', lemma='{s.get('lemma')}', cefr={s.get('cefr')}")


if __name__ == "__main__":
    main()


