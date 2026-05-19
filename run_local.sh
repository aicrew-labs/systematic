#!/bin/bash

echo "🛑 Stopping any existing backend instances..."
pkill -f "uvicorn app.main:app" 2>/dev/null
# Also kill the old react frontend just in case it was running
pkill -f "vite" 2>/dev/null
sleep 1

echo "🚀 Starting Quote Intelligence Backend..."
cd backend || exit
python3 -m uvicorn app.main:app --reload &
BACKEND_PID=$!
cd ..

echo "✅ System is running!"
echo "🌍 Open your browser to: http://localhost:8000/"
echo ""
echo "(Press Ctrl+C to stop the server)"

# Wait for Ctrl+C
trap "echo -e '\n🛑 Shutting down...'; kill $BACKEND_PID 2>/dev/null; exit" INT TERM
wait $BACKEND_PID
