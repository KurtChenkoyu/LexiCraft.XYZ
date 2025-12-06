#!/usr/bin/env python3
"""
Sample Vocabulary Quality Checker

Extracts diverse samples from the generated vocabulary.json for quality review.
Shows examples of different types: common words, validated, failed, different POS, etc.
"""

import json
import random
from pathlib import Path
from collections import defaultdict


def load_vocabulary():
    """Load the generated vocabulary.json"""
    vocab_path = Path(__file__).parent.parent / 'data' / 'vocabulary.json'
    
    if not vocab_path.exists():
        print(f"❌ Vocabulary file not found: {vocab_path}")
        return None
    
    with open(vocab_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def sample_vocabulary(data, num_samples=20):
    """Extract diverse samples for quality review."""
    senses = list(data['senses'].items())
    
    if not senses:
        print("No senses found in vocabulary.json")
        return []
    
    # Categorize senses
    validated = [s for s in senses if s[1].get('validated', False)]
    failed = [s for s in senses if not s[1].get('validated', True)]
    
    # Group by POS
    by_pos = defaultdict(list)
    for sense_id, sense in senses:
        by_pos[sense.get('pos', 'unknown')].append((sense_id, sense))
    
    # Group by CEFR
    by_cefr = defaultdict(list)
    for sense_id, sense in senses:
        by_cefr[sense.get('cefr', 'unknown')].append((sense_id, sense))
    
    # Group by word frequency (common vs rare)
    common_words = []
    rare_words = []
    for sense_id, sense in senses:
        word = sense.get('word', '')
        freq_rank = data['words'].get(word, {}).get('frequency_rank', 9999)
        if freq_rank < 1000:
            common_words.append((sense_id, sense))
        else:
            rare_words.append((sense_id, sense))
    
    samples = []
    
    # 1. Validated examples (good quality)
    if validated:
        samples.append(("✅ VALIDATED (Good Quality)", random.sample(validated, min(3, len(validated)))))
    
    # 2. Failed validation (needs review)
    if failed:
        samples.append(("❌ FAILED VALIDATION (Needs Review)", random.sample(failed, min(3, len(failed)))))
    
    # 3. Common words (high frequency)
    if common_words:
        samples.append(("📊 COMMON WORDS (Freq < 1000)", random.sample(common_words, min(3, len(common_words)))))
    
    # 4. Rare words (low frequency)
    if rare_words:
        samples.append(("📊 RARE WORDS (Freq >= 1000)", random.sample(rare_words, min(2, len(rare_words)))))
    
    # 5. Different POS
    for pos, pos_senses in list(by_pos.items())[:4]:
        if pos_senses:
            samples.append((f"🔤 {pos.upper()} Examples", random.sample(pos_senses, min(2, len(pos_senses)))))
    
    # 6. Different CEFR levels
    for cefr in ['A1', 'A2', 'B1', 'B2']:
        if cefr in by_cefr and by_cefr[cefr]:
            samples.append((f"📚 CEFR {cefr}", random.sample(by_cefr[cefr], min(1, len(by_cefr[cefr])))))
    
    # 7. Random samples to fill up
    remaining = num_samples - sum(len(s[1]) for s in samples)
    if remaining > 0:
        remaining_senses = [s for s in senses if s not in [item for cat, items in samples for item in items]]
        if remaining_senses:
            samples.append(("🎲 RANDOM SAMPLES", random.sample(remaining_senses, min(remaining, len(remaining_senses)))))
    
    return samples


def print_sample(category, samples):
    """Print a category of samples."""
    print(f"\n{'='*80}")
    print(f"{category}")
    print(f"{'='*80}\n")
    
    for i, (sense_id, sense) in enumerate(samples, 1):
        print(f"--- Sample {i} ---")
        print(f"Sense ID: {sense_id}")
        print(f"Word: {sense.get('word', 'N/A')}")
        print(f"POS: {sense.get('pos', 'N/A')}")
        print(f"CEFR: {sense.get('cefr', 'N/A')}")
        print(f"Tier: {sense.get('tier', 'N/A')}")
        print(f"Validated: {sense.get('validated', False)}")
        print()
        
        print(f"Definition EN: {sense.get('definition_en', 'N/A')}")
        print(f"Definition ZH: {sense.get('definition_zh', 'N/A')}")
        print()
        
        example_en = sense.get('example_en', 'N/A')
        example_zh = sense.get('example_zh', 'N/A')
        print(f"Example EN: {example_en}")
        print(f"Example ZH: {example_zh}")
        print()
        
        # Check for quality issues
        issues = []
        if not example_en or example_en == 'N/A':
            issues.append("⚠️ Missing English example")
        if not example_zh or example_zh == 'N/A':
            issues.append("⚠️ Missing Chinese example")
        if len(sense.get('definition_zh', '')) < 2:
            issues.append("⚠️ Chinese definition too short (might be wrong)")
        if sense.get('definition_zh', '') and len(sense.get('definition_zh', '')) == 1:
            issues.append("⚠️ Chinese definition is single character (likely wrong)")
        
        if issues:
            print("QUALITY ISSUES:")
            for issue in issues:
                print(f"  {issue}")
            print()
        
        # Show connections
        conn_counts = sense.get('connection_counts', {})
        if conn_counts.get('total', 0) > 0:
            print(f"Connections: {conn_counts.get('total', 0)} total")
            print(f"  - Related: {conn_counts.get('related', 0)}")
            print(f"  - Opposite: {conn_counts.get('opposite', 0)}")
            print()
        
        print(f"Value: {sense.get('value', {}).get('total_xp', 0)} XP")
        print()


def main():
    print("="*80)
    print("Vocabulary Quality Sampling Tool")
    print("="*80)
    print()
    
    data = load_vocabulary()
    if not data:
        return
    
    # Show overall stats
    stats = data.get('stats', {})
    senses = data.get('senses', {})
    
    print(f"Total Words: {stats.get('words', 0)}")
    print(f"Total Senses: {stats.get('senses', 0)}")
    print(f"Validated: {stats.get('validated', 0)}")
    print(f"Errors: {stats.get('errors', 0)}")
    print()
    
    # Count validation status
    validated_count = sum(1 for s in senses.values() if s.get('validated', False))
    failed_count = len(senses) - validated_count
    print(f"Validation Rate: {validated_count}/{len(senses)} ({validated_count/len(senses)*100:.1f}%)" if senses else "N/A")
    print()
    
    # Get samples
    samples = sample_vocabulary(data, num_samples=25)
    
    # Print samples
    for category, category_samples in samples:
        if category_samples:
            print_sample(category, category_samples)
    
    # Summary of potential issues
    print(f"\n{'='*80}")
    print("QUALITY CHECK SUMMARY")
    print(f"{'='*80}\n")
    
    issues_found = {
        'missing_examples': 0,
        'short_chinese_def': 0,
        'single_char_chinese': 0,
        'no_connections': 0,
    }
    
    for sense_id, sense in senses.items():
        if not sense.get('example_en'):
            issues_found['missing_examples'] += 1
        if len(sense.get('definition_zh', '')) < 2:
            issues_found['short_chinese_def'] += 1
        if len(sense.get('definition_zh', '')) == 1:
            issues_found['single_char_chinese'] += 1
        if sense.get('connection_counts', {}).get('total', 0) == 0:
            issues_found['no_connections'] += 1
    
    print(f"Missing examples: {issues_found['missing_examples']}/{len(senses)}")
    print(f"Short Chinese definitions (<2 chars): {issues_found['short_chinese_def']}/{len(senses)}")
    print(f"Single character Chinese: {issues_found['single_char_chinese']}/{len(senses)}")
    print(f"No connections: {issues_found['no_connections']}/{len(senses)}")
    print()
    
    # Save samples to file for easy review
    output_file = Path(__file__).parent.parent / 'logs' / 'vocabulary_samples.txt'
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("Vocabulary Quality Samples\n")
        f.write("="*80 + "\n\n")
        for category, category_samples in samples:
            if category_samples:
                f.write(f"\n{'='*80}\n")
                f.write(f"{category}\n")
                f.write(f"{'='*80}\n\n")
                for i, (sense_id, sense) in enumerate(category_samples, 1):
                    f.write(f"--- Sample {i} ---\n")
                    f.write(f"Sense ID: {sense_id}\n")
                    f.write(f"Word: {sense.get('word', 'N/A')}\n")
                    f.write(f"POS: {sense.get('pos', 'N/A')}\n")
                    f.write(f"CEFR: {sense.get('cefr', 'N/A')}\n")
                    f.write(f"Validated: {sense.get('validated', False)}\n\n")
                    f.write(f"Definition EN: {sense.get('definition_en', 'N/A')}\n")
                    f.write(f"Definition ZH: {sense.get('definition_zh', 'N/A')}\n\n")
                    f.write(f"Example EN: {sense.get('example_en', 'N/A')}\n")
                    f.write(f"Example ZH: {sense.get('example_zh', 'N/A')}\n\n")
                    f.write(f"Value: {sense.get('value', {}).get('total_xp', 0)} XP\n\n")
    
    print(f"✅ Samples saved to: {output_file}")
    print(f"   Review this file to check quality!")


if __name__ == '__main__':
    main()

