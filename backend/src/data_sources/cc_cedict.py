"""
CC-CEDICT Chinese Dictionary Integration

Parses CC-CEDICT (a free Chinese-English dictionary) to provide
verified Chinese translations for English words.

Source: https://www.mdbg.net/chinese/dictionary?page=cc-cedict
Format: Traditional Simplified [pinyin] /definition1/definition2/

Usage:
    from src.data_sources.cc_cedict import get_translations
    
    translations = get_translations("hello")
    # Returns: ['你好', '哈羅']
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from functools import lru_cache


class CCCedict:
    """CC-CEDICT dictionary loader and lookup."""
    
    _instance = None
    _data: Dict[str, List[Dict]] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._loaded = False
        return cls._instance
    
    def __init__(self):
        if not self._loaded:
            self._load_dictionary()
            self._loaded = True
    
    def _get_source_path(self) -> Path:
        """Get path to CC-CEDICT source file."""
        return Path(__file__).parent.parent.parent / 'data' / 'source' / 'cedict_ts.u8'
    
    def _get_cache_path(self) -> Path:
        """Get path to parsed JSON cache."""
        return Path(__file__).parent.parent.parent / 'data' / 'source' / 'cc-cedict.json'
    
    def _load_dictionary(self):
        """Load dictionary from cache or parse from source."""
        cache_path = self._get_cache_path()
        
        # Try to load from cache first
        if cache_path.exists():
            try:
                with open(cache_path, 'r', encoding='utf-8') as f:
                    self._data = json.load(f)
                print(f"✓ Loaded CC-CEDICT cache: {len(self._data)} English entries")
                return
            except (json.JSONDecodeError, IOError) as e:
                print(f"⚠️ Cache corrupted, reparsing: {e}")
        
        # Parse from source
        self._parse_source()
        
        # Save to cache
        self._save_cache()
    
    def _parse_source(self):
        """Parse CC-CEDICT source file."""
        source_path = self._get_source_path()
        
        if not source_path.exists():
            print(f"⚠️ CC-CEDICT source not found at {source_path}")
            print("  Download from: https://www.mdbg.net/chinese/dictionary?page=cc-cedict")
            self._data = {}
            return
        
        print(f"Parsing CC-CEDICT from {source_path}...")
        
        # Pattern: Traditional Simplified [pinyin] /definition1/definition2/
        # Example: 你好 你好 [ni3 hao3] /Hello!/Hi!/How are you?/
        pattern = re.compile(r'^(\S+)\s+(\S+)\s+\[([^\]]+)\]\s+/(.+)/$')
        
        entries = {}
        english_to_chinese = {}
        line_count = 0
        
        with open(source_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                
                # Skip comments and empty lines
                if not line or line.startswith('#'):
                    continue
                
                match = pattern.match(line)
                if not match:
                    continue
                
                traditional, simplified, pinyin, definitions_str = match.groups()
                definitions = [d.strip() for d in definitions_str.split('/') if d.strip()]
                
                line_count += 1
                
                # Index by English words in definitions
                for definition in definitions:
                    # Extract English words (skip Chinese, punctuation)
                    english_words = re.findall(r'\b[a-zA-Z][a-zA-Z\-\']*[a-zA-Z]\b|\b[a-zA-Z]\b', definition.lower())
                    
                    for word in english_words:
                        word = word.lower()
                        if len(word) < 2:  # Skip single letters
                            continue
                        
                        if word not in english_to_chinese:
                            english_to_chinese[word] = []
                        
                        # Store the entry with context
                        entry = {
                            'traditional': traditional,
                            'simplified': simplified,
                            'pinyin': pinyin,
                            'definition': definition
                        }
                        
                        # Avoid duplicates
                        if entry not in english_to_chinese[word]:
                            english_to_chinese[word].append(entry)
        
        self._data = english_to_chinese
        print(f"✓ Parsed CC-CEDICT: {line_count} Chinese entries → {len(self._data)} English words indexed")
    
    def _save_cache(self):
        """Save parsed data to JSON cache."""
        cache_path = self._get_cache_path()
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump(self._data, f, ensure_ascii=False, indent=None)
        
        size_mb = cache_path.stat().st_size / 1024 / 1024
        print(f"✓ Saved CC-CEDICT cache: {cache_path} ({size_mb:.1f} MB)")
    
    def lookup(self, word: str) -> List[Dict]:
        """
        Look up an English word and return all Chinese translations with context.
        
        Args:
            word: English word to look up
            
        Returns:
            List of dicts with 'traditional', 'simplified', 'pinyin', 'definition'
        """
        return self._data.get(word.lower(), [])
    
    def get_translations(self, word: str, max_results: int = 5) -> List[str]:
        """
        Get just the Traditional Chinese characters for a word.
        
        Args:
            word: English word to look up
            max_results: Maximum number of translations to return
            
        Returns:
            List of Traditional Chinese translations (deduplicated)
        """
        entries = self.lookup(word)
        
        # Get unique traditional characters
        seen = set()
        translations = []
        
        for entry in entries:
            trad = entry['traditional']
            if trad not in seen:
                seen.add(trad)
                translations.append(trad)
            
            if len(translations) >= max_results:
                break
        
        return translations
    
    def get_translations_with_pinyin(self, word: str, max_results: int = 5) -> List[Tuple[str, str]]:
        """
        Get Traditional Chinese translations with pinyin.
        
        Returns:
            List of (traditional_chars, pinyin) tuples
        """
        entries = self.lookup(word)
        
        seen = set()
        results = []
        
        for entry in entries:
            trad = entry['traditional']
            if trad not in seen:
                seen.add(trad)
                results.append((trad, entry['pinyin']))
            
            if len(results) >= max_results:
                break
        
        return results
    
    def get_best_translation_for_definition(
        self, 
        word: str, 
        definition: str,
        pos: str = None
    ) -> Optional[str]:
        """
        Get the best Chinese translation matching a specific English definition.
        
        Uses fuzzy matching to find the entry whose English definition
        best matches the provided sense definition.
        
        Args:
            word: English word
            definition: English definition to match
            pos: Part of speech (n, v, adj, etc.)
            
        Returns:
            Best matching Traditional Chinese translation, or None
        """
        entries = self.lookup(word)
        
        if not entries:
            return None
        
        # Simple matching: check if definition words appear in CC-CEDICT entry
        def_words = set(re.findall(r'\b[a-zA-Z]+\b', definition.lower()))
        
        best_match = None
        best_score = 0
        
        for entry in entries:
            entry_words = set(re.findall(r'\b[a-zA-Z]+\b', entry['definition'].lower()))
            
            # Calculate overlap score
            overlap = len(def_words & entry_words)
            score = overlap / max(len(def_words), 1)
            
            # Bonus for exact word match
            if word.lower() in entry['definition'].lower():
                score += 0.5
            
            # Bonus for POS match (if indicated in definition)
            if pos:
                pos_indicators = {
                    'n': ['noun', '(n)', '/n/'],
                    'v': ['verb', '(v)', 'to '],
                    'adj': ['adjective', '(adj)', '(a)'],
                    'adv': ['adverb', '(adv)'],
                }
                for indicator in pos_indicators.get(pos, []):
                    if indicator in entry['definition'].lower():
                        score += 0.3
                        break
            
            if score > best_score:
                best_score = score
                best_match = entry['traditional']
        
        return best_match


# Singleton instance
_cedict = None


def get_cedict() -> CCCedict:
    """Get the singleton CC-CEDICT instance."""
    global _cedict
    if _cedict is None:
        _cedict = CCCedict()
    return _cedict


@lru_cache(maxsize=10000)
def get_translations(word: str, max_results: int = 5) -> List[str]:
    """
    Get Chinese translations for an English word.
    
    Args:
        word: English word to translate
        max_results: Maximum number of translations
        
    Returns:
        List of Traditional Chinese translations
        
    Example:
        >>> get_translations("hello")
        ['你好', '哈羅', '喂']
    """
    return get_cedict().get_translations(word, max_results)


def get_best_translation(word: str, definition: str, pos: str = None) -> Optional[str]:
    """
    Get the best Chinese translation for a specific word sense.
    
    Args:
        word: English word
        definition: English definition of the specific sense
        pos: Part of speech
        
    Returns:
        Best matching Traditional Chinese translation
        
    Example:
        >>> get_best_translation("bank", "financial institution", "n")
        '銀行'
        >>> get_best_translation("bank", "sloping land beside water", "n")
        '河岸'
    """
    return get_cedict().get_best_translation_for_definition(word, definition, pos)


if __name__ == '__main__':
    # Test the module
    print("\n--- CC-CEDICT Test ---\n")
    
    test_words = ['hello', 'bank', 'run', 'drop', 'break', 'colour']
    
    for word in test_words:
        translations = get_translations(word)
        print(f"{word}: {translations}")
    
    print("\n--- Definition-Specific Lookup ---\n")
    
    print(f"bank (financial): {get_best_translation('bank', 'financial institution where you keep money', 'n')}")
    print(f"bank (river): {get_best_translation('bank', 'sloping land beside a river or lake', 'n')}")

