#!/usr/bin/env python3
"""
Monitor enrichment process and automatically restart when it stops.

This script checks the enrichment status periodically and restarts the process
when it stops (due to quota limits, errors, or completion).
"""

import time
import subprocess
import sys
import json
from pathlib import Path
from datetime import datetime

# Add parent directory for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.pipeline.status import get_status_manager

CHECK_INTERVAL = 60  # Check every 60 seconds
MAX_RESTART_ATTEMPTS = 10  # Maximum restart attempts per day
RESTART_DELAY = 300  # Wait 5 minutes before restarting (in case quota resets)

def check_status():
    """Check current enrichment status."""
    status_manager = get_status_manager()
    status = status_manager.get_status()
    return status

def is_process_running(pid):
    """Check if process with given PID is still running."""
    try:
        # Check if process exists (works on Unix-like systems)
        subprocess.run(['kill', '-0', str(pid)], check=True, 
                      capture_output=True, timeout=1)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        return False

def start_enrichment(workers=10, save_interval=50):
    """Start the enrichment process in daemon mode."""
    script_path = Path(__file__).parent / "enrich_from_vocabulary.py"
    cmd = [
        sys.executable,
        str(script_path),
        "--workers", str(workers),
        "--save-interval", str(save_interval),
        "--resume",
        "--daemon"
    ]
    
    print(f"\n{'='*80}")
    print(f"🚀 Starting enrichment process...")
    print(f"   Command: {' '.join(cmd)}")
    print(f"{'='*80}\n")
    
    # Start in background
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=Path(__file__).parent.parent
    )
    
    # Give it a moment to start
    time.sleep(2)
    
    # Check if it started successfully
    if process.poll() is None:
        print(f"✅ Process started with PID: {process.pid}")
        return process.pid
    else:
        stdout, stderr = process.communicate()
        print(f"❌ Process failed to start:")
        print(f"   STDOUT: {stdout.decode()[:500]}")
        print(f"   STDERR: {stderr.decode()[:500]}")
        return None

def main():
    """Main monitoring loop."""
    print("=" * 80)
    print("🔍 Enrichment Process Monitor")
    print("=" * 80)
    print(f"   Check interval: {CHECK_INTERVAL} seconds")
    print(f"   Max restart attempts: {MAX_RESTART_ATTEMPTS}")
    print(f"   Restart delay: {RESTART_DELAY} seconds")
    print("=" * 80)
    print("\nMonitoring started. Press Ctrl+C to stop.\n")
    
    restart_count = 0
    last_status_time = None
    
    try:
        while True:
            # Check status
            status = check_status()
            current_time = datetime.now()
            
            # Check if process is actually running
            pid = status.pid
            process_running = pid and is_process_running(pid) if pid else False
            
            # Determine state
            if status.state == "running" and process_running:
                # Process is running normally
                if last_status_time is None or (current_time - last_status_time).total_seconds() > 300:
                    # Print status every 5 minutes
                    print(f"[{current_time.strftime('%H:%M:%S')}] ✅ Running - "
                          f"Processed: {status.processed_words:,}/{status.total_senses:,} "
                          f"({status.progress_percent:.1f}%) | "
                          f"Errors: {status.errors} | "
                          f"Cost: ${status.estimated_cost_usd:.2f}")
                    last_status_time = current_time
                    
            elif status.state == "stopped":
                # Process was stopped (likely quota limit)
                print(f"\n[{current_time.strftime('%H:%M:%S')}] ⏹️  Process stopped")
                print(f"   Processed: {status.processed_words:,}/{status.total_senses:,}")
                print(f"   Errors: {status.errors}")
                print(f"   Last error: {status.last_error[:200] if status.last_error else 'None'}")
                
                if restart_count < MAX_RESTART_ATTEMPTS:
                    print(f"\n⏳ Waiting {RESTART_DELAY} seconds before restart...")
                    print(f"   (Restart attempt {restart_count + 1}/{MAX_RESTART_ATTEMPTS})")
                    time.sleep(RESTART_DELAY)
                    
                    new_pid = start_enrichment()
                    if new_pid:
                        restart_count += 1
                        last_status_time = None
                    else:
                        print("❌ Failed to restart. Will try again later.")
                        time.sleep(60)
                else:
                    print(f"\n⚠️  Maximum restart attempts ({MAX_RESTART_ATTEMPTS}) reached.")
                    print("   Please check quota limits and restart manually.")
                    break
                    
            elif status.state == "completed":
                print(f"\n[{current_time.strftime('%H:%M:%S')}] ✅ Enrichment completed!")
                print(f"   Total processed: {status.processed_words:,}")
                print(f"   Total cost: ${status.estimated_cost_usd:.2f}")
                break
                
            elif status.state == "failed":
                print(f"\n[{current_time.strftime('%H:%M:%S')}] ❌ Process failed")
                print(f"   Errors: {status.errors}")
                print(f"   Last error: {status.last_error[:200] if status.last_error else 'None'}")
                
                if restart_count < MAX_RESTART_ATTEMPTS:
                    print(f"\n⏳ Waiting {RESTART_DELAY} seconds before restart...")
                    time.sleep(RESTART_DELAY)
                    new_pid = start_enrichment()
                    if new_pid:
                        restart_count += 1
                        last_status_time = None
                else:
                    print(f"\n⚠️  Maximum restart attempts reached.")
                    break
            else:
                # Idle or unknown state
                if not process_running:
                    print(f"[{current_time.strftime('%H:%M:%S')}] ⚠️  Process not running (state: {status.state})")
                    if restart_count < MAX_RESTART_ATTEMPTS:
                        print(f"   Attempting restart...")
                        time.sleep(10)
                        new_pid = start_enrichment()
                        if new_pid:
                            restart_count += 1
                            last_status_time = None
            
            # Wait before next check
            time.sleep(CHECK_INTERVAL)
            
    except KeyboardInterrupt:
        print("\n\n🛑 Monitor stopped by user")
    except Exception as e:
        print(f"\n❌ Monitor error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()


