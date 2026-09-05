# System Architecture

The REST API is designed to bridge the gap between simple JSON-based web clients and the complex, node-based graph execution engine of ComfyUI.

## 1. The Gateway (`comfy_rest_api.py`)

The gateway is built using Python's `aiohttp` framework. It runs on a separate port (`8000`) to avoid conflicting with ComfyUI's default port (`8188`).

**Key Responsibilities:**
- **Authentication**: Validates all incoming requests via the `X-API-Key` header.
- **Workflow Translation**: Takes a flat JSON payload (e.g., `{"prompt": "cat", "cfg": 7}`) and inflates it into the exact nested Node-Graph API format required by ComfyUI (mapping node IDs to class types and inputs).
- **Dynamic Defaults**: Inspects the requested `model_name` and automatically adjusts standard parameters (Steps, CFG, Image Resolution) to ensure optimal generation quality without user intervention.

## 2. Synchronization (WebSockets)

ComfyUI is entirely asynchronous. When the gateway submits a prompt to `/prompt`, ComfyUI places it in an execution queue and immediately returns a `prompt_id`.

To prevent the client from needing to implement continuous polling:
1. The REST API connects to ComfyUI's WebSocket stream (`ws://127.0.0.1:8188/ws`).
2. It listens for the `executing` broadcast event.
3. Once the broadcast confirms that our specific `prompt_id` has finished executing all nodes, the API fetches the output history.

## 3. Data Delivery

Instead of requiring the client to make a secondary request to download the image file from disk, the REST API:
1. Extracts the filename from the execution history.
2. Downloads the binary image data from ComfyUI internally.
3. Encodes the raw bytes into a Base64 string with a Data URI prefix (`data:image/png;base64,...`).
4. Optionally uses the `qrcode` python library to render a second Base64 image containing all generation parameters.
