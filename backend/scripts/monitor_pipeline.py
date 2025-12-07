#!/usr/bin/env python3
"""
Pipeline Monitoring Script

Quick status check for the vocabulary enrichment pipeline.
Shows progress, rate, ETA, and detects if pipeline is stuck.

Usage:
    python scripts/monitor_pipeline.py
    python scripts/monitor_pipeline.py --watch  # Auto-refresh every 10 seconds
"""

import json
import sys
import time
import os
from pathlib import Path
from datetime import datetime

def get_checkpoint_status():
    """Get status from checkpoint file."""
    checkpoint_path = Path(__file__).parent.parent / 'logs' / 'enrichment_checkpoint.json'
    
    if not checkpoint_path.exists():
        return None
    
    with open(checkpoint_path, 'r') as f:
        cp = json.load(f)
    
    words_processed = len(cp.get('processed_words', []))
    senses_created = len(cp.get('enriched_senses', {}))
    stats = cp.get('stats', {})
    timestamp = cp.get('timestamp', '')
    
    # Check file modification time
    mtime = checkpoint_path.stat().st_mtime
    mtime_dt = datetime.fromtimestamp(mtime)
    age_seconds = (datetime.now() - mtime_dt).total_seconds()
    age_minutes = age_seconds / 60
    
    return {
        'words': words_processed,
        'senses': senses_created,
        'ai_calls': stats.get('ai_calls', 0),
        'timestamp': timestamp,
        'age_minutes': age_minutes,
        'mtime': mtime_dt
    }

def get_status_file():
    """Get status from status file."""
    status_path = Path(__file__).parent.parent / 'logs' / 'pipeline_status.json'
    
    if not status_path.exists():
        return None
    
    with open(status_path, 'r') as f:
        return json.load(f)

def check_process_running():
    """Check if pipeline process is running."""
    import subprocess
    result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
    return 'enrich_vocabulary_v2' in result.stdout

def format_time(seconds):
    """Format seconds into readable time."""
    if seconds < 60:
        return f"{seconds:.0f}s"
    elif seconds < 3600:
        return f"{seconds/60:.1f}m"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h {minutes}m"

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Monitor pipeline status')
    parser.add_argument('--watch', action='store_true', help='Auto-refresh every 10 seconds')
    args = parser.parse_args()
    
    while True:
        # Clear screen if watching
        if args.watch:
            os.system('clear' if os.name != 'nt' else 'cls')
        
        print("=" * 70)
        print("📊 Pipeline V2 Status Monitor")
        print("=" * 70)
        print()
        
        # Check if process is running
        is_running = check_process_running()
        status_icon = "🟢" if is_running else "🔴"
        print(f"Process: {status_icon} {'Running' if is_running else 'Not Running'}")
        print()
        
        # Get checkpoint status
        cp = get_checkpoint_status()
        if cp:
            total_words = 13376  # Total words in master list
            progress_pct = (cp['words'] / total_words * 100) if total_words > 0 else 0
            remaining = total_words - cp['words']
            
            print(f"📝 Progress: {cp['words']:,} / {total_words:,} words ({progress_pct:.1f}%)")
            print(f"   Remaining: {remaining:,} words")
            print(f"   Senses created: {cp['senses']:,}")
            print(f"   AI calls: {cp['ai_calls']:,}")
            print(f"   Estimated cost: ${cp['ai_calls'] * 0.0001:.2f} USD")
            print()
            
            # Check if checkpoint is fresh
            if cp['age_minutes'] < 2:
                print(f"✅ Checkpoint updated {cp['age_minutes']:.1f} minutes ago (fresh)")
            elif cp['age_minutes'] < 5:
                print(f"⚠️  Checkpoint updated {cp['age_minutes']:.1f} minutes ago")
            else:
                print(f"🔴 Checkpoint updated {cp['age_minutes']:.1f} minutes ago (STALE - pipeline may be stuck!)")
            print()
            
            # Calculate rate and ETA
            if cp['timestamp']:
                try:
                    start_dt = datetime.fromisoformat(cp['timestamp'].replace('Z', '+00:00'))
                    # Use checkpoint timestamp as reference
                    # Actually, we need start_time from stats
                    stats = json.load(open(Path(__file__).parent.parent / 'logs' / 'enrichment_checkpoint.json'))['stats']
                    start_time = stats.get('start_time', '')
                    if start_time:
                        start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                        elapsed = (datetime.now() - start_dt).total_seconds()
                        if elapsed > 0:
                            rate = cp['words'] / elapsed * 60  # words per minute
                            eta_seconds = (remaining / (rate / 60)) if rate > 0 else 0
                            print(f"⚡ Rate: {rate:.1f} words/minute")
                            print(f"⏱️  ETA: {format_time(eta_seconds)}")
                except:
                    pass
        else:
            print("❌ No checkpoint found")
        
        print()
        
        # Get status file
        status = get_status_file()
        if status:
            print("📋 Status File:")
            print(f"   State: {status.get('state', 'unknown')}")
            print(f"   Current word: {status.get('current_word', 'N/A')}")
            if status.get('updated_at'):
                updated = datetime.fromisoformat(status['updated_at'].replace('Z', '+00:00'))
                age = (datetime.now() - updated).total_seconds() / 60
                print(f"   Last updated: {age:.1f} minutes ago")
        
        print()
        print("=" * 70)
        
        if not args.watch:
            break
        
        print("\nRefreshing in 10 seconds... (Ctrl+C to stop)")
        time.sleep(10)

if __name__ == '__main__':
    main()

