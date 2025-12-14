#!/bin/bash
# Start the LexiCraft backend server
# Usage: ./start-server.sh

cd "$(dirname "$0")"

# Use the venv from this directory
./venv/bin/uvicorn src.main:app --reload --port 8000 --log-level info

