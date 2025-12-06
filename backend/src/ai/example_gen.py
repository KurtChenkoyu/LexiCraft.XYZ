"""
Example Generator V2

Generates example sentences for vocabulary learning with:
- Balanced context (60% universal, 40% Taiwan-specific)
- Two Chinese versions: translation + explanation
- Connection pathway logic for non-literal meanings

Usage:
    from src.ai.example_gen import generate_example
    
    result = generate_example(
        word="break",
        definition="a fortunate opportunity",
        pos="n"
    )
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass
from .base import BaseAIModule, LLMConfig


@dataclass
class GeneratedExample:
    """A generated example sentence with translations."""
    example_en: str
    example_zh_translation: str  # Direct/literal translation
    example_zh_explanation: str  # Explanation with nuances and connection pathways
    context: str  # 'universal', 'taiwan', 'school', 'work', 'social'
    word_highlighted: bool


class ExampleGenerator(BaseAIModule):
    """
    Generates example sentences for vocabulary learning.
    
    V2 Changes:
    - Balanced context (not overly Taiwan-centric)
    - Two Chinese versions (translation + explanation)
    - Connection pathway logic for idioms/metaphors
    """
    
    def get_prompt_template(self) -> str:
        return """Create an example sentence for a Taiwan B1/B2 vocabulary app.

Word: {word}
Meaning: {definition}
Part of Speech: {pos}

REQUIREMENTS:
1. LENGTH: 8-15 words (ideal: 10-12)
2. CLARITY: The meaning of "{word}" must be OBVIOUS from context
3. TONE: Natural, conversational (not formal/textbook)
4. GRAMMAR: Common patterns appropriate for B1/B2 level

CONTEXT BALANCE (IMPORTANT):
- Prefer UNIVERSAL contexts that any student can relate to
- Taiwan-specific references are OK but NOT forced

UNIVERSAL CONTEXTS (prefer these ~60%):
- School: studying, exams, homework, projects, classes, teachers
- Daily life: shopping, eating, weather, transport, health
- Social: friends, messaging, weekends, hobbies, plans
- Work: jobs, tasks, meetings, colleagues
- Technology: phones, apps, internet, social media

TAIWAN CONTEXTS (use naturally ~40%, don't force):
- OK: MRT, convenience stores, bubble tea (if natural)
- AVOID: Forcing 學測, 夜市 into every example
- NO code-switching: Don't mix Chinese words in English

GOOD EXAMPLES:
✅ "Be careful not to drop your phone!" (universal)
✅ "I stayed up late studying for the exam." (universal)
✅ "The train was really crowded this morning." (natural local reference)

BAD EXAMPLES:
❌ "I forgot about the 學測 when I saw the star." (forced + code-switch)
❌ "He dropped his phone on the 捷運!" (code-switch)
❌ "After 補習班, I drank 珍珠奶茶." (too many forced references)

CHINESE VERSIONS (provide TWO):

1. TRANSLATION (example_zh_translation):
   - Direct translation showing English structure
   - Helps learners see how English expresses the idea

2. EXPLANATION (example_zh_explanation):
   - Explains nuances, cultural context, or hidden meanings
   - For non-literal/idiomatic uses of "{word}":
     * Show the CONNECTION PATHWAY: literal → metaphor → meaning
     * Structure: literal meaning → how it extends → final meaning
     * Example for "break" (opportunity): 「break」原本是打破、中斷的意思，這裡引申為打破困境獲得的好機會。
   - AVOID "不是...而是" (creates disconnection)
   - Vary explanation style (don't always use "想像一下")

Return a JSON object:
{{
    "example_en": "Natural example with {word}.",
    "example_zh_translation": "直接翻譯（顯示英文結構）",
    "example_zh_explanation": "解釋說明（包含nuances和連接路徑）",
    "context": "universal/taiwan/school/work/social"
}}

CRITICAL:
- The word "{word}" MUST appear in the example
- Both Chinese versions are REQUIRED
- Make meaning crystal clear from context
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
    
    def create_example(
        self,
        word: str,
        definition: str,
        pos: str = 'n'
    ) -> GeneratedExample:
        """
        Generate an example sentence with translations.
        
        Args:
            word: The target word
            definition: The simplified definition
            pos: Part of speech
            
        Returns:
            GeneratedExample with English and Chinese sentences
        """
        pos_full = self.POS_MAP.get(pos, pos)
        
        prompt = self.format_prompt(
            word=word,
            definition=definition,
            pos=pos_full
        )
        
        try:
            result = self.generate_json(prompt)
            
            # Handle various response formats
            if isinstance(result, list) and result:
                result = result[0]
            elif 'items' in result and isinstance(result['items'], list):
                result = result['items'][0]
            elif 'examples' in result and isinstance(result['examples'], list):
                result = result['examples'][0]
            
            example_en = result.get('example_en', '')
            example_zh_translation = result.get('example_zh_translation', result.get('example_zh', ''))
            example_zh_explanation = result.get('example_zh_explanation', '')
            context = result.get('context', 'universal')
            
            # Validate the example contains the word
            word_in_example = word.lower() in example_en.lower()
            
            if not word_in_example:
                print(f"⚠️ Word '{word}' not in example, attempting retry...")
                # Simple retry with explicit instruction
                retry_prompt = f"""The example sentence MUST contain the word "{word}".
                
Previous example was missing the word. Generate a new one.

Word: {word}
Meaning: {definition}

Return JSON: {{"example_en": "...", "example_zh_translation": "...", "example_zh_explanation": "...", "context": "..."}}"""
                
                retry_result = self.generate_json(retry_prompt)
                if isinstance(retry_result, list):
                    retry_result = retry_result[0]
                
                example_en = retry_result.get('example_en', example_en)
                example_zh_translation = retry_result.get('example_zh_translation', example_zh_translation)
                example_zh_explanation = retry_result.get('example_zh_explanation', example_zh_explanation)
                word_in_example = word.lower() in example_en.lower()
            
            return GeneratedExample(
                example_en=example_en,
                example_zh_translation=example_zh_translation,
                example_zh_explanation=example_zh_explanation,
                context=context,
                word_highlighted=word_in_example
            )
            
        except Exception as e:
            print(f"⚠️ Example generation failed for '{word}': {e}")
            return GeneratedExample(
                example_en=f"This is an example with {word}.",
                example_zh_translation=f"這是一個使用{word}的例子。",
                example_zh_explanation='',
                context='fallback',
                word_highlighted=True
            )


# Singleton instance
_generator = None


def get_generator(config: LLMConfig = None) -> ExampleGenerator:
    """Get or create the example generator instance."""
    global _generator
    if _generator is None:
        _generator = ExampleGenerator(config)
    return _generator


def generate_example(
    word: str,
    definition: str,
    pos: str = 'n'
) -> GeneratedExample:
    """
    Generate an example sentence with translations.
    
    Args:
        word: The target word
        definition: The definition
        pos: Part of speech
        
    Returns:
        GeneratedExample object
    """
    gen = get_generator()
    return gen.create_example(word, definition, pos)


if __name__ == '__main__':
    print("\n=== Example Generator V2 Test ===\n")
    
    test_cases = [
        ('drop', 'to let something fall from your hand', 'v'),
        ('bank', 'a financial institution where you keep money', 'n'),
        ('break', 'a fortunate opportunity', 'n'),
        ('popular', 'liked by many people', 'a'),
        ('run', 'to move fast using your legs', 'v'),
    ]
    
    for word, definition, pos in test_cases:
        print(f"Word: {word} ({pos})")
        print(f"Definition: {definition}")
        
        result = generate_example(word, definition, pos)
        
        print(f"Example EN: {result.example_en}")
        print(f"Translation: {result.example_zh_translation}")
        print(f"Explanation: {result.example_zh_explanation}")
        print(f"Context: {result.context}")
        print(f"Word present: {result.word_highlighted}")
        print()
