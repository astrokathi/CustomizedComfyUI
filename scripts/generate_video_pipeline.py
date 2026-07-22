#!/usr/bin/env python3
import os
import sys
import json
import time
import urllib.request
import urllib.parse
import argparse
import subprocess
from dotenv import load_dotenv

# Optional: if they have openai installed
try:
    from openai import OpenAI
except ImportError:
    print("ERROR: openai package is missing. Run: pip install openai")
    sys.exit(1)

# Load environment variables
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
load_dotenv(os.path.join(PROJECT_ROOT, ".env"), override=True)

COMFY_URL = f"http://127.0.0.1:{os.getenv('COMFYUI_PORT', '8188')}"

def generate_prompts(video_prompt, frames_count):
    """Uses NVIDIA Nemotron to generate a JSON list of sequential frame prompts."""
    api_key = os.getenv("NVIDIA_API_KEY")
    api_base = os.getenv("NVIDIA_API_BASE")
    model = os.getenv("NVIDIA_MODEL", "nvidia/nemotron-ultra-253b-v1")

    if not api_key:
        print("ERROR: NVIDIA_API_KEY is not set in .env")
        sys.exit(1)

    client = OpenAI(api_key=api_key, base_url=api_base)
    
    sys_prompt = f"""You are an AI video director. The user will give you a video concept.
You must output a JSON array of exactly {frames_count} strings. 
Each string is a highly detailed, descriptive image prompt for Stable Diffusion representing a single frame of the video.
The frames should sequentially evolve to create a smooth animation.
CRITICAL: You must strictly enforce visual consistency. The subject, environment, lighting, art style, and camera angles should have microscopic, consistent variations between frames to ensure a buttery smooth video. Avoid sudden cuts or large changes in the scene.
DO NOT output anything other than the raw JSON array. No markdown, no explanations."""

    print(f"[*] Requesting {frames_count} sequential prompts from NVIDIA LLM...")
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": video_prompt}
            ],
            temperature=0.7,
            max_tokens=4000
        )
    except Exception as e:
        print(f"[!] NVIDIA API error: {e}")
        print("[*] Falling back to local Ollama...")
        client = OpenAI(api_key="ollama", base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434") + "/v1")
        response = client.chat.completions.create(
            model=os.getenv("OLLAMA_MODEL", "llama3"),
            messages=[
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": video_prompt}
            ],
            temperature=0.7,
            max_tokens=4000
        )
    
    raw_text = response.choices[0].message.content.strip()
    if raw_text.startswith("```json"):
        raw_text = raw_text[7:-3]
    elif raw_text.startswith("```"):
        raw_text = raw_text[3:-3]
        
    try:
        prompts = json.loads(raw_text)
        if len(prompts) != frames_count:
            print(f"[!] Warning: Requested {frames_count} frames, but LLM returned {len(prompts)}.")
        return prompts
    except json.JSONDecodeError as e:
        print("ERROR: Failed to parse LLM response as JSON.")
        print(raw_text)
        sys.exit(1)

def queue_prompt(workflow_api_dict):
    """Queues a prompt to ComfyUI and returns the prompt_id."""
    data = json.dumps({"prompt": workflow_api_dict}).encode('utf-8')
    req = urllib.request.Request(f"{COMFY_URL}/prompt", data=data, headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read())['prompt_id']
    except Exception as e:
        print(f"ERROR: Failed to connect to ComfyUI at {COMFY_URL}. Is it running?")
        sys.exit(1)

def wait_for_image(prompt_id):
    """Polls ComfyUI history until the prompt_id is completed and returns the output filename."""
    while True:
        try:
            req = urllib.request.Request(f"{COMFY_URL}/history/{prompt_id}")
            with urllib.request.urlopen(req) as response:
                history = json.loads(response.read())
                if prompt_id in history:
                    outputs = history[prompt_id].get('outputs', {})
                    for node_id, node_output in outputs.items():
                        if 'images' in node_output:
                            return node_output['images'][0]['filename']
        except Exception:
            pass
        time.sleep(1)

def download_image(filename, save_path):
    """Downloads an image from ComfyUI."""
    url = f"{COMFY_URL}/view?filename={urllib.parse.quote(filename)}&type=output"
    urllib.request.urlretrieve(url, save_path)

def main():
    parser = argparse.ArgumentParser(description="ComfyUI LLM Video Generator Pipeline")
    parser.add_argument("--prompt", type=str, required=True, help="The main video concept")
    parser.add_argument("--negative", type=str, default="ugly, blurry, low resolution, deformed", help="Negative prompt")
    parser.add_argument("--fps", type=int, default=8, help="Frames per second")
    parser.add_argument("--seconds", type=int, default=2, help="Duration in seconds")
    parser.add_argument("--prefix", type=str, default="llm_video", help="Prefix for output files")
    parser.add_argument("--workflow", type=str, required=True, help="Path to your ComfyUI workflow JSON (MUST BE API FORMAT)")
    parser.add_argument("--pos-node", type=str, default="2", help="Node ID for the positive prompt text")
    parser.add_argument("--neg-node", type=str, default="5", help="Node ID for the negative prompt text")
    parser.add_argument("--seed-node", type=str, default="4", help="Node ID for the KSampler (to lock seed)")
    
    args = parser.parse_args()
    
    frames_count = args.fps * args.seconds
    
    # 1. Generate Prompts
    frame_prompts = generate_prompts(args.prompt, frames_count)
    print(f"[✓] Generated {len(frame_prompts)} prompts.")
    
    # 2. Load Workflow
    with open(args.workflow, 'r') as f:
        workflow = json.load(f)
        
    # Lock the seed to prevent extreme temporal flickering
    if args.seed_node in workflow and "seed" in workflow[args.seed_node]["inputs"]:
        workflow[args.seed_node]["inputs"]["seed"] = 123456789 

    # 3. Setup output directory
    base_out_dir = os.path.join(PROJECT_ROOT, "data", "output", args.prefix)
    frames_dir = os.path.join(base_out_dir, "frames")
    os.makedirs(frames_dir, exist_ok=True)
    
    # 4. Generate Images Sequentially
    print(f"[*] Starting sequential generation for {len(frame_prompts)} frames to prevent OOM...")
    for i, f_prompt in enumerate(frame_prompts):
        frame_num = i + 1
        print(f"  -> Frame {frame_num}/{len(frame_prompts)}: Queueing...")
        
        # Inject prompts
        if args.pos_node in workflow:
            workflow[args.pos_node]["inputs"]["text"] = f_prompt
        if args.neg_node in workflow:
            workflow[args.neg_node]["inputs"]["text"] = args.negative
            
        prompt_id = queue_prompt(workflow)
        
        # Wait for completion
        output_filename = wait_for_image(prompt_id)
        
        # Download and rename sequentially for ffmpeg
        save_path = os.path.join(frames_dir, f"frame_{frame_num:04d}.png")
        download_image(output_filename, save_path)
        print(f"     [✓] Saved {save_path}")
        
    # 5. Stitch with FFmpeg
    video_out = os.path.join(base_out_dir, f"{args.prefix}.mp4")
    print(f"[*] Stitching frames into video at {args.fps} FPS...")
    
    ffmpeg_cmd = [
        "ffmpeg", "-y", 
        "-framerate", str(args.fps),
        "-i", os.path.join(frames_dir, "frame_%04d.png"),
        "-c:v", "libx264", 
        "-pix_fmt", "yuv420p", 
        video_out
    ]
    
    try:
        subprocess.run(ffmpeg_cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"\n=============================================")
        print(f" SUCCESS! Video saved to:")
        print(f" {video_out}")
        print(f"=============================================\n")
    except FileNotFoundError:
        print("\n[!] FFmpeg is not installed! The frames were saved, but video compilation failed.")
        print("    Install it via: brew install ffmpeg")
        print(f"    Then run manually: {' '.join(ffmpeg_cmd)}")

if __name__ == "__main__":
    main()
