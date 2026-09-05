import os
import json
import asyncio
import base64
import random
import urllib.parse
import uuid
import qrcode
from io import BytesIO
from aiohttp import web
import aiohttp

COMFY_URL = "http://127.0.0.1:8188"
COMFY_WS = "ws://127.0.0.1:8188/ws"
API_KEY = os.environ.get("COMFY_REST_API_KEY", "secret-key-123")

WORKFLOW_API = {
  "3": {
    "inputs": {
      "seed": 0,
      "steps": 25,
      "cfg": 7.5,
      "sampler_name": "dpmpp_2m",
      "scheduler": "karras",
      "denoise": 1,
      "model": [ "4", 0 ],
      "positive": [ "6", 0 ],
      "negative": [ "7", 0 ],
      "latent_image": [ "5", 0 ]
    },
    "class_type": "KSampler"
  },
  "4": {
    "inputs": {
      "ckpt_name": "v1-5-pruned-emaonly.safetensors"
    },
    "class_type": "CheckpointLoaderSimple"
  },
  "5": {
    "inputs": {
      "width": 512,
      "height": 768,
      "batch_size": 1
    },
    "class_type": "EmptyLatentImage"
  },
  "6": {
    "inputs": {
      "text": "prompt goes here",
      "clip": [ "4", 1 ]
    },
    "class_type": "CLIPTextEncode"
  },
  "7": {
    "inputs": {
      "text": "negative prompt goes here",
      "clip": [ "4", 1 ]
    },
    "class_type": "CLIPTextEncode"
  },
  "8": {
    "inputs": {
      "samples": [ "3", 0 ],
      "vae": [ "4", 2 ]
    },
    "class_type": "VAEDecode"
  },
  "9": {
    "inputs": {
      "filename_prefix": "rest_api",
      "images": [ "8", 0 ]
    },
    "class_type": "SaveImage"
  }
}

async def check_auth(request):
    auth_header = request.headers.get("Authorization", "")
    api_key_header = request.headers.get("X-API-Key", "")
    
    token = ""
    if auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
    elif api_key_header:
        token = api_key_header
        
    if token != API_KEY:
        raise web.HTTPUnauthorized(reason="Invalid API Key")

async def get_models(request):
    await check_auth(request)
    model_type = request.match_info.get('type', 'checkpoints')
    
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{COMFY_URL}/object_info/CheckpointLoaderSimple") as resp:
            if resp.status == 200:
                data = await resp.json()
                models = data.get("CheckpointLoaderSimple", {}).get("input", {}).get("required", {}).get("ckpt_name", [])
                if isinstance(models, list) and len(models) > 0 and isinstance(models[0], list):
                    models = models[0]
                return web.json_response({"status": "success", "models": models})
            return web.HTTPInternalServerError(reason="Failed to fetch from ComfyUI")

async def background_free_memory():
    """Fire-and-forget task to clear memory AFTER the response is sent back to the client."""
    try:
        async with aiohttp.ClientSession() as session:
            free_payload = {"unload_models": True, "free_memory": True}
            async with session.post(f"{COMFY_URL}/free", json=free_payload) as free_resp:
                if free_resp.status == 200:
                    print("Memory successfully freed in the background after execution.")
    except Exception as e:
        print(f"Error freeing memory in background: {e}")

def generate_qr_base64(data_dict):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(json.dumps(data_dict, indent=2))
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode("utf-8")

def get_model_defaults(model_name):
    defaults = {
        "v1-5-pruned-emaonly.safetensors": {"cfg": 7.5, "steps": 25, "width": 512, "height": 512, "sampler_name": "euler_ancestral", "scheduler": "normal"},
        "DreamShaper_8_pruned.safetensors": {"cfg": 6.5, "steps": 28, "width": 512, "height": 768, "sampler_name": "dpmpp_2m", "scheduler": "karras"},
        "DreamShaperXL_Lightning.safetensors": {"cfg": 2.0, "steps": 6, "width": 1024, "height": 1024, "sampler_name": "dpmpp_2m", "scheduler": "karras"},
        "DreamShaperXL_Turbo_v2.safetensors": {"cfg": 2.0, "steps": 6, "width": 1024, "height": 1024, "sampler_name": "dpmpp_2m", "scheduler": "karras"},
        "Juggernaut_RunDiffusionPhoto2_Lightning_4Steps.safetensors": {"cfg": 1.5, "steps": 5, "width": 1344, "height": 768, "sampler_name": "dpmpp_2m_sde", "scheduler": "karras"},
        "RealVisXL_V5.0_Lightning_fp16.safetensors": {"cfg": 1.5, "steps": 6, "width": 896, "height": 1152, "sampler_name": "dpmpp_2m_sde", "scheduler": "karras"}
    }
    return defaults.get(model_name, defaults["DreamShaper_8_pruned.safetensors"])

async def generate_image(request):
    await check_auth(request)
    try:
        payload = await request.json()
    except Exception:
        raise web.HTTPBadRequest(reason="Invalid JSON")
        
    prompt = payload.get("prompt")
    if not prompt:
        raise web.HTTPBadRequest(reason="'prompt' is mandatory")
        
    model_name = payload.get("model_name", "DreamShaper_8_pruned.safetensors")
    negative_prompt = payload.get("negative_prompt", "")
    
    # Apply dynamic defaults based on model
    defaults = get_model_defaults(model_name)
    cfg = payload.get("cfg", defaults["cfg"])
    steps = payload.get("steps", defaults["steps"])
    seed = payload.get("seed", random.randint(1, 999999999999999))
    width = payload.get("width", defaults["width"])
    height = payload.get("height", defaults["height"])
    sampler_name = payload.get("sampler_name", defaults["sampler_name"])
    scheduler = payload.get("scheduler", defaults["scheduler"])
    
    # Configure the graph template
    graph = json.loads(json.dumps(WORKFLOW_API))
    graph["4"]["inputs"]["ckpt_name"] = model_name
    graph["6"]["inputs"]["text"] = prompt
    graph["7"]["inputs"]["text"] = negative_prompt
    graph["5"]["inputs"]["width"] = width
    graph["5"]["inputs"]["height"] = height
    graph["3"]["inputs"]["seed"] = seed
    graph["3"]["inputs"]["steps"] = steps
    graph["3"]["inputs"]["cfg"] = cfg
    graph["3"]["inputs"]["sampler_name"] = sampler_name
    graph["3"]["inputs"]["scheduler"] = scheduler
    
    client_id = str(uuid.uuid4())
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.ws_connect(f"{COMFY_WS}?clientId={client_id}") as ws:
                post_data = {"prompt": graph, "client_id": client_id}
                async with session.post(f"{COMFY_URL}/prompt", json=post_data) as resp:
                    if resp.status != 200:
                        err = await resp.text()
                        raise web.HTTPInternalServerError(reason=f"ComfyUI Error: {err}")
                    resp_json = await resp.json()
                    prompt_id = resp_json["prompt_id"]
                    
                # Wait for the generation to finish
                while True:
                    msg = await ws.receive()
                    if msg.type == aiohttp.WSMsgType.TEXT:
                        message = json.loads(msg.data)
                        if message["type"] == "executing":
                            data = message["data"]
                            if data["node"] is None and data["prompt_id"] == prompt_id:
                                break
                
                # Fetch the generated image filename from history
                async with session.get(f"{COMFY_URL}/history/{prompt_id}") as hist_resp:
                    history = await hist_resp.json()
                    history_data = history[prompt_id]
                    
                outputs = history_data.get("outputs", {})
                if "9" not in outputs or "images" not in outputs["9"]:
                    raise web.HTTPInternalServerError(reason="Failed to find generated image in history")
                    
                image_info = outputs["9"]["images"][0]
                filename = image_info["filename"]
                subfolder = image_info["subfolder"]
                folder_type = image_info["type"]
                
                url_params = urllib.parse.urlencode({
                    "filename": filename,
                    "subfolder": subfolder,
                    "type": folder_type
                })
                
                # Instead of downloading base64, construct the static URL
                path_parts = []
                if subfolder:
                    path_parts.append(subfolder)
                path_parts.append(filename)
                
                relative_path = "/".join(path_parts)
                image_url = f"http://127.0.0.1:8000/output/{urllib.parse.quote(relative_path)}"
                
                # Generate the config info
                config_data = {
                    "prompt": prompt,
                    "negative_prompt": negative_prompt,
                    "model_name": model_name,
                    "cfg": str(cfg),
                    "steps": str(steps),
                    "seed": seed,
                    "width": width,
                    "height": height,
                    "sampler_function": sampler_name,
                    "scheduler": scheduler
                }
                
                response_data = {
                    "status": "success",
                    "image_url": image_url,
                    "config": config_data
                }
                
                if payload.get("qr_code") is True:
                    # Save QR code directly to output dir so we can serve it by URL too
                    qr_img = qrcode.make(json.dumps(config_data))
                    qr_filename = f"qr_{prompt_id}.png"
                    qr_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "output", qr_filename)
                    qr_img.save(qr_path)
                    
                    response_data["qrcode_url"] = f"http://127.0.0.1:8000/output/{urllib.parse.quote(qr_filename)}"
                
                return web.json_response(response_data)
        finally:
            # Always explicitly free ComfyUI memory to prevent out-of-memory errors on next load.
            # We use asyncio.create_task so it happens asynchronously AFTER we return the response.
            asyncio.create_task(background_free_memory())

app = web.Application(client_max_size=1024**3)
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)
app.router.add_static('/output/', path=OUTPUT_DIR, name='output')
app.router.add_get('/api/v1/models/{type}', get_models)
app.router.add_post('/api/v1/generate', generate_image)

if __name__ == '__main__':
    print(f"Starting ComfyUI REST API on port 8000...")
    print(f"API Key required (X-API-Key or Bearer): {API_KEY}")
    web.run_app(app, host='0.0.0.0', port=8000)
