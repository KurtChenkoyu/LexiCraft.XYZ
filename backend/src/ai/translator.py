"""
Translation Validator and Generator

Validates or generates Chinese translations for vocabulary learning.
Uses multiple sources: OMW (authoritative), CC-CEDICT (hints), AI (generation).

V2 Changes:
- Uses unified chinese_translation source
- Generates explanations (definition_zh_explanation)
- Stricter validation for Taiwan Traditional Chinese

Usage:
    from src.ai.translator import generate_translation
    
    result = generate_translation(
        word="bank",
        definition="a financial institution",
        sense_id="bank.n.01",
        pos="n"
    )
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from .base import BaseAIModule, LLMConfig

# Import the unified Chinese translation source
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from src.data_sources.chinese_translation import get_chinese_translation, ChineseTranslation


@dataclass
class TranslationResult:
    """Result of translation generation."""
    translation: str  # Concise translation (2-6 characters)
    explanation: str  # Explanation for understanding
    source: str  # 'omw', 'cc-cedict', 'ai'
    confidence: str  # 'high', 'medium', 'low'
    pinyin: Optional[str] = None


class TranslationGenerator(BaseAIModule):
    """
    Generates and validates Chinese translations.
    
    Uses authoritative sources first, then AI for generation/explanation.
    """
    
    POS_MAP = {
        'n': 'noun',
        'v': 'verb',
        'a': 'adjective',
        'adj': 'adjective',
        'r': 'adverb',
        'adv': 'adverb',
        's': 'adjective',
    }
    
    def get_prompt_template(self) -> str:
        return """You are a Chinese translation expert for English vocabulary learning apps in Taiwan.

Target Word: {word}
Part of Speech: {pos}
English Definition: {definition}

{authority_section}

YOUR TASK:
{task_instruction}

TRANSLATION REQUIREMENTS:
1. MATCH THE MEANING: The translation must match the SPECIFIC definition given.
2. TAIWAN MANDARIN: Use Taiwan Traditional Chinese (繁體中文), natural Taiwan usage.
3. APPROPRIATE LENGTH: 2-6 characters typically (concrete nouns can be shorter).
4. LEARNER-FRIENDLY: Common vocabulary that B1/B2 learners would recognize.

EXPLANATION REQUIREMENTS (CRITICAL):
Write an explanation that helps learners UNDERSTAND the meaning deeply.

For LITERAL meanings:
- Simply explain what it means in natural Chinese
- Example: 「銀行」是存放金錢和處理財務的機構。

For NON-LITERAL/EXTENDED meanings (idioms, metaphors):
- Show the CONNECTION PATHWAY: literal → metaphor → meaning
- Structure: Start with literal meaning → show extension → arrive at current meaning
- Example: 「break」原本是打破、中斷的意思。想像你被困住了，突然出現一個缺口讓你通過，這就是你的機會。

EXPLANATION STYLE (vary these):
- Direct: "指的是..." (refers to...)
- Pathway: "原本的意思是...，引申為..." (original meaning...extends to...)
- Context: "在這個情境下..." (in this context...)

AVOID in explanations:
- ❌ "不是...而是" (not...but rather) - creates disconnection
- ❌ "字面上...但實際上" (literally...but actually) - creates disconnection
- ❌ Starting every explanation with "想像一下" - too repetitive

Return a JSON object:
{{
    "translation": "繁體中文翻譯 (2-6 characters)",
    "explanation": "幫助理解的中文說明",
    "confidence": "high/medium/low"
}}
"""
    
    def create_translation(
        self,
        word: str,
        definition: str,
        sense_id: str = None,
        pos: str = 'n'
    ) -> TranslationResult:
        """
        Generate Chinese translation and explanation.
        
        Uses authoritative sources (OMW, CC-CEDICT) first, then AI.
        Always generates explanation with AI.
        """
        pos_full = self.POS_MAP.get(pos, pos)
        
        # 1. Get authoritative translation if available
        auth_result = get_chinese_translation(word, sense_id, definition, pos)
        
        if auth_result.source in ['omw', 'cc-cedict'] and auth_result.translation:
            # Have authoritative translation - just generate explanation
            authority_section = f"""AUTHORITATIVE TRANSLATION (from {auth_result.source.upper()}):
Translation: {auth_result.translation}
Alternatives: {', '.join(auth_result.alternatives[:3]) if auth_result.alternatives else 'None'}

This translation is from a trusted source. Use it unless it's clearly wrong for this meaning."""
            
            task_instruction = f"""1. VERIFY the translation "{auth_result.translation}" matches the meaning "{definition}".
   - If it matches: Use it and set confidence to "high"
   - If it doesn't match well: Choose from alternatives or generate a better one
2. GENERATE an explanation that helps learners understand this meaning."""
        else:
            # No authoritative translation - generate with AI
            if auth_result.alternatives:
                authority_section = f"""REFERENCE OPTIONS (from CC-CEDICT, use as hints only):
{', '.join(auth_result.alternatives[:5])}

These are possible translations but may not match this specific meaning."""
            else:
                authority_section = "No authoritative translation found. Generate an appropriate one."
            
            task_instruction = """1. GENERATE the best Traditional Chinese translation for this specific meaning.
2. GENERATE an explanation that helps learners understand this meaning."""
        
        prompt = self.format_prompt(
            word=word,
            pos=pos_full,
            definition=definition,
            authority_section=authority_section,
            task_instruction=task_instruction
        )
        
        try:
            result = self.generate_json(prompt)
            
            translation = result.get('translation', auth_result.translation or '')
            explanation = result.get('explanation', '')
            confidence = result.get('confidence', 'medium')
            
            # Determine final source
            if auth_result.source in ['omw', 'cc-cedict'] and translation == auth_result.translation:
                source = auth_result.source
            else:
                source = 'ai'
            
            return TranslationResult(
                translation=translation,
                explanation=explanation,
                source=source,
                confidence=confidence
            )
            
        except Exception as e:
            print(f"⚠️ Translation generation failed for '{word}': {e}")
            # Return authoritative translation if available
            if auth_result.translation:
                return TranslationResult(
                    translation=auth_result.translation,
                    explanation='',
                    source=auth_result.source,
                    confidence='low'
                )
            return TranslationResult(
                translation='',
                explanation='',
                source='none',
                confidence='low'
            )


# Singleton instance
_generator = None


def get_generator(config: LLMConfig = None) -> TranslationGenerator:
    """Get or create the translation generator instance."""
    global _generator
    if _generator is None:
        _generator = TranslationGenerator(config)
    return _generator


def generate_translation(
    word: str,
    definition: str,
    sense_id: str = None,
    pos: str = 'n'
) -> TranslationResult:
    """
    Generate Chinese translation and explanation.
    
    Args:
        word: English word
        definition: English definition
        sense_id: WordNet sense ID (optional but recommended)
        pos: Part of speech
        
    Returns:
        TranslationResult with translation, explanation, source, confidence
    """
    gen = get_generator()
    return gen.create_translation(word, definition, sense_id, pos)


# Legacy function for backward compatibility
def validate_translation(
    word: str,
    definition: str,
    pos: str = 'n',
    cc_cedict_translation: Optional[str] = None,
    cc_cedict_options: Optional[List[str]] = None
) -> TranslationResult:
    """Legacy function - redirects to generate_translation."""
    return generate_translation(word, definition, None, pos)


if __name__ == '__main__':
    import warnings
    warnings.filterwarnings('ignore')
    
    print("\n=== Translation Generator Test ===\n")
    
    test_cases = [
        ('bank', 'depository_financial_institution.n.01', 'a financial institution where you keep money', 'n'),
        ('popular', 'popular.a.01', 'liked by many people', 'a'),
        ('break', 'break.n.02', 'a fortunate opportunity', 'n'),
        ('run', 'run.v.01', 'move fast using your legs', 'v'),
        ('therefore', 'therefore.r.01', 'as a consequence; for that reason', 'r'),
    ]
    
    for word, sense_id, definition, pos in test_cases:
        print(f"Word: {word} ({sense_id})")
        print(f"Definition: {definition}")
        
        result = generate_translation(word, definition, sense_id, pos)
        
        print(f"Translation: {result.translation} (source: {result.source})")
        print(f"Explanation: {result.explanation}")
        print(f"Confidence: {result.confidence}")
        print()
