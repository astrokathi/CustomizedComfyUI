<skill>
<name>Generate Image API</name>
<description>Autonomously bootstraps the ComfyUI API, performs prompt engineering, and generates an image via the REST API.</description>

<instructions>
This skill allows you to autonomously handle user requests for image generation by bootstrapping the necessary servers, downloading required checkpoint models, and performing advanced prompt engineering before executing the API request.

<prerequisites>
Before attempting to generate an image, you MUST verify the environment:

1. <step>Check Models</step>: Verify if the requested model exists in `models/checkpoints/`. Default to `DreamShaper_8_pruned.safetensors` if unspecified.
   - If missing, download it:
     ```bash
     wget -O models/checkpoints/DreamShaper_8_pruned.safetensors https://huggingface.co/Lykon/DreamShaper/resolve/main/DreamShaper_8_pruned.safetensors
     # OR for v1.5:
     wget -O models/checkpoints/v1-5-pruned-emaonly.safetensors https://huggingface.co/runwayml/stable-diffusion-v1-5/resolve/main/v1-5-pruned-emaonly.safetensors
     ```

2. <step>Check ComfyUI</step>: Check if ComfyUI is running on port 8188.
   - If not, start it in the background:
     ```bash
     python main.py &
     ```

3. <step>Check REST API</step>: Check if the REST API is running on port 8000.
   - If not, start it in the background:
     ```bash
     ./venv/bin/python comfy_rest_api.py &
     ```
</prerequisites>

<prompt_engineering>
When the user provides a simple prompt (e.g., "a cat in space"), you should autonomously expand it into a highly detailed, comma-separated prompt optimized for Stable Diffusion 1.5. 
- Example: `masterpiece, best quality, ultra-detailed, 8k resolution, a futuristic cat floating in deep space, glowing neon stars, cinematic lighting, dramatic shadows, sharp focus`
- Also generate an appropriate negative prompt to avoid bad anatomy, lowres, and artifacts.
</prompt_engineering>

<execution>
Use `curl` to submit the payload to the REST API.

```bash
curl -X POST http://localhost:8000/api/v1/generate \
     -H "X-API-Key: secret-key-123" \
     -H "Content-Type: application/json" \
     -d '{
           "prompt": "your enhanced positive prompt",
           "negative_prompt": "your enhanced negative prompt",
           "model_name": "DreamShaper_8_pruned.safetensors"
         }'
```

Parse the JSON response and inform the user that the image and QR code have been generated successfully!
</execution>
</instructions>
</skill>
