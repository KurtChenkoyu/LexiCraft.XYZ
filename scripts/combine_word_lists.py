#!/usr/bin/env python3
"""
Combine Word Lists: CEFR + Taiwan + Corpus Frequency
Target: 3,000-4,000 words for Phase 1

Weighted Scoring:
- CEFR A1-B2: 40%
- Taiwan MOE: 30%
- Corpus Frequency: 30%
"""

import csv
import json
import re
from collections import defaultdict
from pathlib import Path

# Configuration
TARGET_COUNT = 3500  # Target 3,000-4,000 words
CEFR_WEIGHT = 0.4
TAIWAN_WEIGHT = 0.3
CORPUS_WEIGHT = 0.3

# File paths
SCRIPT_DIR = Path(__file__).parent
GOOGLE_10K_PATH = SCRIPT_DIR / "google-10000-english.txt"
OXFORD_3000_PATH = SCRIPT_DIR / "Oxford3000_Vocab-main" / "oxford3000_vocabulary_with_collocations_and_definitions_datasets.csv"
TAIWAN_MOE_PATH = SCRIPT_DIR / "taiwan_moe_words.txt"  # Optional, will be created if not exists
OUTPUT_CSV = SCRIPT_DIR / "combined_word_list_phase1.csv"
OUTPUT_JSON = SCRIPT_DIR / "combined_word_list_phase1.json"
OUTPUT_TXT = SCRIPT_DIR / "combined_word_list_phase1.txt"


def normalize_word(word):
    """Normalize word to lowercase and remove extra whitespace"""
    if not word:
        return None
    word = word.strip().lower()
    # Remove non-alphabetic characters except hyphens and apostrophes
    word = re.sub(r'[^a-z\-\']', '', word)
    return word if word else None


def load_google_10k():
    """Load Google 10K word list (Corpus Frequency source)"""
    print("Loading Google 10K word list...")
    words = {}
    
    if not GOOGLE_10K_PATH.exists():
        print(f"Warning: {GOOGLE_10K_PATH} not found")
        return words
    
    with open(GOOGLE_10K_PATH, 'r', encoding='utf-8') as f:
        for rank, line in enumerate(f, 1):
            word = normalize_word(line.strip())
            if word:
                words[word] = rank  # Lower rank = higher frequency = higher score
    
    print(f"Loaded {len(words)} words from Google 10K")
    return words


def load_oxford_3000():
    """Load Oxford 3000 CEFR words"""
    print("Loading Oxford 3000 CEFR word list...")
    words = {}
    
    if not OXFORD_3000_PATH.exists():
        print(f"Warning: {OXFORD_3000_PATH} not found")
        return words
    
    # CEFR level scores (A1-B2 only for MVP)
    cefr_scores = {
        'A1': 4.0,
        'A2': 4.0,
        'B1': 3.0,
        'B2': 3.0,
        'C1': 0.0,  # Exclude for MVP
        'C2': 0.0,  # Exclude for MVP
    }
    
    with open(OXFORD_3000_PATH, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            word = normalize_word(row.get('Word', ''))
            if word:
                # Oxford 3000 is all A1-B2, so assign high score
                # If we had CEFR levels, we'd use them here
                words[word] = 4.0  # Default high score for Oxford 3000 words
    
    print(f"Loaded {len(words)} words from Oxford 3000")
    return words


def load_taiwan_moe():
    """Load Taiwan MOE curriculum words"""
    print("Loading Taiwan MOE word list...")
    words = {}
    
    if not TAIWAN_MOE_PATH.exists():
        print(f"Warning: {TAIWAN_MOE_PATH} not found - creating placeholder")
        # For now, we'll use a subset of common words that are likely in Taiwan curriculum
        # In production, this would be loaded from actual Taiwan MOE sources
        return words
    
    with open(TAIWAN_MOE_PATH, 'r', encoding='utf-8') as f:
        for rank, line in enumerate(f, 1):
            word = normalize_word(line.strip())
            if word:
                # Lower rank = higher priority in curriculum
                words[word] = rank
    
    print(f"Loaded {len(words)} words from Taiwan MOE")
    return words


def create_taiwan_moe_placeholder(corpus_words, cefr_words):
    """
    Create a placeholder Taiwan MOE list by selecting common words
    that are likely in Taiwan curriculum (elementary/junior high level)
    """
    print("Creating Taiwan MOE placeholder from common curriculum words...")
    
    # Common words that are typically in Taiwan elementary/junior high curriculum
    # These are basic, everyday words that students learn early
    taiwan_common = set()
    
    # Take top 2000 words from corpus (likely in curriculum)
    corpus_sorted = sorted(corpus_words.items(), key=lambda x: x[1])[:2000]
    for word, _ in corpus_sorted:
        if word and len(word) > 2:  # Skip very short words
            taiwan_common.add(word)
    
    # Also include all CEFR words (they overlap with curriculum)
    for word in cefr_words:
        if word:
            taiwan_common.add(word)
    
    # Convert to dict with ranking
    taiwan_words = {}
    for rank, word in enumerate(sorted(taiwan_common), 1):
        taiwan_words[word] = rank
    
    print(f"Created placeholder with {len(taiwan_words)} words")
    return taiwan_words


def combine_word_lists(cefr_words, taiwan_words, corpus_words, target_count=TARGET_COUNT):
    """Combine word lists with weighted scoring"""
    print(f"\nCombining word lists with weights: CEFR {CEFR_WEIGHT*100}%, Taiwan {TAIWAN_WEIGHT*100}%, Corpus {CORPUS_WEIGHT*100}%...")
    
    word_scores = defaultdict(float)
    word_sources = defaultdict(set)
    
    # Normalize CEFR scores (0-1 scale)
    max_cefr_score = max(cefr_words.values()) if cefr_words else 1.0
    for word, score in cefr_words.items():
        normalized_score = score / max_cefr_score if max_cefr_score > 0 else 0
        word_scores[word] += normalized_score * CEFR_WEIGHT
        word_sources[word].add('CEFR')
    
    # Normalize Taiwan scores (inverse rank, 0-1 scale)
    max_taiwan_rank = max(taiwan_words.values()) if taiwan_words else 1
    for word, rank in taiwan_words.items():
        normalized_score = (max_taiwan_rank - rank + 1) / max_taiwan_rank if max_taiwan_rank > 0 else 0
        word_scores[word] += normalized_score * TAIWAN_WEIGHT
        word_sources[word].add('Taiwan')
    
    # Normalize Corpus scores (inverse rank, 0-1 scale)
    max_corpus_rank = max(corpus_words.values()) if corpus_words else 10000
    for word, rank in corpus_words.items():
        normalized_score = (max_corpus_rank - rank + 1) / max_corpus_rank if max_corpus_rank > 0 else 0
        word_scores[word] += normalized_score * CORPUS_WEIGHT
        word_sources[word].add('Corpus')
    
    # Sort by combined score
    sorted_words = sorted(word_scores.items(), key=lambda x: x[1], reverse=True)
    
    # Return top N words with metadata
    result = []
    for word, score in sorted_words[:target_count]:
        result.append({
            'word': word,
            'score': round(score, 4),
            'sources': sorted(word_sources[word]),
            'cefr_rank': cefr_words.get(word, None),
            'taiwan_rank': taiwan_words.get(word, None),
            'corpus_rank': corpus_words.get(word, None),
        })
    
    return result


def export_to_csv(words, output_path):
    """Export word list to CSV"""
    print(f"\nExporting to CSV: {output_path}")
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['word', 'score', 'sources', 'cefr_rank', 'taiwan_rank', 'corpus_rank'])
        writer.writeheader()
        for word_data in words:
            # Convert sources set to string
            word_data_copy = word_data.copy()
            word_data_copy['sources'] = ','.join(word_data['sources'])
            writer.writerow(word_data_copy)
    
    print(f"Exported {len(words)} words to CSV")


def export_to_json(words, output_path):
    """Export word list to JSON"""
    print(f"\nExporting to JSON: {output_path}")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(words, f, indent=2, ensure_ascii=False)
    
    print(f"Exported {len(words)} words to JSON")


def export_to_txt(words, output_path):
    """Export word list to plain text (one word per line)"""
    print(f"\nExporting to TXT: {output_path}")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        for word_data in words:
            f.write(word_data['word'] + '\n')
    
    print(f"Exported {len(words)} words to TXT")


def main():
    """Main execution"""
    print("=" * 60)
    print("Word List Combination Script - Phase 1")
    print("=" * 60)
    
    # Load word lists
    corpus_words = load_google_10k()
    cefr_words = load_oxford_3000()
    taiwan_words = load_taiwan_moe()
    
    # Create Taiwan MOE placeholder if needed
    if not taiwan_words:
        taiwan_words = create_taiwan_moe_placeholder(corpus_words, cefr_words)
    
    # Combine word lists
    final_words = combine_word_lists(cefr_words, taiwan_words, corpus_words, target_count=TARGET_COUNT)
    
    # Export results
    export_to_csv(final_words, OUTPUT_CSV)
    export_to_json(final_words, OUTPUT_JSON)
    export_to_txt(final_words, OUTPUT_TXT)
    
    # Print summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total words compiled: {len(final_words)}")
    print(f"Target range: 3,000-4,000 words")
    print(f"\nSource breakdown:")
    
    source_counts = defaultdict(int)
    for word_data in final_words:
        for source in word_data['sources']:
            source_counts[source] += 1
    
    for source, count in sorted(source_counts.items()):
        print(f"  - {source}: {count} words")
    
    print(f"\nFiles created:")
    print(f"  - {OUTPUT_CSV}")
    print(f"  - {OUTPUT_JSON}")
    print(f"  - {OUTPUT_TXT}")
    
    print("\n✅ Phase 1 word list compilation complete!")
    print("Ready for database population (pending database schema completion)")


if __name__ == "__main__":
    main()

