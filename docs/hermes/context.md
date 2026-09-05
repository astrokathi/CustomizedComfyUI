# Project Context: ComfyUI REST API

This project contains a local instance of ComfyUI alongside a custom REST API wrapper (`comfy_rest_api.py`).

## Architecture
- **ComfyUI**: The core image generation engine running on `http://127.0.0.1:8188`.
- **REST API**: A standalone Python application running on `http://127.0.0.1:8000` that handles API Key authentication, payload validation, and websocket synchronization with ComfyUI.

## The Generation Pipeline
When a request is sent to `POST /api/v1/generate`:
1. The REST API maps the simplified JSON payload to the complex node structure required by ComfyUI.
2. The payload is sent to ComfyUI's `/prompt` endpoint.
3. The API listens to the ComfyUI websocket to track execution progress without polling.
4. Once completed, the API fetches the image, encodes it into Base64, and simultaneously generates a QR Code containing the image configuration parameters (CFG, Steps, Seed, Model).
5. Both Base64 strings are returned to the client.
