"""
Data Sources for Vocabulary Pipeline V2

These modules provide authoritative data from external sources:
- CC-CEDICT: Chinese translations
- EVP/CEFR: Difficulty levels (A1-C2)
- Spelling: British → American normalization
"""

from .cc_cedict import get_translations, CCCedict
from .evp_cefr import get_cefr_level, EVPCefr
from .spelling import normalize_spelling, SpellingNormalizer

__all__ = [
    'get_translations', 'CCCedict',
    'get_cefr_level', 'EVPCefr',
    'normalize_spelling', 'SpellingNormalizer'
]

