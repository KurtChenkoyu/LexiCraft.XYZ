"""
Vocabulary Loader - Utility for loading and managing vocabulary.json
"""

import json
from typing import Dict, List, Optional, Tuple
from collections import defaultdict


class VocabularyLoader:
    """Loads and provides access to vocabulary data."""
    
    def __init__(self, vocab_file: str):
        """Initialize with path to vocabulary.json"""
        self.vocab_file = vocab_file
        self.data = self._load()
        self.sense_index = self.data.get('senses', {})
        self.word_to_senses = self._build_word_index()
        self.lemma_to_senses = self._build_lemma_index()
    
    def _load(self) -> Dict:
        """Load vocabulary JSON file."""
        with open(self.vocab_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _build_word_index(self) -> Dict[str, List[str]]:
        """Build index of word -> list of sense IDs."""
        index = defaultdict(list)
        for sense_id, sense_data in self.sense_index.items():
            word = sense_data.get('word', '')
            if word:
                index[word.lower()].append(sense_id)
        return dict(index)
    
    def _build_lemma_index(self) -> Dict[str, List[str]]:
        """Build index of lemma (from sense_id) -> list of sense IDs.
        
        Example: 'press.v.01' has lemma 'press'
        This allows finding senses even when the 'word' field is an inflected form.
        """
        index = defaultdict(list)
        for sense_id in self.sense_index.keys():
            lemma = self.extract_word_from_sense_id(sense_id)
            if lemma:
                index[lemma.lower()].append(sense_id)
        return dict(index)
    
    def get_sense(self, sense_id: str) -> Optional[Dict]:
        """Get sense data by ID."""
        return self.sense_index.get(sense_id)
    
    def sense_exists(self, sense_id: str) -> bool:
        """Check if a sense exists."""
        return sense_id in self.sense_index
    
    def get_senses_for_word(self, word: str) -> List[str]:
        """Get all sense IDs for a given word (by word field)."""
        return self.word_to_senses.get(word.lower(), [])
    
    def get_senses_by_lemma(self, lemma: str) -> List[str]:
        """Get all sense IDs by lemma (extracted from sense_id).
        
        This is more reliable than get_senses_for_word because:
        - sense_id 'press.v.01' has lemma 'press' but word might be 'pressed'
        - Searching by lemma finds all senses regardless of inflection
        """
        return self.lemma_to_senses.get(lemma.lower(), [])
    
    def get_senses_by_lemma_and_pos(self, lemma: str, pos: str) -> List[str]:
        """Get sense IDs matching both lemma and POS.
        
        Args:
            lemma: The base word (e.g., 'press')
            pos: Part of speech ('n', 'v', 'a', 'r', 's', 'adj', 'adv')
        
        Returns:
            List of matching sense IDs (e.g., ['press.v.01', 'press.v.02'])
        """
        # Normalize POS
        pos_map = {'adj': 'a', 'adv': 'r', 'noun': 'n', 'verb': 'v'}
        normalized_pos = pos_map.get(pos.lower(), pos.lower())
        
        candidates = self.get_senses_by_lemma(lemma)
        matching = []
        
        for sense_id in candidates:
            sense_data = self.sense_index.get(sense_id, {})
            sense_pos = sense_data.get('pos', '')
            
            # Normalize sense POS
            sense_pos_norm = pos_map.get(sense_pos.lower(), sense_pos.lower())
            
            if sense_pos_norm == normalized_pos:
                matching.append(sense_id)
        
        return matching
    
    def get_all_sense_ids(self) -> List[str]:
        """Get all sense IDs."""
        return list(self.sense_index.keys())
    
    def extract_word_from_sense_id(self, sense_id: str) -> str:
        """Extract word/lemma from sense ID (e.g., 'formal.a.01' -> 'formal')."""
        return sense_id.split('.')[0] if '.' in sense_id else sense_id
    
    def extract_pos_from_sense_id(self, sense_id: str) -> str:
        """Extract POS from sense ID (e.g., 'formal.a.01' -> 'a')."""
        parts = sense_id.split('.')
        return parts[1] if len(parts) >= 2 else ''
    
    def save(self, output_file: str):
        """Save modified vocabulary data."""
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)
    
    def update_sense(self, sense_id: str, updated_data: Dict):
        """Update a sense with new data."""
        if sense_id in self.sense_index:
            self.sense_index[sense_id].update(updated_data)
    
    def get_stats(self) -> Dict:
        """Get vocabulary statistics."""
        return self.data.get('stats', {})
