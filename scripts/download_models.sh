#!/usr/bin/env bash

set -euo pipefail

echo "==============================="
echo " Downloading Baseline Models"
echo "==============================="

# Checkpoints
echo "[1/3] Downloading SD 1.5 Checkpoint (~4GB)..."
curl -L -C - "https://huggingface.co/runwayml/stable-diffusion-v1-5/resolve/main/v1-5-pruned-emaonly.safetensors" -o "data/models/checkpoints/v1-5-pruned-emaonly.safetensors"

# VAE
echo ""
echo "[2/3] Downloading VAE (~335MB)..."
curl -L -C - "https://huggingface.co/stabilityai/sd-vae-ft-mse-original/resolve/main/vae-ft-mse-840000-ema-pruned.safetensors" -o "data/models/vae/vae-ft-mse-840000-ema-pruned.safetensors"

# Upscaler
echo ""
echo "[3/3] Downloading RealESRGAN_x4plus (~67MB)..."
curl -L -C - "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth" -o "data/models/upscale_models/RealESRGAN_x4plus.pth"

echo ""
echo "All downloads completed successfully!"
