#!/usr/bin/env python3
"""
Automated Batch Runner
Runs all enrichment batches sequentially:
- Batch 2: Ranks 1001-2000
- Batch 3: Ranks 2001-3000
- Batch 4: Ranks 3001-3500
"""

import subprocess
import sys
import time
from datetime import datetime
from src.database.neo4j_connection import Neo4jConnection

BATCHES = [
    {"name": "Batch 2", "min_rank": 1001, "max_rank": 2000, "limit": 2000},
    {"name": "Batch 3", "min_rank": 2001, "max_rank": 3000, "limit": 2000},
    {"name": "Batch 4", "min_rank": 3001, "max_rank": 3500, "limit": 1000},
]

def check_batch_complete(conn: Neo4jConnection, min_rank: int, max_rank: int) -> bool:
    """Check if a batch is complete (all words in range are enriched)"""
    with conn.get_session() as session:
        # Count pending words in range
        result = session.run("""
            MATCH (w:Word)-[:HAS_SENSE]->(s:Sense)
            WHERE w.frequency_rank >= $min_rank 
              AND w.frequency_rank <= $max_rank
              AND s.enriched IS NULL
            RETURN count(DISTINCT w) as pending
        """, min_rank=min_rank, max_rank=max_rank).single()
        
        return result['pending'] == 0

def get_batch_progress(conn: Neo4jConnection, min_rank: int, max_rank: int):
    """Get progress for a batch"""
    with conn.get_session() as session:
        result = session.run("""
            MATCH (w:Word)
            WHERE w.frequency_rank >= $min_rank AND w.frequency_rank <= $max_rank
            WITH count(w) as total
            MATCH (w:Word)-[:HAS_SENSE]->(s:Sense)
            WHERE w.frequency_rank >= $min_rank AND w.frequency_rank <= $max_rank
            WITH total, DISTINCT w
            WHERE EXISTS {
                MATCH (w)-[:HAS_SENSE]->(s2:Sense)
                WHERE s2.enriched = true
            }
            RETURN total, count(w) as enriched
        """, min_rank=min_rank, max_rank=max_rank).single()
        
        return {
            'total': result['total'],
            'enriched': result['enriched'],
            'pct': (result['enriched'] / result['total'] * 100) if result['total'] > 0 else 0
        }

def run_batch(batch_info: dict, batch_size: int = 10):
    """Run a single batch"""
    name = batch_info['name']
    min_rank = batch_info['min_rank']
    max_rank = batch_info['max_rank']
    limit = batch_info['limit']
    
    print("=" * 70)
    print(f"🚀 Starting {name} (Ranks {min_rank}-{max_rank})")
    print("=" * 70)
    print()
    
    # Build command
    cmd = [
        sys.executable, "-m", "src.agent_batched",
        "--batch-size", str(batch_size),
        "--min-rank", str(min_rank),
        "--max-rank", str(max_rank),
        "--limit", str(limit)
    ]
    
    # Run the batch
    try:
        result = subprocess.run(cmd, cwd="/Users/kurtchen/LexiCraft.xyz/backend")
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Error running {name}: {e}")
        return False

def run_all_batches(batch_size: int = 10, start_from: int = 2):
    """Run all batches sequentially"""
    print("=" * 70)
    print("🏭 Automated Batch Enrichment Runner")
    print("=" * 70)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    conn = Neo4jConnection()
    try:
        if not conn.verify_connectivity():
            print("❌ Failed to connect to Neo4j")
            return False
        
        # Start from specified batch (default: 2, since Batch 1 is done)
        batches_to_run = [b for b in BATCHES if int(b['name'].split()[-1]) >= start_from]
        
        for i, batch_info in enumerate(batches_to_run, start=start_from):
            batch_num = int(batch_info['name'].split()[-1])
            name = batch_info['name']
            min_rank = batch_info['min_rank']
            max_rank = batch_info['max_rank']
            
            # Check if already complete
            if check_batch_complete(conn, min_rank, max_rank):
                progress = get_batch_progress(conn, min_rank, max_rank)
                print(f"✅ {name} already complete ({progress['enriched']}/{progress['total']} words)")
                print()
                continue
            
            # Show current progress
            progress = get_batch_progress(conn, min_rank, max_rank)
            print(f"📊 {name} Status: {progress['enriched']}/{progress['total']} words ({progress['pct']:.1f}%)")
            print()
            
            # Run the batch
            success = run_batch(batch_info, batch_size)
            
            if not success:
                print(f"❌ {name} failed. Stopping.")
                return False
            
            # Verify completion
            time.sleep(2)  # Brief pause for database to update
            if check_batch_complete(conn, min_rank, max_rank):
                print(f"✅ {name} complete!")
            else:
                progress = get_batch_progress(conn, min_rank, max_rank)
                print(f"⚠️ {name} partially complete: {progress['enriched']}/{progress['total']} words")
                print("   You may need to run this batch again to complete it.")
            
            print()
            
            # Brief pause between batches
            if i < len(batches_to_run):
                print("⏸️  Pausing 5 seconds before next batch...")
                time.sleep(5)
                print()
        
        print("=" * 70)
        print("🎉 All batches complete!")
        print(f"Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)
        return True
        
    finally:
        conn.close()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run all enrichment batches sequentially")
    parser.add_argument("--batch-size", type=int, default=10, 
                       help="Words per API call (default: 10)")
    parser.add_argument("--start-from", type=int, default=2,
                       help="Start from batch number (default: 2)")
    args = parser.parse_args()
    
    success = run_all_batches(batch_size=args.batch_size, start_from=args.start_from)
    sys.exit(0 if success else 1)

