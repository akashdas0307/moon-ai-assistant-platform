#!/bin/bash

# ═══════════════════════════════════════════
#   Moon-AI Dev Launcher (WSL / Linux / Mac)
#   Usage: ./moon.sh [install|run|reload|stop]
# ═══════════════════════════════════════════

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PATH="$SCRIPT_DIR/backend/venv"
PID_FILE="$SCRIPT_DIR/.moon_pids"

activate_venv() {
  if [ -f "$VENV_PATH/bin/activate" ]; then
    source "$VENV_PATH/bin/activate"
  else
    echo ""
    echo "⚠️  Virtual environment not found at backend/venv"
    echo "    Run: cd backend && python -m venv venv"
    echo ""
    exit 1
  fi
}

install_all() {
  echo ""
  echo "📦 Installing Moon-AI dependencies..."
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo ""
  echo "🐍 [1/2] Installing Python dependencies..."
  activate_venv
  pip install -r "$SCRIPT_DIR/backend/requirements.txt"
  echo ""
  echo "⚛️  [2/2] Installing Node.js dependencies..."
  cd "$SCRIPT_DIR/frontend" && npm install
  echo ""
  echo "✅ All dependencies installed! Run ./moon.sh run to start."
  echo ""
}

run_services() {
  echo ""
  echo "🌙 Starting Moon-AI..."
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "   Backend  → http://localhost:8000"
  echo "   Frontend → http://localhost:5173"
  echo "   Press Ctrl+C to stop all services"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo ""

  activate_venv

  # Start backend from project root so imports resolve correctly
  cd "$SCRIPT_DIR"
  uvicorn backend.main:app --reload --port 8000 &
  BACKEND_PID=$!

  # Start frontend
  cd "$SCRIPT_DIR/frontend"
  npm run dev &
  FRONTEND_PID=$!

  # Save PIDs for stop/reload
  echo "$BACKEND_PID $FRONTEND_PID" > "$PID_FILE"

  # Graceful shutdown on Ctrl+C
  trap "stop_services; exit 0 " SIGINT SIGTERM
  wait
}

stop_services() {
  echo ""
  echo "🛑 Stopping Moon-AI services..."

  if [ -f "$PID_FILE" ]; then
    read -r BACKEND_PID FRONTEND_PID < "$PID_FILE"
    kill "$BACKEND_PID" 2>/dev/null && echo "   ✓ Backend stopped"
    kill "$FRONTEND_PID" 2>/dev/null && echo "   ✓ Frontend stopped"
    rm -f "$PID_FILE"
  else
    # Fallback: kill by port
    lsof -ti:8000 | xargs kill -9 2>/dev/null && echo "   ✓ Backend (port 8000) stopped"
    lsof -ti:5173 | xargs kill -9 2>/dev/null && echo "   ✓ Frontend (port 5173) stopped"
  fi

  echo "   Done."
  echo ""
}

reload_services() {
  echo ""
  echo "🔄 Reloading Moon-AI services..."
  stop_services
  sleep 1
  run_services
}

case "$1" in
  install) install_all ;;
  run)     run_services ;;
  reload)  reload_services ;;
  stop)    stop_services ;;
  *)
    echo ""
    echo "🌙 Moon-AI Dev Launcher"
    echo ""
    echo "Usage: ./moon.sh [command]"
    echo ""
    echo "Commands:"
    echo "  install   Install all Python + Node.js dependencies"
    echo "  run       Start backend + frontend services"
    echo "  reload    Stop and restart all services"
    echo "  stop      Stop all running services"
    echo ""
    ;;
esac
