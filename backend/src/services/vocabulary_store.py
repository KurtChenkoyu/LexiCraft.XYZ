"""
Vocabulary Store - In-Memory Vocabulary Data Service

This service loads vocabulary data from a pre-exported JSON file and provides
fast in-memory lookups. Supports both V2 and V3 schema formats.

V3 Changes:
- Denormalized structure (all data embedded in sense)
- 'indices' instead of separate 'bandIndex'
- 'other_senses' embedded for polysemy checking
- 'connections.confused' for CONFUSED_WITH relationships

Usage:
    from src.services.vocabulary_store import vocabulary_store
    
    # Get a sense by ID
    sense = vocabulary_store.get_sense("apple.n.01")
    
    # Get random blocks in a frequency band
    blocks = vocabulary_store.get_random_senses_in_band(1000, count=10)
    
    # MCQ-specific methods
    confused = vocabulary_store.get_confused_senses("accept.v.01")
    other_senses = vocabulary_store.get_other_senses_of_word("accept.v.01")
"""

import json
import random
from pathlib import Path
from typing import Dict, List, Optional, Any, Set


class VocabularyStore:
    """
    In-memory vocabulary store for fast lookups.
    
    Singleton pattern - loads data once at startup.
    Supports both V2 (normalized) and V3 (denormalized) formats.
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
        
        # Core data stores
        self._senses: Dict[str, Dict[str, Any]] = {}
        self._loaded = False
        self._version = None
        
        # Indices (V3 format)
        self._by_word: Dict[str, List[str]] = {}
        self._by_band: Dict[int, List[str]] = {}
        self._by_pos: Dict[str, List[str]] = {}
        
        # Legacy V2 compatibility
        self._words: Dict[str, Dict[str, Any]] = {}  # V2 only
        self._relationships: Dict[str, Dict[str, List[str]]] = {}  # V2 only
        
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
            print(f"WARNING: vocabulary.json not found. Run enrich_vocabulary_v2.py first.")
            print(f"Searched in: {[str(p) for p in possible_paths]}")
            return False
        
        try:
            print(f"Loading vocabulary from {data_file}...")
            with open(data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self._version = data.get('version', '2.0')
            self._senses = data.get('senses', {})
            
            # Load format-specific data
            if self._version.startswith('3'):
                # V3 format: indices are pre-built
                self._load_v3_indices(data)
            else:
                # V2 format: legacy compatibility
                self._load_v2_data(data)
            
            self._loaded = True
            print(f"  Loaded vocabulary V{self._version}: {len(self._senses)} senses")
            return True
            
        except Exception as e:
            print(f"ERROR loading vocabulary data: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _extract_lemma(self, sense_id: str) -> str:
        """
        Extract lemma from sense_id.
        
        e.g., 'be.v.01' -> 'be'
             'apple.n.01' -> 'apple'
        """
        parts = sense_id.split('.')
        return parts[0] if parts else sense_id

    def _load_v3_indices(self, data: Dict):
        """
        Load indices from V3 format, rebuilding byWord from sense_ids.
        
        The JSON's byWord index uses word forms (e.g., 'were' -> be.v.01),
        but we need lemma-based lookup (e.g., 'be' -> be.v.01).
        We rebuild the index using lemmas extracted from sense_ids.
        """
        indices = data.get('indices', {})
        
        # Keep original byWordForm for exact form matching if needed
        self._by_word_form = indices.get('byWord', {})
        
        # Rebuild byWord using lemmas from sense_ids
        self._by_word = {}
        for sense_id in self._senses.keys():
            lemma = self._extract_lemma(sense_id)
            if lemma not in self._by_word:
                self._by_word[lemma] = []
            if sense_id not in self._by_word[lemma]:
                self._by_word[lemma].append(sense_id)
        
        # Convert band keys to integers
        raw_by_band = indices.get('byBand', {})
        self._by_band = {int(k): v for k, v in raw_by_band.items()}
        
        self._by_pos = indices.get('byPos', {})
        
        print(f"  Loaded indices: {len(self._by_word)} lemmas (rebuilt), {len(self._by_band)} bands")
    
    def _load_v2_data(self, data: Dict):
        """Load V2 format with legacy compatibility."""
        self._words = data.get('words', {})
        self._relationships = data.get('relationships', {})
        
        # Convert bandIndex keys to integers
        raw_band_index = data.get('bandIndex', {})
        self._by_band = {int(k): v for k, v in raw_band_index.items()}
        
        # Build byWord index from words dict
        for word_name, word_data in self._words.items():
            self._by_word[word_name] = word_data.get('senses', [])
        
        # Build byPos index from senses
        for sense_id, sense_data in self._senses.items():
            pos = sense_data.get('pos', 'n')
            if pos not in self._by_pos:
                self._by_pos[pos] = []
            self._by_pos[pos].append(sense_id)
        
        print(f"  Loaded V2 data: {len(self._words)} words")
    
    @property
    def is_loaded(self) -> bool:
        """Check if vocabulary data is loaded."""
        return self._loaded
    
    @property
    def version(self) -> str:
        """Get the vocabulary schema version."""
        return self._version or 'unknown'
    
    # =========================================================================
    # CORE LOOKUP METHODS
    # =========================================================================
    
    def get_sense(self, sense_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a sense by ID.
        
        In V3, this returns all data including connections and other_senses.
        
        Args:
            sense_id: Sense ID (e.g., "apple.n.01")
            
        Returns:
            Sense data dictionary or None
        """
        return self._senses.get(sense_id)
    
    def get_senses_for_word(self, word_name: str) -> List[Dict[str, Any]]:
        """
        Get all senses for a word.
        
        Args:
            word_name: Word name
            
        Returns:
            List of sense data dictionaries
        """
        sense_ids = self._by_word.get(word_name, [])
        return [self._senses[sid] for sid in sense_ids if sid in self._senses]
    
    def get_sense_ids_for_word(self, word_name: str) -> List[str]:
        """
        Get sense IDs for a word.
        
        Args:
            word_name: Word name
            
        Returns:
            List of sense IDs
        """
        return self._by_word.get(word_name, [])
    
    # =========================================================================
    # MCQ-SPECIFIC METHODS (V3)
    # =========================================================================
    
    def get_confused_senses(self, sense_id: str) -> List[Dict[str, Any]]:
        """
        Get CONFUSED_WITH senses for MCQ distractors.
        
        Args:
            sense_id: Source sense ID
            
        Returns:
            List of confused sense data with 'sense_id' and 'reason'
        """
        sense = self.get_sense(sense_id)
        if not sense:
            return []
        
        # V3 format: embedded in connections
        connections = sense.get('connections', {})
        confused_refs = connections.get('confused', [])
        
        # Expand references to full sense data
        result = []
        for ref in confused_refs:
            if isinstance(ref, dict):
                conf_sense_id = ref.get('sense_id')
                reason = ref.get('reason', 'unknown')
            else:
                conf_sense_id = ref
                reason = 'unknown'
            
            conf_sense = self.get_sense(conf_sense_id)
            if conf_sense:
                result.append({
                    'sense_id': conf_sense_id,
                    'word': conf_sense.get('word', ''),
                    'definition_zh': conf_sense.get('definition_zh', ''),
                    'definition_en': conf_sense.get('definition_en', ''),
                    'pos': conf_sense.get('pos'),
                    'frequency_rank': conf_sense.get('frequency_rank'),
                    'reason': reason
                })
        
        return result
    
    def get_related_senses(self, sense_id: str) -> List[Dict[str, Any]]:
        """
        Get RELATED_TO senses.
        
        Args:
            sense_id: Source sense ID
            
        Returns:
            List of related sense data
        """
        sense = self.get_sense(sense_id)
        if not sense:
            return []
        
        # Try V3 format first (embedded)
        connections = sense.get('connections', {})
        related_ids = connections.get('related', [])
        
        # Fall back to V2 relationships dict
        if not related_ids and sense_id in self._relationships:
            related_ids = self._relationships[sense_id].get('related', [])
        
        return self._expand_sense_refs(related_ids)
    
    def get_opposite_senses(self, sense_id: str) -> List[Dict[str, Any]]:
        """
        Get OPPOSITE_TO senses.
        
        Args:
            sense_id: Source sense ID
            
        Returns:
            List of opposite sense data
        """
        sense = self.get_sense(sense_id)
        if not sense:
            return []
        
        # Try V3 format first (embedded)
        connections = sense.get('connections', {})
        opposite_ids = connections.get('opposite', [])
        
        # Fall back to V2 relationships dict
        if not opposite_ids and sense_id in self._relationships:
            opposite_ids = self._relationships[sense_id].get('opposite', [])
        
        return self._expand_sense_refs(opposite_ids)
    
    def get_other_senses_of_word(self, sense_id: str) -> List[str]:
        """
        Get other sense IDs of the same word (for polysemy checking).
        
        In V3, this is embedded directly. In V2, we look up via word.
        
        Args:
            sense_id: Source sense ID
            
        Returns:
            List of other sense IDs for the same word
        """
        sense = self.get_sense(sense_id)
        if not sense:
            return []
        
        # V3 format: embedded
        if 'other_senses' in sense:
            return sense['other_senses']
        
        # V2 fallback: look up by word
        word = sense.get('word')
        if word:
            all_senses = self._by_word.get(word, [])
            return [s for s in all_senses if s != sense_id]
        
        return []
    
    def _expand_sense_refs(self, sense_ids: List[str]) -> List[Dict[str, Any]]:
        """Expand sense IDs to full sense data."""
        result = []
        for sid in sense_ids:
            sense = self.get_sense(sid)
            if sense:
                result.append({
                    'sense_id': sid,
                    'word': sense.get('word', ''),
                    'definition_zh': sense.get('definition_zh', ''),
                    'definition_en': sense.get('definition_en', ''),
                    'pos': sense.get('pos'),
                    'frequency_rank': sense.get('frequency_rank')
                })
        return result
    
    # =========================================================================
    # BAND/FREQUENCY METHODS
    # =========================================================================
    
    def get_random_senses_in_band(
        self, 
        band: int, 
        count: int = 10,
        exclude_senses: Optional[List[str]] = None,
        pos: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get random senses from a frequency band.
        
        Args:
            band: Frequency band (1000, 2000, 3000, etc.)
            count: Number of senses to return
            exclude_senses: Sense IDs to exclude
            pos: Optional POS filter
            
        Returns:
            List of sense data dictionaries
        """
        exclude_set = set(exclude_senses or [])
        
        # Get senses in this band
        band_senses = self._by_band.get(band, [])
        
        # Filter
        available = []
        for sid in band_senses:
            if sid in exclude_set:
                continue
            if pos:
                sense = self._senses.get(sid)
                if sense and sense.get('pos') != pos:
                    continue
            available.append(sid)
        
        # Random sample
        if len(available) <= count:
            selected = available
        else:
            selected = random.sample(available, count)
        
        return [self._senses[sid] for sid in selected if sid in self._senses]
    
    def get_senses_by_rank_range(
        self, 
        min_rank: int, 
        max_rank: int,
        pos: Optional[str] = None,
        exclude_words: Optional[Set[str]] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get senses within a frequency rank range.
        
        Args:
            min_rank: Minimum frequency rank
            max_rank: Maximum frequency rank
            pos: Optional POS filter
            exclude_words: Words to exclude
            limit: Maximum results
            
        Returns:
            List of sense data dictionaries
        """
        exclude_words = exclude_words or set()
        results = []
        
        for sense in self._senses.values():
            rank = sense.get('frequency_rank')
            if rank is None:
                continue
            if not (min_rank <= rank <= max_rank):
                continue
            if pos and sense.get('pos') != pos:
                continue
            if sense.get('word') in exclude_words:
                continue
            
            results.append(sense)
            if len(results) >= limit:
                break
        
        return results
    
    def get_senses_by_pos(self, pos: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get senses by part of speech.
        
        Args:
            pos: Part of speech (n, v, a, r, s)
            limit: Maximum results
            
        Returns:
            List of sense data dictionaries
        """
        sense_ids = self._by_pos.get(pos, [])[:limit]
        return [self._senses[sid] for sid in sense_ids if sid in self._senses]
    
    # =========================================================================
    # TRAP/DISTRACTOR METHODS (for Survey/MCQ)
    # =========================================================================
    
    def get_random_traps(
        self, 
        exclude_word: str, 
        count: int = 3,
        rank: Optional[int] = None,
        pos: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get random senses to use as trap/distractor options.
        
        For survey/MCQ generation.
        
        Args:
            exclude_word: Word to exclude (the target word)
            count: Number of traps needed
            rank: Optional frequency rank to match (within ±500)
            pos: Optional POS to match
            
        Returns:
            List of sense data dictionaries
        """
        candidates = []
        
        if rank:
            # Get senses from nearby bands
            search_radius = 500
            for band in self._by_band:
                band_min = band - 999  # e.g., band 2000 covers 1001-2000
                band_max = band
                if rank - search_radius <= band_max and rank + search_radius >= band_min:
                    for sid in self._by_band[band]:
                        sense = self._senses.get(sid)
                        if sense and sense.get('word') != exclude_word:
                            if pos and sense.get('pos') != pos:
                                continue
                            candidates.append(sense)
        else:
            # Get random senses from any band
            for sid, sense in self._senses.items():
                if sense.get('word') != exclude_word:
                    if pos and sense.get('pos') != pos:
                        continue
                    candidates.append(sense)
        
        # Random sample
        if len(candidates) <= count:
            return candidates
        
        return random.sample(candidates, count)
    
    # =========================================================================
    # BLOCK/DETAIL METHODS
    # =========================================================================
    
    def get_starter_pack(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get a starter pack of blocks across frequency bands.
        
        Args:
            limit: Total number of blocks to return
            
        Returns:
            List of block dictionaries
        """
        bands_config = [
            (1000, 10),
            (2000, 10),
            (3000, 15),
            (4000, 15),
        ]
        
        all_blocks = []
        
        for band, count in bands_config:
            senses = self.get_random_senses_in_band(band, count)
            for sense in senses:
                all_blocks.append(self._sense_to_block(sense))
        
        random.shuffle(all_blocks)
        return all_blocks[:limit]
    
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
        
        # Build connections list
        connections = []
        
        for related in self.get_related_senses(sense_id):
            connections.append({
                'sense_id': related['sense_id'],
                'word': related['word'],
                'type': 'RELATED_TO'
            })
        
        for opposite in self.get_opposite_senses(sense_id):
            connections.append({
                'sense_id': opposite['sense_id'],
                'word': opposite['word'],
                'type': 'OPPOSITE_TO'
            })
        
        # Build definition with explanation
        definition_zh = sense.get('definition_zh', '')
        definition_zh_explanation = sense.get('definition_zh_explanation', '')
        if definition_zh_explanation:
            definition_zh = f"{definition_zh} {definition_zh_explanation}".strip()
        
        example_zh = sense.get('example_zh_translation', sense.get('example_zh', ''))
        example_zh_explanation = sense.get('example_zh_explanation', '')
        if example_zh_explanation:
            example_zh = f"{example_zh} {example_zh_explanation}".strip()
        
        # Get network data (V3)
        network = sense.get('network', {})
        
        return {
            'sense_id': sense_id,
            'word': sense.get('word', ''),
            'pos': sense.get('pos'),
            'tier': sense.get('tier', 1),
            'base_xp': network.get('total_xp', 100),
            'connection_count': len(connections),
            'total_value': network.get('total_xp', 100),
            'rank': sense.get('frequency_rank'),
            'cefr': sense.get('cefr'),
            'definition_en': sense.get('definition_en', ''),
            'definition_zh': definition_zh,
            'example_en': sense.get('example_en', ''),
            'example_zh': example_zh,
            'connections': connections,
        }
    
    def _sense_to_block(self, sense: Dict[str, Any]) -> Dict[str, Any]:
        """Convert sense data to block format."""
        definition_preview = sense.get('definition_en', '')[:100]
        network = sense.get('network', {})
        
        return {
            'sense_id': sense.get('id', ''),
            'word': sense.get('word', ''),
            'definition_preview': definition_preview,
            'definition_zh': sense.get('definition_zh', ''),
            'rank': sense.get('frequency_rank'),
            'tier': sense.get('tier', 1),
            'base_xp': network.get('total_xp', 100),
            'connection_count': network.get('hop_1_count', 0),
            'total_value': network.get('total_xp', 100),
            'status': 'raw',
        }
    
    # =========================================================================
    # LEGACY V2 COMPATIBILITY
    # =========================================================================
    
    def get_word(self, word_name: str) -> Optional[Dict[str, Any]]:
        """
        Get a word by name (V2 compatibility).
        
        In V3, returns synthesized word data from first sense.
        
        Args:
            word_name: Word name (e.g., "apple")
            
        Returns:
            Word data dictionary or None
        """
        # V2 format
        if self._words:
            return self._words.get(word_name)
        
        # V3: synthesize from senses
        sense_ids = self._by_word.get(word_name, [])
        if not sense_ids:
            return None
        
        first_sense = self._senses.get(sense_ids[0])
        if not first_sense:
            return None
        
        return {
            'name': word_name,
            'frequency_rank': first_sense.get('frequency_rank'),
            'moe_level': first_sense.get('moe_level'),
            'senses': sense_ids
        }
    
    def get_connections(self, sense_id: str) -> List[Dict[str, Any]]:
        """
        Get all connections for a sense (V2 compatibility).
        
        Args:
            sense_id: Source sense ID
            
        Returns:
            List of connection dictionaries
        """
        connections = []
        
        for related in self.get_related_senses(sense_id):
            connections.append({
                'sense_id': related['sense_id'],
                'word': related['word'],
                'type': 'RELATED_TO'
            })
        
        for opposite in self.get_opposite_senses(sense_id):
            connections.append({
                'sense_id': opposite['sense_id'],
                'word': opposite['word'],
                'type': 'OPPOSITE_TO'
            })
        
        return connections


# Singleton instance
vocabulary_store = VocabularyStore()
