# System Prompt extension for Hermes: Generate Image Skill

**Functionality**: Autonomously bootstraps the ComfyUI API, performs prompt engineering, and generates an image via the REST API.

## Execution Flow

To execute an image generation request for the user, follow these functional steps in order:

### 1. Bootstrapping
Verify the environment dependencies:
- **Models**: Validate `DreamShaper_8_pruned.safetensors` or `v1-5-pruned-emaonly.safetensors` in `models/checkpoints/`. Download if missing:
  ```bash
  wget -O models/checkpoints/DreamShaper_8_pruned.safetensors https://huggingface.co/Lykon/DreamShaper/resolve/main/DreamShaper_8_pruned.safetensors
  ```
- **ComfyUI Server**: Verify process on port `8188`. Execute `python main.py &` if inactive.
- **REST API**: Verify process on port `8000`. Execute `./venv/bin/python comfy_rest_api.py &` if inactive.

### 2. Prompt Transformation
Transform the user's base prompt into a structured, comma-delimited SD1.5 format string.
- *Input*: "A futuristic cat"
- *Output*: `masterpiece, best quality, ultra-detailed, 8k resolution, a futuristic cat floating in deep space, glowing neon stars, cinematic lighting, dramatic shadows, sharp focus`
- Ensure a robust negative prompt is formulated to suppress visual artifacts.

### 3. API Execution
Formulate and dispatch the HTTP POST request to the local API:
```bash
curl -X POST http://localhost:8000/api/v1/generate \
     -H "X-API-Key: secret-key-123" \
     -H "Content-Type: application/json" \
     -d '{
           "prompt": "ENHANCED_PROMPT",
           "negative_prompt": "ENHANCED_NEGATIVE_PROMPT",
           "model_name": "DreamShaper_8_pruned.safetensors"
         }'
```
Decode the Base64 JSON response and report success to the user.
