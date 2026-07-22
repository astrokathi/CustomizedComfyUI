#!/usr/bin/env bash
#
# ComfyUI Setup Script — One-time initialization
# Run from project root: bash scripts/setup.sh
#
set -euo pipefail

PROJECT_ROOT="/Volumes/Kathi/AntiGravity/ComfyUI"
APP_DIR="${PROJECT_ROOT}/app"
VENV_DIR="${PROJECT_ROOT}/venv"
PYTHON_VERSION="3.11"

echo "======================================"
echo " ComfyUI Setup — MacBook Air M1 (MPS)"
echo "======================================"
echo ""

# ---- Step 1: Check Python version ----
echo "[1/8] Checking Python version..."
if ! command -v python3 &>/dev/null; then
    echo "ERROR: python3 not found. Install Python ${PYTHON_VERSION} via pyenv:"
    echo "  brew install pyenv"
    echo "  pyenv install 3.11.8"
    echo "  pyenv global 3.11.8"
    exit 1
fi
PY_VER=$(python3 --version | awk '{print $2}')
echo "  Found Python ${PY_VER}"

# ---- Step 2: Create directory structure ----
echo "[2/8] Creating directory structure..."
mkdir -p "${PROJECT_ROOT}/data/models/checkpoints"
mkdir -p "${PROJECT_ROOT}/data/models/loras"
mkdir -p "${PROJECT_ROOT}/data/models/vae"
mkdir -p "${PROJECT_ROOT}/data/models/controlnet"
mkdir -p "${PROJECT_ROOT}/data/models/upscale_models"
mkdir -p "${PROJECT_ROOT}/data/models/clip"
mkdir -p "${PROJECT_ROOT}/data/models/clip_vision"
mkdir -p "${PROJECT_ROOT}/data/models/embeddings"
mkdir -p "${PROJECT_ROOT}/data/models/diffusion_models"
mkdir -p "${PROJECT_ROOT}/data/models/configs"
mkdir -p "${PROJECT_ROOT}/data/output"
mkdir -p "${PROJECT_ROOT}/data/input"
mkdir -p "${PROJECT_ROOT}/data/user"
mkdir -p "${PROJECT_ROOT}/data/temp"
mkdir -p "${PROJECT_ROOT}/cache/pip"
mkdir -p "${PROJECT_ROOT}/cache/huggingface"
mkdir -p "${PROJECT_ROOT}/cache/torch"
mkdir -p "${PROJECT_ROOT}/tmp"
mkdir -p "${PROJECT_ROOT}/db"
echo "  Done."

# ---- Step 3: Clone ComfyUI ----
echo "[3/8] Cloning ComfyUI..."
if [ -d "${APP_DIR}/.git" ]; then
    echo "  ComfyUI already cloned. Pulling latest..."
    cd "${APP_DIR}" && git pull
else
    git clone https://github.com/comfyanonymous/ComfyUI.git "${APP_DIR}"
fi
echo "  Done."

# ---- Step 4: Create Python virtual environment ----
echo "[4/8] Creating virtual environment..."
if [ ! -d "${VENV_DIR}" ]; then
    python3 -m venv "${VENV_DIR}"
fi
source "${VENV_DIR}/bin/activate"
echo "  Using: $(which python)"

# ---- Step 5: Install PyTorch (MPS-enabled) ----
echo "[5/8] Installing PyTorch with MPS support..."
export PIP_CACHE_DIR="${PROJECT_ROOT}/cache/pip"
pip install --upgrade pip
pip install torch torchvision torchaudio
echo "  Verifying MPS..."
python -c "import torch; avail=torch.backends.mps.is_available(); print(f'  MPS available: {avail}'); assert avail, 'MPS not available!'"
echo "  Done."

# ---- Step 6: Install ComfyUI dependencies ----
echo "[6/8] Installing ComfyUI dependencies..."
cd "${APP_DIR}"
pip install -r requirements.txt
echo "  Done."

# ---- Step 7: Install auth node dependencies ----
echo "[7/8] Installing auth custom node dependencies..."
if [ -f "${APP_DIR}/custom_nodes/comfyui-secure-auth/requirements.txt" ]; then
    pip install -r "${APP_DIR}/custom_nodes/comfyui-secure-auth/requirements.txt"
fi
echo "  Done."

# ---- Step 8: Setup .env ----
echo "[8/8] Setting up environment file..."
if [ ! -f "${PROJECT_ROOT}/.env" ]; then
    cp "${PROJECT_ROOT}/.env.example" "${PROJECT_ROOT}/.env"
    echo "  Created .env from template. Please edit it with your credentials:"
    echo "    1. Run: python ${PROJECT_ROOT}/scripts/generate-password-hash.py"
    echo "    2. Edit: ${PROJECT_ROOT}/.env"
else
    echo "  .env already exists. Skipping."
fi

# ---- Step 9: Start PostgreSQL ----
echo ""
echo "[Bonus] Starting PostgreSQL..."
if command -v docker &>/dev/null; then
    cd "${PROJECT_ROOT}"
    docker compose up -d
    echo "  PostgreSQL starting. Check with: docker compose ps"
else
    echo "  Docker not found. Install Docker Desktop to run PostgreSQL."
fi

# ---- Step 10: Init DB schema ----
echo ""
echo "[Bonus] Initializing database schema..."
sleep 3  # wait for PG to start
if command -v docker &>/dev/null; then
    docker compose exec -T db psql -U "${POSTGRES_USER:-comfyui}" -d "${POSTGRES_DB:-comfyui}" <<'SQL' 2>/dev/null || echo "  DB schema init will happen on first ComfyUI launch."
CREATE TABLE IF NOT EXISTS auth_sessions (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) NOT NULL,
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS generation_history (
    id SERIAL PRIMARY KEY,
    prompt_id VARCHAR(255),
    workflow_json JSONB,
    output_files TEXT[],
    status VARCHAR(50),
    execution_time_ms INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS cleanup_logs (
    id SERIAL PRIMARY KEY,
    files_deleted INTEGER DEFAULT 0,
    bytes_freed BIGINT DEFAULT 0,
    retention_days INTEGER,
    executed_at TIMESTAMP DEFAULT NOW()
);
SQL
fi

echo ""
echo "======================================"
echo " Setup Complete!"
echo "======================================"
echo ""
echo "Next steps:"
echo "  1. Edit your .env file with credentials"
echo "  2. Generate password hash: python scripts/generate-password-hash.py"
echo "  3. Launch: bash scripts/start.sh"
echo "  4. Open: http://localhost:8188"
echo ""
