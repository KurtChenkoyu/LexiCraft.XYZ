"""
Chinese Translation Source - Unified Interface

Combines multiple sources for Chinese translations:
1. Open Multilingual Wordnet (OMW) - Authoritative, sense-aligned
2. CC-CEDICT - Large coverage, but needs careful scoring
3. AI Generation - Fallback when authoritative sources unavailable

Priority: OMW > CC-CEDICT (improved scoring) > AI

Usage:
    from src.data_sources.chinese_translation import get_chinese_translation
    
    result = get_chinese_translation(
        word="bank",
        sense_id="bank.n.01",
        definition="a financial institution"
    )
    # Returns: ChineseTranslation(translation="銀行", source="omw", confidence="high")
"""

import re
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from functools import lru_cache

# NLTK WordNet with OMW
from nltk.corpus import wordnet as wn

# Simplified to Traditional Chinese conversion
try:
    from opencc import OpenCC
    _converter = OpenCC('s2t')  # Simplified to Traditional
    HAS_OPENCC = True
except ImportError:
    HAS_OPENCC = False
    _converter = None

# CC-CEDICT
from .cc_cedict import get_cedict


# Stop words to ignore in CC-CEDICT scoring
STOP_WORDS = {
    'a', 'an', 'the', 'of', 'to', 'in', 'on', 'at', 'for', 'and', 'or', 
    'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had',
    'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might',
    'must', 'can', 'etc', 'eg', 'ie', 'vs', 'it', 'its', 'this', 'that',
    'with', 'as', 'by', 'from', 'into', 'through', 'during', 'before', 'after',
    'above', 'below', 'between', 'under', 'again', 'further', 'then', 'once',
    'here', 'there', 'when', 'where', 'why', 'how', 'all', 'each', 'few',
    'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only',
    'own', 'same', 'so', 'than', 'too', 'very', 'just', 'also'
}


@dataclass
class ChineseTranslation:
    """Result of Chinese translation lookup."""
    translation: str  # Traditional Chinese
    source: str  # 'omw', 'cc-cedict', 'ai', 'none'
    confidence: str  # 'high', 'medium', 'low'
    alternatives: List[str]  # Other possible translations
    pinyin: Optional[str] = None


def simplified_to_traditional(text: str) -> str:
    """Convert Simplified Chinese to Traditional Chinese."""
    if HAS_OPENCC and _converter:
        return _converter.convert(text)
    return text


def _is_chinese(text: str) -> bool:
    """Check if text contains Chinese characters."""
    for char in text:
        if '\u4e00' <= char <= '\u9fff':  # CJK Unified Ideographs
            return True
    return False


@lru_cache(maxsize=10000)
def get_omw_translation(sense_id: str) -> Optional[str]:
    """
    Get Chinese translation from Open Multilingual Wordnet.
    
    This is the most authoritative source as it's aligned with WordNet senses.
    
    Args:
        sense_id: WordNet sense ID (e.g., "bank.n.01")
        
    Returns:
        Traditional Chinese translation if available
    """
    try:
        synset = wn.synset(sense_id)
        
        # Try Mandarin Chinese first (cmn)
        cmn_lemmas = synset.lemma_names('cmn')
        if cmn_lemmas:
            # Filter: must contain Chinese characters, remove grammatical markers
            for lemma in cmn_lemmas:
                clean = lemma.replace('+', '')
                if clean and _is_chinese(clean):
                    return simplified_to_traditional(clean)
        
        # Note: Skip zsm (Malay) as it often returns Malay words, not Chinese
        # The zsm code in OMW is sometimes misused
                
        return None
    except Exception as e:
        return None


def get_omw_alternatives(sense_id: str, max_results: int = 5) -> List[str]:
    """Get all OMW Chinese translations for a sense."""
    try:
        synset = wn.synset(sense_id)
        results = []
        
        # Only use cmn (Mandarin Chinese) - zsm often has Malay words
        try:
            lemmas = synset.lemma_names('cmn')
            for lemma in lemmas:
                clean = lemma.replace('+', '')
                # Must contain actual Chinese characters
                if clean and _is_chinese(clean) and clean not in results:
                    results.append(simplified_to_traditional(clean))
                if len(results) >= max_results:
                    return results
        except:
            pass
        
        return results
    except:
        return []


def get_cedict_translation_improved(
    word: str,
    definition: str,
    pos: str = None
) -> Optional[str]:
    """
    Get CC-CEDICT translation with IMPROVED scoring.
    
    Fixes:
    - Ignores stop words in overlap calculation
    - Prioritizes entries where word is PRIMARY meaning
    - Penalizes entries where word is just mentioned
    """
    cedict = get_cedict()
    entries = cedict.lookup(word)
    
    if not entries:
        return None
    
    # Filter definition words (excluding stop words)
    def_words = set(re.findall(r'\b[a-zA-Z]+\b', definition.lower()))
    def_words -= STOP_WORDS
    
    best_match = None
    best_score = -1
    
    for entry in entries:
        entry_def = entry['definition'].lower()
        entry_words = set(re.findall(r'\b[a-zA-Z]+\b', entry_def))
        entry_words -= STOP_WORDS
        
        # Calculate overlap score (excluding stop words)
        if def_words:
            overlap = len(def_words & entry_words)
            score = overlap / len(def_words)
        else:
            score = 0
        
        # STRONG BONUS: Definition starts with the word or equals the word
        # This means it's the PRIMARY meaning, not just mentioned
        entry_def_clean = entry_def.strip()
        if entry_def_clean == word.lower():
            score += 2.0  # Perfect match - just the word
        elif entry_def_clean.startswith(f"{word.lower()} ") or entry_def_clean.startswith(f"to {word.lower()}"):
            score += 1.5  # Definition starts with the word
        elif entry_def_clean.startswith(f"({word.lower()})"):
            score += 1.0  # Word in parentheses at start
        
        # MEDIUM BONUS: Short definition containing the word
        # Short definitions are more likely to be direct translations
        if len(entry_def) < 30 and word.lower() in entry_def:
            score += 0.5
        
        # PENALTY: Word appears in parentheses mid-definition (descriptive)
        if f'({word.lower()})' in entry_def and not entry_def_clean.startswith(f'({word.lower()})'):
            score -= 0.3
        
        # PENALTY: Word appears after "e.g.", "such as", "like" (example, not definition)
        example_patterns = ['e.g.', 'eg.', 'such as', 'like ', 'for example', 'i.e.']
        for pattern in example_patterns:
            if pattern in entry_def and entry_def.index(pattern) < entry_def.find(word.lower()):
                score -= 0.5
                break
        
        # PENALTY: Very long definition (word is likely just mentioned)
        if len(entry_def) > 80:
            score -= 0.3
        if len(entry_def) > 120:
            score -= 0.3
        
        # POS bonus
        if pos:
            pos_indicators = {
                'n': ['noun', '(n)'],
                'v': ['verb', '(v)', 'to '],
                'a': ['adj', '(adj)', '(a)'],
                'adj': ['adj', '(adj)', '(a)'],
                'r': ['adv', '(adv)'],
                'adv': ['adv', '(adv)'],
            }
            for indicator in pos_indicators.get(pos, []):
                if indicator in entry_def:
                    score += 0.2
                    break
        
        if score > best_score:
            best_score = score
            best_match = entry['traditional']
    
    # Only return if score is reasonable
    if best_score > 0.3:
        return best_match
    return None


def get_cedict_alternatives(word: str, max_results: int = 5) -> List[str]:
    """Get CC-CEDICT translation options as hints for AI."""
    cedict = get_cedict()
    entries = cedict.lookup(word)
    
    seen = set()
    results = []
    
    for entry in entries:
        trad = entry['traditional']
        if trad not in seen:
            seen.add(trad)
            results.append(trad)
        if len(results) >= max_results:
            break
    
    return results


def get_chinese_translation(
    word: str,
    sense_id: str = None,
    definition: str = None,
    pos: str = None
) -> ChineseTranslation:
    """
    Get the best Chinese translation using multiple sources.
    
    Priority:
    1. OMW (if sense_id provided) - Authoritative, sense-aligned
    2. CC-CEDICT (improved scoring) - Large coverage
    3. Return empty for AI to generate
    
    Args:
        word: English word
        sense_id: WordNet sense ID (optional but recommended)
        definition: English definition for CC-CEDICT matching
        pos: Part of speech
        
    Returns:
        ChineseTranslation with translation and source info
    """
    alternatives = []
    
    # 1. Try OMW first (most authoritative)
    if sense_id:
        omw_translation = get_omw_translation(sense_id)
        omw_alternatives = get_omw_alternatives(sense_id)
        
        if omw_translation:
            return ChineseTranslation(
                translation=omw_translation,
                source='omw',
                confidence='high',
                alternatives=omw_alternatives
            )
        
        alternatives.extend(omw_alternatives)
    
    # 2. Try CC-CEDICT with improved scoring
    if definition:
        cedict_translation = get_cedict_translation_improved(word, definition, pos)
        cedict_alternatives = get_cedict_alternatives(word)
        
        if cedict_translation:
            # Add alternatives that aren't the main translation
            for alt in cedict_alternatives:
                if alt != cedict_translation and alt not in alternatives:
                    alternatives.append(alt)
            
            return ChineseTranslation(
                translation=cedict_translation,
                source='cc-cedict',
                confidence='medium',
                alternatives=alternatives[:5]
            )
        
        # Add CC-CEDICT alternatives even if no good match
        for alt in cedict_alternatives:
            if alt not in alternatives:
                alternatives.append(alt)
    
    # 3. No authoritative translation found - return for AI generation
    return ChineseTranslation(
        translation='',
        source='none',
        confidence='low',
        alternatives=alternatives[:5]
    )


if __name__ == '__main__':
    print("\n=== Chinese Translation Source Test ===\n")
    
    test_cases = [
        ('bank', 'depository_financial_institution.n.01', 'a financial institution', 'n'),
        ('bank', 'bank.n.01', 'sloping land beside water', 'n'),
        ('run', 'run.v.01', 'move fast by using legs', 'v'),
        ('popular', 'popular.a.01', 'liked by many people', 'a'),
        ('therefore', 'therefore.r.01', 'as a consequence', 'r'),
        ('month', 'calendar_month.n.01', 'a time unit of approximately 30 days', 'n'),
        ('star', 'star.n.03', 'a celestial body visible in the night sky', 'n'),
    ]
    
    for word, sense_id, definition, pos in test_cases:
        result = get_chinese_translation(word, sense_id, definition, pos)
        print(f"{word} ({sense_id}):")
        print(f"  Translation: {result.translation}")
        print(f"  Source: {result.source}")
        print(f"  Confidence: {result.confidence}")
        print(f"  Alternatives: {result.alternatives[:3]}")
        print()

