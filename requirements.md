# ComfyUI Setup — Requirements

## 1. Runtime Environment

| Requirement | Decision |
|---|---|
| **Platform** | MacBook Air M1 (8 GB unified memory) |
| **Runtime** | Native Python venv with MPS (Metal Performance Shaders) — **NOT Docker** |
| **Python** | 3.11.x (pyenv managed) |
| **GPU** | Apple M1 GPU via MPS + shared unified RAM |
| **Storage** | ALL data (models, outputs, cache, temp, DB) stored on external disk at `/Volumes/Kathi/AntiGravity/ComfyUI/` — **zero data on MacBook internal storage** |

## 2. Authentication

| Requirement | Decision |
|---|---|
| **Auth type** | Custom login page (Option C) — full browser UI, not Basic Auth |
| **Exposure** | Will be exposed via **ngrok** — must block intruders |
| **Password hashing** | PBKDF2-HMAC-SHA256 (600,000 iterations) with user-provided secret string as salt |
| **Credential storage** | Hashed password + username stored as `.env` values |
| **Session management** | JWT HS256 tokens in HTTP-only secure cookies, signed with the secret |
| **Secret string** | User-provided, stored in `.env` as `AUTH_SECRET` |

## 3. LLM Integration

| Requirement | Decision |
|---|---|
| **Primary LLM** | NVIDIA Nemotron-3 Ultra (free endpoint at `https://integrate.api.nvidia.com/v1`) |
| **API Key** | Already available, stored in `.env` as `NVIDIA_API_KEY` |
| **Secondary LLM** | Ollama (already running natively at `http://localhost:11434`) |
| **Ollama Docker** | NOT needed — use existing host installation directly |

## 4. Database

| Requirement | Decision |
|---|---|
| **Engine** | PostgreSQL 16 (Alpine, ARM64) via Docker Compose |
| **Data path** | `/Volumes/Kathi/AntiGravity/ComfyUI/db` |
| **Purpose** | Auth sessions, generation history, user data, cleanup logs |
| **Access** | Native Python app connects via `localhost:5432` |

## 5. Data Storage Layout

All paths are under `/Volumes/Kathi/AntiGravity/ComfyUI/`:

| Directory | Purpose |
|---|---|
| `data/models/` | AI models (checkpoints, LoRAs, VAE, ControlNet, etc.) |
| `data/output/` | Generated images and videos |
| `data/input/` | Source images for workflows |
| `data/user/` | Saved workflows and settings |
| `data/temp/` | Temporary processing files |
| `cache/pip/` | pip download cache |
| `cache/huggingface/` | HuggingFace model cache |
| `cache/torch/` | PyTorch hub cache |
| `tmp/` | System TMPDIR redirect |
| `db/` | PostgreSQL data files |

## 6. Scripts

| Script | Purpose |
|---|---|
| `scripts/setup.sh` | One-time: clone ComfyUI, create venv, install deps, create dirs, init DB |
| `scripts/start.sh` | Launch ComfyUI with MPS-optimized flags + start PostgreSQL |
| `scripts/stop.sh` | Gracefully stop ComfyUI + PostgreSQL |
| `scripts/clean-history.bash` | Delete output files older than N days (default 7, configurable via argument) |
| `scripts/generate-password-hash.py` | Generate PBKDF2-HMAC-SHA256 hash for .env |

## 7. M1 Optimizations

- `--force-fp16` — half-precision to save memory
- `--force-upcast-attention` — prevents black images on MPS
- `--use-split-cross-attention` — memory-efficient attention for 8 GB RAM
- `PYTORCH_MPS_HIGH_WATERMARK_RATIO=0.0` — prevents MPS OOM
- `PYTORCH_ENABLE_MPS_FALLBACK=1` — CPU fallback for unsupported MPS ops
