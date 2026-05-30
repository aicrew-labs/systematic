#!/bin/bash
# Quote Intelligence — local dev runner
#
# Starts the FastAPI backend (port 8000) and the React frontend (port 5173).
# Backend uses python3.11 because the codebase uses union-type syntax (int | None).
# Press Ctrl+C to stop both.

set -e
cd "$(dirname "$0")"

# ── Pick a Python ≥ 3.10 ────────────────────────────────────────────────────
PY=""
for candidate in python3.12 python3.11 python3.10; do
    if command -v "$candidate" >/dev/null 2>&1; then
        PY="$candidate"
        break
    fi
done
if [ -z "$PY" ]; then
    echo "ERROR: Python 3.10+ is required (found system python3 = $(python3 --version))."
    echo "       Install with: brew install python@3.11"
    exit 1
fi
echo "Using $PY for backend"

# ── Stop any existing instances ─────────────────────────────────────────────
echo "Stopping existing backend / frontend instances..."
pkill -f "uvicorn app.main:app" 2>/dev/null || true
pkill -f "vite"                  2>/dev/null || true
lsof -ti :8000 2>/dev/null | xargs kill -9 2>/dev/null || true
lsof -ti :5173 2>/dev/null | xargs kill -9 2>/dev/null || true
sleep 1

# ── Start backend ───────────────────────────────────────────────────────────
echo "Starting backend on http://localhost:8000 ..."
(cd backend && "$PY" -m uvicorn app.main:app --reload --port 8000) &
BACKEND_PID=$!

# NOTE: The active dashboard for this branch is the static HTML served by the
# backend at http://localhost:8000/ (it has login + auth). The React app under
# /frontend is an older, unused prototype and is intentionally NOT started here.
FRONTEND_PID=""

echo ""
echo "✅ Backend running."
echo "   Open the dashboard → http://localhost:8000/"
echo "   (You'll be redirected to /login — default admin / admin123)"
echo ""
echo "(Press Ctrl+C to stop)"

cleanup() {
    echo ""
    echo "Shutting down..."
    kill "$BACKEND_PID" 2>/dev/null || true
    exit 0
}
trap cleanup INT TERM

wait
