#!/bin/bash

# Integration Test Runner for LexiSurvey
# Runs all integration tests and verification scripts

set -e

echo "=========================================="
echo "LexiSurvey Integration Tests"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if we're in the backend directory
if [ ! -f "requirements.txt" ]; then
    echo -e "${RED}Error: Must run from backend directory${NC}"
    exit 1
fi

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# Install test dependencies if needed
echo "Checking dependencies..."
pip install -q pytest pytest-asyncio httpx

echo ""
echo "=========================================="
echo "1. Testing CONFUSED_WITH Relationships"
echo "=========================================="
python scripts/verify_confused_with.py
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ CONFUSED_WITH verification passed${NC}"
else
    echo -e "${RED}❌ CONFUSED_WITH verification failed${NC}"
    exit 1
fi

echo ""
echo "=========================================="
echo "2. Running Integration Tests"
echo "=========================================="
pytest tests/test_survey_integration.py -v
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Integration tests passed${NC}"
else
    echo -e "${RED}❌ Integration tests failed${NC}"
    exit 1
fi

echo ""
echo "=========================================="
echo "3. Testing CONFUSED_WITH Usage"
echo "=========================================="
pytest tests/test_confused_with_relationships.py -v
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ CONFUSED_WITH tests passed${NC}"
else
    echo -e "${RED}❌ CONFUSED_WITH tests failed${NC}"
    exit 1
fi

echo ""
echo "=========================================="
echo -e "${GREEN}✅ All tests passed!${NC}"
echo "=========================================="


