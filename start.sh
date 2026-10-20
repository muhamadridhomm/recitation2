#!/usr/bin/env bash

# Find script directory
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

echo "====================================================="
echo " Starting Islamic Note-taking & Collaboration App... "
echo "====================================================="

# 1. Start backend server
echo "Starting Backend API (FastAPI) on port 8000..."
cd "$DIR/backend"
if [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "Virtual environment 'venv' not found in backend/ directory. Please run setup first."
    exit 1
fi
python3 -m uvicorn app.main:app --port 8000 > backend.log 2>&1 &
BACKEND_PID=$!

# 2. Start frontend server
echo "Starting Frontend UI (SvelteKit) on port 5173..."
cd "$DIR/frontend"
npm run dev -- --port 5173 > frontend.log 2>&1 &
FRONTEND_PID=$!

# Cleanup function to kill servers when user stops this script
cleanup() {
    echo ""
    echo "Shutting down servers..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    exit
}
trap cleanup SIGINT SIGTERM EXIT

# Wait a brief moment for servers to spin up
sleep 3

# 3. Open default browser
echo "Launching web workspace..."
if command -v xdg-open > /dev/null; then
  xdg-open http://localhost:5173
elif command -v open > /dev/null; then
  open http://localhost:5173
else
  echo "-----------------------------------------------------"
  echo "Server started successfully."
  echo "Please open http://localhost:5173 in your browser."
  echo "-----------------------------------------------------"
fi

echo "Application is running. Press [CTRL+C] to stop."
wait
