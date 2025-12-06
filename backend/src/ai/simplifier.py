"""
Definition Simplifier

Converts academic WordNet definitions into B1/B2 level definitions
that are clear, concise, and appropriate for Taiwan EFL learners.

Usage:
    from src.ai.simplifier import simplify_definition
    
    simple = simplify_definition(
        word="break",
        definition="an act of breaking or a result of breaking",
        pos="n"
    )
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass
from .base import BaseAIModule, LLMConfig


@dataclass
class SimplifiedDefinition:
    """A simplified definition."""
    definition_en: str
    word_type: str  # "noun", "verb", "adjective", etc.
    is_simplified: bool
    original: str


class DefinitionSimplifier(BaseAIModule):
    """
    Simplifies WordNet definitions for B1/B2 learners.
    
    Transforms academic definitions like:
    "terminate the employment of" → "to fire someone from their job"
    
    Rules:
    - Maximum 15 words
    - Use only common vocabulary
    - Start with word type (noun/verb/adj) when helpful
    - Be clear and specific
    """
    
    def get_prompt_template(self) -> str:
        return """Rewrite this dictionary definition for a B1/B2 English learner.

Word: {word}
Part of Speech: {pos_full}
Original Definition: {definition}

REQUIREMENTS:
1. Maximum 15 words
2. Use only common, everyday vocabulary
3. Be clear and specific - the meaning should be immediately obvious
4. Don't use the word "{word}" in the definition (unless unavoidable)
5. If it's a verb, you may start with "to" (e.g., "to make something happen")
6. Avoid academic or technical language

EXAMPLES of good simplifications:
- "terminate the employment of" → "to fire someone from their job"
- "a sum of money paid regularly" → "regular payment of money"
- "the act of moving something from one place to another" → "moving something to a different place"
- "cause to move by pulling" → "to pull something so it moves"

Return ONLY the simplified definition as plain text, nothing else.
Do not include quotes, explanations, or formatting.
"""
    
    POS_MAP = {
        'n': 'noun',
        'v': 'verb',
        'a': 'adjective',
        'r': 'adverb',
        's': 'adjective (satellite)',
    }
    
    def simplify(
        self,
        word: str,
        definition: str,
        pos: str = 'n'
    ) -> SimplifiedDefinition:
        """
        Simplify a definition for B1/B2 learners.
        
        Args:
            word: The target word
            definition: Original WordNet definition
            pos: Part of speech ('n', 'v', 'a', 'r', 's')
            
        Returns:
            SimplifiedDefinition with the simplified text
        """
        # Short definitions may not need simplification
        if len(definition.split()) <= 8 and not self._has_complex_vocab(definition):
            return SimplifiedDefinition(
                definition_en=definition,
                word_type=self.POS_MAP.get(pos, 'word'),
                is_simplified=False,
                original=definition
            )
        
        pos_full = self.POS_MAP.get(pos, 'word')
        
        prompt = self.format_prompt(
            word=word,
            pos_full=pos_full,
            definition=definition
        )
        
        try:
            # Use non-JSON mode for plain text response
            result = self.generate(prompt, json_mode=False)
            
            # Clean up the response
            simplified = result.strip()
            
            # Remove quotes if present
            if simplified.startswith('"') and simplified.endswith('"'):
                simplified = simplified[1:-1]
            if simplified.startswith("'") and simplified.endswith("'"):
                simplified = simplified[1:-1]
            
            # Validate length
            if len(simplified.split()) > 20:
                # Too long, take first 15 words
                words = simplified.split()[:15]
                simplified = ' '.join(words)
                if not simplified.endswith('.'):
                    simplified += '...'
            
            return SimplifiedDefinition(
                definition_en=simplified,
                word_type=pos_full,
                is_simplified=True,
                original=definition
            )
            
        except Exception as e:
            print(f"⚠️ Simplification failed for '{word}': {e}")
            # Return original if simplification fails
            return SimplifiedDefinition(
                definition_en=definition,
                word_type=pos_full,
                is_simplified=False,
                original=definition
            )
    
    def _has_complex_vocab(self, text: str) -> bool:
        """Check if text contains complex vocabulary."""
        complex_indicators = [
            'terminate', 'pursuant', 'thereof', 'whereby', 'hitherto',
            'aforementioned', 'notwithstanding', 'pertaining', 'cognate',
            'constitute', 'comprising', 'encompasses', 'denoting',
            'characterized by', 'indicative of', 'relating to',
        ]
        text_lower = text.lower()
        return any(indicator in text_lower for indicator in complex_indicators)


# Singleton instance
_simplifier = None


def get_simplifier(config: LLMConfig = None) -> DefinitionSimplifier:
    """Get or create the simplifier instance."""
    global _simplifier
    if _simplifier is None:
        _simplifier = DefinitionSimplifier(config)
    return _simplifier


def simplify_definition(
    word: str,
    definition: str,
    pos: str = 'n'
) -> str:
    """
    Simplify a definition for B1/B2 learners.
    
    Args:
        word: The target word
        definition: Original definition
        pos: Part of speech
        
    Returns:
        Simplified definition string
        
    Example:
        >>> simplify_definition("fire", "terminate the employment of", "v")
        'to fire someone from their job'
    """
    result = get_simplifier().simplify(word, definition, pos)
    return result.definition_en


if __name__ == '__main__':
    print("\n--- Definition Simplifier Test ---\n")
    
    test_cases = [
        ('break', 'an act of breaking or a result of breaking', 'n'),
        ('drop', 'let fall to the ground', 'v'),
        ('run', 'move fast by using one\'s feet, with one foot off the ground at any given time', 'v'),
        ('bank', 'a financial institution that accepts deposits and channels the money into lending activities', 'n'),
        ('terminate', 'bring to an end or halt', 'v'),
    ]
    
    for word, definition, pos in test_cases:
        result = get_simplifier().simplify(word, definition, pos)
        print(f"Word: {word} ({result.word_type})")
        print(f"  Original: {result.original}")
        print(f"  Simplified: {result.definition_en}")
        print(f"  Changed: {'Yes' if result.is_simplified else 'No'}")
        print()

