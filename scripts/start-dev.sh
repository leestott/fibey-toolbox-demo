#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "=== Starting Fibey Agent (dev mode) ==="

# Start FastAPI gateway
echo "Starting gateway on :8080..."
cd "$PROJECT_ROOT"
uv run uvicorn fibey.gateway.api_server:app --reload --port 8080 &
GATEWAY_PID=$!

# Start Vite dev server
echo "Starting UI on :5173..."
cd "$PROJECT_ROOT/ui"
npm run dev &
UI_PID=$!

# Cleanup on exit
trap "kill $GATEWAY_PID $UI_PID 2>/dev/null; echo 'Servers stopped.'" EXIT

echo "Gateway: http://localhost:8080"
echo "UI:      http://localhost:5173"
echo "Press Ctrl+C to stop."

wait
