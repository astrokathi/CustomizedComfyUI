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
                return web.json_response({"models": models})
            return web.HTTPInternalServerError(reason="Failed to fetch from ComfyUI")

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

async def generate_image(request):
    await check_auth(request)
    try:
        payload = await request.json()
    except Exception:
        raise web.HTTPBadRequest(reason="Invalid JSON")
        
    prompt = payload.get("prompt")
    if not prompt:
        raise web.HTTPBadRequest(reason="'prompt' is mandatory")
        
    model_name = payload.get("model_name", "v1-5-pruned-emaonly.safetensors")
    negative_prompt = payload.get("negative_prompt", "")
    
    # Apply dynamic defaults based on model
    if model_name == "DreamShaper_8_pruned.safetensors":
        cfg = payload.get("cfg", 7.5)
        steps = payload.get("steps", 30)
        seed = payload.get("seed", random.randint(1, 999999999999999))
        width = payload.get("width", 768)
        height = payload.get("height", 512)
    else:
        # Default to v1_5_pruned_emaonly.safetensors values
        cfg = payload.get("cfg", 7.5)
        steps = payload.get("steps", 25)
        seed = payload.get("seed", random.randint(1, 999999999999999))
        width = payload.get("width", 512)
        height = payload.get("height", 768)
        
    sampler_name = payload.get("sampler_name", "dpmpp_2m")
    scheduler = payload.get("scheduler", "karras")
    
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
            
            # Download the actual image bytes
            async with session.get(f"{COMFY_URL}/view?{url_params}") as img_resp:
                img_bytes = await img_resp.read()
                
            gen_image_b64 = "data:image/png;base64," + base64.b64encode(img_bytes).decode("utf-8")
            
            # Generate the QR Code with config info
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
                "image": gen_image_b64,
                "config": config_data
            }
            
            if payload.get("qr_code") is True:
                qr_b64 = generate_qr_base64(config_data)
                response_data["qrcode"] = "data:image/png;base64," + qr_b64
            
            return web.json_response(response_data)

app = web.Application(client_max_size=1024**3)
app.router.add_get('/api/v1/models/{type}', get_models)
app.router.add_post('/api/v1/generate', generate_image)

if __name__ == '__main__':
    print(f"Starting ComfyUI REST API on port 8000...")
    print(f"API Key required (X-API-Key or Bearer): {API_KEY}")
    web.run_app(app, host='0.0.0.0', port=8000)
