#!/bin/bash
# Quick setup script for Google API

echo "🔧 Google API Setup Helper"
echo "=========================="
echo ""

# Check if .env exists
if [ -f .env ]; then
    echo "✓ .env file already exists"
    if grep -q "GOOGLE_API_KEY" .env; then
        echo "✓ GOOGLE_API_KEY is already set"
        echo ""
        echo "You're all set! You can test it with:"
        echo "  python3 -m src.agent --word bank --mock"
        echo ""
    else
        echo ""
        echo "⚠️  GOOGLE_API_KEY not found in .env"
        echo ""
        echo "Please add your API key to .env:"
        echo "  GOOGLE_API_KEY=your_api_key_here"
        echo ""
        echo "Get your API key from: https://aistudio.google.com/"
    fi
else
    echo "Creating .env file..."
    cat > .env << EOF
# Google Generative AI (Gemini) API
# Get your API key from: https://aistudio.google.com/
GOOGLE_API_KEY=your_api_key_here

# Neo4j Aura Connection (if you have it)
# NEO4J_URI=neo4j+s://xxxxx.databases.neo4j.io
# NEO4J_USER=neo4j
# NEO4J_PASSWORD=your_password_here

# PostgreSQL (Supabase) Connection (if you have it)
# DATABASE_URL=postgresql://postgres:password@db.xxxxx.supabase.co:5432/postgres
EOF
    echo "✓ Created .env file"
    echo ""
    echo "⚠️  Please edit .env and add your Google API key:"
    echo "  1. Get your API key from: https://aistudio.google.com/"
    echo "  2. Replace 'your_api_key_here' with your actual API key"
    echo ""
fi

echo "📖 For detailed instructions, see: GOOGLE_API_SETUP.md"

