#!/bin/bash
MAIN_PID=$(ps aux | grep "main_factory" | grep -v grep | awk '{print $2}')
ADV_PID=$(ps aux | grep "adversary_builder" | grep -v grep | awk '{print $2}')

if [ -z "$MAIN_PID" ] && [ -z "$ADV_PID" ]; then
    echo "✅ BOTH PROCESSES COMPLETE!"
    echo "Main Factory: $(grep -i "complete\|done\|finished" main_factory.log 2>/dev/null | tail -1 || echo "Check log manually")"
    echo "Adversary Builder: $(grep -i "complete\|done\|finished" adversary_builder.log 2>/dev/null | tail -1 || echo "Check log manually")"
    exit 0
elif [ -z "$MAIN_PID" ]; then
    echo "✅ Main Factory COMPLETE"
    echo "⏳ Adversary Builder still running (PID: $ADV_PID)"
    exit 1
elif [ -z "$ADV_PID" ]; then
    echo "⏳ Main Factory still running (PID: $MAIN_PID)"
    echo "✅ Adversary Builder COMPLETE"
    exit 1
else
    echo "⏳ Both processes still running"
    echo "Main Factory (PID: $MAIN_PID): $(tail -1 main_factory.log 2>/dev/null | grep -o 'Processing.*' | head -1 || echo 'checking...')"
    exit 2
fi
