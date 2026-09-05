# ComfyUI Video Loop & REST API Gateway

![Architecture Banner](docs/assets/banner.jpg)

Welcome to the custom **ComfyUI REST API & Video Looper** project. This repository extends the powerful ComfyUI backend with a lightning-fast, asynchronous REST API gateway and a custom autonomous video looping suite.

## Features

- 🎨 **Stable Diffusion 1.5 & SDXL Support**: Fully integrated and automated node workflows.
- ⚡ **REST API Gateway**: A custom `aiohttp` web server providing standard `GET` and `POST` endpoints with API Key authentication.
- 🔁 **Video Looper**: Custom nodes that safely prevent VAE degradation during long generation cycles using Latent Feedback loops.
- 🧠 **AI Autonomous Skills**: Includes drop-in `SKILL.md` files allowing Claude, Gemini, ChatGPT, and Hermes to autonomously engineer prompts, start servers, and execute generations.
- 📱 **QR Code Metadata**: Optionally embed the exact generation metadata directly into a scannable QR Code attached to the payload.

## Developer Documentation

We have prepared comprehensive developer documentation intended to be hosted via GitHub Pages.

**📚 [Read the Documentation](docs/README.md)**

*Includes OpenAPI specifications, architecture diagrams, and detailed usage instructions.*

## Quick Start
```bash
# 1. Start the core ComfyUI engine
python main.py &

# 2. Start the REST API Gateway
./venv/bin/python comfy_rest_api.py &
```
