#!/bin/bash

# Navigate to the project root directory
cd "$(dirname "$0")/.."

echo "🎨 Starting ComfyUI Project Servers..."

# Function to handle cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Stopping all servers..."
    kill $(jobs -p) 2>/dev/null
    wait $(jobs -p) 2>/dev/null
    echo "✅ All servers stopped."
    exit
}

# Trap SIGINT (Ctrl+C) and SIGTERM
trap cleanup SIGINT SIGTERM

# Check for virtual environment
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment and installing dependencies..."
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

# 1. Start the core ComfyUI Server (Port 8188)
echo "🚀 Starting core ComfyUI server..."
bash scripts/start.sh > comfyui.log 2>&1 &
COMFY_PID=$!

# Wait for ComfyUI to initialize
sleep 3

# 2. Start the Custom REST API Server (Port 8000)
echo "🚀 Starting ComfyUI REST API..."
python comfy_rest_api.py &
API_PID=$!

# Wait for REST API to initialize
sleep 2

# 3. Start the MCP Client Gradio UI (Port 7860)
# Note: The MCP server (comfy_mcp_server.py) is automatically spawned by the client per request
echo "🚀 Starting MCP Client UI..."
export NVIDIA_API_KEY="${NVIDIA_API_KEY:-dummy_key}"
python mcp_client_ui.py &
UI_PID=$!

echo ""
echo "======================================================="
echo "🌟 ALL SERVERS ARE RUNNING!"
echo "======================================================="
echo "Core ComfyUI UI : http://127.0.0.1:8188"
echo "REST API Docs   : http://127.0.0.1:8000/docs"
echo "AI Art Director : http://127.0.0.1:7860"
echo "======================================================="
echo "Press Ctrl+C to stop all servers."
echo ""

# Wait for all background processes
wait
