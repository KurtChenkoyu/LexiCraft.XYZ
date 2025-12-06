#!/bin/bash
# Wrapper script to run all batches sequentially

cd "$(dirname "$0")"
source venv/bin/activate

python -m scripts.run_all_batches "$@"

