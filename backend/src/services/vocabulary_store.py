"""
Vocabulary Store - In-Memory Vocabulary Data Service

This service loads vocabulary data from a pre-exported JSON file and provides
fast in-memory lookups. It replaces Neo4j queries for production runtime.

Usage:
    from src.services.vocabulary_store import vocabulary_store
    
    # Get a sense by ID
    sense = vocabulary_store.get_sense("apple.n.01")
    
    # Get random blocks in a frequency band
    blocks = vocabulary_store.get_random_senses_in_band(1000, count=10)
"""

import json
import random
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass


@dataclass
class Sense:
    """Sense data structure."""
    id: str
    word: str
    definition_en: str
    definition_zh: str
    example_en: str
    example_zh: str
    pos: Optional[str]
    frequency_rank: Optional[int]
    enriched: bool = False


@dataclass
class Word:
    """Word data structure."""
    name: str
    frequency_rank: Optional[int]
    moe_level: Optional[int]
    ngsl_rank: Optional[int]
    senses: List[str]


class VocabularyStore:
    """
    In-memory vocabulary store for fast lookups.
    
    Singleton pattern - loads data once at startup.
    """
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if VocabularyStore._initialized:
            return
        
        self._words: Dict[str, Dict[str, Any]] = {}
        self._senses: Dict[str, Dict[str, Any]] = {}
        self._relationships: Dict[str, Dict[str, List[str]]] = {}
        self._band_index: Dict[int, List[str]] = {}
        self._loaded = False
        self._version = None
        
        # Try to load data immediately
        self._load_data()
        VocabularyStore._initialized = True
    
    def _load_data(self) -> bool:
        """Load vocabulary data from JSON file."""
        if self._loaded:
            return True
        
        # Try multiple possible locations
        possible_paths = [
            Path(__file__).parent.parent.parent / 'data' / 'vocabulary.json',  # backend/data/
            Path(__file__).parent.parent.parent.parent / 'data' / 'vocabulary.json',  # project root/data/
        ]
        
        data_file = None
        for path in possible_paths:
            if path.exists():
                data_file = path
                break
        
        if not data_file:
            print(f"WARNING: vocabulary.json not found. Run export_vocabulary_json.py first.")
            print(f"Searched in: {[str(p) for p in possible_paths]}")
            return False
        
        try:
            print(f"Loading vocabulary from {data_file}...")
            with open(data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self._version = data.get('version', '1.0')
            self._words = data.get('words', {})
            self._senses = data.get('senses', {})
            self._relationships = data.get('relationships', {})
            
            # Convert band index keys to integers
            raw_band_index = data.get('bandIndex', {})
            self._band_index = {int(k): v for k, v in raw_band_index.items()}
            
            self._loaded = True
            print(f"  Loaded {len(self._words)} words, {len(self._senses)} senses")
            return True
            
        except Exception as e:
            print(f"ERROR loading vocabulary data: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    @property
    def is_loaded(self) -> bool:
        """Check if vocabulary data is loaded."""
        return self._loaded
    
    def get_sense(self, sense_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a sense by ID.
        
        Args:
            sense_id: Sense ID (e.g., "apple.n.01")
            
        Returns:
            Sense data dictionary or None
        """
        return self._senses.get(sense_id)
    
    def get_word(self, word_name: str) -> Optional[Dict[str, Any]]:
        """
        Get a word by name.
        
        Args:
            word_name: Word name (e.g., "apple")
            
        Returns:
            Word data dictionary or None
        """
        return self._words.get(word_name)
    
    def get_senses_for_word(self, word_name: str) -> List[Dict[str, Any]]:
        """
        Get all senses for a word.
        
        Args:
            word_name: Word name
            
        Returns:
            List of sense data dictionaries
        """
        word = self._words.get(word_name)
        if not word:
            return []
        
        sense_ids = word.get('senses', [])
        return [self._senses[sid] for sid in sense_ids if sid in self._senses]
    
    def get_random_senses_in_band(
        self, 
        band: int, 
        count: int = 10,
        exclude_senses: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Get random senses from a frequency band.
        
        Args:
            band: Frequency band (1000, 2000, 3000, etc.)
            count: Number of senses to return
            exclude_senses: Sense IDs to exclude
            
        Returns:
            List of sense data dictionaries
        """
        exclude_set = set(exclude_senses or [])
        
        # Get senses in this band
        band_senses = self._band_index.get(band, [])
        
        # Filter out excluded senses
        available = [sid for sid in band_senses if sid not in exclude_set]
        
        # Random sample
        if len(available) <= count:
            selected = available
        else:
            selected = random.sample(available, count)
        
        return [self._senses[sid] for sid in selected if sid in self._senses]
    
    def get_starter_pack(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get a starter pack of blocks across frequency bands.
        
        Mirrors the logic from MineService.get_starter_pack but using in-memory data.
        
        Args:
            limit: Total number of blocks to return
            
        Returns:
            List of block dictionaries
        """
        # Sample from each frequency band
        bands_config = [
            (1000, 10),   # 10 blocks from top 1000
            (2000, 10),   # 10 from 1001-2000
            (3000, 15),   # 15 from 2001-3000
            (4000, 15),   # 15 from 3001-4000
        ]
        
        all_blocks = []
        
        for band, count in bands_config:
            senses = self.get_random_senses_in_band(band, count)
            for sense in senses:
                all_blocks.append(self._sense_to_block(sense))
        
        # Shuffle and limit
        random.shuffle(all_blocks)
        return all_blocks[:limit]
    
    def get_related_senses(self, sense_id: str) -> List[str]:
        """
        Get related sense IDs for a sense.
        
        Args:
            sense_id: Source sense ID
            
        Returns:
            List of related sense IDs
        """
        rels = self._relationships.get(sense_id, {})
        return rels.get('related', [])
    
    def get_opposite_senses(self, sense_id: str) -> List[str]:
        """
        Get opposite sense IDs for a sense.
        
        Args:
            sense_id: Source sense ID
            
        Returns:
            List of opposite sense IDs
        """
        rels = self._relationships.get(sense_id, {})
        return rels.get('opposite', [])
    
    def get_connections(self, sense_id: str) -> List[Dict[str, Any]]:
        """
        Get all connections for a sense with full details.
        
        Args:
            sense_id: Source sense ID
            
        Returns:
            List of connection dictionaries with sense_id, word, type
        """
        connections = []
        
        # Related senses
        for related_id in self.get_related_senses(sense_id):
            sense = self.get_sense(related_id)
            if sense:
                connections.append({
                    'sense_id': related_id,
                    'word': sense.get('word', ''),
                    'type': 'RELATED_TO'
                })
        
        # Opposite senses
        for opposite_id in self.get_opposite_senses(sense_id):
            sense = self.get_sense(opposite_id)
            if sense:
                connections.append({
                    'sense_id': opposite_id,
                    'word': sense.get('word', ''),
                    'type': 'OPPOSITE_TO'
                })
        
        return connections
    
    def get_block_detail(self, sense_id: str) -> Optional[Dict[str, Any]]:
        """
        Get full block detail with connections.
        
        Args:
            sense_id: Sense ID
            
        Returns:
            Block detail dictionary or None
        """
        sense = self.get_sense(sense_id)
        if not sense:
            return None
        
        connections = self.get_connections(sense_id)
        
        # Calculate definition with explanation
        definition_zh = sense.get('definition_zh', '')
        definition_zh_explanation = sense.get('definition_zh_explanation', '')
        if definition_zh_explanation:
            definition_zh = f"{definition_zh} {definition_zh_explanation}".strip()
        
        example_zh = sense.get('example_zh', '')
        example_zh_explanation = sense.get('example_zh_explanation', '')
        if example_zh_explanation:
            example_zh = f"{example_zh} {example_zh_explanation}".strip()
        
        return {
            'sense_id': sense_id,
            'word': sense.get('word', ''),
            'tier': 1,  # Default tier
            'base_xp': 100,  # Default base XP
            'connection_count': len(connections),
            'total_value': 100 + len(connections) * 10,  # Base + connection bonus
            'rank': sense.get('frequency_rank'),
            'definition_en': sense.get('definition_en', ''),
            'definition_zh': definition_zh,
            'example_en': sense.get('example_en', ''),
            'example_zh': example_zh,
            'connections': connections,
        }
    
    def _sense_to_block(self, sense: Dict[str, Any]) -> Dict[str, Any]:
        """Convert sense data to block format."""
        definition_preview = sense.get('definition_en', '')[:100]
        
        return {
            'sense_id': sense.get('id', ''),
            'word': sense.get('word', ''),
            'definition_preview': definition_preview,
            'definition_zh': sense.get('definition_zh', ''),
            'rank': sense.get('frequency_rank'),
            'tier': 1,
            'base_xp': 100,
            'connection_count': 0,  # Not computed for list view
            'total_value': 100,
            'status': 'raw',  # Will be enriched with user progress
        }
    
    def get_random_traps(
        self, 
        exclude_word: str, 
        count: int = 3,
        rank: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get random senses to use as trap/distractor options.
        
        For survey/MCQ generation.
        
        Args:
            exclude_word: Word to exclude (the target word)
            count: Number of traps needed
            rank: Optional frequency rank to match (within ±500)
            
        Returns:
            List of sense data dictionaries
        """
        candidates = []
        
        if rank:
            # Get senses from nearby bands
            search_radius = 500
            for band in self._band_index:
                band_min = band - 999  # e.g., band 2000 covers 1001-2000
                band_max = band
                if rank - search_radius <= band_max and rank + search_radius >= band_min:
                    for sid in self._band_index[band]:
                        sense = self._senses.get(sid)
                        if sense and sense.get('word') != exclude_word:
                            candidates.append(sense)
        else:
            # Get random senses from any band
            for sid, sense in self._senses.items():
                if sense.get('word') != exclude_word:
                    candidates.append(sense)
        
        # Random sample
        if len(candidates) <= count:
            return candidates
        
        return random.sample(candidates, count)
    
    def search_senses_by_rank(
        self, 
        min_rank: int, 
        max_rank: int,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search senses by frequency rank range.
        
        Args:
            min_rank: Minimum frequency rank
            max_rank: Maximum frequency rank
            limit: Maximum results
            
        Returns:
            List of sense data dictionaries
        """
        results = []
        
        for sense in self._senses.values():
            rank = sense.get('frequency_rank')
            if rank and min_rank <= rank <= max_rank:
                results.append(sense)
                if len(results) >= limit:
                    break
        
        return results


# Singleton instance
vocabulary_store = VocabularyStore()

