"""
Free Dictionary API Client - Layer 2

Augments WordNet with "common sense" relationships from Free Dictionary API.
Adds missing synonyms/antonyms that WordNet doesn't have (like "informal" for "formal").
"""

import requests
import time
import threading
from typing import Dict, List, Set
from .vocabulary_loader import VocabularyLoader


class FreeDictAPIClient:
    """Client for Free Dictionary API."""
    
    BASE_URL = "https://api.dictionaryapi.dev/api/v2/entries/en/{word}"
    RATE_LIMIT_DELAY = 0.15  # 150ms between requests (400/min safe rate)
    
    def __init__(self, vocab_loader: VocabularyLoader):
        """Initialize with vocabulary loader."""
        self.vocab_loader = vocab_loader
        self.cache = {}  # Cache API responses
        self.stats = {
            'total_requests': 0,
            'cache_hits': 0,
            'api_errors': 0,
            'synonyms_added': 0,
            'antonyms_added': 0,
        }
        self.last_request_time = 0
        self.rate_limit_lock = threading.Lock()  # Thread-safe rate limiting
        self.cache_lock = threading.Lock()  # Thread-safe cache access
        self.stats_lock = threading.Lock()  # Thread-safe stats
    
    def fetch(self, word: str) -> Dict:
        """
        Fetch common synonyms/antonyms from Free Dictionary API.
        
        Returns:
            {'synonyms': List[str], 'antonyms': List[str]}
        """
        # Check cache first (thread-safe)
        with self.cache_lock:
            if word in self.cache:
                with self.stats_lock:
                    self.stats['cache_hits'] += 1
                return self.cache[word]
        
        # Rate limiting
        self._wait_for_rate_limit()
        
        try:
            with self.stats_lock:
                self.stats['total_requests'] += 1
            response = requests.get(
                self.BASE_URL.format(word=word),
                timeout=5
            )
            
            if response.status_code != 200:
                result = {'synonyms': [], 'antonyms': []}
                with self.cache_lock:
                    self.cache[word] = result
                return result
            
            data = response.json()[0]
            synonyms = set()
            antonyms = set()
            
            # Extract from all meanings
            for meaning in data.get('meanings', []):
                for definition in meaning.get('definitions', []):
                    synonyms.update(definition.get('synonyms', []))
                    antonyms.update(definition.get('antonyms', []))
            
            result = {
                'synonyms': list(synonyms),
                'antonyms': list(antonyms)
            }
            
            # Cache the result (thread-safe)
            with self.cache_lock:
                self.cache[word] = result
            
            return result
            
        except Exception as e:
            with self.stats_lock:
                self.stats['api_errors'] += 1
            print(f"⚠️  API error for '{word}': {e}")
            result = {'synonyms': [], 'antonyms': []}
            with self.cache_lock:
                self.cache[word] = result
            return result
    
    def _wait_for_rate_limit(self):
        """Enforce rate limiting (thread-safe)."""
        with self.rate_limit_lock:
            elapsed = time.time() - self.last_request_time
            if elapsed < self.RATE_LIMIT_DELAY:
                time.sleep(self.RATE_LIMIT_DELAY - elapsed)
            self.last_request_time = time.time()
    
    def merge_with_existing(self, our_data: Dict, api_data: Dict, word: str) -> Dict:
        """
        Smart merge: add missing words from API to our connections.
        
        Args:
            our_data: Current connections dict with 'related' and 'opposite'
            api_data: API response with 'synonyms' and 'antonyms'
            word: The word being enriched
        
        Returns:
            Updated connections dict
        """
        # Get current words in our data
        our_related_words = set()
        for sense_id in our_data.get('related', []):
            w = self.vocab_loader.extract_word_from_sense_id(sense_id)
            our_related_words.add(w)
        
        our_opposite_words = set()
        for sense_id in our_data.get('opposite', []):
            w = self.vocab_loader.extract_word_from_sense_id(sense_id)
            our_opposite_words.add(w)
        
        # Find missing synonyms
        api_synonyms = set(api_data.get('synonyms', []))
        missing_synonyms = api_synonyms - our_related_words
        
        for missing_word in missing_synonyms:
            sense_ids = self.vocab_loader.get_senses_for_word(missing_word)
            if sense_ids:
                # Add first matching sense (could be improved with POS matching)
                if 'related' not in our_data:
                    our_data['related'] = []
                our_data['related'].append(sense_ids[0])
                with self.stats_lock:
                    self.stats['synonyms_added'] += 1
        
        # Find missing antonyms
        api_antonyms = set(api_data.get('antonyms', []))
        missing_antonyms = api_antonyms - our_opposite_words
        
        for missing_word in missing_antonyms:
            sense_ids = self.vocab_loader.get_senses_for_word(missing_word)
            if sense_ids:
                if 'opposite' not in our_data:
                    our_data['opposite'] = []
                our_data['opposite'].append(sense_ids[0])
                with self.stats_lock:
                    self.stats['antonyms_added'] += 1
        
        return our_data
    
    def get_stats(self) -> Dict:
        """Get API usage statistics."""
        return self.stats.copy()

