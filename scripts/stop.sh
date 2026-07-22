#!/usr/bin/env bash
#
# ComfyUI Graceful Shutdown Script
#
set -euo pipefail

PROJECT_ROOT="/Volumes/Kathi/AntiGravity/ComfyUI"

echo "=============================="
echo " Stopping ComfyUI"
echo "=============================="

# ---- Stop ComfyUI (find by port) ----
echo "[→] Stopping ComfyUI process..."
COMFYUI_PID=$(lsof -ti :8188 2>/dev/null || true)
if [ -n "${COMFYUI_PID}" ]; then
    kill -SIGTERM ${COMFYUI_PID} 2>/dev/null || true
    echo "[✓] ComfyUI process (PID: ${COMFYUI_PID}) sent SIGTERM"
    # Wait up to 10 seconds for graceful shutdown
    for i in $(seq 1 10); do
        if ! kill -0 ${COMFYUI_PID} 2>/dev/null; then
            echo "[✓] ComfyUI stopped"
            break
        fi
        sleep 1
    done
    # Force kill if still running
    if kill -0 ${COMFYUI_PID} 2>/dev/null; then
        kill -9 ${COMFYUI_PID} 2>/dev/null || true
        echo "[!] ComfyUI force-killed"
    fi
else
    echo "[✓] ComfyUI not running"
fi

# ---- Stop PostgreSQL ----
echo "[→] Stopping PostgreSQL..."
cd "${PROJECT_ROOT}"
if command -v docker &>/dev/null; then
    docker compose down 2>/dev/null || true
    echo "[✓] PostgreSQL stopped"
else
    echo "[!] Docker not found"
fi

echo ""
echo "All services stopped."
