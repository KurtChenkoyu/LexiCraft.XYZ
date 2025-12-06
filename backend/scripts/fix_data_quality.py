"""
Data Quality Fix Script

Identifies and fixes words with wrong definitions:
1. Finds words where sense_id doesn't match word name (mismatched senses)
2. Re-enriches them with correct primary senses
3. Optionally removes wrong senses

Usage:
    python3 scripts/fix_data_quality.py --word brave
    python3 scripts/fix_data_quality.py --check-all
    python3 scripts/fix_data_quality.py --fix-all --dry-run
"""

import argparse
import sys
from pathlib import Path

# Add parent directory to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from src.database.neo4j_connection import Neo4jConnection
from src.agent import get_enrichment, update_graph
from src.structure_miner import get_skeletons


def check_word_quality(conn: Neo4jConnection, word: str = None):
    """Check data quality for a specific word or all words."""
    with conn.get_session() as session:
        if word:
            # Check specific word
            result = session.run('''
                MATCH (w:Word {name: $word})-[:HAS_SENSE]->(s:Sense)
                WHERE s.definition_zh IS NOT NULL
                WITH w, s,
                     CASE 
                       WHEN s.id STARTS WITH toLower(w.name) THEN 'MATCH'
                       ELSE 'MISMATCH'
                     END as match_status
                RETURN w.name as word, s.id as sense_id, s.definition_zh as def_zh, 
                       match_status, s.enriched as enriched
                ORDER BY COALESCE(s.usage_ratio, 0) DESC
            ''', word=word)
            
            print(f"\n{'='*60}")
            print(f"CHECKING: {word.upper()}")
            print(f"{'='*60}")
            
            for record in result:
                status_icon = "✅" if record['match_status'] == 'MATCH' else "⚠️"
                print(f"\n{status_icon} Sense: {record['sense_id']}")
                print(f"   Status: {record['match_status']}")
                print(f"   Enriched: {record.get('enriched', 'N/A')}")
                print(f"   Definition: {record['def_zh']}")
        else:
            # Check all words with mismatched senses
            result = session.run('''
                MATCH (w:Word)-[:HAS_SENSE]->(s:Sense)
                WHERE s.definition_zh IS NOT NULL
                WITH w, s,
                     CASE 
                       WHEN s.id STARTS WITH toLower(w.name) THEN 'MATCH'
                       ELSE 'MISMATCH'
                     END as match_status
                WHERE match_status = 'MISMATCH'
                AND w.frequency_rank <= 8000
                RETURN DISTINCT w.name as word, w.frequency_rank as rank, 
                       collect(s.id)[0] as wrong_sense_id,
                       collect(s.definition_zh)[0] as wrong_def
                ORDER BY w.frequency_rank ASC
                LIMIT 50
            ''')
            
            print(f"\n{'='*60}")
            print("WORDS WITH MISMATCHED SENSES (Top 50)")
            print(f"{'='*60}")
            
            count = 0
            for record in result:
                count += 1
                print(f"\n{count}. {record['word']} (rank {int(record['rank'])})")
                print(f"   Wrong sense: {record['wrong_sense_id']}")
                print(f"   Definition: {record['wrong_def'][:80]}...")


def fix_word(conn: Neo4jConnection, word: str, dry_run: bool = False, force: bool = False):
    """Re-enrich a word with correct primary senses."""
    print(f"\n{'='*60}")
    print(f"FIXING: {word.upper()}")
    print(f"{'='*60}")
    
    # Step 1: Check current state
    with conn.get_session() as session:
        result = session.run('''
            MATCH (w:Word {name: $word})-[:HAS_SENSE]->(s:Sense)
            WHERE s.definition_zh IS NOT NULL
            RETURN s.id as sense_id, s.definition_zh as def_zh, s.enriched as enriched,
                   CASE 
                     WHEN s.id STARTS WITH toLower($word) THEN 'MATCH'
                     ELSE 'MISMATCH'
                   END as match_status
            ORDER BY COALESCE(s.usage_ratio, 0) DESC
        ''', word=word)
        
        current_senses = list(result)
        if current_senses:
            print(f"\nCurrent senses in database:")
            for record in current_senses:
                status_icon = "✅" if record['match_status'] == 'MATCH' else "⚠️"
                print(f"  {status_icon} {record['sense_id']}: {record['def_zh'][:60]}...")
    
    # Step 2: Get fresh skeletons from WordNet
    print(f"\n1. Fetching skeletons from WordNet...")
    skeletons = get_skeletons(word, limit=5)
    
    if not skeletons:
        print(f"   ❌ No WordNet data found for '{word}'")
        return False
    
    print(f"   ✅ Found {len(skeletons)} senses")
    for i, skel in enumerate(skeletons, 1):
        print(f"      {i}. {skel['id']}: {skel['definition'][:60]}...")
    
    # Step 3: Filter to only senses where sense_id matches word name
    matching_skeletons = [s for s in skeletons if s['id'].startswith(word.lower())]
    
    if not matching_skeletons:
        print(f"\n   ⚠️  No matching sense IDs found. All senses:")
        for skel in skeletons:
            print(f"      - {skel['id']}")
        print(f"   Using top 3 skeletons as fallback...")
        matching_skeletons = skeletons[:3]  # Use top 3 as fallback
    
    print(f"\n2. Using {len(matching_skeletons)} matching senses:")
    for skel in matching_skeletons:
        print(f"   - {skel['id']}")
    
    # Step 4: Re-enrich with Gemini
    if dry_run:
        print(f"\n3. [DRY RUN] Would re-enrich with Gemini API...")
        print(f"   [DRY RUN] Would update {len(matching_skeletons)} senses")
        return True
    
    print(f"\n3. Re-enriching with Gemini API...")
    try:
        from src.agent import get_enrichment, update_graph
        
        # If force=True, we need to mark senses as unenriched first
        if force:
            print(f"   Marking existing senses as unenriched (force mode)...")
            with conn.get_session() as session:
                session.run('''
                    MATCH (w:Word {name: $word})-[:HAS_SENSE]->(s:Sense)
                    WHERE s.id IN $sense_ids
                    SET s.enriched = NULL
                ''', word=word, sense_ids=[s['id'] for s in matching_skeletons])
        
        enriched_data = get_enrichment(word, matching_skeletons, mock=False)
        
        if enriched_data:
            print(f"   ✅ Got {len(enriched_data)} enriched senses")
            
            # Step 5: Update database
            print(f"\n4. Updating database...")
            update_graph(conn, enriched_data)
            print(f"   ✅ Database updated")
            
            # Step 6: Check result
            print(f"\n5. Verifying fix...")
            with conn.get_session() as session:
                result = session.run('''
                    MATCH (w:Word {name: $word})-[:HAS_SENSE]->(s:Sense)
                    WHERE s.definition_zh IS NOT NULL
                    AND s.id IN $sense_ids
                    RETURN s.id as sense_id, s.definition_zh as def_zh
                ''', word=word, sense_ids=[s['id'] for s in matching_skeletons])
                
                fixed_senses = list(result)
                if fixed_senses:
                    print(f"   ✅ Fixed senses:")
                    for record in fixed_senses:
                        print(f"      - {record['sense_id']}: {record['def_zh'][:60]}...")
            
            return True
        else:
            print(f"   ❌ No enriched data returned")
            return False
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    parser = argparse.ArgumentParser(description='Fix data quality issues in word definitions')
    parser.add_argument('--word', type=str, help='Specific word to check/fix')
    parser.add_argument('--check-all', action='store_true', help='Check all words with issues')
    parser.add_argument('--fix-all', action='store_true', help='Fix all problematic words')
    parser.add_argument('--dry-run', action='store_true', help='Dry run (don\'t actually fix)')
    parser.add_argument('--force', action='store_true', help='Force re-enrichment even if already enriched')
    
    args = parser.parse_args()
    
    conn = Neo4jConnection()
    try:
        if not conn.verify_connectivity():
            print("❌ Failed to connect to Neo4j")
            return
        
        if args.word:
            if args.dry_run:
                check_word_quality(conn, args.word)
                print(f"\n[DRY RUN] Would fix '{args.word}'...")
                fix_word(conn, args.word, dry_run=True, force=args.force)
            else:
                check_word_quality(conn, args.word)
                fix_word(conn, args.word, dry_run=False, force=args.force)
        elif args.check_all:
            check_word_quality(conn)
        elif args.fix_all:
            print("⚠️  --fix-all not yet implemented. Use --word to fix specific words.")
        else:
            parser.print_help()
            
    finally:
        conn.close()


if __name__ == "__main__":
    main()

