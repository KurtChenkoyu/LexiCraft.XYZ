"""
Batch Fix Data Quality Script

Fixes all words with mismatched sense IDs by re-enriching them with correct primary senses.

Usage:
    python3 scripts/batch_fix_data_quality.py --limit 10 --dry-run
    python3 scripts/batch_fix_data_quality.py --limit 50
    python3 scripts/batch_fix_data_quality.py --priority-only  # Fix only high-priority words
"""

import argparse
import sys
import time
from pathlib import Path

# Add parent directory to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from src.database.neo4j_connection import Neo4jConnection
from src.agent import get_enrichment, update_graph
from src.structure_miner import get_skeletons


# High-priority words that appear frequently in surveys
PRIORITY_WORDS = [
    'brave', 'bread', 'bother', 'creature', 'possess', 'alternatively', 
    'advert', 'sympathy', 'cope', 'complaint', 'knit', 'recognition'
]


def get_problematic_words(conn: Neo4jConnection, limit: int = None, priority_only: bool = False):
    """Get list of words with mismatched sense IDs."""
    with conn.get_session() as session:
        if priority_only:
            # Fix only priority words
            words = []
            for word in PRIORITY_WORDS:
                result = session.run('''
                    MATCH (w:Word {name: $word})-[:HAS_SENSE]->(s:Sense)
                    WHERE s.definition_zh IS NOT NULL
                    WITH w, s,
                         CASE 
                           WHEN s.id STARTS WITH toLower($word) THEN 'MATCH'
                           ELSE 'MISMATCH'
                         END as match_status
                    WHERE match_status = 'MISMATCH'
                    RETURN DISTINCT w.name as word, w.frequency_rank as rank
                    LIMIT 1
                ''', word=word)
                row = result.single()
                if row:
                    words.append((row['word'], int(row['rank'])))
            return words
        else:
            # Get all problematic words
            query = '''
                MATCH (w:Word)-[:HAS_SENSE]->(s:Sense)
                WHERE s.definition_zh IS NOT NULL
                AND w.frequency_rank <= 8000
                WITH w, s,
                     CASE 
                       WHEN s.id STARTS WITH toLower(w.name) THEN 'MATCH'
                       ELSE 'MISMATCH'
                     END as match_status
                WHERE match_status = 'MISMATCH'
                RETURN DISTINCT w.name as word, w.frequency_rank as rank
                ORDER BY w.frequency_rank ASC
            '''
            if limit:
                query += f' LIMIT {limit}'
            
            result = session.run(query)
            return [(record['word'], int(record['rank'])) for record in result]


def fix_word(conn: Neo4jConnection, word: str, force: bool = True):
    """Re-enrich a word with correct primary senses."""
    try:
        # Get fresh skeletons from WordNet
        skeletons = get_skeletons(word, limit=5)
        
        if not skeletons:
            return False, f"No WordNet data"
        
        # Filter to only senses where sense_id matches word name
        matching_skeletons = [s for s in skeletons if s['id'].startswith(word.lower())]
        
        if not matching_skeletons:
            # Use top 3 as fallback
            matching_skeletons = skeletons[:3]
        
        # Mark senses as unenriched if force=True
        if force:
            with conn.get_session() as session:
                session.run('''
                    MATCH (w:Word {name: $word})-[:HAS_SENSE]->(s:Sense)
                    WHERE s.id IN $sense_ids
                    SET s.enriched = NULL
                ''', word=word, sense_ids=[s['id'] for s in matching_skeletons])
        
        # Re-enrich with Gemini
        enriched_data = get_enrichment(word, matching_skeletons, mock=False)
        
        if enriched_data:
            update_graph(conn, enriched_data)
            return True, f"Fixed {len(enriched_data)} senses"
        else:
            return False, "No enriched data returned"
            
    except Exception as e:
        return False, str(e)


def main():
    parser = argparse.ArgumentParser(description='Batch fix data quality issues')
    parser.add_argument('--limit', type=int, help='Limit number of words to fix')
    parser.add_argument('--priority-only', action='store_true', help='Fix only priority words')
    parser.add_argument('--dry-run', action='store_true', help='Dry run (don\'t actually fix)')
    parser.add_argument('--delay', type=float, default=2.0, help='Delay between API calls (seconds)')
    
    args = parser.parse_args()
    
    conn = Neo4jConnection()
    try:
        if not conn.verify_connectivity():
            print("❌ Failed to connect to Neo4j")
            return
        
        # Get problematic words
        print("🔍 Finding problematic words...")
        words = get_problematic_words(conn, limit=args.limit, priority_only=args.priority_only)
        
        if not words:
            print("✅ No problematic words found!")
            return
        
        print(f"📊 Found {len(words)} words to fix")
        if args.dry_run:
            print("\n[DRY RUN MODE - No changes will be made]\n")
        
        # Fix each word
        success_count = 0
        fail_count = 0
        
        for i, (word, rank) in enumerate(words, 1):
            print(f"\n[{i}/{len(words)}] Fixing '{word}' (rank {rank})...")
            
            if args.dry_run:
                print(f"  [DRY RUN] Would fix '{word}'...")
                success_count += 1
            else:
                success, message = fix_word(conn, word, force=True)
                if success:
                    print(f"  ✅ {message}")
                    success_count += 1
                else:
                    print(f"  ❌ Failed: {message}")
                    fail_count += 1
                
                # Rate limiting
                if i < len(words):
                    time.sleep(args.delay)
        
        # Summary
        print(f"\n{'='*60}")
        print("SUMMARY")
        print(f"{'='*60}")
        print(f"Total: {len(words)}")
        print(f"Success: {success_count}")
        print(f"Failed: {fail_count}")
        
    finally:
        conn.close()


if __name__ == "__main__":
    main()

