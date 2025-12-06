#!/usr/bin/env python3
"""
Populate Learning Points from Word List

Reads word list from scripts/combined_word_list_phase1.txt and creates
learning points in Neo4j using WordNet for definitions and examples.

Usage:
    python populate_learning_points.py [--limit N] [--tier 1|2|both]
"""

import sys
import os
import argparse
from pathlib import Path

# Add parent directory to path to import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

import nltk
from nltk.corpus import wordnet as wn
from src.database.neo4j_connection import Neo4jConnection
from src.database.neo4j_crud.learning_points import create_learning_point
from src.models.learning_point import LearningPoint

# Download NLTK data if needed
try:
    nltk.data.find('corpora/wordnet')
except LookupError:
    print("Downloading WordNet data...")
    nltk.download('wordnet', quiet=True)
    nltk.download('omw-1.4', quiet=True)


def normalize_word(word: str) -> str:
    """Normalize word for ID generation."""
    return word.lower().strip().replace(' ', '_').replace('-', '_')


def generate_id(word: str, pos: str, tier: int, index: int) -> str:
    """
    Generate unique ID for learning point.
    
    Format:
    - Tier 1: {word}_{pos}1 (e.g., beat_v1, beat_n1)
    - Tier 2: {word}_{pos}{index} (e.g., beat_v2, beat_v3, beat_n2)
    
    For Tier 2, index starts at 2 (since 1 is used for Tier 1).
    """
    normalized = normalize_word(word)
    pos_map = {'n': 'n', 'v': 'v', 'a': 'a', 's': 'a', 'r': 'r'}
    pos_code = pos_map.get(pos, 'x')
    
    if tier == 1:
        return f"{normalized}_{pos_code}1"
    else:
        # Tier 2: use index starting from 2
        return f"{normalized}_{pos_code}{index + 1}"


def get_word_synsets(word: str):
    """Get all synsets for a word, grouped by POS."""
    synsets = wn.synsets(word)
    
    # Group by POS
    by_pos = {}
    for syn in synsets:
        pos = syn.pos()
        if pos not in by_pos:
            by_pos[pos] = []
        by_pos[pos].append(syn)
    
    return by_pos


def create_learning_points_for_word(
    conn: Neo4jConnection,
    word: str,
    frequency_rank: int,
    tier_limit: int = 2
) -> tuple[int, int]:
    """
    Create learning points for a word.
    
    Args:
        conn: Neo4j connection
        word: The word to process
        frequency_rank: Rank from word list
        tier_limit: Maximum tier to create (1 or 2)
        
    Returns:
        Tuple of (tier1_count, tier2_count) created
    """
    tier1_count = 0
    tier2_count = 0
    
    synsets_by_pos = get_word_synsets(word)
    
    if not synsets_by_pos:
        return tier1_count, tier2_count
    
    # Create Tier 1 learning points (first meaning per POS)
    for pos, synsets in synsets_by_pos.items():
        if not synsets:
            continue
            
        syn = synsets[0]  # First synset for this POS (Tier 1)
        
        try:
            lp_id = generate_id(word, pos, 1, 0)
            definition = syn.definition()
            examples = syn.examples()
            example = examples[0] if examples else ""
            
            learning_point = LearningPoint(
                id=lp_id,
                word=word,
                type="word",
                tier=1,
                definition=definition,
                example=example,
                frequency_rank=frequency_rank,
                difficulty="B1",
                register="both",
                contexts=[],
                metadata={
                    "pos": pos,
                    "synset_id": syn.name(),
                    "synset_offset": syn.offset()
                }
            )
            
            if create_learning_point(conn, learning_point):
                tier1_count += 1
            # If creation fails due to existing ID, that's okay - skip silently
                
        except Exception as e:
            # Only log if it's not a constraint violation (ID already exists)
            error_str = str(e)
            if "already exists" not in error_str.lower() and "constraint" not in error_str.lower():
                print(f"  Error creating Tier 1 learning point for '{word}' ({pos}): {e}")
            continue
    
    # Create Tier 2 learning points (additional meanings) if tier_limit >= 2
    if tier_limit >= 2:
        for pos, synsets in synsets_by_pos.items():
            if len(synsets) <= 1:
                continue  # No additional meanings
                
            # Process additional synsets (Tier 2)
            for index, syn in enumerate(synsets[1:], start=0):
                try:
                    lp_id = generate_id(word, pos, 2, index)
                    definition = syn.definition()
                    examples = syn.examples()
                    example = examples[0] if examples else ""
                    
                    learning_point = LearningPoint(
                        id=lp_id,
                        word=word,
                        type="word",
                        tier=2,
                        definition=definition,
                        example=example,
                        frequency_rank=frequency_rank,
                        difficulty="B1",
                        register="both",
                        contexts=[],
                        metadata={
                            "pos": pos,
                            "synset_id": syn.name(),
                            "synset_offset": syn.offset()
                        }
                    )
                    
                    if create_learning_point(conn, learning_point):
                        tier2_count += 1
                    # If creation fails due to existing ID, that's okay - skip silently
                        
                except Exception as e:
                    # Only log if it's not a constraint violation (ID already exists)
                    error_str = str(e)
                    if "already exists" not in error_str.lower() and "constraint" not in error_str.lower():
                        print(f"  Error creating Tier 2 learning point for '{word}' ({pos}, index {index}): {e}")
                    continue
    
    return tier1_count, tier2_count


def load_word_list(word_list_path: str) -> list[tuple[str, int]]:
    """
    Load word list from file.
    
    Returns:
        List of (word, rank) tuples
    """
    words = []
    with open(word_list_path, 'r', encoding='utf-8') as f:
        for rank, line in enumerate(f, start=1):
            word = line.strip()
            if word:
                words.append((word, rank))
    return words


def main():
    parser = argparse.ArgumentParser(description='Populate learning points from word list')
    parser.add_argument(
        '--limit',
        type=int,
        default=None,
        help='Limit number of words to process (for testing)'
    )
    parser.add_argument(
        '--tier',
        type=int,
        choices=[1, 2],
        default=2,
        help='Maximum tier to create (1 or 2, default: 2)'
    )
    parser.add_argument(
        '--word-list',
        type=str,
        default='scripts/combined_word_list_phase1.txt',
        help='Path to word list file (relative to project root)'
    )
    
    args = parser.parse_args()
    
    # Get project root (parent of backend/)
    project_root = Path(__file__).parent.parent.parent
    word_list_path = project_root / args.word_list
    
    if not word_list_path.exists():
        print(f"Error: Word list file not found: {word_list_path}")
        sys.exit(1)
    
    print(f"Loading word list from: {word_list_path}")
    words = load_word_list(str(word_list_path))
    
    if args.limit:
        words = words[:args.limit]
        print(f"Processing limited to {args.limit} words")
    
    print(f"Total words to process: {len(words)}")
    print(f"Tier limit: {args.tier}")
    print()
    
    # Connect to Neo4j
    try:
        conn = Neo4jConnection()
        if not conn.verify_connectivity():
            print("Error: Failed to connect to Neo4j")
            sys.exit(1)
        print("Connected to Neo4j")
    except Exception as e:
        print(f"Error connecting to Neo4j: {e}")
        sys.exit(1)
    
    # Process words
    total_tier1 = 0
    total_tier2 = 0
    skipped = 0
    errors = 0
    
    for i, (word, rank) in enumerate(words, start=1):
        try:
            tier1, tier2 = create_learning_points_for_word(conn, word, rank, args.tier)
            
            if tier1 == 0 and tier2 == 0:
                skipped += 1
                print(f"[{i}/{len(words)}] {word}: SKIPPED (no WordNet data)")
            else:
                total_tier1 += tier1
                total_tier2 += tier2
                print(f"[{i}/{len(words)}] {word}: Tier1={tier1}, Tier2={tier2}")
            
            # Progress update every 100 words
            if i % 100 == 0:
                print(f"\nProgress: {i}/{len(words)} words processed")
                print(f"  Tier 1: {total_tier1}, Tier 2: {total_tier2}, Skipped: {skipped}, Errors: {errors}\n")
                
        except Exception as e:
            errors += 1
            print(f"[{i}/{len(words)}] {word}: ERROR - {e}")
            continue
    
    # Final summary
    print("\n" + "="*60)
    print("POPULATION COMPLETE")
    print("="*60)
    print(f"Words processed: {len(words)}")
    print(f"Tier 1 learning points created: {total_tier1}")
    print(f"Tier 2 learning points created: {total_tier2}")
    print(f"Total learning points: {total_tier1 + total_tier2}")
    print(f"Words skipped (no WordNet data): {skipped}")
    print(f"Errors: {errors}")
    print("="*60)
    
    conn.close()


if __name__ == "__main__":
    main()

