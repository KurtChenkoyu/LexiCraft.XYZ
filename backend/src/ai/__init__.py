"""
AI Pipeline Modules for Vocabulary Enrichment V2

These modules use LLMs (primarily Gemini) to:
- Select the most useful word senses
- Simplify definitions for B1/B2 learners
- Validate Chinese translations
- Generate Taiwan-context examples
- Validate examples match intended senses
"""

from .sense_selector import SenseSelector, select_senses
from .simplifier import DefinitionSimplifier, simplify_definition
from .translator import TranslationGenerator, generate_translation, validate_translation
from .example_gen import ExampleGenerator, generate_example
from .validator import ExampleValidator, validate_example

__all__ = [
    'SenseSelector', 'select_senses',
    'DefinitionSimplifier', 'simplify_definition',
    'TranslationGenerator', 'generate_translation', 'validate_translation',
    'ExampleGenerator', 'generate_example',
    'ExampleValidator', 'validate_example',
]

