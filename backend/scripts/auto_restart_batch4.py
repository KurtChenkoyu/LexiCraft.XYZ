#!/usr/bin/env python3
"""
Auto-restart Batch 4 enrichment process.
Checks status every 2 minutes and restarts if process stops.
"""

import time
import subprocess
import sys
from datetime import datetime
from src.database.neo4j_connection import Neo4jConnection

def get_batch4_status(conn):
    """Get Batch 4 status"""
    with conn.get_session() as session:
        total_result = session.run("""
            MATCH (w:Word)
            WHERE w.frequency_rank >= 3001 AND w.frequency_rank <= 3500
            RETURN count(w) as total
        """).single()
        total = total_result['total']
        
        enriched_result = session.run("""
            MATCH (w:Word)-[:HAS_SENSE]->(s:Sense)
            WHERE w.frequency_rank >= 3001 AND w.frequency_rank <= 3500
            WITH DISTINCT w
            WHERE EXISTS {
                MATCH (w)-[:HAS_SENSE]->(s2:Sense)
                WHERE s2.enriched = true
            }
            RETURN count(w) as enriched
        """).single()
        enriched = enriched_result['enriched']
        
        pending_result = session.run("""
            MATCH (w:Word)-[:HAS_SENSE]->(s:Sense)
            WHERE w.frequency_rank >= 3001 
              AND w.frequency_rank <= 3500
              AND s.enriched IS NULL
            RETURN count(DISTINCT w) as pending
        """).single()
        pending = pending_result['pending']
        
        return {'total': total, 'enriched': enriched, 'pending': pending}

def is_process_running():
    """Check if Batch 4 enrichment process is running"""
    try:
        result = subprocess.run(
            ["pgrep", "-f", "agent_batched.*3001.*3500"],
            capture_output=True,
            text=True
        )
        return result.returncode == 0 and result.stdout.strip() != ""
    except:
        return False

def restart_process():
    """Restart Batch 4 enrichment process"""
    print(f"\n{'='*70}")
    print(f"🔄 Restarting Batch 4 enrichment - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*70}\n")
    
    cmd = [
        sys.executable, "-m", "src.agent_batched",
        "--min-rank", "3001",
        "--max-rank", "3500",
        "--batch-size", "10"
    ]
    
    process = subprocess.Popen(
        cmd,
        cwd="/Users/kurtchen/LexiCraft.xyz/backend",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    return process

def main():
    """Main monitoring loop"""
    print("=" * 70)
    print("🤖 Batch 4 Auto-Restart Monitor")
    print("=" * 70)
    print("Checking every 2 minutes. Press Ctrl+C to stop.")
    print()
    
    conn = Neo4jConnection()
    if not conn.verify_connectivity():
        print("❌ Failed to connect to Neo4j")
        return
    
    last_enriched = None
    check_interval = 120  # 2 minutes
    
    try:
        while True:
            # Check if process is running
            if not is_process_running():
                print(f"\n⚠️  Process not running at {datetime.now().strftime('%H:%M:%S')}")
                restart_process()
                time.sleep(10)
            
            # Check progress
            try:
                status = get_batch4_status(conn)
                enriched = status['enriched']
                total = status['total']
                pending = status['pending']
                pct = (enriched / total * 100) if total > 0 else 0
                
                if last_enriched is not None:
                    progress = enriched - last_enriched
                    if progress > 0:
                        print(f"✅ Progress: {enriched}/{total} ({pct:.1f}%) - +{progress} words since last check")
                    else:
                        print(f"⏳ Status: {enriched}/{total} ({pct:.1f}%) - {pending} pending")
                else:
                    print(f"📊 Initial: {enriched}/{total} ({pct:.1f}%) - {pending} pending")
                
                last_enriched = enriched
                
                # Check if complete
                if pending == 0:
                    print("\n" + "=" * 70)
                    print("🎉 Batch 4 Complete! All words enriched.")
                    print("=" * 70)
                    break
                    
            except Exception as e:
                print(f"⚠️  Error checking progress: {e}")
            
            # Wait before next check
            time.sleep(check_interval)
            
    except KeyboardInterrupt:
        print("\n\n⏹️  Monitoring stopped by user")
    finally:
        conn.close()

if __name__ == "__main__":
    main()

