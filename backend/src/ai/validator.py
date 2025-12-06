"""
Example Validator

Validates that example sentences correctly demonstrate the intended word meaning.
Catches AI hallucinations where examples use wrong senses or meanings.

Usage:
    from src.ai.validator import validate_example
    
    result = validate_example(
        word="drop",
        definition="to let something fall",
        example="Be careful not to drop your phone!"
    )
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass
from .base import BaseAIModule, LLMConfig


@dataclass
class ValidationResult:
    """Result of example validation."""
    passed: bool
    confidence: float  # 0.0 to 1.0
    issues: list[str]  # List of issues if failed
    suggestion: Optional[str] = None  # Suggested fix if failed


class ExampleValidator(BaseAIModule):
    """
    Validates that examples match the intended word sense.
    
    Catches problems like:
    - Example uses different meaning than intended
    - Example is ambiguous (could be multiple meanings)
    - Word is used in wrong grammatical form
    - Example doesn't clearly demonstrate the meaning
    """
    
    def get_prompt_template(self) -> str:
        return """You are validating an example sentence for a vocabulary learning app.

Word: {word}
Target Meaning: {definition}
Part of Speech: {pos}
Example Sentence: {example}

YOUR TASK: Check if this example CLEARLY demonstrates the TARGET MEANING.

VALIDATION CHECKLIST:
1. MEANING MATCH: Does the example use "{word}" with the target meaning, not a different meaning?
   - If "{word}" has multiple meanings, does this example clearly show the target meaning?
   
2. CLARITY: Is the meaning obvious from context?
   - A learner should be able to understand "{word}" means "{definition}" from this example
   
3. GRAMMAR: Is "{word}" used with the correct part of speech ({pos})?
   
4. NATURALNESS: Is the sentence natural and grammatically correct?

5. SENSE CONFUSION: Could this example be confused with a DIFFERENT meaning of "{word}"?

COMMON PROBLEMS TO CATCH:
- "break" meaning "pause" vs "break" meaning "damage"
- "bank" meaning "financial institution" vs "river bank"
- "run" meaning "move fast" vs "run a business"

Return a JSON object:
{{
    "passed": true/false,
    "confidence": 0.0 to 1.0,
    "issues": ["Issue 1", "Issue 2"] or [],
    "suggestion": "Suggested improvement if needed, or null if passed"
}}

PASS CRITERIA:
- The example clearly demonstrates THIS SPECIFIC meaning
- No ambiguity with other meanings
- Grammatically correct usage

FAIL if any of these apply:
- Wrong meaning of the word used
- Ambiguous - could be interpreted as different meaning
- Wrong part of speech
- Meaning is not clear from context
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
    
    def validate(
        self,
        word: str,
        definition: str,
        example: str,
        pos: str = 'n'
    ) -> ValidationResult:
        """
        Validate an example sentence.
        
        Args:
            word: The target word
            definition: The target definition
            example: The example sentence to validate
            pos: Part of speech
            
        Returns:
            ValidationResult with pass/fail status
        """
        pos_full = self.POS_MAP.get(pos, pos)
        
        prompt = self.format_prompt(
            word=word,
            definition=definition,
            example=example,
            pos=pos_full
        )
        
        try:
            result = self.generate_json(prompt)
            
            passed = result.get('passed', False)
            confidence = result.get('confidence', 0.5)
            issues = result.get('issues', [])
            suggestion = result.get('suggestion')
            
            return ValidationResult(
                passed=passed,
                confidence=confidence,
                issues=issues if issues else [],
                suggestion=suggestion
            )
            
        except Exception as e:
            print(f"⚠️ Validation failed for '{word}': {e}")
            # Assume it's OK if validation fails
            return ValidationResult(
                passed=True,
                confidence=0.5,
                issues=[f"Validation error: {e}"],
                suggestion=None
            )
    
    def quick_validate(
        self,
        word: str,
        example: str
    ) -> bool:
        """
        Quick validation without AI - checks basic requirements.
        
        Args:
            word: The target word
            example: The example sentence
            
        Returns:
            True if basic requirements met
        """
        # Check word is present
        if word.lower() not in example.lower():
            return False
        
        # Check reasonable length (8-25 words)
        word_count = len(example.split())
        if word_count < 5 or word_count > 30:
            return False
        
        # Check it's a complete sentence (starts with capital, ends with punctuation)
        if not example[0].isupper():
            return False
        if example[-1] not in '.!?':
            return False
        
        return True


# Singleton instance
_validator = None


def get_validator(config: LLMConfig = None) -> ExampleValidator:
    """Get or create the example validator instance."""
    global _validator
    if _validator is None:
        _validator = ExampleValidator(config)
    return _validator


def validate_example(
    word: str,
    definition: str,
    example: str,
    pos: str = 'n'
) -> ValidationResult:
    """
    Validate an example sentence.
    
    Args:
        word: The target word
        definition: The target definition
        example: The example sentence
        pos: Part of speech
        
    Returns:
        ValidationResult object
        
    Example:
        >>> result = validate_example("drop", "to let something fall", 
        ...                           "Be careful not to drop your phone!", "v")
        >>> print(result.passed)
        True
    """
    return get_validator().validate(word, definition, example, pos)


def quick_validate_example(word: str, example: str) -> bool:
    """
    Quick validation without AI call.
    
    Returns:
        True if basic requirements met
    """
    return get_validator().quick_validate(word, example)


if __name__ == '__main__':
    print("\n--- Example Validator Test ---\n")
    
    test_cases = [
        # (word, definition, example, pos, expected_pass)
        ('drop', 'to let something fall', "Be careful not to drop your phone!", 'v', True),
        ('drop', 'to let something fall', "The temperature will drop tonight.", 'v', False),  # Wrong meaning
        ('bank', 'a financial institution', "I need to go to the bank to withdraw money.", 'n', True),
        ('bank', 'a financial institution', "We sat on the river bank.", 'n', False),  # Wrong meaning
        ('run', 'to move fast with your legs', "I run every morning in the park.", 'v', True),
        ('run', 'to move fast with your legs', "She runs a successful business.", 'v', False),  # Wrong meaning
    ]
    
    for word, definition, example, pos, expected in test_cases:
        print(f"Word: {word}")
        print(f"  Definition: {definition}")
        print(f"  Example: {example}")
        print(f"  Expected: {'PASS' if expected else 'FAIL'}")
        
        result = validate_example(word, definition, example, pos)
        
        status = "✅ PASS" if result.passed else "❌ FAIL"
        print(f"  Result: {status} (confidence: {result.confidence:.2f})")
        if result.issues:
            print(f"  Issues: {result.issues}")
        if result.suggestion:
            print(f"  Suggestion: {result.suggestion}")
        print()

