# ComfyUI Project Plan

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    /Volumes/Kathi/AntiGravity/ComfyUI           │
│                         (External Disk — Project Root)          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐    ┌──────────────────┐    ┌──────────────┐  │
│  │  ComfyUI      │    │  Auth Middleware  │    │  PostgreSQL  │  │
│  │  (Native MPS) │◄──►│  (Custom Node)   │    │  (Docker)    │  │
│  │  Port: 8188   │    │  Login UI + JWT   │    │  Port: 5432  │  │
│  └──────┬───────┘    └────────┬─────────┘    └──────┬───────┘  │
│         │                     │                      │          │
│         ▼                     ▼                      ▼          │
│  ┌──────────────┐    ┌──────────────────┐    ┌──────────────┐  │
│  │ data/output/  │    │ .env (hashed pw)  │    │ db/pgdata/   │  │
│  │ data/models/  │    │ JWT sessions      │    │              │  │
│  │ data/input/   │    │                   │    │              │  │
│  │ cache/        │    │                   │    │              │  │
│  └──────────────┘    └──────────────────┘    └──────────────┘  │
│                                                                 │
│  ┌──────────────────────────────────────┐                      │
│  │ LLM Backends (OpenAI-compatible API) │                      │
│  │  • NVIDIA Nemotron: integrate.api.nvidia.com/v1             │
│  │  • Ollama: localhost:11434                                  │
│  └──────────────────────────────────────┘                      │
│                                                                 │
│  ┌──────────────────────┐                                      │
│  │ ngrok (user-managed) │                                      │
│  │ Exposes port 8188    │                                      │
│  └──────────────────────┘                                      │
└─────────────────────────────────────────────────────────────────┘
```

## Directory Structure

```
/Volumes/Kathi/AntiGravity/ComfyUI/
├── app/                                    ← ComfyUI source (git clone)
│   ├── main.py                             ← ComfyUI entry point
│   ├── custom_nodes/
│   │   └── comfyui-secure-auth/           ← Custom auth node (our code)
│   │       ├── __init__.py                 ← Registers middleware with PromptServer
│   │       ├── auth_middleware.py          ← PBKDF2 + JWT auth logic
│   │       ├── db_manager.py              ← PostgreSQL session/history storage
│   │       ├── requirements.txt
│   │       ├── static/
│   │       │   ├── login.css
│   │       │   └── login.js
│   │       └── templates/
│   │           └── login.html              ← Beautiful login page
│   └── ...
│
├── venv/                                   ← Python 3.11 virtual environment
│
├── data/
│   ├── models/
│   │   ├── checkpoints/
│   │   ├── loras/
│   │   ├── vae/
│   │   ├── controlnet/
│   │   ├── upscale_models/
│   │   ├── clip/
│   │   ├── clip_vision/
│   │   ├── embeddings/
│   │   ├── diffusion_models/
│   │   └── configs/
│   ├── output/
│   ├── input/
│   ├── user/
│   └── temp/
│
├── cache/
│   ├── pip/
│   ├── huggingface/
│   └── torch/
│
├── tmp/                                    ← TMPDIR redirect
│
├── db/                                     ← PostgreSQL data (Docker-managed)
│   └── pgdata/                             ← Actual PG data files
│
├── scripts/
│   ├── setup.sh                            ← One-time full project setup
│   ├── start.sh                            ← Launch ComfyUI + DB
│   ├── stop.sh                             ← Graceful shutdown
│   ├── clean-history.bash                  ← Prune old output files
│   └── generate-password-hash.py           ← PBKDF2-HMAC-SHA256 hash generator
│
├── config/
│   ├── extra_model_paths.yaml              ← Model path overrides
│   └── llm_config.json                     ← LLM endpoint configuration
│
├── docker-compose.yml                      ← PostgreSQL service ONLY
├── .env.example                            ← Template with all variables
├── .env                                    ← Actual secrets (git-ignored)
├── .gitignore
├── requirements.md                         ← This document
└── project_plan.md                         ← This document
```

## Implementation Phases

### Phase 1: Project Skeleton
Create all directories, configuration files, .env.example, .gitignore, docker-compose.yml.

### Phase 2: Auth Custom Node
Build `comfyui-secure-auth` with:
- `__init__.py` — hook into ComfyUI's PromptServer
- `auth_middleware.py` — PBKDF2 password verification + JWT session management
- `db_manager.py` — PostgreSQL integration for sessions + history
- `templates/login.html` — beautiful, responsive login page
- `static/login.css` + `static/login.js` — login page assets

### Phase 3: Scripts
- `setup.sh` — clones ComfyUI, creates venv, installs everything, inits DB
- `start.sh` — sets env vars, starts DB, launches ComfyUI
- `stop.sh` — graceful shutdown
- `clean-history.bash` — find+delete old files with configurable retention
- `generate-password-hash.py` — interactive hash generator

### Phase 4: LLM Configuration
- `config/llm_config.json` — endpoint details for Nemotron + Ollama
- Environment variable documentation

### Phase 5: Verification
- Test DB connectivity
- Test auth flow (login, session, logout)
- Test ComfyUI launches with MPS
- Test clean-history script

## Authentication Flow

```
User visits http://localhost:8188
         │
         ▼
┌─────────────────────┐     No     ┌──────────────────┐
│ Has valid JWT cookie?│ ──────────►│ Serve login.html  │
└─────────┬───────────┘            └────────┬─────────┘
          │ Yes                              │
          ▼                                  ▼
┌─────────────────────┐            ┌──────────────────┐
│ Pass through to      │            │ POST /auth/login  │
│ ComfyUI normally     │            │ with user:pass    │
└─────────────────────┘            └────────┬─────────┘
                                            │
                                            ▼
                                   ┌──────────────────┐
                                   │ PBKDF2-HMAC-SHA256│
                                   │ hash(pass,secret) │
                                   │ == stored_hash?   │
                                   └────────┬─────────┘
                                     Yes    │    No
                                   ┌────────┴────────┐
                                   ▼                  ▼
                          ┌──────────────┐   ┌──────────────┐
                          │ Set JWT cookie│   │ Return 401   │
                          │ + redirect /  │   │ + error msg  │
                          └──────────────┘   └──────────────┘
```

## Password Hash Generation

```bash
# User runs:
python scripts/generate-password-hash.py

# Interactive prompts:
#   Enter your secret string: <secret>
#   Enter password: <password>
#   Confirm password: <password>
#
# Output:
#   AUTH_PASSWORD_HASH=a1b2c3d4e5f6...
#   (copy this to your .env file)
```

## Database Schema

```sql
-- Auth sessions (for tracking/auditing, JWT is stateless)
CREATE TABLE auth_sessions (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) NOT NULL,
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP NOT NULL
);

-- Generation history
CREATE TABLE generation_history (
    id SERIAL PRIMARY KEY,
    prompt_id VARCHAR(255),
    workflow_json JSONB,
    output_files TEXT[],
    status VARCHAR(50),
    execution_time_ms INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Cleanup logs
CREATE TABLE cleanup_logs (
    id SERIAL PRIMARY KEY,
    files_deleted INTEGER DEFAULT 0,
    bytes_freed BIGINT DEFAULT 0,
    retention_days INTEGER,
    executed_at TIMESTAMP DEFAULT NOW()
);
```

## Environment Variables

```env
# === Authentication ===
AUTH_USERNAME=admin
AUTH_PASSWORD_HASH=<pbkdf2_hmac_sha256_hex>
AUTH_SECRET=<your_secret_string>
AUTH_SESSION_EXPIRY_HOURS=24

# === Database ===
POSTGRES_USER=comfyui
POSTGRES_PASSWORD=<strong_password>
POSTGRES_DB=comfyui
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# === LLM — NVIDIA Nemotron ===
NVIDIA_API_KEY=<your_nvidia_api_key>
NVIDIA_API_BASE=https://integrate.api.nvidia.com/v1
NVIDIA_MODEL=nvidia/nemotron-ultra-253b-v1

# === LLM — Ollama ===
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3

# === ComfyUI ===
COMFYUI_PORT=8188
COMFYUI_HOST=0.0.0.0
```
