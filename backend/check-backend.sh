#!/bin/bash
# ============================================
# LexiCraft Backend Health Check Script
# ============================================
# Verifies which backend is running and if it's the correct one
# ============================================

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

EXPECTED_PROJECT="LexiCraft.xyz"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Backend Health Check${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check if backend is running
if ! lsof -ti :8000 >/dev/null 2>&1; then
    echo -e "${RED}❌ No backend running on port 8000${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Backend process found on port 8000${NC}"
echo ""

# Get process info
PID=$(lsof -ti :8000 | head -1)
PROC_CMD=$(ps -p "$PID" -o command= 2>/dev/null || echo "")
PROC_CWD=$(lsof -p "$PID" 2>/dev/null | grep cwd | awk '{print $9}' || echo "")

echo -e "${BLUE}Process Info:${NC}"
echo "  PID: $PID"
echo "  Command: ${PROC_CMD:0:80}..."
echo "  Working Directory: $PROC_CWD"
echo ""

# Check if it's from the wrong project
# Only check the working directory, not the Python path (which might contain old paths)
if [[ "$PROC_CWD" == *"earn-money-back-project"* ]]; then
    echo -e "${RED}❌ WRONG BACKEND: Running from earn-money-back-project!${NC}"
    echo -e "${YELLOW}   This is the OLD project. Kill it and start the correct one.${NC}"
    exit 1
elif [[ ! "$PROC_CWD" == *"$EXPECTED_PROJECT"* ]]; then
    echo -e "${RED}❌ WRONG BACKEND: Not running from $EXPECTED_PROJECT!${NC}"
    echo -e "${YELLOW}   Found: $PROC_CWD${NC}"
    echo -e "${YELLOW}   Expected: .../$EXPECTED_PROJECT/backend${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Backend is from correct project${NC}"
echo ""

# Check health endpoint
echo -e "${BLUE}Checking health endpoint...${NC}"
HEALTH_RESPONSE=$(curl -s --max-time 2 http://localhost:8000/health 2>/dev/null || echo "")

if [ -z "$HEALTH_RESPONSE" ]; then
    echo -e "${RED}❌ Backend not responding to /health${NC}"
    exit 1
fi

# Extract project path from response
PROJECT_PATH=$(echo "$HEALTH_RESPONSE" | grep -o '"project_path":"[^"]*' | cut -d'"' -f4 || echo "")

if [ -n "$PROJECT_PATH" ]; then
    if [[ "$PROJECT_PATH" == *"$EXPECTED_PROJECT"* ]]; then
        echo -e "${GREEN}✅ Health check passed${NC}"
        echo -e "${GREEN}   Project path: $PROJECT_PATH${NC}"
        echo ""
        echo -e "${GREEN}✅ Backend is running correctly!${NC}"
    else
        echo -e "${RED}❌ Health check shows wrong project path: $PROJECT_PATH${NC}"
        exit 1
    fi
else
    echo -e "${YELLOW}⚠️  Health check responded but couldn't parse project path${NC}"
    echo "Response: $HEALTH_RESPONSE"
fi

