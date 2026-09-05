# 🚀 Starting the Servers

The ComfyUI REST API Gateway project utilizes three interconnected servers running simultaneously. We have provided an automated deployment script to make starting them as effortless as possible.

## Prerequisites

Before starting the servers, ensure you have set your `NVIDIA_API_KEY` in your environment (this is required by the MCP AI Client for the Nemotron LLM):

```bash
export NVIDIA_API_KEY="your-api-key"
```

## Using the Unified Startup Script (Recommended)

The easiest way to boot the entire ecosystem is by using our integrated script:

```bash
./deploy/servers_start.sh
```

### What this script does:
1. **Virtual Environment**: Automatically creates a Python `venv` and installs the required dependencies from `requirements.txt` if they are missing.
2. **Core ComfyUI Server**: Boots the core engine on `http://127.0.0.1:8188` in the background.
3. **REST API Gateway**: Boots the FastAPI wrapper on `http://127.0.0.1:8000` in the background.
4. **AI Art Director (MCP Client UI)**: Boots the Gradio Chatbot on `http://127.0.0.1:7860` in the background.

When you are finished, simply press **Ctrl+C** in your terminal. The script will safely terminate all background processes.

---

## Starting Servers Manually

If you prefer to start the servers independently (e.g. for debugging), you can do so from the project root:

1. **Activate Environment**:
   ```bash
   source venv/bin/activate
   ```

2. **Start ComfyUI**:
   ```bash
   python server.py
   ```

3. **Start REST API**:
   ```bash
   python comfy_rest_api.py
   ```

4. **Start MCP Client UI**:
   ```bash
   python mcp_client_ui.py
   ```

[🔙 Back to Home](README.md)
