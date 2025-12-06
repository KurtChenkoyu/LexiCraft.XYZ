#!/bin/bash
# Quick wrapper to monitor Batch 2 progress

cd "$(dirname "$0")"
source venv/bin/activate

if [ "$1" == "--watch" ] || [ "$1" == "-w" ]; then
    # Continuous monitoring
    python -m scripts.monitor_batch2 --interval 60
else
    # Single check
    python -m scripts.monitor_batch2 --once
fi

