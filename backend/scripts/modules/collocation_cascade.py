"""
Collocation Cascade - Layer 3

Cascading collocation extractor using 3 sources in priority order:
1. NGSL Phrase List (Priority 1 - The "Teacher")
2. WordNet Lemmas (Priority 2 - The "Dictionary")
3. Datamuse API (Priority 3 - The "Crowd" - Fallback)

Ensures every word gets rich phrase data with quality prioritization.
"""

import csv
import requests
import time
import threading
from typing import Dict, List, Set
from collections import defaultdict


class NGSLPhraseLoader:
    """Loads and provides NGSL phrase data."""
    
    def __init__(self, ngsl_phrase_file: str):
        """Load NGSL phrase list and index by anchor word."""
        self.phrases_by_word = self._load_and_index(ngsl_phrase_file)
        self.stats = {
            'total_phrases': 0,
            'unique_words': 0,
        }
    
    def _load_and_index(self, filepath: str) -> Dict[str, List[str]]:
        """
        Load NGSL phrase CSV and create lookup dictionary.
        
        Expected format:
        phrase,anchor_word,frequency
        "run out of",run,12500
        "formal education",formal,8900
        """
        phrases_index = defaultdict(list)
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    phrase = row.get('phrase', '').strip()
                    anchor = row.get('anchor_word', '').strip()
                    
                    if phrase and anchor:
                        phrases_index[anchor].append(phrase)
                        self.stats['total_phrases'] += 1
            
            self.stats['unique_words'] = len(phrases_index)
            print(f"✅ Loaded {self.stats['total_phrases']} NGSL phrases for {self.stats['unique_words']} words")
            
        except FileNotFoundError:
            print(f"⚠️  NGSL phrase file not found: {filepath}")
            print("    Continuing without NGSL phrases (will rely on Datamuse)")
        except Exception as e:
            print(f"⚠️  Error loading NGSL phrases: {e}")
        
        return dict(phrases_index)
    
    def get_phrases(self, word: str) -> List[str]:
        """Get all NGSL phrases for a word (instant lookup)."""
        return self.phrases_by_word.get(word, [])


class DatamuseAPIClient:
    """Fallback collocation source for words not covered by NGSL/WordNet."""
    
    BASE_URL = "https://api.datamuse.com/words"
    RATE_LIMIT_DELAY = 0.15  # 150ms between requests
    
    def __init__(self):
        """Initialize Datamuse client."""
        self.cache = {}
        self.stats = {
            'total_requests': 0,
            'cache_hits': 0,
            'api_errors': 0,
        }
        self.last_request_time = 0
        self.rate_limit_lock = threading.Lock()  # Thread-safe rate limiting
        self.cache_lock = threading.Lock()  # Thread-safe cache access
        self.stats_lock = threading.Lock()  # Thread-safe stats
    
    def get_collocations(self, word: str, pos: str) -> Dict:
        """
        Get statistical collocations from Datamuse.
        
        Args:
            word: The word to get collocations for
            pos: Part of speech ('a' = adjective, 'n' = noun, 'v' = verb, 'r' = adverb)
        
        Returns:
            {'all_phrases': List[str]}
        """
        cache_key = f"{word}_{pos}"
        
        # Check cache (thread-safe)
        with self.cache_lock:
            if cache_key in self.cache:
                with self.stats_lock:
                    self.stats['cache_hits'] += 1
                return self.cache[cache_key]
        
        phrases = []
        
        try:
            if pos == 'a':  # Adjective
                phrases = self._get_adjective_collocations(word)
            elif pos == 'n':  # Noun
                phrases = self._get_noun_collocations(word)
            elif pos == 'v':  # Verb
                phrases = self._get_verb_collocations(word)
            elif pos == 'r':  # Adverb
                phrases = self._get_adverb_collocations(word)
        
        except Exception as e:
            with self.stats_lock:
                self.stats['api_errors'] += 1
            print(f"⚠️  Datamuse error for '{word}' ({pos}): {e}")
        
        result = {'all_phrases': phrases}
        with self.cache_lock:
            self.cache[cache_key] = result
        return result
    
    def _get_adjective_collocations(self, word: str) -> List[str]:
        """Get adjective+noun collocations (e.g., 'formal education')."""
        results = self._query(f"?rel_jjb={word}&max=10")
        return [f"{word} {r['word']}" for r in results]
    
    def _get_noun_collocations(self, word: str) -> List[str]:
        """Get noun collocations (e.g., 'word choice' for 'choice')."""
        results = self._query(f"?rel_trg={word}&max=10")
        return [f"{r['word']} {word}" for r in results]
    
    def _get_verb_collocations(self, word: str) -> List[str]:
        """Get verb+preposition collocations (e.g., 'run out of')."""
        results = self._query(f"?lc={word}&sp=*&max=10")
        prep_words = {'up', 'down', 'out', 'in', 'on', 'off', 'over', 'through', 'away', 'back'}
        return [f"{word} {r['word']}" for r in results if r['word'] in prep_words]
    
    def _get_adverb_collocations(self, word: str) -> List[str]:
        """Get adverb collocations."""
        # Adverbs are tricky, try trigger words
        results = self._query(f"?rel_trg={word}&max=5")
        return [f"{word} {r['word']}" for r in results[:5]]
    
    def _query(self, params: str) -> List[Dict]:
        """Execute Datamuse query with error handling."""
        self._wait_for_rate_limit()
        
        try:
            with self.stats_lock:
                self.stats['total_requests'] += 1
            response = requests.get(self.BASE_URL + params, timeout=3)
            
            if response.status_code == 200:
                return response.json()
            else:
                return []
        
        except Exception as e:
            print(f"⚠️  Datamuse query error: {e}")
            return []
    
    def _wait_for_rate_limit(self):
        """Enforce rate limiting (thread-safe)."""
        with self.rate_limit_lock:
            elapsed = time.time() - self.last_request_time
            if elapsed < self.RATE_LIMIT_DELAY:
                time.sleep(self.RATE_LIMIT_DELAY - elapsed)
            self.last_request_time = time.time()


class CollocationCascade:
    """
    Cascading collocation extractor using 3 sources in priority order.
    Ensures every word gets rich phrase data with quality prioritization.
    """
    
    def __init__(self, ngsl_phrase_file: str, wordnet_phrases: Dict[str, List[str]] = None):
        """
        Initialize cascade with NGSL file and optional WordNet phrases.
        
        Args:
            ngsl_phrase_file: Path to NGSL CSV file
            wordnet_phrases: Optional dict of word -> phrases from WordNet lemmas
        """
        self.ngsl_loader = NGSLPhraseLoader(ngsl_phrase_file)
        self.wordnet_phrases = wordnet_phrases or {}
        self.datamuse_client = DatamuseAPIClient()
        self.min_phrases = 5  # Minimum phrases per word before hitting API
        
        self.stats = {
            'total_words': 0,
            'ngsl_hits': 0,
            'wordnet_hits': 0,
            'datamuse_hits': 0,
            'phrases_from_ngsl': 0,
            'phrases_from_wordnet': 0,
            'phrases_from_datamuse': 0,
        }
        self.stats_lock = threading.Lock()  # Thread-safe stats
    
    def get_collocations(self, word: str, pos: str) -> Dict:
        """
        Get collocations using cascading priority system.
        
        Strategy:
        1. Start with NGSL (high quality, exam-relevant)
        2. Add WordNet lemmas (already extracted, zero cost)
        3. If < 5 phrases total, fill with Datamuse (long tail coverage)
        
        Args:
            word: The word to get collocations for
            pos: Part of speech
        
        Returns:
            {
                'all_phrases': List[str],
                'source_breakdown': {
                    'ngsl': int,
                    'wordnet': int,
                    'datamuse': int
                }
            }
        """
        with self.stats_lock:
            self.stats['total_words'] += 1
        
        all_phrases = []
        
        # Priority 1: NGSL (The Teacher)
        ngsl_phrases = self.ngsl_loader.get_phrases(word)
        if ngsl_phrases:
            with self.stats_lock:
                self.stats['ngsl_hits'] += 1
                self.stats['phrases_from_ngsl'] += len(ngsl_phrases)
        all_phrases.extend(ngsl_phrases)
        
        # Priority 2: WordNet (The Dictionary)
        wordnet_phrases_list = self.wordnet_phrases.get(word, [])
        if wordnet_phrases_list:
            with self.stats_lock:
                self.stats['wordnet_hits'] += 1
                self.stats['phrases_from_wordnet'] += len(wordnet_phrases_list)
        # Add only unique phrases
        for phrase in wordnet_phrases_list:
            if phrase not in all_phrases:
                all_phrases.append(phrase)
        
        # Priority 3: Datamuse (The Crowd) - Only if needed
        datamuse_count = 0
        if len(all_phrases) < self.min_phrases:
            datamuse_phrases = self.datamuse_client.get_collocations(word, pos)
            for phrase in datamuse_phrases.get('all_phrases', []):
                if phrase not in all_phrases:
                    all_phrases.append(phrase)
                    datamuse_count += 1
                if len(all_phrases) >= self.min_phrases:
                    break
            
            if datamuse_count > 0:
                with self.stats_lock:
                    self.stats['datamuse_hits'] += 1
                    self.stats['phrases_from_datamuse'] += datamuse_count
        
        return {
            'all_phrases': all_phrases,
            'source_breakdown': {
                'ngsl': len(ngsl_phrases),
                'wordnet': len(wordnet_phrases_list),
                'datamuse': datamuse_count
            }
        }
    
    def get_stats(self) -> Dict:
        """Get cascade statistics."""
        stats = self.stats.copy()
        
        # Add coverage percentages
        if stats['total_words'] > 0:
            stats['ngsl_coverage'] = f"{(stats['ngsl_hits'] / stats['total_words']) * 100:.1f}%"
            stats['wordnet_coverage'] = f"{(stats['wordnet_hits'] / stats['total_words']) * 100:.1f}%"
            stats['datamuse_coverage'] = f"{(stats['datamuse_hits'] / stats['total_words']) * 100:.1f}%"
        
        return stats

