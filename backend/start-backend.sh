#!/bin/bash
# ============================================
# LexiCraft Backend Startup Script
# ============================================
# This script ensures ONLY the correct backend runs by:
# 1. Killing any old/wrong backend processes
# 2. Verifying the correct project path
# 3. Starting the backend from the correct location
# ============================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get the script directory (backend/)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
EXPECTED_PROJECT_NAME="LexiCraft.xyz"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}LexiCraft Backend Startup${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Verify we're in the correct project
if [[ ! "$PROJECT_ROOT" == *"$EXPECTED_PROJECT_NAME"* ]]; then
    echo -e "${RED}❌ ERROR: Wrong project directory!${NC}"
    echo -e "${YELLOW}Expected: .../$EXPECTED_PROJECT_NAME/backend${NC}"
    echo -e "${YELLOW}Found: $PROJECT_ROOT${NC}"
    echo ""
    echo -e "${YELLOW}This script should only be run from the LexiCraft.xyz project.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Project path verified: $PROJECT_ROOT${NC}"
echo ""

# Step 1: Find and kill ALL backend processes on port 8000
echo -e "${YELLOW}🔍 Checking for existing backend processes...${NC}"

# Find processes using port 8000
PORT_PIDS=$(lsof -ti :8000 2>/dev/null || true)

if [ -n "$PORT_PIDS" ]; then
    echo -e "${YELLOW}⚠️  Found processes on port 8000: $PORT_PIDS${NC}"
    
    # Check each process to see if it's from the wrong project
    for PID in $PORT_PIDS; do
        # Get the process working directory
        PROC_CWD=$(lsof -p "$PID" 2>/dev/null | grep cwd | awk '{print $9}' || echo "")
        PROC_CMD=$(ps -p "$PID" -o command= 2>/dev/null || echo "")
        
        # Check if it's from a different project
        if [[ "$PROC_CMD" == *"earn-money-back-project"* ]] || [[ "$PROC_CWD" == *"earn-money-back-project"* ]]; then
            echo -e "${RED}❌ Killing WRONG backend (PID $PID) from earn-money-back-project${NC}"
            kill -9 "$PID" 2>/dev/null || true
        elif [[ "$PROC_CMD" == *"uvicorn"* ]] && [[ ! "$PROC_CWD" == *"$EXPECTED_PROJECT_NAME"* ]]; then
            echo -e "${RED}❌ Killing WRONG backend (PID $PID) from different project${NC}"
            kill -9 "$PID" 2>/dev/null || true
        else
            echo -e "${YELLOW}⚠️  Found backend process (PID $PID) - checking if it's correct...${NC}"
            # If it's from the correct project, we'll kill it anyway to restart fresh
            kill -9 "$PID" 2>/dev/null || true
        fi
    done
    
    sleep 1
    echo -e "${GREEN}✅ Cleared port 8000${NC}"
else
    echo -e "${GREEN}✅ No existing processes on port 8000${NC}"
fi

# Step 2: Kill any uvicorn processes from wrong projects
echo ""
echo -e "${YELLOW}🔍 Checking for uvicorn processes from wrong projects...${NC}"

ALL_UVICORN=$(ps aux | grep "[u]vicorn.*8000" | awk '{print $2}' || true)

if [ -n "$ALL_UVICORN" ]; then
    for PID in $ALL_UVICORN; do
        PROC_CMD=$(ps -p "$PID" -o command= 2>/dev/null || echo "")
        PROC_CWD=$(lsof -p "$PID" 2>/dev/null | grep cwd | awk '{print $9}' || echo "")
        
        if [[ "$PROC_CMD" == *"earn-money-back-project"* ]] || [[ "$PROC_CWD" == *"earn-money-back-project"* ]]; then
            echo -e "${RED}❌ Killing wrong uvicorn (PID $PID) from earn-money-back-project${NC}"
            kill -9 "$PID" 2>/dev/null || true
        elif [[ ! "$PROC_CWD" == *"$EXPECTED_PROJECT_NAME"* ]] && [[ "$PROC_CMD" == *"uvicorn"* ]]; then
            echo -e "${RED}❌ Killing wrong uvicorn (PID $PID) from different project${NC}"
            kill -9 "$PID" 2>/dev/null || true
        fi
    done
fi

# Step 3: Verify port is free
sleep 1
if lsof -ti :8000 >/dev/null 2>&1; then
    echo -e "${RED}❌ ERROR: Port 8000 is still in use!${NC}"
    echo -e "${YELLOW}Please manually kill the process: lsof -ti :8000 | xargs kill -9${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Port 8000 is free${NC}"
echo ""

# Step 4: Verify virtual environment exists
if [ ! -d "$SCRIPT_DIR/venv" ]; then
    echo -e "${RED}❌ ERROR: Virtual environment not found!${NC}"
    echo -e "${YELLOW}Please create it: cd $SCRIPT_DIR && python3 -m venv venv${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Virtual environment found${NC}"
echo ""

# Step 5: Start the backend
echo -e "${BLUE}🚀 Starting backend server...${NC}"
echo -e "${BLUE}   Project: $PROJECT_ROOT${NC}"
echo -e "${BLUE}   Backend:  $SCRIPT_DIR${NC}"
echo ""

cd "$SCRIPT_DIR"
source venv/bin/activate

# Enable debug logging for learner pipeline
export DEBUG_LEARNER_PIPELINE=true

# Start uvicorn with reload
exec uvicorn src.main:app --reload --port 8000 --log-level info


