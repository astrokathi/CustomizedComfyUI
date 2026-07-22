#!/usr/bin/env bash
#
# ComfyUI Launch Script — MacBook Air M1 (MPS-optimized)
#
set -euo pipefail

PROJECT_ROOT="/Volumes/Kathi/AntiGravity/ComfyUI"
APP_DIR="${PROJECT_ROOT}/app"
VENV_DIR="${PROJECT_ROOT}/venv"

echo "=============================="
echo " Starting ComfyUI (MPS Mode)"
echo "=============================="

# ---- Load .env ----
if [ -f "${PROJECT_ROOT}/.env" ]; then
    set -a
    source "${PROJECT_ROOT}/.env"
    set +a
    echo "[✓] Loaded .env"
else
    echo "[✗] ERROR: .env file not found. Run setup.sh first."
    exit 1
fi

# ---- Start PostgreSQL ----
echo "[→] Starting PostgreSQL..."
cd "${PROJECT_ROOT}"
if command -v docker &>/dev/null; then
    docker compose up -d 2>/dev/null
    echo "[✓] PostgreSQL started"
else
    echo "[!] Docker not found. PostgreSQL will not be available."
fi

# ---- Activate venv ----
if [ ! -d "${VENV_DIR}" ]; then
    echo "[✗] ERROR: Virtual environment not found. Run setup.sh first."
    exit 1
fi
source "${VENV_DIR}/bin/activate"
echo "[✓] Virtual environment activated"

# ---- Set environment variables (MPS + cache redirection) ----
export PYTORCH_MPS_HIGH_WATERMARK_RATIO=0.0
export PYTORCH_ENABLE_MPS_FALLBACK=1
export HF_HOME="${PROJECT_ROOT}/cache/huggingface"
export TORCH_HOME="${PROJECT_ROOT}/cache/torch"
export PIP_CACHE_DIR="${PROJECT_ROOT}/cache/pip"
export TMPDIR="${PROJECT_ROOT}/tmp"
export HOME="${PROJECT_ROOT}/cache"  # Prevents any dotfiles on Mac storage
echo "[✓] Environment variables set (MPS + cache → project dir)"

# ---- Launch ComfyUI ----
echo ""
echo "Launching ComfyUI on http://${COMFYUI_HOST:-0.0.0.0}:${COMFYUI_PORT:-8188}"
echo "Press Ctrl+C to stop."
echo ""

cd "${APP_DIR}"
python main.py \
    --listen "${COMFYUI_HOST:-0.0.0.0}" \
    --port "${COMFYUI_PORT:-8188}" \
    --force-fp16 \
    --force-upcast-attention \
    --use-split-cross-attention \
    --output-directory "${PROJECT_ROOT}/data/output" \
    --temp-directory "${PROJECT_ROOT}/data/temp" \
    --input-directory "${PROJECT_ROOT}/data/input" \
    --user-directory "${PROJECT_ROOT}/data/user" \
    --database-url "sqlite:///${PROJECT_ROOT}/data/user/comfyui.db" \
    --extra-model-paths-config "${PROJECT_ROOT}/config/extra_model_paths.yaml"
