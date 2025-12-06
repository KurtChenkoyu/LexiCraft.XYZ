#!/usr/bin/env python3
"""
Monitor Batch 2 Enrichment Progress
Tracks progress for ranks 1001-2000 (A2/B1 Gap)
"""

import time
import sys
from datetime import datetime
from src.database.neo4j_connection import Neo4jConnection

def get_batch2_status(conn: Neo4jConnection):
    """Get detailed status for Batch 2 (ranks 1001-2000)"""
    with conn.get_session() as session:
        # Total words in range
        total_result = session.run("""
            MATCH (w:Word)
            WHERE w.frequency_rank >= 1001 AND w.frequency_rank <= 2000
            RETURN count(w) as total
        """).single()
        total = total_result['total']
        
        # Enriched words in range
        enriched_result = session.run("""
            MATCH (w:Word)-[:HAS_SENSE]->(s:Sense)
            WHERE w.frequency_rank >= 1001 AND w.frequency_rank <= 2000
            WITH DISTINCT w
            WHERE EXISTS {
                MATCH (w)-[:HAS_SENSE]->(s2:Sense)
                WHERE s2.enriched = true
            }
            RETURN count(w) as enriched
        """).single()
        enriched = enriched_result['enriched']
        
        # Pending words in range
        pending_result = session.run("""
            MATCH (w:Word)-[:HAS_SENSE]->(s:Sense)
            WHERE w.frequency_rank >= 1001 
              AND w.frequency_rank <= 2000
              AND s.enriched IS NULL
            RETURN count(DISTINCT w) as pending
        """).single()
        pending = pending_result['pending']
        
        # Total enriched senses in range
        senses_result = session.run("""
            MATCH (w:Word)-[:HAS_SENSE]->(s:Sense)
            WHERE w.frequency_rank >= 1001 
              AND w.frequency_rank <= 2000
              AND s.enriched = true
            RETURN count(s) as enriched_senses
        """).single()
        enriched_senses = senses_result['enriched_senses']
        
        # Overall status
        overall_result = session.run("""
            MATCH (w:Word)-[:HAS_SENSE]->(s:Sense)
            WHERE s.enriched = true
            RETURN count(DISTINCT w) as total_enriched
        """).single()
        total_enriched = overall_result['total_enriched']
        
        return {
            'total': total,
            'enriched': enriched,
            'pending': pending,
            'enriched_senses': enriched_senses,
            'total_enriched': total_enriched,
            'pct': (enriched / total * 100) if total > 0 else 0
        }

def print_progress_bar(current, total, width=50):
    """Print a progress bar"""
    if total == 0:
        return "[" + " " * width + "]"
    filled = int(width * current / total)
    bar = "█" * filled + "░" * (width - filled)
    return f"[{bar}]"

def monitor_once(conn: Neo4jConnection):
    """Run a single status check"""
    status = get_batch2_status(conn)
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    print("=" * 70)
    print(f"📊 Batch 2 Enrichment Monitor - {timestamp}")
    print("=" * 70)
    print()
    print("🎯 Target Range: Ranks 1001-2000 (A2/B1 Gap)")
    print()
    print(f"   Total Words in Range: {status['total']}")
    print(f"   ✅ Enriched: {status['enriched']} ({status['pct']:.1f}%)")
    print(f"   ⏳ Pending: {status['pending']}")
    print(f"   📝 Enriched Senses: {status['enriched_senses']}")
    print()
    print("   Progress:")
    print(f"   {print_progress_bar(status['enriched'], status['total'])}")
    print()
    print("=" * 70)
    print(f"📈 Overall Database Status:")
    print(f"   Total Words Enriched: {status['total_enriched']}/3,500 ({status['total_enriched']/3500*100:.1f}%)")
    print("=" * 70)
    
    # Check if complete
    if status['pending'] == 0:
        print()
        print("=" * 70)
        print("🎉 Batch 2 Complete! All words in range 1001-2000 are enriched.")
        print("=" * 70)
        print()
    elif status['pending'] > 0:
        # Estimate remaining batches
        # More realistic calculation accounting for:
        # - Rate limits: 60 requests/minute (free tier)
        # - 429 errors with exponential backoff
        # - Daily limits: 1,500 requests/day
        # - Actual processing time: ~2-3 hours for 3,500 words = 0.32-0.49 words/sec
        batches_remaining = (status['pending'] + 9) // 10  # Round up (assuming batch_size=10)
        
        # Conservative estimate: use 0.35 words/sec (middle of 0.32-0.49 range)
        # This accounts for rate limits, 429 errors, and daily quotas
        words_per_second = 0.35
        estimated_seconds = status['pending'] / words_per_second
        
        # Also show optimistic estimate (if no rate limit issues)
        optimistic_seconds = batches_remaining * 2.5  # 2.5 sec per batch if no delays
        
        print()
        print(f"⏱️  Estimated Remaining:")
        print(f"   Conservative: ~{estimated_seconds/60:.1f} minutes ({batches_remaining} batches)")
        print(f"   Optimistic: ~{optimistic_seconds/60:.1f} minutes (if no rate limits)")
        print(f"   Note: Actual time depends on API rate limits and daily quotas")
        print()
    
    return status

def monitor_loop(conn: Neo4jConnection, interval=60):
    """Monitor continuously with periodic updates"""
    print("🔄 Starting continuous monitoring (Ctrl+C to stop)...")
    print()
    
    try:
        previous_enriched = 0
        while True:
            status = monitor_once(conn)
            
            # Show rate if we have previous data
            if previous_enriched > 0:
                new_words = status['enriched'] - previous_enriched
                if new_words > 0:
                    print(f"⚡ Rate: +{new_words} words since last check")
                    print()
            
            previous_enriched = status['enriched']
            
            # Check if complete
            if status['pending'] == 0:
                print("🎉 Batch 2 Complete! All words in range 1001-2000 are enriched.")
                break
            
            print(f"⏳ Next update in {interval} seconds...")
            print()
            time.sleep(interval)
            
    except KeyboardInterrupt:
        print("\n\n✅ Monitoring stopped by user.")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Monitor Batch 2 enrichment progress")
    parser.add_argument("--interval", type=int, default=60, 
                       help="Update interval in seconds (default: 60)")
    parser.add_argument("--once", action="store_true", 
                       help="Run once and exit (default: continuous)")
    args = parser.parse_args()
    
    conn = Neo4jConnection()
    try:
        if conn.verify_connectivity():
            if args.once:
                monitor_once(conn)
            else:
                monitor_loop(conn, interval=args.interval)
        else:
            print("❌ Failed to connect to Neo4j")
            sys.exit(1)
    finally:
        conn.close()

