import os
import aiohttp
from mcp.server.fastmcp import FastMCP, Context

mcp = FastMCP("ComfyUI-REST-API")
API_URL = "http://localhost:8000/api/v1/generate"
API_KEY = os.environ.get("COMFY_REST_API_KEY", "secret-key-123")

@mcp.tool()
def select_optimal_model(use_case_description: str) -> str:
    """
    Analyzes the user's desired image use-case and returns the optimal model_name and its ideal default parameters.
    You MUST call this tool before calling text_to_image if the user has not explicitly specified a model name.
    
    Valid use cases include:
    - "cinematic", "movie", "gritty", "architectural"
    - "photography", "dslr", "realistic skin", "candid"
    - "digital painting", "concept art", "video game"
    - "2.5D", "fantasy", "illustration"
    """
    desc = use_case_description.lower()
    
    if any(keyword in desc for keyword in ["cinematic", "movie", "gritty", "architectural"]):
        model = "Juggernaut_RunDiffusionPhoto2_Lightning_4Steps.safetensors"
        reason = "Excellent for cinematic realism, movie frames, gritty lighting, and architectural depth."
    elif any(keyword in desc for keyword in ["photography", "dslr", "realistic skin", "candid", "photo", "realistic human"]):
        model = "RealVisXL_V5.0_Lightning_fp16.safetensors"
        reason = "Excellent for DSLR camera fidelity, candid photography, and zero AI plastic sheen."
    elif any(keyword in desc for keyword in ["digital painting", "high resolution", "semi-realistic", "video game"]):
        model = "DreamShaperXL_Lightning.safetensors"
        reason = "Excellent for high-resolution digital painting, semi-realistic character art, and video game assets."
    elif any(keyword in desc for keyword in ["2.5d", "fantasy", "illustration", "vibrant", "stylized"]):
        model = "DreamShaper_8_pruned.safetensors"
        reason = "Excellent for 2.5D illustration, fantasy portraits, and digital concept art."
    else:
        # Fallback
        model = "DreamShaper_8_pruned.safetensors"
        reason = "Defaulting to DreamShaper 8 as it is the most versatile all-rounder."

    return f"Recommended Model: {model}\nReasoning: {reason}\nYou may now pass this model_name into the text_to_image tool."

@mcp.tool()
async def text_to_image(
    prompt: str,
    ctx: Context,
    model_name: str = "DreamShaper_8_pruned.safetensors",
    negative_prompt: str = "",
    cfg: float = None,
    steps: int = None,
    width: int = None,
    height: int = None,
) -> str:
    """
    Generates an image via the ComfyUI REST API.
    
    ### IMPORTANT: Model Context & Operational Constraints
    You MUST adhere to these default values and limitations depending on the requested model_name:

    1. DreamShaper_8_pruned.safetensors (DEFAULT):
       - CFG: 6.5
       - Steps: 28
       - Width/Height: 512x768 (Portrait) or 768x512 (Landscape)
       - Optimal for 2.5D illustration, fantasy, digital concept art.
    
    2. DreamShaperXL_Lightning.safetensors OR DreamShaperXL_Turbo_v2.safetensors:
       - CFG: 2.0 (MUST be low for Lightning/Turbo!)
       - Steps: 6 (MUST be low for Lightning/Turbo!)
       - Width/Height: 1024x1024 (Native SDXL)
       
    3. Juggernaut_RunDiffusionPhoto2_Lightning_4Steps.safetensors:
       - CFG: 1.5
       - Steps: 5
       - Width/Height: 1344x768 (Widescreen cinematic)
       - Optimal for photorealistic cinematic film stills.
       
    4. RealVisXL_V5.0_Lightning_fp16.safetensors:
       - CFG: 1.5
       - Steps: 6
       - Width/Height: 896x1152 (Portrait photography)
       
    5. v1-5-pruned-emaonly.safetensors:
       - CFG: 7.5
       - Steps: 25
       - Width/Height: 512x512
       
    If cfg, steps, width, or height are omitted, the API will automatically inject the optimal defaults listed above based on the chosen model.
    """
    
    ctx.info(f"Starting image generation using {model_name}...")
    
    payload = {
        "prompt": prompt,
        "negative_prompt": negative_prompt,
        "model_name": model_name
    }
    
    if cfg is not None: payload["cfg"] = cfg
    if steps is not None: payload["steps"] = steps
    if width is not None: payload["width"] = width
    if height is not None: payload["height"] = height
    
    headers = {
        "X-API-Key": API_KEY,
        "Content-Type": "application/json"
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(API_URL, json=payload, headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    
                    # Log to MCP Client
                    ctx.info(f"Generation successful! {model_name} generated the image with CFG {data['config']['cfg']} and {data['config']['steps']} Steps.")
                    
                    # Return formatted Markdown containing the image and configuration
                    b64_image = data.get("image", "")
                    config = data.get("config", {})
                    
                    md_response = f"### Image Generated Successfully!\n\n"
                    md_response += f"![Generated Image]({b64_image})\n\n"
                    md_response += f"**Model**: {config.get('model_name')}\n"
                    md_response += f"**Steps**: {config.get('steps')} | **CFG**: {config.get('cfg')}\n"
                    md_response += f"**Resolution**: {config.get('width')}x{config.get('height')}\n"
                    md_response += f"**Prompt**: {config.get('prompt')}\n"
                    
                    return md_response
                else:
                    err_text = await resp.text()
                    ctx.error(f"API Error: {err_text}")
                    return f"Failed to generate image. Error {resp.status}: {err_text}"
        except Exception as e:
            ctx.error(f"Connection Error: {str(e)}")
            return f"Failed to connect to REST API: {str(e)}"

if __name__ == "__main__":
    mcp.run()
