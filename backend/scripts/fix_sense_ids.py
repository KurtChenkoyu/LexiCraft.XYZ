#!/usr/bin/env python3
"""
Fix Empty and Invalid sense_ids in Vocabulary Connections

This script post-processes vocabulary.json to:
1. Populate empty sense_ids arrays by matching display_words to vocabulary
2. Replace invalid sense_ids with valid matches
3. Ensure POS matching (verbs → verbs, nouns → nouns)

Usage:
    python fix_sense_ids.py
    
Output:
    backend/data/vocabulary_fixed.json
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from collections import defaultdict

# Import vocabulary loader directly (avoid __init__.py imports)
sys.path.insert(0, str(Path(__file__).parent / "modules"))
from vocabulary_loader import VocabularyLoader

# Configuration
INPUT_FILE = Path(__file__).parent.parent / "data" / "vocabulary.json"
OUTPUT_FILE = Path(__file__).parent.parent / "data" / "vocabulary_fixed.json"

# CEFR ordering for picking best match
CEFR_ORDER = {'A1': 1, 'A2': 2, 'B1': 3, 'B2': 4, 'C1': 5, 'C2': 6}


class SenseIdFixer:
    """Fixes empty and invalid sense_ids in vocabulary connections."""
    
    def __init__(self, vocab_loader: VocabularyLoader):
        self.vocab = vocab_loader
        self.stats = {
            'total_connections': 0,
            'empty_fixed': 0,
            'invalid_fixed': 0,  # Includes misaligned
            'unfixable': 0,
            'already_valid': 0,
        }
        self.unfixable_words = defaultdict(int)
    
    def is_aligned(self, display_word: str, sense_id: str) -> bool:
        """Check if sense_id is correctly aligned with display_word.
        
        A sense_id is aligned if:
        - The sense exists
        - The lemma from sense_id matches display_word (allowing inflections)
        - OR the sense's word field matches display_word
        """
        if not sense_id or not self.vocab.sense_exists(sense_id):
            return False
        
        sense = self.vocab.get_sense(sense_id)
        if not sense:
            return False
        
        # Extract lemma from sense_id (e.g., "press.v.01" -> "press")
        lemma = self.vocab.extract_word_from_sense_id(sense_id).lower()
        word = sense.get('word', '').lower()
        display_lower = display_word.lower()
        
        # Check if display_word matches lemma or word
        if display_lower == lemma or display_lower == word:
            return True
        
        # Allow for common inflections (e.g., "pressed" -> "press")
        # Remove common suffixes and check base match
        base_word = display_lower.rstrip('s').rstrip('ed').rstrip('ing').rstrip('er').rstrip('est')
        if base_word == lemma or base_word == word:
            return True
        
        # Check if one contains the other (for compound words)
        if lemma in display_lower or display_lower in lemma:
            return True
        
        return False
    
    def find_best_sense_id(
        self, 
        display_word: str, 
        source_pos: str, 
        source_cefr: str
    ) -> Optional[str]:
        """Find the best matching sense_id for a display word.
        
        Priority:
        1. Match by lemma AND POS
        2. Match by lemma only (if no POS match)
        3. Pick closest CEFR level
        """
        # Try lemma + POS match first
        candidates = self.vocab.get_senses_by_lemma_and_pos(display_word, source_pos)
        
        # If no POS match, try lemma only
        if not candidates:
            candidates = self.vocab.get_senses_by_lemma(display_word)
        
        # Also try exact word match
        if not candidates:
            candidates = self.vocab.get_senses_for_word(display_word)
        
        if not candidates:
            return None
        
        if len(candidates) == 1:
            return candidates[0]
        
        # Multiple candidates: pick best by CEFR proximity and POS match
        source_level = CEFR_ORDER.get(source_cefr, 3)  # Default to B1
        
        def score_candidate(sense_id: str) -> Tuple[int, int]:
            """Score: (POS match, CEFR distance). Lower is better."""
            sense = self.vocab.get_sense(sense_id)
            if not sense:
                return (1, 10)  # Worst score
            
            sense_pos = sense.get('pos', '')
            pos_match = 0 if sense_pos == source_pos else 1
            
            sense_cefr = sense.get('cefr', 'B1')
            cefr_distance = abs(CEFR_ORDER.get(sense_cefr, 3) - source_level)
            
            return (pos_match, cefr_distance)
        
        candidates.sort(key=score_candidate)
        return candidates[0]
    
    def fix_connection_type(
        self, 
        connection: Dict, 
        source_pos: str, 
        source_cefr: str
    ) -> Tuple[Dict, int, int, int]:
        """Fix sense_ids for a single connection type (synonyms/antonyms/similar_words).
        
        Returns:
            (fixed_connection, empty_fixed, invalid_fixed, unfixable)
        """
        display_words = connection.get('display_words') or []
        sense_ids = connection.get('sense_ids') or []
        
        if not display_words:
            return connection, 0, 0, 0
        
        empty_fixed = 0
        invalid_fixed = 0
        unfixable = 0
        
        new_sense_ids = []
        new_display_words = []
        
        for i, word in enumerate(display_words):
            # Get existing sense_id if any
            existing_id = sense_ids[i] if i < len(sense_ids) else None
            
            # Check if existing ID is valid AND aligned
            if existing_id and self.vocab.sense_exists(existing_id) and self.is_aligned(word, existing_id):
                new_sense_ids.append(existing_id)
                new_display_words.append(word)
                continue
            
            # Need to find a valid sense_id (either missing, invalid, or misaligned)
            found_id = self.find_best_sense_id(word, source_pos, source_cefr)
            
            if found_id:
                new_sense_ids.append(found_id)
                new_display_words.append(word)
                
                if existing_id is None or existing_id == '':
                    empty_fixed += 1
                else:
                    invalid_fixed += 1  # Includes misaligned
            else:
                # Can't find valid sense - remove this word
                unfixable += 1
                self.unfixable_words[word] += 1
        
        return {
            'display_words': new_display_words,
            'sense_ids': new_sense_ids
        }, empty_fixed, invalid_fixed, unfixable
    
    def fix_sense(self, sense_id: str, sense_data: Dict) -> Dict:
        """Fix all connections for a single sense."""
        connections = sense_data.get('connections', {})
        if not connections:
            return sense_data
        
        source_pos = sense_data.get('pos', '')
        source_cefr = sense_data.get('cefr', 'B1')
        
        # Connection types to fix
        conn_types = ['synonyms', 'antonyms', 'similar_words']
        
        for conn_type in conn_types:
            if conn_type not in connections:
                continue
            
            conn = connections[conn_type]
            if not isinstance(conn, dict):
                continue
            
            self.stats['total_connections'] += 1
            
            # Check if already valid AND aligned
            display_words = conn.get('display_words') or []
            sense_ids = conn.get('sense_ids') or []
            
            # Only skip if all sense_ids exist AND are correctly aligned
            if sense_ids and len(sense_ids) == len(display_words):
                all_valid_and_aligned = all(
                    sid and self.vocab.sense_exists(sid) and self.is_aligned(word, sid)
                    for word, sid in zip(display_words, sense_ids)
                )
                if all_valid_and_aligned:
                    self.stats['already_valid'] += 1
                    continue
            
            # Fix the connection
            fixed_conn, empty, invalid, unfixable = self.fix_connection_type(
                conn, source_pos, source_cefr
            )
            
            connections[conn_type] = fixed_conn
            self.stats['empty_fixed'] += empty
            self.stats['invalid_fixed'] += invalid
            self.stats['unfixable'] += unfixable
        
        sense_data['connections'] = connections
        return sense_data
    
    def run(self):
        """Run the fix process on all senses."""
        print("\n" + "="*60)
        print("🔧 Fixing Empty and Invalid sense_ids")
        print("="*60 + "\n")
        
        total_senses = len(self.vocab.sense_index)
        print(f"📊 Total senses: {total_senses}")
        
        # Process each sense
        for i, (sense_id, sense_data) in enumerate(self.vocab.sense_index.items()):
            self.vocab.sense_index[sense_id] = self.fix_sense(sense_id, sense_data)
            
            # Progress
            if (i + 1) % 1000 == 0:
                print(f"⏳ Processed {i + 1}/{total_senses} senses...")
        
        # Save output
        self.vocab.save(str(OUTPUT_FILE))
        
        # Print summary
        print("\n" + "="*60)
        print("✅ Fix Complete!")
        print("="*60)
        print(f"📊 Total connections processed: {self.stats['total_connections']}")
        print(f"✅ Already valid: {self.stats['already_valid']}")
        print(f"🔧 Empty arrays fixed: {self.stats['empty_fixed']}")
        print(f"🔧 Invalid IDs replaced: {self.stats['invalid_fixed']}")
        print(f"❌ Unfixable (removed): {self.stats['unfixable']}")
        print(f"\n📁 Output: {OUTPUT_FILE}")
        
        # Show top unfixable words
        if self.unfixable_words:
            print(f"\n⚠️  Top 20 unfixable words (not in vocabulary):")
            sorted_words = sorted(
                self.unfixable_words.items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:20]
            for word, count in sorted_words:
                print(f"   - {word}: {count} occurrences")


def main():
    print(f"📖 Loading vocabulary from {INPUT_FILE}")
    vocab = VocabularyLoader(str(INPUT_FILE))
    print(f"✅ Loaded {len(vocab.sense_index)} senses")
    print(f"📚 Lemma index: {len(vocab.lemma_to_senses)} lemmas")
    
    fixer = SenseIdFixer(vocab)
    fixer.run()


if __name__ == "__main__":
    main()

