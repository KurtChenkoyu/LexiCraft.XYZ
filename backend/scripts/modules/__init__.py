"""
Stage 3 Enrichment Modules

This package contains all the modules for the complete dictionary enrichment pipeline.
"""

from .vocabulary_loader import VocabularyLoader
from .deep_wordnet import DeepWordNetExtractor
from .free_dict_client import FreeDictAPIClient
from .collocation_cascade import CollocationCascade, NGSLPhraseLoader, DatamuseAPIClient
from .merger import DataMerger

__all__ = [
    'VocabularyLoader',
    'DeepWordNetExtractor',
    'FreeDictAPIClient',
    'CollocationCascade',
    'NGSLPhraseLoader',
    'DatamuseAPIClient',
    'DataMerger',
]

