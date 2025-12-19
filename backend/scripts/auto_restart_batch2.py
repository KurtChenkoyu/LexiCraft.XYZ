#!/usr/bin/env python3
"""
Auto-restart Batch 2 enrichment process.
Checks status every 2 minutes and restarts if process stops.
"""

import time
import subprocess
import sys
from datetime import datetime
from src.database.neo4j_connection import Neo4jConnection
from scripts.monitor_batch2 import get_batch2_status

def is_process_running():
    """Check if Batch 2 enrichment process is running"""
    try:
        result = subprocess.run(
            ["pgrep", "-f", "agent_batched.*1001.*2000"],
            capture_output=True,
            text=True
        )
        return result.returncode == 0 and result.stdout.strip() != ""
    except:
        return False

def restart_process():
    """Restart Batch 2 enrichment process"""
    print(f"\n{'='*70}")
    print(f"🔄 Restarting Batch 2 enrichment - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*70}\n")
    
    cmd = [
        sys.executable, "-m", "src.agent_batched",
        "--min-rank", "1001",
        "--max-rank", "2000",
        "--batch-size", "10"
    ]
    
    # Start in background
    process = subprocess.Popen(
        cmd,
        cwd="/Users/kurtchen/LexiCraft.xyz/backend",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    return process

def check_progress(conn):
    """Check current Batch 2 progress"""
    status = get_batch2_status(conn)
    return status['enriched'], status['total'], status['pending']

def main():
    """Main monitoring loop"""
    print("=" * 70)
    print("🤖 Batch 2 Auto-Restart Monitor")
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
                time.sleep(10)  # Wait a bit before checking again
            
            # Check progress
            try:
                enriched, total, pending = check_progress(conn)
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
                    print("🎉 Batch 2 Complete! All words enriched.")
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

