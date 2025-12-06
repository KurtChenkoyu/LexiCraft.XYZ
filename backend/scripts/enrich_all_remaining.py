#!/usr/bin/env python3
"""
Enrich all remaining unenriched senses.
This script processes all senses that are not yet enriched.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database.neo4j_connection import Neo4jConnection
from src.agent_batched import run_batched_agent

def enrich_all_remaining(conn: Neo4jConnection, batch_size: int = 10, mock: bool = False):
    """
    Enrich all remaining unenriched senses.
    
    Args:
        conn: Neo4j connection
        batch_size: Number of words to process per API call (default: 10)
        mock: Use mock data instead of real API calls
    """
    print("=" * 80)
    print("ENRICHING ALL REMAINING SENSES")
    print("=" * 80)
    print()
    
    # Check current status
    with conn.get_session() as session:
        # Count unenriched senses
        result = session.run("""
            MATCH (w:Word)-[:HAS_SENSE]->(s:Sense)
            WHERE s.enriched IS NULL OR s.enriched = false
            RETURN count(DISTINCT w) as words_with_unenriched,
                   count(s) as unenriched_senses
        """).single()
        
        words_with_unenriched = result['words_with_unenriched']
        unenriched_senses = result['unenriched_senses']
        
        print(f"Current Status:")
        print(f"  Words with unenriched senses: {words_with_unenriched:,}")
        print(f"  Total unenriched senses: {unenriched_senses:,}")
        print()
        
        if unenriched_senses == 0:
            print("✅ All senses are already enriched!")
            return
        
        # Estimate batches needed
        estimated_batches = (words_with_unenriched + batch_size - 1) // batch_size
        print(f"Estimated batches: ~{estimated_batches} (batch_size={batch_size})")
        print()
    
    # Use the batched agent to process all remaining words
    # No limit specified = process all
    print("Starting batched enrichment...")
    print("(This may take a while depending on API rate limits)")
    print()
    
    run_batched_agent(
        conn=conn,
        batch_size=batch_size,
        limit=None,  # Process all
        mock=mock
    )
    
    print()
    print("=" * 80)
    print("ENRICHMENT COMPLETE")
    print("=" * 80)
    
    # Verify final status
    with conn.get_session() as session:
        result = session.run("""
            MATCH (w:Word)-[:HAS_SENSE]->(s:Sense)
            WHERE s.enriched IS NULL OR s.enriched = false
            RETURN count(DISTINCT w) as words_with_unenriched,
                   count(s) as unenriched_senses
        """).single()
        
        remaining_words = result['words_with_unenriched']
        remaining_senses = result['unenriched_senses']
        
        if remaining_senses == 0:
            print("✅ All senses are now enriched!")
        else:
            print(f"⚠️ {remaining_senses:,} senses still unenriched across {remaining_words:,} words")
            print("   (This may be due to API errors or rate limits)")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Enrich all remaining unenriched senses")
    parser.add_argument("--batch-size", type=int, default=10, 
                       help="Number of words to process per API call (default: 10)")
    parser.add_argument("--mock", action="store_true", 
                       help="Use mock data instead of real API calls")
    args = parser.parse_args()
    
    conn = Neo4jConnection()
    try:
        if conn.verify_connectivity():
            enrich_all_remaining(conn, batch_size=args.batch_size, mock=args.mock)
        else:
            print("❌ Failed to connect to Neo4j database.")
            sys.exit(1)
    finally:
        conn.close()


