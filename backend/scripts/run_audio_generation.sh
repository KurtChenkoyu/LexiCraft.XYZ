#!/bin/bash
# Run audio generation in background with logging

cd "$(dirname "$0")/.."
SCRIPT_DIR="$(pwd)"
cd "$SCRIPT_DIR/.."

LOG_FILE="$SCRIPT_DIR/emoji_audio_generation.log"
PID_FILE="$SCRIPT_DIR/emoji_audio_generation.pid"

# Check if already running
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p "$PID" > /dev/null 2>&1; then
        echo "⚠️  Generation already running (PID: $PID)"
        echo "   Check status: python3 backend/scripts/check_audio_status.py"
        exit 1
    else
        # Stale PID file
        rm "$PID_FILE"
    fi
fi

# Start generation in background
echo "🚀 Starting audio generation in background..."
echo "   Log file: $LOG_FILE"
echo "   PID file: $PID_FILE"
echo ""

cd backend

# Activate venv if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
    PYTHON_CMD="python"
elif [ -d ".venv" ]; then
    source .venv/bin/activate
    PYTHON_CMD="python"
else
    PYTHON_CMD="python3"
fi

nohup $PYTHON_CMD scripts/generate_emoji_audio_variants.py \
    --resume \
    --skip-existing \
    --parallel-words 3 \
    --parallel-voices 5 \
    > "$LOG_FILE" 2>&1 &

PID=$!
echo $PID > "$PID_FILE"

echo "✅ Generation started (PID: $PID)"
echo ""
echo "📊 Check status:"
echo "   python3 backend/scripts/check_audio_status.py"
echo ""
echo "📋 View logs:"
echo "   tail -f $LOG_FILE"
echo ""
echo "🛑 Stop generation:"
echo "   kill $PID"

