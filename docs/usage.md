# Usage Guide

This guide explains how to interact with the API endpoints once both ComfyUI and the REST Gateway are running.

## Starting the Services

You must ensure both services are running. It is highly recommended to run them in separate terminal windows, or use background processes.

```bash
# Terminal 1
cd /Volumes/Kathi/AntiGravity/ComfyUI
python main.py

# Terminal 2
cd /Volumes/Kathi/AntiGravity/ComfyUI
./venv/bin/python comfy_rest_api.py
```

## Making Requests

### 1. Listing Available Models
Before generating, it is useful to know which models the backend currently has loaded in its `models/checkpoints/` directory.

```bash
curl -X GET http://localhost:8000/api/v1/models/checkpoints \
     -H "X-API-Key: secret-key-123"
```

### 2. Generating an Image
The `POST /api/v1/generate` endpoint requires a minimum of one parameter: `prompt`.

```bash
curl -X POST http://localhost:8000/api/v1/generate \
     -H "X-API-Key: secret-key-123" \
     -H "Content-Type: application/json" \
     -d '{
           "prompt": "a beautiful cinematic rendering of a distant galaxy",
           "model_name": "DreamShaper_8_pruned.safetensors",
           "qr_code": true
         }'
```

**Custom Overrides:**
If you wish to bypass the automatic defaults, you can inject parameters directly:
```json
{
  "prompt": "a beautiful cinematic rendering of a distant galaxy",
  "cfg": 9.5,
  "steps": 40,
  "width": 1024,
  "height": 512
}
```

### Processing the Response

The API returns a JSON dictionary containing the base64 encoded images.
Because they are formatted with the `data:image/png;base64,` prefix, you can directly embed them into HTML or frontend frameworks without any decoding step:

```html
<!-- Example Frontend Implementation -->
<img src="data:image/png;base64,iVBORw0KGgoAAA..." alt="Generated Image" />
```
