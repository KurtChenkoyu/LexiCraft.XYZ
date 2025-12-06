#!/usr/bin/env python3
"""
Sample Checkpoint Quality Checker

Extracts samples from the checkpoint file (where the pipeline is actively saving).
This shows the most recent generated data.
"""

import json
import random
from pathlib import Path
from collections import defaultdict


def load_checkpoint():
    """Load the checkpoint file"""
    checkpoint_path = Path(__file__).parent.parent / 'logs' / 'enrichment_checkpoint.json'
    
    if not checkpoint_path.exists():
        print(f"❌ Checkpoint file not found: {checkpoint_path}")
        return None
    
    with open(checkpoint_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def print_sample(sense_id, sense, i):
    """Print a single sense sample"""
    print(f"\n{'─'*80}")
    print(f"Sample {i}: {sense_id}")
    print(f"{'─'*80}")
    print(f"Word: {sense.get('word', 'N/A')}")
    print(f"POS: {sense.get('pos', 'N/A')}")
    print(f"CEFR: {sense.get('cefr', 'N/A')}")
    print(f"Tier: {sense.get('tier', 'N/A')}")
    print(f"Validated: {sense.get('validated', False)}")
    print()
    
    def_en = sense.get('definition_en', 'N/A')
    def_zh = sense.get('definition_zh', 'N/A')
    print(f"Definition EN: {def_en}")
    print(f"Definition ZH: {def_zh}")
    
    # Check for issues
    issues = []
    if len(def_zh) == 1:
        issues.append("❌ Single character (likely wrong)")
    elif len(def_zh) < 3:
        issues.append("⚠️ Very short (might be wrong)")
    if def_zh and def_zh.isascii() and len(def_zh) <= 3:
        issues.append("⚠️ Looks like English/abbreviation (IP, etc.)")
    
    if issues:
        print("  " + " | ".join(issues))
    print()
    
    example_en = sense.get('example_en', 'N/A')
    example_zh = sense.get('example_zh', 'N/A')
    print(f"Example EN: {example_en}")
    print(f"Example ZH: {example_zh}")
    
    if not example_en or example_en == 'N/A':
        print("  ⚠️ Missing English example")
    if not example_zh or example_zh == 'N/A':
        print("  ⚠️ Missing Chinese example")
    print()
    
    conn_counts = sense.get('connection_counts', {})
    if conn_counts.get('total', 0) > 0:
        print(f"Connections: {conn_counts.get('total', 0)} (Related: {conn_counts.get('related', 0)}, Opposite: {conn_counts.get('opposite', 0)})")
    print(f"Value: {sense.get('value', {}).get('total_xp', 0)} XP")


def main():
    print("="*80)
    print("Checkpoint Quality Sampling Tool")
    print("="*80)
    print()
    
    data = load_checkpoint()
    if not data:
        return
    
    senses = data.get('enriched_senses', {})
    print(f"Total senses in checkpoint: {len(senses)}")
    print()
    
    if not senses:
        print("No senses found in checkpoint")
        return
    
    # Categorize
    validated = [(sid, s) for sid, s in senses.items() if s.get('validated', False)]
    failed = [(sid, s) for sid, s in senses.items() if not s.get('validated', True)]
    
    # Group by POS
    by_pos = defaultdict(list)
    for sid, s in senses.items():
        by_pos[s.get('pos', 'unknown')].append((sid, s))
    
    # Find problematic Chinese definitions
    problematic = []
    for sid, s in senses.items():
        def_zh = s.get('definition_zh', '')
        if len(def_zh) == 1 or (def_zh and def_zh.isascii() and len(def_zh) <= 3):
            problematic.append((sid, s))
    
    print(f"Validated: {len(validated)}")
    print(f"Failed validation: {len(failed)}")
    print(f"Problematic Chinese definitions: {len(problematic)}")
    print()
    
    # Show samples
    print("="*80)
    print("✅ VALIDATED SAMPLES (Good Quality)")
    print("="*80)
    if validated:
        for i, (sid, s) in enumerate(random.sample(validated, min(5, len(validated))), 1):
            print_sample(sid, s, i)
    else:
        print("No validated samples yet")
    
    print("\n\n" + "="*80)
    print("❌ FAILED VALIDATION SAMPLES")
    print("="*80)
    if failed:
        for i, (sid, s) in enumerate(random.sample(failed, min(5, len(failed))), 1):
            print_sample(sid, s, i)
    else:
        print("No failed samples")
    
    print("\n\n" + "="*80)
    print("⚠️ PROBLEMATIC CHINESE DEFINITIONS (Need Review)")
    print("="*80)
    if problematic:
        for i, (sid, s) in enumerate(random.sample(problematic, min(10, len(problematic))), 1):
            print_sample(sid, s, i)
    else:
        print("No problematic definitions found")
    
    # Show by POS
    print("\n\n" + "="*80)
    print("📊 SAMPLES BY PART OF SPEECH")
    print("="*80)
    for pos in ['n', 'v', 'adj', 'a', 'r', 'adv']:
        if pos in by_pos:
            print(f"\n{pos.upper()} ({len(by_pos[pos])} total):")
            for i, (sid, s) in enumerate(random.sample(by_pos[pos], min(2, len(by_pos[pos]))), 1):
                print_sample(sid, s, i)
    
    # Save to file
    output_file = Path(__file__).parent.parent / 'logs' / 'checkpoint_samples.txt'
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("Checkpoint Quality Samples\n")
        f.write("="*80 + "\n\n")
        f.write(f"Total senses: {len(senses)}\n")
        f.write(f"Validated: {len(validated)}\n")
        f.write(f"Failed: {len(failed)}\n")
        f.write(f"Problematic Chinese: {len(problematic)}\n\n")
        
        f.write("\n" + "="*80 + "\n")
        f.write("PROBLEMATIC CHINESE DEFINITIONS\n")
        f.write("="*80 + "\n\n")
        for sid, s in problematic[:20]:
            f.write(f"{sid}: {s.get('word')} - {s.get('definition_en')} → {s.get('definition_zh')}\n")
    
    print(f"\n\n✅ Detailed samples saved to: {output_file}")


if __name__ == '__main__':
    main()

