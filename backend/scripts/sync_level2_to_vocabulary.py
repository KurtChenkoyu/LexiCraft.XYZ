"""
Sync Level 2 enrichment data from Neo4j to vocabulary.json

This script exports examples_contextual, examples_opposite, examples_similar,
and examples_confused from Neo4j Sense nodes to the vocabulary.json file
used by VocabularyStore for MCQ generation.

Usage:
    python scripts/sync_level2_to_vocabulary.py           # Sync all
    python scripts/sync_level2_to_vocabulary.py --limit 100  # Sync first 100
    python scripts/sync_level2_to_vocabulary.py --dry-run    # Preview without saving
"""

import json
import argparse
from pathlib import Path
from typing import Dict, List, Optional
import sys

# Add parent directory for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database.neo4j_connection import Neo4jConnection


def fetch_level2_data(conn: Neo4jConnection, limit: Optional[int] = None) -> Dict[str, Dict]:
    """
    Fetch all Level 2 enrichment data from Neo4j.
    
    Returns:
        Dict mapping sense_id to Level 2 data
    """
    level2_data = {}
    
    query = """
        MATCH (s:Sense)
        WHERE s.stage2_enriched = true
        RETURN s.id as sense_id,
               s.examples_contextual as examples_contextual,
               s.examples_opposite as examples_opposite,
               s.examples_similar as examples_similar,
               s.examples_confused as examples_confused,
               s.stage2_version as stage2_version
    """
    if limit:
        query += f" LIMIT {limit}"
    
    with conn.get_session() as session:
        result = session.run(query)
        
        for record in result:
            sense_id = record["sense_id"]
            
            # Parse JSON strings
            def parse_json(val):
                if not val:
                    return []
                if isinstance(val, str):
                    try:
                        return json.loads(val)
                    except json.JSONDecodeError:
                        return []
                return val
            
            level2_data[sense_id] = {
                "examples_contextual": parse_json(record["examples_contextual"]),
                "examples_opposite": parse_json(record["examples_opposite"]),
                "examples_similar": parse_json(record["examples_similar"]),
                "examples_confused": parse_json(record["examples_confused"]),
                "stage2_version": record.get("stage2_version", 1)
            }
    
    return level2_data


def update_vocabulary_json(
    vocab_path: Path,
    level2_data: Dict[str, Dict],
    dry_run: bool = False
) -> Dict[str, int]:
    """
    Update vocabulary.json with Level 2 data.
    
    Returns:
        Stats dict with counts
    """
    # Load existing vocabulary
    with open(vocab_path, 'r', encoding='utf-8') as f:
        vocab = json.load(f)
    
    stats = {
        "total_senses": len(vocab.get("senses", {})),
        "level2_senses": len(level2_data),
        "updated": 0,
        "skipped_not_found": 0,
        "skipped_same_version": 0
    }
    
    senses = vocab.get("senses", {})
    
    for sense_id, l2_data in level2_data.items():
        if sense_id not in senses:
            stats["skipped_not_found"] += 1
            continue
        
        # Check if already has same version
        current_version = senses[sense_id].get("stage2_version", 0) or 0
        new_version = l2_data.get("stage2_version", 1) or 1
        
        if current_version >= new_version:
            stats["skipped_same_version"] += 1
            continue
        
        # Update sense with Level 2 data
        senses[sense_id]["examples_contextual"] = l2_data["examples_contextual"]
        senses[sense_id]["examples_opposite"] = l2_data["examples_opposite"]
        senses[sense_id]["examples_similar"] = l2_data["examples_similar"]
        senses[sense_id]["examples_confused"] = l2_data["examples_confused"]
        senses[sense_id]["stage2_version"] = new_version
        stats["updated"] += 1
    
    if not dry_run:
        # Save updated vocabulary
        with open(vocab_path, 'w', encoding='utf-8') as f:
            json.dump(vocab, f, ensure_ascii=False, indent=2)
    
    return stats


def main():
    parser = argparse.ArgumentParser(
        description="Sync Level 2 enrichment data from Neo4j to vocabulary.json"
    )
    parser.add_argument(
        "--limit", type=int, default=None,
        help="Limit number of senses to sync"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Preview changes without saving"
    )
    parser.add_argument(
        "--vocab-path", type=str,
        default="data/vocabulary.json",
        help="Path to vocabulary.json"
    )
    args = parser.parse_args()
    
    vocab_path = Path(args.vocab_path)
    if not vocab_path.exists():
        print(f"❌ Vocabulary file not found: {vocab_path}")
        return 1
    
    print("🔄 Syncing Level 2 enrichment data from Neo4j to vocabulary.json")
    if args.dry_run:
        print("   (DRY RUN - no changes will be saved)")
    
    # Connect to Neo4j
    conn = Neo4jConnection()
    if not conn.verify_connectivity():
        print("❌ Failed to connect to Neo4j")
        return 1
    
    try:
        # Fetch Level 2 data
        print("\n📥 Fetching Level 2 data from Neo4j...")
        level2_data = fetch_level2_data(conn, limit=args.limit)
        print(f"   Found {len(level2_data)} senses with Level 2 enrichment")
        
        # Show sample
        if level2_data:
            sample_id = list(level2_data.keys())[0]
            sample = level2_data[sample_id]
            print(f"\n📋 Sample ({sample_id}):")
            print(f"   examples_contextual: {len(sample['examples_contextual'])} examples")
            print(f"   examples_opposite: {len(sample['examples_opposite'])} examples")
            print(f"   examples_similar: {len(sample['examples_similar'])} examples")
            print(f"   examples_confused: {len(sample['examples_confused'])} examples")
            print(f"   stage2_version: {sample['stage2_version']}")
        
        # Update vocabulary.json
        print(f"\n📤 Updating {vocab_path}...")
        stats = update_vocabulary_json(vocab_path, level2_data, dry_run=args.dry_run)
        
        # Print summary
        print(f"\n{'='*50}")
        print("📊 Sync Summary")
        print(f"{'='*50}")
        print(f"   Total senses in vocabulary: {stats['total_senses']}")
        print(f"   Level 2 senses in Neo4j: {stats['level2_senses']}")
        print(f"   Updated: {stats['updated']}")
        print(f"   Skipped (not in vocabulary): {stats['skipped_not_found']}")
        print(f"   Skipped (same/newer version): {stats['skipped_same_version']}")
        
        if args.dry_run:
            print(f"\n⚠️ DRY RUN - no changes saved. Run without --dry-run to apply.")
        else:
            print(f"\n✅ Sync complete!")
        
        return 0
        
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())

