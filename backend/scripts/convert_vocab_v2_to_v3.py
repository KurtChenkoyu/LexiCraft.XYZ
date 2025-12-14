#!/usr/bin/env python3
"""
Convert Vocabulary JSON from V2 to V3 Format

This script converts an existing V2 vocabulary.json to the new V3 format:
- V2: Normalized (words, senses, relationships separate)
- V3: Denormalized (all data embedded in sense)

Changes:
1. Removes top-level 'words' dict (data embedded in each sense)
2. Adds 'other_senses' to each sense for polysemy checking
3. Adds 'connections.confused' from Levenshtein mining
4. Flattens hop data into 'network' object
5. Adds 'indices' (byWord, byBand, byPos) for fast lookups

Usage:
    cd backend
    python scripts/convert_vocab_v2_to_v3.py
    python scripts/convert_vocab_v2_to_v3.py --input data/vocabulary.json --output data/vocabulary_v3.json
"""

import json
import sys
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Set, Any
from difflib import SequenceMatcher

# Optional tqdm - use simple progress if not available
try:
    from tqdm import tqdm
except ImportError:
    def tqdm(iterable, desc=None, **kwargs):
        """Fallback progress indicator."""
        items = list(iterable)
        total = len(items)
        for i, item in enumerate(items):
            if desc and (i % 500 == 0 or i == total - 1):
                print(f"  {desc}: {i+1}/{total}")
            yield item


# Common ESL confusion pairs (curated list for Taiwan learners)
COMMON_CONFUSIONS = {
    'accept': [('except', 'spelling'), ('expect', 'spelling')],
    'affect': [('effect', 'spelling')],
    'effect': [('affect', 'spelling')],
    'advice': [('advise', 'spelling')],
    'advise': [('advice', 'spelling')],
    'lose': [('loose', 'spelling')],
    'loose': [('lose', 'spelling')],
    'quite': [('quiet', 'spelling')],
    'quiet': [('quite', 'spelling')],
    'then': [('than', 'spelling')],
    'than': [('then', 'spelling')],
    'their': [('there', 'sound'), ("they're", 'sound')],
    'there': [('their', 'sound'), ("they're", 'sound')],
    'to': [('too', 'sound'), ('two', 'sound')],
    'too': [('to', 'sound'), ('two', 'sound')],
    'two': [('to', 'sound'), ('too', 'sound')],
    'your': [("you're", 'sound')],
    'its': [("it's", 'spelling')],
    'principal': [('principle', 'spelling')],
    'principle': [('principal', 'spelling')],
    'stationary': [('stationery', 'spelling')],
    'stationery': [('stationary', 'spelling')],
    'complement': [('compliment', 'spelling')],
    'compliment': [('complement', 'spelling')],
    'desert': [('dessert', 'spelling')],
    'dessert': [('desert', 'spelling')],
    'lead': [('led', 'spelling')],
    'breath': [('breathe', 'spelling')],
    'breathe': [('breath', 'spelling')],
    'cloth': [('clothe', 'spelling')],
    'clothe': [('cloth', 'spelling')],
    'through': [('thorough', 'spelling'), ('threw', 'sound')],
    'threw': [('through', 'sound')],
    'weather': [('whether', 'sound')],
    'whether': [('weather', 'sound')],
    'where': [('were', 'sound'), ('wear', 'sound')],
    'were': [('where', 'sound'), ('wear', 'sound')],
    'wear': [('where', 'sound'), ('were', 'sound')],
    'hear': [('here', 'sound')],
    'here': [('hear', 'sound')],
    'knew': [('new', 'sound')],
    'new': [('knew', 'sound')],
    'know': [('no', 'sound')],
    'no': [('know', 'sound')],
    'right': [('write', 'sound')],
    'write': [('right', 'sound')],
    'sea': [('see', 'sound')],
    'see': [('sea', 'sound')],
    'week': [('weak', 'sound')],
    'weak': [('week', 'sound')],
    'borrow': [('lend', 'semantic')],
    'lend': [('borrow', 'semantic')],
    'bring': [('take', 'semantic')],
    'take': [('bring', 'semantic')],
    'learn': [('teach', 'semantic')],
    'teach': [('learn', 'semantic')],
    'say': [('tell', 'semantic')],
    'tell': [('say', 'semantic')],
    'listen': [('hear', 'semantic')],
    'look': [('see', 'semantic'), ('watch', 'semantic')],
    'watch': [('look', 'semantic'), ('see', 'semantic')],
    'make': [('do', 'semantic')],
    'do': [('make', 'semantic')],
}


def levenshtein_distance(s1: str, s2: str) -> int:
    """Calculate Levenshtein edit distance between two strings."""
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    
    if len(s2) == 0:
        return len(s1)
    
    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    
    return previous_row[-1]


def mine_confused_words(word: str, all_words: Set[str], word_to_senses: Dict[str, List[str]]) -> List[Dict]:
    """
    Find words that could be confused with the target word.
    Returns list of {sense_id, reason} dicts.
    """
    confused = []
    word_lower = word.lower()
    seen_words = {word_lower}
    
    # 1. Check curated confusion pairs first (highest quality)
    if word_lower in COMMON_CONFUSIONS:
        for confused_word, reason in COMMON_CONFUSIONS[word_lower]:
            if confused_word in word_to_senses and confused_word not in seen_words:
                senses = word_to_senses[confused_word]
                if senses:
                    confused.append({
                        'sense_id': senses[0],
                        'reason': reason
                    })
                    seen_words.add(confused_word)
    
    # 2. Find spelling-similar words via Levenshtein (limit to avoid explosion)
    word_len = len(word)
    candidates_checked = 0
    max_candidates = 500
    
    for candidate in all_words:
        if candidates_checked >= max_candidates:
            break
        
        candidate_lower = candidate.lower()
        
        if candidate_lower in seen_words:
            continue
        
        if abs(len(candidate) - word_len) > 2:
            continue
        
        candidates_checked += 1
        
        distance = levenshtein_distance(word_lower, candidate_lower)
        
        if 0 < distance <= 2:
            senses = word_to_senses.get(candidate, [])
            if senses:
                confused.append({
                    'sense_id': senses[0],
                    'reason': 'spelling'
                })
                seen_words.add(candidate_lower)
            
            if len(confused) >= 10:
                break
    
    return confused


def load_master_vocab_frequency(backend_dir: Path) -> Dict[str, Dict]:
    """Load frequency data from master_vocab.csv."""
    master_vocab_path = backend_dir.parent / 'data' / 'processed' / 'master_vocab.csv'
    
    freq_data = {}
    if master_vocab_path.exists():
        print(f"Loading frequency data from {master_vocab_path}...")
        with open(master_vocab_path, 'r') as f:
            # Skip header
            f.readline()
            for line in f:
                parts = line.strip().split(',')
                if len(parts) >= 4:
                    word = parts[0]
                    freq_data[word] = {
                        'frequency_rank': int(parts[1]) if parts[1] else None,
                        'moe_level': int(parts[2]) if parts[2] else None,
                        'ngsl_rank': int(parts[3]) if parts[3] else None
                    }
        print(f"  Loaded frequency data for {len(freq_data)} words")
    else:
        print(f"  Warning: master_vocab.csv not found at {master_vocab_path}")
    
    return freq_data


def convert_v2_to_v3(input_path: Path, output_path: Path):
    """Convert V2 vocabulary.json to V3 format."""
    print(f"Loading V2 vocabulary from {input_path}...")
    
    with open(input_path, 'r', encoding='utf-8') as f:
        v2_data = json.load(f)
    
    version = v2_data.get('version', '1.0')
    if version.startswith('3'):
        print(f"Already V3 format (version {version}), no conversion needed.")
        return
    
    print(f"Converting from V{version} to V3...")
    
    words_dict = v2_data.get('words', {})
    senses_dict = v2_data.get('senses', {})
    relationships_dict = v2_data.get('relationships', {})
    band_index_v2 = v2_data.get('bandIndex', {})
    
    # Load frequency data from master_vocab.csv
    backend_dir = Path(__file__).parent.parent
    master_freq = load_master_vocab_frequency(backend_dir)
    
    print(f"  Words: {len(words_dict)}")
    print(f"  Senses: {len(senses_dict)}")
    print(f"  Relationships: {len(relationships_dict)}")
    
    # Build word -> sense_ids mapping
    word_to_senses = {}
    for word_name, word_data in words_dict.items():
        word_to_senses[word_name] = word_data.get('senses', [])
    
    # Also build from senses if words dict is incomplete
    for sense_id, sense_data in senses_dict.items():
        word = sense_data.get('word')
        if word:
            if word not in word_to_senses:
                word_to_senses[word] = []
            if sense_id not in word_to_senses[word]:
                word_to_senses[word].append(sense_id)
    
    all_words = set(word_to_senses.keys())
    
    # Mine CONFUSED_WITH relationships
    print("Mining CONFUSED_WITH relationships...")
    word_confused_cache = {}
    for word in tqdm(all_words, desc="  Mining confused"):
        confused = mine_confused_words(word, all_words, word_to_senses)
        word_confused_cache[word] = confused
    
    # Convert senses to V3 format
    print("Converting senses to V3 format...")
    v3_senses = {}
    
    for sense_id, sense_data in tqdm(senses_dict.items(), desc="  Converting"):
        word = sense_data.get('word', '')
        
        # Get word metadata (prefer master_vocab.csv, then words_dict)
        word_meta = master_freq.get(word) or words_dict.get(word, {})
        
        # Get other senses of the same word
        all_senses_of_word = word_to_senses.get(word, [])
        other_senses = [s for s in all_senses_of_word if s != sense_id]
        
        # Get relationships
        rels = relationships_dict.get(sense_id, {})
        related = rels.get('related', [])
        opposite = rels.get('opposite', [])
        
        # Get confused words
        confused = word_confused_cache.get(word, [])
        
        # Get existing connections or build new ones
        existing_connections = sense_data.get('connections', {})
        
        # Flatten hop data
        hop_1 = sense_data.get('hop_1', {})
        hop_2 = sense_data.get('hop_2', {})
        network_value = sense_data.get('network_value', {})
        value = sense_data.get('value', {})
        
        network = {
            'hop_1_count': hop_1.get('count', len(related) + len(opposite)),
            'hop_2_count': hop_2.get('count', 0),
            'total_reachable': network_value.get('total_reachable', 0),
            'total_xp': value.get('total_xp', 100)
        }
        
        # Build V3 sense
        v3_sense = {
            'id': sense_id,
            'word': word,
            'pos': sense_data.get('pos'),
            'frequency_rank': sense_data.get('frequency_rank') or word_meta.get('frequency_rank'),
            'moe_level': word_meta.get('moe_level'),
            'cefr': sense_data.get('cefr'),
            'tier': sense_data.get('tier', 1),
            'definition_en': sense_data.get('definition_en', sense_data.get('definition', '')),
            'definition_zh': sense_data.get('definition_zh', ''),
            'definition_zh_explanation': sense_data.get('definition_zh_explanation', ''),
            'translation_source': sense_data.get('translation_source'),
            'example_en': sense_data.get('example_en', ''),
            'example_zh_translation': sense_data.get('example_zh_translation', sense_data.get('example_zh', '')),
            'example_zh_explanation': sense_data.get('example_zh_explanation', ''),
            'example_context': sense_data.get('example_context'),
            'validated': sense_data.get('validated', False),
            'connections': {
                'related': existing_connections.get('related', related),
                'opposite': existing_connections.get('opposite', opposite),
                'confused': confused,
                'phrases': existing_connections.get('phrases', []),
                'morphological': existing_connections.get('morphological', [])
            },
            'other_senses': other_senses,
            'network': network
        }
        
        v3_senses[sense_id] = v3_sense
    
    # Build indices
    print("Building indices...")
    by_word = {}
    by_band = {str(band): [] for band in [1000, 2000, 3000, 4000, 5000, 6000, 7000, 8000, 9999]}
    by_pos = {}
    
    for sense_id, sense_data in v3_senses.items():
        word = sense_data.get('word')
        freq = sense_data.get('frequency_rank', 9999) or 9999
        pos = sense_data.get('pos', 'n')
        
        # byWord
        if word:
            if word not in by_word:
                by_word[word] = []
            by_word[word].append(sense_id)
        
        # byBand
        for band in [1000, 2000, 3000, 4000, 5000, 6000, 7000, 8000]:
            if freq <= band:
                by_band[str(band)].append(sense_id)
                break
        else:
            by_band['9999'].append(sense_id)
        
        # byPos
        if pos:
            if pos not in by_pos:
                by_pos[pos] = []
            by_pos[pos].append(sense_id)
    
    # Count stats
    confused_count = sum(
        1 for s in v3_senses.values()
        if s.get('connections', {}).get('confused')
    )
    validated_count = sum(
        1 for s in v3_senses.values()
        if s.get('validated')
    )
    
    # Build V3 output
    v3_data = {
        'version': '3.0',
        'exportedAt': datetime.now().isoformat(),
        'stats': {
            'senses': len(v3_senses),
            'words': len(by_word),
            'validated': validated_count,
            'withConfused': confused_count
        },
        'senses': v3_senses,
        'indices': {
            'byWord': by_word,
            'byBand': by_band,
            'byPos': by_pos
        }
    }
    
    # Write output
    print(f"\nWriting V3 vocabulary to {output_path}...")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(v3_data, f, ensure_ascii=False, indent=2)
    
    file_size = output_path.stat().st_size / 1024 / 1024
    
    print("\n" + "=" * 60)
    print("Conversion Complete!")
    print("=" * 60)
    print(f"Senses: {len(v3_senses)}")
    print(f"Words: {len(by_word)}")
    print(f"With CONFUSED_WITH: {confused_count}")
    print(f"Validated: {validated_count}")
    print(f"File size: {file_size:.2f} MB")


def main():
    parser = argparse.ArgumentParser(description='Convert vocabulary.json from V2 to V3 format')
    parser.add_argument('--input', type=str, default='data/vocabulary.json',
                        help='Input V2 vocabulary.json path')
    parser.add_argument('--output', type=str, default=None,
                        help='Output V3 vocabulary.json path (defaults to overwriting input)')
    parser.add_argument('--frontend', action='store_true',
                        help='Also update landing-page/data/vocabulary.json')
    args = parser.parse_args()
    
    backend_dir = Path(__file__).parent.parent
    
    input_path = backend_dir / args.input
    output_path = Path(args.output) if args.output else input_path
    
    if not input_path.exists():
        print(f"ERROR: Input file not found: {input_path}")
        return 1
    
    convert_v2_to_v3(input_path, output_path)
    
    # Optionally copy to frontend
    if args.frontend:
        frontend_path = backend_dir.parent / 'landing-page' / 'data' / 'vocabulary.json'
        print(f"\nCopying to frontend: {frontend_path}...")
        import shutil
        shutil.copy(output_path, frontend_path)
        print("Done!")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())

