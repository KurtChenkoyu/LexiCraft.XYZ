#!/usr/bin/env python3
"""
Monitor Level 2 content generation progress.
Shows current status, progress, and estimated completion time.
"""

import sys
import json
import time
from pathlib import Path
from datetime import datetime, timedelta

# Add backend to path and import directly
backend_path = str(Path(__file__).parent.parent)
sys.path.insert(0, backend_path)

# Import Neo4j connection directly to avoid database models import
import importlib.util
spec = importlib.util.spec_from_file_location("neo4j_connection", f"{backend_path}/src/database/neo4j_connection.py")
neo4j_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(neo4j_module)
Neo4jConnection = neo4j_module.Neo4jConnection

def load_checkpoint(checkpoint_file: str = "level2_checkpoint.json"):
    """Load checkpoint data."""
    checkpoint_path = Path(checkpoint_file)
    if checkpoint_path.exists():
        try:
            with open(checkpoint_path, 'r') as f:
                return json.load(f)
        except:
            return None
    return None

def get_database_status(conn: Neo4jConnection):
    """Get current database status."""
    session = conn.get_session()
    
    # Total eligible
    result = session.run("""
        MATCH (s:Sense)
        WHERE s.enriched = true 
          AND (s.stage2_enriched IS NULL OR s.stage2_enriched = false)
        RETURN count(s) as remaining
    """)
    remaining = result.single()['remaining']
    
    # Total completed
    result = session.run("""
        MATCH (s:Sense)
        WHERE s.stage2_enriched = true
        RETURN count(s) as completed
    """)
    completed = result.single()['completed']
    
    session.close()
    return completed, remaining

def monitor_level2(checkpoint_file: str = "level2_checkpoint.json"):
    """Monitor Level 2 generation progress."""
    conn = Neo4jConnection()
    
    print("=" * 60)
    print("Level 2 Content Generation Monitor")
    print("=" * 60)
    
    # Database status
    completed, remaining = get_database_status(conn)
    total = completed + remaining
    
    print(f"\n📊 Database Status:")
    print(f"   Completed: {completed:,} / {total:,} ({completed/total*100:.1f}%)")
    print(f"   Remaining: {remaining:,}")
    
    # Checkpoint status
    checkpoint = load_checkpoint(checkpoint_file)
    if checkpoint:
        processed = checkpoint.get("total_processed", 0)
        start_time = checkpoint.get("start_time")
        last_updated = checkpoint.get("last_updated")
        
        print(f"\n📋 Checkpoint Status:")
        print(f"   Total processed (this run): {processed:,}")
        
        if start_time:
            elapsed = time.time() - start_time
            print(f"   Time elapsed: {elapsed/3600:.1f} hours ({elapsed/60:.1f} minutes)")
            
            if processed > 0 and elapsed > 0:
                rate = processed / elapsed
                print(f"   Rate: {rate*60:.1f} senses/minute ({rate:.2f} senses/second)")
                
                if remaining > 0:
                    eta_seconds = remaining / rate
                    eta = timedelta(seconds=int(eta_seconds))
                    print(f"   ETA: {eta} ({eta_seconds/3600:.1f} hours)")
        
        if last_updated:
            last_update_time = datetime.fromtimestamp(last_updated)
            time_since_update = time.time() - last_updated
            print(f"   Last update: {last_update_time.strftime('%Y-%m-%d %H:%M:%S')} ({time_since_update/60:.1f} minutes ago)")
            
            if time_since_update > 300:  # 5 minutes
                print(f"   ⚠️  WARNING: No update in {time_since_update/60:.1f} minutes - process may be stuck!")
    else:
        print(f"\n📋 Checkpoint Status:")
        print(f"   No checkpoint file found - process may not be running")
    
    conn.close()
    
    print(f"\n{'='*60}")
    print("💡 To check if process is running:")
    print("   ps aux | grep agent_stage2")
    print("💡 To view live logs:")
    print("   tail -f level2_enrichment.log")

if __name__ == "__main__":
    checkpoint_file = sys.argv[1] if len(sys.argv) > 1 else "level2_checkpoint.json"
    monitor_level2(checkpoint_file)

