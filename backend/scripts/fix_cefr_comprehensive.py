#!/usr/bin/env python3
"""
Comprehensive CEFR Level Fix

Uses multiple authoritative sources to fix CEFR levels:
1. EVP-CEFR exact match (word + POS)
2. Taiwan MOE level → CEFR mapping
3. Common words override list
4. Frequency estimation (with caps for common words)

Usage:
    python fix_cefr_comprehensive.py
"""

import json
import csv
from pathlib import Path
from typing import Dict, Optional
from collections import defaultdict

# File paths
VOCAB_FILE = Path(__file__).parent.parent / "data" / "vocabulary.json"
EVP_FILE = Path(__file__).parent.parent / "data" / "source" / "evp-cefr.json"
MOE_FILE = Path(__file__).parent.parent.parent / "data" / "source" / "moe_7000.csv"
OUTPUT_FILE = Path(__file__).parent.parent / "data" / "vocabulary.json"

# MOE Level → CEFR mapping
MOE_TO_CEFR = {
    1: 'A1',  # Most basic (elementary)
    2: 'A2',  # Basic
    3: 'B1',  # Intermediate
    4: 'B2',  # Upper-intermediate
    5: 'C1',  # Advanced
    6: 'C2',  # Most advanced
}

# Common words that should be A1/A2 regardless of frequency
COMMON_WORDS_OVERRIDE = {
    # A1 - Most common everyday words
    'doctor': 'A1',
    'teacher': 'A1',
    'student': 'A1',
    'friend': 'A1',
    'house': 'A1',
    'car': 'A1',
    'book': 'A1',
    'water': 'A1',
    'food': 'A1',
    'time': 'A1',
    'day': 'A1',
    'year': 'A1',
    'man': 'A1',
    'woman': 'A1',
    'child': 'A1',
    'mother': 'A1',
    'father': 'A1',
    'sister': 'A1',
    'brother': 'A1',
    'school': 'A1',
    'home': 'A1',
    'family': 'A1',
    'people': 'A1',
    'work': 'A1',
    'play': 'A1',
    'eat': 'A1',
    'drink': 'A1',
    'sleep': 'A1',
    'walk': 'A1',
    'run': 'A1',
    'see': 'A1',
    'hear': 'A1',
    'say': 'A1',
    'talk': 'A1',
    'read': 'A1',
    'write': 'A1',
    'good': 'A1',
    'bad': 'A1',
    'big': 'A1',
    'small': 'A1',
    'new': 'A1',
    'old': 'A1',
    'hot': 'A1',
    'cold': 'A1',
    'happy': 'A1',
    'sad': 'A1',
    
    # A2 - Common but slightly more complex
    'hospital': 'A2',
    'office': 'A2',
    'restaurant': 'A2',
    'store': 'A2',
    'money': 'A2',
    'buy': 'A2',
    'sell': 'A2',
    'help': 'A2',
    'learn': 'A2',
    'teach': 'A2',
    'understand': 'A2',
    'remember': 'A2',
    'forget': 'A2',
    'important': 'A2',
    'easy': 'A2',
    'difficult': 'A2',
    'beautiful': 'A2',
    'ugly': 'A2',
}


def load_evp_data() -> Dict[str, Dict]:
    """Load EVP-CEFR data."""
    if not EVP_FILE.exists():
        print(f"⚠️  EVP file not found: {EVP_FILE}")
        return {}
    
    with open(EVP_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Convert to word+pos key format
    evp_map = {}
    for word, info in data.items():
        pos = info.get('pos', '')
        key = f"{word.lower()}:{pos}" if pos else word.lower()
        evp_map[key] = info.get('level')
        # Also add word-only key (lower priority)
        if word.lower() not in evp_map:
            evp_map[word.lower()] = info.get('level')
    
    print(f"✅ Loaded {len(data)} EVP entries")
    return evp_map


def load_moe_data() -> Dict[str, int]:
    """Load Taiwan MOE word list."""
    if not MOE_FILE.exists():
        print(f"⚠️  MOE file not found: {MOE_FILE}")
        return {}
    
    moe_map = {}
    with open(MOE_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            word = row.get('word', '').strip().lower()
            level = row.get('moe_level', '').strip()
            if word and level:
                try:
                    moe_map[word] = int(level)
                except ValueError:
                    pass
    
    print(f"✅ Loaded {len(moe_map)} MOE entries")
    return moe_map


def get_cefr_from_moe(moe_level: int) -> str:
    """Convert MOE level to CEFR."""
    return MOE_TO_CEFR.get(moe_level, 'B1')


def get_best_cefr(
    lemma: str,
    pos: str,
    current_cefr: str,
    frequency_rank: Optional[int],
    evp_map: Dict,
    moe_map: Dict
) -> str:
    """
    Get best CEFR level using priority order:
    1. EVP-CEFR exact match (word + POS)
    2. Common words override
    3. Taiwan MOE level → CEFR
    4. EVP-CEFR word-only match
    5. Frequency estimation (capped at B1 for MOE Level 1-2 words)
    """
    lemma_lower = lemma.lower()
    
    # Priority 1: EVP-CEFR exact match (word + POS)
    evp_key = f"{lemma_lower}:{pos}"
    if evp_key in evp_map and evp_map[evp_key]:
        return evp_map[evp_key]
    
    # Priority 2: Common words override
    if lemma_lower in COMMON_WORDS_OVERRIDE:
        return COMMON_WORDS_OVERRIDE[lemma_lower]
    
    # Priority 3: Taiwan MOE level → CEFR
    if lemma_lower in moe_map:
        moe_level = moe_map[lemma_lower]
        return get_cefr_from_moe(moe_level)
    
    # Priority 4: EVP-CEFR word-only match
    if lemma_lower in evp_map and evp_map[lemma_lower]:
        return evp_map[lemma_lower]
    
    # Priority 5: Frequency estimation (with cap for common words)
    if frequency_rank is not None:
        # If word is in MOE Level 1-2, cap at B1 (can't be C-level)
        if lemma_lower in moe_map and moe_map[lemma_lower] <= 2:
            estimated = estimate_cefr_from_frequency(frequency_rank)
            # Cap at B1 for basic MOE words
            if estimated in ('B2', 'C1', 'C2'):
                return 'B1'
            return estimated
        return estimate_cefr_from_frequency(frequency_rank)
    
    # Keep current if reasonable, otherwise default to B1
    if current_cefr in ('A1', 'A2', 'B1', 'B2', 'C1', 'C2'):
        return current_cefr
    return 'B1'


def estimate_cefr_from_frequency(frequency_rank: int) -> str:
    """Estimate CEFR from frequency rank (same as evp_cefr.py)."""
    if frequency_rank < 500:
        return 'A1'
    elif frequency_rank < 1500:
        return 'A2'
    elif frequency_rank < 3000:
        return 'B1'
    elif frequency_rank < 5000:
        return 'B2'
    elif frequency_rank < 8000:
        return 'C1'
    else:
        return 'C2'


def extract_lemma(sense_id: str) -> str:
    """Extract lemma from sense_id (e.g., 'press.v.01' -> 'press')."""
    return sense_id.split('.')[0] if '.' in sense_id else sense_id


def main():
    print("\n" + "="*60)
    print("🔧 Comprehensive CEFR Level Fix")
    print("="*60 + "\n")
    
    # Load data sources
    evp_map = load_evp_data()
    moe_map = load_moe_data()
    
    # Load vocabulary
    print(f"📖 Loading vocabulary from {VOCAB_FILE}...")
    with open(VOCAB_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    senses = data.get('senses', {})
    print(f"✅ Loaded {len(senses)} senses\n")
    
    # Statistics
    stats = {
        'total': len(senses),
        'fixed': 0,
        'unchanged': 0,
        'by_source': defaultdict(int),
    }
    
    # Fix each sense
    for sense_id, sense_data in senses.items():
        lemma = extract_lemma(sense_id)
        pos = sense_data.get('pos', '')
        current_cefr = sense_data.get('cefr', 'B1')
        frequency_rank = sense_data.get('frequency_rank')
        
        # Get best CEFR
        new_cefr = get_best_cefr(
            lemma=lemma,
            pos=pos,
            current_cefr=current_cefr,
            frequency_rank=frequency_rank,
            evp_map=evp_map,
            moe_map=moe_map
        )
        
        # Track source
        if f"{lemma.lower()}:{pos}" in evp_map:
            stats['by_source']['EVP-POS'] += 1
        elif lemma.lower() in COMMON_WORDS_OVERRIDE:
            stats['by_source']['Override'] += 1
        elif lemma.lower() in moe_map:
            stats['by_source']['MOE'] += 1
        elif lemma.lower() in evp_map:
            stats['by_source']['EVP-Word'] += 1
        elif frequency_rank:
            stats['by_source']['Frequency'] += 1
        else:
            stats['by_source']['Default'] += 1
        
        # Update if changed
        if new_cefr != current_cefr:
            sense_data['cefr'] = new_cefr
            stats['fixed'] += 1
        else:
            stats['unchanged'] += 1
    
    # Save
    print(f"\n💾 Saving to {OUTPUT_FILE}...")
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    # Print summary
    print("\n" + "="*60)
    print("✅ Fix Complete!")
    print("="*60)
    print(f"📊 Total senses: {stats['total']:,}")
    print(f"🔧 Fixed: {stats['fixed']:,}")
    print(f"✅ Unchanged: {stats['unchanged']:,}")
    print(f"\n📋 Fixed by source:")
    for source, count in sorted(stats['by_source'].items(), key=lambda x: x[1], reverse=True):
        print(f"   {source}: {count:,}")
    
    # Show examples
    print(f"\n📋 Sample fixes:")
    sample_words = ['doctor', 'teacher', 'friend', 'house', 'car']
    for word in sample_words:
        for sense_id, sense_data in senses.items():
            if extract_lemma(sense_id).lower() == word.lower():
                print(f"   {sense_id}: {sense_data.get('cefr')} (pos: {sense_data.get('pos')})")
                break


if __name__ == "__main__":
    main()

