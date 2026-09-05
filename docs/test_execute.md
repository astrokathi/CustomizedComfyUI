# ComfyUI REST API Integration Tests

This file contains ready-to-use cURL commands to test the ComfyUI REST API for each supported model. The REST API automatically injects the perfect default parameters (CFG, steps, dimensions) based on the `model_name` you specify.

> **Note**: These commands pipe the output directly into `jq` and `base64 --decode` to save the generated image directly to your disk, preventing your terminal from being flooded with base64 string data.

## 1. DreamShaper 8 (SD 1.5)
*Use Case: Great all-rounder for 2.5D illustration and concept art.*
```bash
curl -s -X POST http://127.0.0.1:8000/api/v1/generate \
  -H "Content-Type: application/json" \
  -H "X-API-Key: secret-key-123" \
  -d '{
    "prompt": "masterpiece, highly detailed, 2.5D illustration of a futuristic cyber-knight, neon glowing sword",
    "negative_prompt": "worst quality, low quality, bad anatomy, missing fingers",
    "model_name": "DreamShaper_8_pruned.safetensors"
  }' | jq -r '.image' | sed 's/data:image\/png;base64,//' | base64 --decode > dreamshaper8.png
```

## 2. Juggernaut RunDiffusion Photo2 Lightning (SDXL)
*Use Case: Cinematic realism, movie frames, and gritty lighting.*
```bash
curl -s -X POST http://127.0.0.1:8000/api/v1/generate \
  -H "Content-Type: application/json" \
  -H "X-API-Key: secret-key-123" \
  -d '{
    "prompt": "cinematic movie frame, wide shot, gritty lighting, an abandoned gothic cathedral, dramatic shadows",
    "negative_prompt": "worst quality, low quality, illustration, cartoon",
    "model_name": "Juggernaut_RunDiffusionPhoto2_Lightning_4Steps.safetensors"
  }' | jq -r '.image' | sed 's/data:image\/png;base64,//' | base64 --decode > juggernaut.png
```

## 3. RealVisXL V5.0 Lightning (SDXL)
*Use Case: DSLR Candid Photography with natural skin textures.*
```bash
curl -s -X POST http://127.0.0.1:8000/api/v1/generate \
  -H "Content-Type: application/json" \
  -H "X-API-Key: secret-key-123" \
  -d '{
    "prompt": "candid dslr photography, detailed human face, natural skin texture, soft sunlight, highly detailed",
    "negative_prompt": "worst quality, low quality, ai plastic sheen, smooth skin",
    "model_name": "RealVisXL_V5.0_Lightning_fp16.safetensors"
  }' | jq -r '.image' | sed 's/data:image\/png;base64,//' | base64 --decode > realvis.png
```

## 4. DreamShaper XL Lightning (SDXL)
*Use Case: High-res digital painting & character art.*
```bash
curl -s -X POST http://127.0.0.1:8000/api/v1/generate \
  -H "Content-Type: application/json" \
  -H "X-API-Key: secret-key-123" \
  -d '{
    "prompt": "masterpiece, 8k resolution, semi-realistic character art of a forest elf rogue",
    "negative_prompt": "worst quality, low quality, bad anatomy",
    "model_name": "DreamShaperXL_Lightning.safetensors"
  }' | jq -r '.image' | sed 's/data:image\/png;base64,//' | base64 --decode > dreamshaper-lightning.png
```

## 5. DreamShaper XL Turbo v2 (SDXL)
*Use Case: Fast High-res digital art.*
```bash
curl -s -X POST http://127.0.0.1:8000/api/v1/generate \
  -H "Content-Type: application/json" \
  -H "X-API-Key: secret-key-123" \
  -d '{
    "prompt": "masterpiece, 8k resolution, epic digital painting of a cosmic nebula",
    "negative_prompt": "worst quality, low quality, text, watermark",
    "model_name": "DreamShaperXL_Turbo_v2.safetensors"
  }' | jq -r '.image' | sed 's/data:image\/png;base64,//' | base64 --decode > dreamshaper-turbo.png
```

## 6. SD 1.5 Pruned (SD 1.5)
*Use Case: Unbiased baseline model.*
```bash
curl -s -X POST http://127.0.0.1:8000/api/v1/generate \
  -H "Content-Type: application/json" \
  -H "X-API-Key: secret-key-123" \
  -d '{
    "prompt": "a beautiful landscape, mountains, lake, sunset",
    "negative_prompt": "worst quality, low quality",
    "model_name": "v1-5-pruned-emaonly.safetensors"
  }' | jq -r '.image' | sed 's/data:image\/png;base64,//' | base64 --decode > sd15.png
```
