#!/usr/bin/env python3
"""
Comprehensive Sense Extraction for MOE 7000 Words

Extracts ALL WordNet senses for MOE 7000 curriculum words, calculates tier/value,
and merges with existing enriched vocabulary data.

Key Strategy:
- Extract ALL senses (free - just WordNet data)
- Calculate tier and value for all senses (existing + new)
- Merge with existing enrichment (preserve all Gemini-generated content)
- Mark new senses as enriched: false (selective enrichment later)

Usage:
    python extract_comprehensive_senses.py
"""

import json
import csv
import nltk
from pathlib import Path
from typing import Dict, List, Optional, Set
from collections import defaultdict

# Ensure WordNet is available
try:
    nltk.data.find('corpora/wordnet')
except LookupError:
    print("Downloading WordNet...")
    nltk.download('wordnet')
    nltk.download('omw-1.4')

from nltk.corpus import wordnet as wn

# File paths
MOE_FILE = Path(__file__).parent.parent.parent / "data" / "source" / "moe_7000.csv"
VOCAB_FILE = Path(__file__).parent.parent / "data" / "vocabulary.json"
OUTPUT_FILE = Path(__file__).parent.parent / "data" / "vocabulary_comprehensive.json"

# Tier-based base XP (from recalculate_block_values.py - Frequency-Aligned Design)
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
    # Also handle new connection format
    'synonyms': 10,
    'antonyms': 10,
    'similar_words': 10,
}


def load_moe_words() -> Dict[str, int]:
    """Load MOE 7000 word list with levels."""
    if not MOE_FILE.exists():
        print(f"⚠️  MOE file not found: {MOE_FILE}")
        return {}
    
    moe_words = {}
    with open(MOE_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            word = row.get('word', '').strip().lower()
            level = row.get('moe_level', '').strip()
            if word and level:
                try:
                    moe_words[word] = int(level)
                except ValueError:
                    pass
    
    print(f"✅ Loaded {len(moe_words)} MOE words")
    return moe_words


def load_existing_vocab() -> Dict:
    """Load existing vocabulary.json."""
    if not VOCAB_FILE.exists():
        print(f"⚠️  Vocabulary file not found: {VOCAB_FILE}")
        return {'senses': {}, 'version': '3.0', 'stats': {}}
    
    with open(VOCAB_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"✅ Loaded {len(data.get('senses', {}))} existing senses")
    return data


def extract_lemma(sense_id: str) -> str:
    """Extract lemma from sense_id (e.g., 'press.v.01' -> 'press')."""
    return sense_id.split('.')[0] if '.' in sense_id else sense_id


def calculate_tier_for_new_sense(
    synset,
    lemma: str,
    sense_num: int,
    all_senses_for_lemma: List[str],
    frequency_rank: Optional[int],
    moe_level: Optional[int]
) -> int:
    """Assign tier (1-7) based on sense characteristics."""
    # Default: Tier 1 (Basic Block)
    tier = 1
    
    # Tier 2 (Multi-Block): If word has multiple senses and this is 2nd-3rd sense
    if len(all_senses_for_lemma) > 1 and sense_num in (2, 3):
        if frequency_rank and frequency_rank < 5000:
            tier = 2
    
    # Tier 3+ would need phrase/idiom detection (future enhancement)
    # For now, most new senses start at Tier 1
    
    return tier


def calculate_value_for_sense(tier: int, connections: Dict) -> Dict[str, int]:
    """Calculate value using existing formula from recalculate_block_values.py"""
    base_xp = TIER_BASE_XP.get(tier, 100)
    
    # Count connections (handle both old and new formats)
    connection_bonus = 0
    connection_counts = {}
    
    for conn_type, bonus in CONNECTION_BONUSES.items():
        if conn_type in connections:
            # New format: {display_words: [], sense_ids: []}
            if isinstance(connections[conn_type], dict):
                count = len(connections[conn_type].get('sense_ids', []))
            # Old format: array
            elif isinstance(connections[conn_type], list):
                count = len(connections[conn_type])
            else:
                count = 0
        else:
            count = 0
        
        connection_counts[conn_type] = count
        connection_bonus += count * bonus
    
    total_xp = base_xp + connection_bonus
    
    return {
        'base_xp': base_xp,
        'connection_bonus': connection_bonus,
        'total_xp': total_xp
    }


def extract_all_senses_for_word(
    word: str,
    moe_level: int,
    existing_vocab: Dict,
    existing_senses_by_lemma: Dict[str, List[str]]
) -> List[Dict]:
    """Extract ALL WordNet senses for a word."""
    synsets = wn.synsets(word)
    
    if not synsets:
        return []
    
    senses = []
    lemma = word.lower()
    all_senses_for_lemma = existing_senses_by_lemma.get(lemma, [])
    
    # Get frequency_rank and cefr from existing vocab if available
    # (Check first sense of this word if it exists)
    frequency_rank = None
    cefr = None
    for sense_id in all_senses_for_lemma:
        if sense_id in existing_vocab.get('senses', {}):
            existing_sense = existing_vocab['senses'][sense_id]
            frequency_rank = existing_sense.get('frequency_rank')
            cefr = existing_sense.get('cefr')
            break
    
    for synset in synsets:
        sense_id = synset.name()
        sense_num = int(sense_id.split('.')[-1])
        pos = synset.pos()
        
        # Check if this sense already exists in vocab
        existing_sense = existing_vocab.get('senses', {}).get(sense_id)
        
        if existing_sense:
            # Keep existing enrichment
            sense_data = existing_sense.copy()
            sense_data['enriched'] = True
            
            # Calculate value if missing
            if 'value' not in sense_data or not sense_data.get('value', {}).get('total_xp'):
                tier = sense_data.get('tier', 1)
                connections = sense_data.get('connections', {})
                sense_data['value'] = calculate_value_for_sense(tier, connections)
        else:
            # New sense - create basic entry
            sense_data = {
                'id': sense_id,
                'word': word,
                'lemma': lemma,
                'pos': pos,
                'moe_level': moe_level,
                'frequency_rank': frequency_rank,
                'cefr': cefr,
                'tier': calculate_tier_for_new_sense(
                    synset, lemma, sense_num, all_senses_for_lemma, frequency_rank, moe_level
                ),
                'definition_en': synset.definition(),  # WordNet basic definition
                'definition_zh': '',  # Will be enriched later
                'enriched': False,  # Not yet enriched
                'connections': {},  # Will be enriched later
                'other_senses': [],  # Will be populated after all senses extracted
                'network': {
                    'hop_1_count': 0,
                    'hop_2_count': 0,
                    'total_reachable': 0,
                    'total_xp': 0  # Will be calculated
                }
            }
            
            # Calculate value (no connections yet, so just base_xp)
            sense_data['value'] = calculate_value_for_sense(
                sense_data['tier'],
                {}
            )
        
        senses.append(sense_data)
    
    return senses


def build_other_senses_index(all_senses: Dict[str, Dict]) -> Dict[str, List[str]]:
    """Build index of lemma -> list of sense_ids for other_senses field."""
    lemma_to_senses = defaultdict(list)
    
    for sense_id, sense_data in all_senses.items():
        lemma = extract_lemma(sense_id)
        lemma_to_senses[lemma].append(sense_id)
    
    return lemma_to_senses


def populate_other_senses(all_senses: Dict[str, Dict]):
    """Populate other_senses field for all senses."""
    lemma_to_senses = build_other_senses_index(all_senses)
    
    for sense_id, sense_data in all_senses.items():
        lemma = extract_lemma(sense_id)
        other_senses = [sid for sid in lemma_to_senses[lemma] if sid != sense_id]
        sense_data['other_senses'] = sorted(other_senses)


def main():
    print("\n" + "="*60)
    print("🔍 Comprehensive Sense Extraction for MOE 7000 Words")
    print("="*60 + "\n")
    
    # Load data
    print("📖 Loading data sources...")
    moe_words = load_moe_words()
    existing_vocab = load_existing_vocab()
    
    if not moe_words:
        print("❌ No MOE words loaded. Exiting.")
        return
    
    # Build index of existing senses by lemma
    existing_senses_by_lemma = defaultdict(list)
    for sense_id in existing_vocab.get('senses', {}).keys():
        lemma = extract_lemma(sense_id)
        existing_senses_by_lemma[lemma].append(sense_id)
    
    # Start with ALL existing senses (preserve everything)
    print(f"\n💾 Preserving all existing senses...")
    all_senses = {}
    existing_senses = existing_vocab.get('senses', {})
    
    for sense_id, sense_data in existing_senses.items():
        # Copy existing sense and mark as enriched
        sense_copy = sense_data.copy()
        sense_copy['enriched'] = True
        
        # Calculate value if missing
        if 'value' not in sense_copy or not sense_copy.get('value', {}).get('total_xp'):
            tier = sense_copy.get('tier', 1)
            connections = sense_copy.get('connections', {})
            sense_copy['value'] = calculate_value_for_sense(tier, connections)
        
        all_senses[sense_id] = sense_copy
    
    print(f"✅ Preserved {len(all_senses)} existing senses")
    
    # Extract all senses for MOE words (will add new ones or update existing)
    print(f"\n⛏️  Extracting ALL WordNet senses for {len(moe_words)} MOE words...")
    stats = {
        'words_processed': 0,
        'senses_extracted': 0,
        'existing_senses_updated': 0,
        'new_senses_created': 0,
        'words_with_no_senses': 0,
    }
    
    for word, moe_level in moe_words.items():
        senses = extract_all_senses_for_word(
            word, moe_level, existing_vocab, existing_senses_by_lemma
        )
        
        if not senses:
            stats['words_with_no_senses'] += 1
            continue
        
        for sense_data in senses:
            sense_id = sense_data['id']
            
            if sense_id in all_senses:
                # Sense already exists - update with MOE data but preserve enrichment
                existing = all_senses[sense_id]
                # Update MOE level and other metadata, but keep enrichment
                existing['moe_level'] = moe_level
                if not existing.get('frequency_rank') and sense_data.get('frequency_rank'):
                    existing['frequency_rank'] = sense_data['frequency_rank']
                if not existing.get('cefr') and sense_data.get('cefr'):
                    existing['cefr'] = sense_data['cefr']
                stats['existing_senses_updated'] += 1
            else:
                # New sense
                all_senses[sense_id] = sense_data
                stats['new_senses_created'] += 1
        
        stats['senses_extracted'] += len(senses)
        stats['words_processed'] += 1
        
        if stats['words_processed'] % 100 == 0:
            print(f"  Processed {stats['words_processed']}/{len(moe_words)} words...")
    
    # Populate other_senses
    print(f"\n🔗 Populating other_senses field...")
    populate_other_senses(all_senses)
    
    # Calculate value for existing senses that don't have it
    print(f"\n💰 Calculating value for all senses...")
    value_calculated = 0
    for sense_id, sense_data in all_senses.items():
        if 'value' not in sense_data or not sense_data.get('value', {}).get('total_xp'):
            tier = sense_data.get('tier', 1)
            connections = sense_data.get('connections', {})
            sense_data['value'] = calculate_value_for_sense(tier, connections)
            value_calculated += 1
    
    # Calculate enrichment status
    enriched_count = sum(1 for s in all_senses.values() if s.get('enriched'))
    unenriched_count = len(all_senses) - enriched_count
    
    # Build output structure
    print(f"\n💾 Building output structure...")
    from datetime import datetime
    output_data = {
        'version': '3.0',
        'exportedAt': datetime.now().isoformat(),
        'stats': {
            'senses': len(all_senses),
            'words': len(moe_words),
            'enriched': enriched_count,
            'unenriched': unenriched_count,
        },
        'senses': all_senses
    }
    
    # Save output
    print(f"\n💾 Saving to {OUTPUT_FILE}...")
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    # Print summary
    print("\n" + "="*60)
    print("✅ Extraction Complete!")
    print("="*60)
    print(f"📊 Words processed: {stats['words_processed']:,}")
    print(f"📊 Total senses: {len(all_senses):,}")
    print(f"📊 Existing senses preserved: {len(existing_senses):,}")
    print(f"📊 Existing senses updated with MOE data: {stats['existing_senses_updated']:,}")
    print(f"📊 New senses created: {stats['new_senses_created']:,}")
    print(f"📊 Value calculated: {value_calculated:,}")
    print(f"📊 Words with no WordNet senses: {stats['words_with_no_senses']:,}")
    
    # Tier distribution
    tier_dist = defaultdict(int)
    for sense_data in all_senses.values():
        tier = sense_data.get('tier', 1)
        tier_dist[tier] += 1
    
    print(f"\n📊 Tier distribution:")
    for tier in sorted(tier_dist.keys()):
        print(f"   Tier {tier}: {tier_dist[tier]:,} senses")
    
    # Enrichment status (already calculated above)
    print(f"\n📊 Enrichment status:")
    print(f"   Enriched: {enriched_count:,} ({enriched_count/len(all_senses)*100:.1f}%)")
    print(f"   Unenriched: {unenriched_count:,} ({unenriched_count/len(all_senses)*100:.1f}%)")
    
    # MOE coverage
    moe_senses = sum(1 for s in all_senses.values() if s.get('moe_level'))
    print(f"\n📊 MOE coverage:")
    print(f"   Senses with MOE level: {moe_senses:,} ({moe_senses/len(all_senses)*100:.1f}%)")
    
    print(f"\n📁 Output file: {OUTPUT_FILE}")
    print(f"\n💡 Next steps:")
    print(f"   1. Review statistics above")
    print(f"   2. Run enrichment script for high-priority senses")
    print(f"   3. Run bidirectional loop closure")


if __name__ == "__main__":
    main()

