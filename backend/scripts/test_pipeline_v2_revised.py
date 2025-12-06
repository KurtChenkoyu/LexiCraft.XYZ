#!/usr/bin/env python3
"""
Test Script for Pipeline V2 Revised Prompts

Tests the updated modules:
1. Chinese Translation (OMW + CC-CEDICT + improved scoring)
2. Translation Generator (with explanations)
3. Example Generator (balanced context)

Run this before the full pipeline to verify quality.
"""

import sys
import warnings
from pathlib import Path

# Suppress warnings for cleaner output
warnings.filterwarnings('ignore')

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from nltk.corpus import wordnet as wn
import nltk
nltk.download('wordnet', quiet=True)
nltk.download('omw-1.4', quiet=True)

from src.data_sources.chinese_translation import get_chinese_translation
from src.ai.translator import generate_translation
from src.ai.example_gen import generate_example
from src.ai.simplifier import simplify_definition
from src.ai.sense_selector import select_senses


def print_section(title):
    print(f"\n{'='*70}")
    print(f" {title}")
    print(f"{'='*70}\n")


def test_chinese_source():
    """Test the Chinese translation source (OMW + CC-CEDICT)."""
    print_section("1. Chinese Translation Source Test")
    
    test_cases = [
        ('bank', 'depository_financial_institution.n.01', 'financial institution', 'n'),
        ('popular', 'popular.a.01', 'liked by many people', 'a'),
        ('therefore', 'therefore.r.01', 'as a consequence', 'r'),
        ('month', 'calendar_month.n.01', 'time unit of 30 days', 'n'),
        ('star', 'star.n.03', 'celestial body', 'n'),
        ('break', 'break.n.02', 'a fortunate opportunity', 'n'),
    ]
    
    results = []
    for word, sense_id, definition, pos in test_cases:
        result = get_chinese_translation(word, sense_id, definition, pos)
        status = '✅' if result.translation and result.source != 'none' else '⚠️'
        print(f"{status} {word}: {result.translation or '(none)'}")
        print(f"   Source: {result.source}, Confidence: {result.confidence}")
        if result.alternatives:
            print(f"   Alternatives: {result.alternatives[:3]}")
        results.append((word, result.translation, result.source))
        print()
    
    return results


def test_translation_generator():
    """Test the translation generator with explanations."""
    print_section("2. Translation Generator Test (with Explanations)")
    
    test_cases = [
        ('bank', 'depository_financial_institution.n.01', 'a financial institution where you keep money', 'n'),
        ('break', 'break.n.02', 'a fortunate opportunity', 'n'),
        ('popular', 'popular.a.01', 'liked by many people', 'a'),
        ('run', 'run.v.01', 'move fast using your legs', 'v'),
    ]
    
    results = []
    for word, sense_id, definition, pos in test_cases:
        print(f"Word: {word} ({pos})")
        print(f"Definition: {definition}")
        
        result = generate_translation(word, definition, sense_id, pos)
        
        print(f"Translation: {result.translation}")
        print(f"Source: {result.source}")
        print(f"Explanation: {result.explanation}")
        print()
        
        results.append({
            'word': word,
            'translation': result.translation,
            'explanation': result.explanation,
            'source': result.source
        })
    
    return results


def test_example_generator():
    """Test the example generator with balanced context."""
    print_section("3. Example Generator Test (Balanced Context)")
    
    test_cases = [
        ('drop', 'to let something fall', 'v'),
        ('bank', 'a financial institution', 'n'),
        ('break', 'a fortunate opportunity', 'n'),
        ('popular', 'liked by many people', 'a'),
        ('therefore', 'as a consequence', 'r'),
    ]
    
    results = []
    taiwan_count = 0
    universal_count = 0
    
    for word, definition, pos in test_cases:
        print(f"Word: {word}")
        
        result = generate_example(word, definition, pos)
        
        print(f"Example EN: {result.example_en}")
        print(f"Translation: {result.example_zh_translation}")
        print(f"Explanation: {result.example_zh_explanation[:100]}..." if len(result.example_zh_explanation) > 100 else f"Explanation: {result.example_zh_explanation}")
        print(f"Context: {result.context}")
        print(f"Word present: {'✅' if result.word_highlighted else '❌'}")
        print()
        
        if result.context in ['taiwan']:
            taiwan_count += 1
        else:
            universal_count += 1
        
        results.append({
            'word': word,
            'example_en': result.example_en,
            'context': result.context,
            'has_word': result.word_highlighted
        })
    
    print(f"Context balance: Universal={universal_count}, Taiwan={taiwan_count}")
    
    return results


def test_full_pipeline_sample():
    """Test a full enrichment flow for one word."""
    print_section("4. Full Pipeline Sample: 'break'")
    
    word = 'break'
    
    # Get WordNet senses
    synsets = wn.synsets(word)[:5]
    print(f"WordNet senses for '{word}':")
    senses_data = []
    for syn in synsets:
        sense_data = {
            'id': syn.name(),  # sense_selector expects 'id'
            'definition': syn.definition(),
            'pos': syn.pos(),
        }
        senses_data.append(sense_data)
        print(f"  - {syn.name()}: {syn.definition()[:60]}...")
    print()
    
    # Select best senses
    print("Selecting best senses for B1/B2...")
    selected = select_senses(word, senses_data, max_senses=2)
    
    for i, sense in enumerate(selected, 1):
        print(f"\n--- Sense {i}: {sense.sense_id} ---")
        print(f"Definition: {sense.definition}")
        print(f"Priority: {sense.priority}, Reason: {sense.reason}")
        
        # Simplify definition
        simplified = simplify_definition(word, sense.definition, sense.pos)
        print(f"Simplified: {simplified}")
        
        # Get translation + explanation
        trans_result = generate_translation(word, simplified, sense.sense_id, sense.pos)
        print(f"Translation: {trans_result.translation} (source: {trans_result.source})")
        print(f"Explanation: {trans_result.explanation}")
        
        # Generate example
        example_result = generate_example(word, simplified, sense.pos)
        print(f"Example EN: {example_result.example_en}")
        print(f"Example ZH: {example_result.example_zh_translation}")
        print(f"Context: {example_result.context}")


def main():
    print("\n" + "="*70)
    print(" PIPELINE V2 REVISED - QUALITY TEST")
    print("="*70)
    
    # Test 1: Chinese source
    test_chinese_source()
    
    # Test 2: Translation generator
    test_translation_generator()
    
    # Test 3: Example generator
    test_example_generator()
    
    # Test 4: Full pipeline sample
    test_full_pipeline_sample()
    
    print_section("TEST COMPLETE")
    print("Review the output above to verify quality before running full pipeline.")
    print("\nKey things to check:")
    print("  1. Chinese translations are correct (not 糠, 愛玉冰, etc.)")
    print("  2. Explanations show connection pathways (not '不是...而是')")
    print("  3. Examples are not overly Taiwan-centric (no code-switching)")
    print("  4. Context balance is reasonable (60% universal, 40% Taiwan)")


if __name__ == '__main__':
    main()

