import os
import asyncio
import json
import re
from openai import AsyncOpenAI
import gradio as gr
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# NVIDIA LLM Config
NVIDIA_API_KEY = os.environ.get("NVIDIA_API_KEY")
if not NVIDIA_API_KEY:
    print("WARNING: NVIDIA_API_KEY environment variable not set. Using dummy key for testing, but API calls will fail.")
    NVIDIA_API_KEY = "dummy_key"

openai_client = AsyncOpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key=NVIDIA_API_KEY
)

MODEL = "nvidia/nemotron-3-super-120b-a12b"

# MCP Server Config
server_params = StdioServerParameters(
    command="./venv/bin/python",
    args=["comfy_mcp_server.py"]
)

PRESETS = [
    "✨ No Preset (Freeform) | AI Autonomously Decides",
    "✏️ Minimalist Flat Vector | Model: DreamShaperXL_Lightning.safetensors | Prefix: Minimalist flat vector illustration, solid colors, clean lines, corporate memphis style, white background",
    "🖼️ Vintage Polaroid | Model: RealVisXL_V5.0_Lightning_fp16.safetensors | Prefix: Vintage polaroid photo, 1980s aesthetic, film grain, faded colors, flash photography",
    "🧩 3D Isometric | Model: DreamShaperXL_Lightning.safetensors | Prefix: 3D isometric render, tilt-shift, claymation style, octane render, soft lighting, clean background",
    "📸 Photorealistic Cinematic | Model: Juggernaut_RunDiffusionPhoto2_Lightning_4Steps.safetensors | Prefix: Professional cinematic film still, masterpiece, 8k resolution, highly detailed, dramatic lighting",
    "🌸 Studio Ghibli Anime | Model: DreamShaper_8_pruned.safetensors | Prefix: Anime style illustration, Studio Ghibli style, vibrant colors, beautiful anime art",
    "🖌️ Watercolor Wash | Model: DreamShaper_8_pruned.safetensors | Prefix: Beautiful watercolor painting, soft edges, pastel colors, artistic brush strokes, paper texture",
    "🖤 Ink & Crosshatch | Model: DreamShaper_8_pruned.safetensors | Prefix: Black and white ink sketch, crosshatching, pen and ink, highly detailed, comic book style",
    "🧱 Lego / Voxel Art | Model: DreamShaperXL_Lightning.safetensors | Prefix: Voxel art, macro photography of lego bricks, 3d blocky style, colorful, clean studio lighting",
    "🕹️ Cyberpunk Neon | Model: DreamShaperXL_Lightning.safetensors | Prefix: Cyberpunk aesthetic, neon lighting, dark synthwave, futuristic, glowing accents"
]

SYSTEM_PROMPT = """You are a highly capable AI Art Director. Your goal is to help the user generate stunning images using ComfyUI.
You have access to THREE tools:
1. `select_optimal_model`: Call this FIRST with the user's base request to determine the best model to use. (Skip if user provided a preset model).
2. `ram_checker`: Call this SECOND to verify the system has enough memory to load the model.
3. `text_to_image`: Call this THIRD to actually generate the image using the final verified model name.

IMPORTANT INSTRUCTIONS:
- You MUST aggressively enhance the user's simple prompt into a highly detailed, comma-separated Stable Diffusion prompt.
- If the user provides a "Style Preset Prefix" in their request, you MUST prepend it exactly to the beginning of your positive prompt!
- If the user selects "Create Variation (Same Seed)", you MUST lookup the exact Seed and Model used in the LAST generated image (from the chat history) and use them! Enhance their new prompt to improve clarity, lighting, or focus while keeping the exact same structural composition via the Seed.
- You MUST pass the exact `model_name` into `text_to_image`.
- At the very end of your final response to the user, you MUST provide exactly 3 creative follow-up prompt suggestions (e.g. "Try this with dramatic neon lighting", "Change the time of day to sunset") formatted as a bulleted list under the heading "💡 Try these variations:".

HOW TO USE TOOLS:
To use a tool, you MUST output a JSON block inside backticks like this:
```json
{
  "tool": "select_optimal_model",
  "args": {
    "use_case_description": "the user's request"
  }
}
```
Or for the ram checker:
```json
{
  "tool": "ram_checker",
  "args": {
    "model_name": "the model from select_optimal_model"
  }
}
```
Or for the image generation:
```json
{
  "tool": "text_to_image",
  "args": {
    "prompt": "enhanced positive prompt",
    "negative_prompt": "enhanced negative prompt",
    "model_name": "returned model name",
    "seed": 123456789
  }
}
```
Stop writing after outputting the JSON tool call. The system will execute the tool and provide you with the result. You must then use the result to either call the next tool or respond to the user.
"""

def extract_tool_call(content):
    if not content:
        return None
    
    # Try to find ```json ... ``` blocks
    match = re.search(r"```json\s*(\{.*?\})\s*```", content, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except:
            pass
            
    # Fallback to finding any { ... } that looks like our tool call
    match = re.search(r"(\{[\s\n]*\"tool\"[\s\n]*:.*?\})", content, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except:
            pass
            
    return None

async def chat_with_agent(message, history, preset, mode):
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    
    # Format Gradio history for OpenAI
    for item in history:
        if isinstance(item, (list, tuple)) and len(item) == 2:
            messages.append({"role": "user", "content": item[0]})
            messages.append({"role": "assistant", "content": item[1]})
        elif isinstance(item, dict):
            messages.append({"role": item.get("role", "user"), "content": item.get("content", "")})
        
    injected_prompt = f"User Message: {message}\n"
    
    if mode == "Create Variation (Same Seed, Enhanced Prompt)":
        injected_prompt += "\nINSTRUCTION: The user wants a variation of the PREVIOUS image. Look at the last image's config in the chat history, extract its exact 'Seed' and 'Model', and use them! Improve the user's prompt for better clarity/lighting."
        
    if preset and preset != "✨ No Preset (Freeform) | AI Autonomously Decides":
        try:
            _, model_part, prefix_part = preset.split(" | ")
            model_name = model_part.replace("Model: ", "")
            prefix = prefix_part.replace("Prefix: ", "")
            injected_prompt += f"\nINSTRUCTION: The user selected a stylistic preset. You MUST use model_name='{model_name}' and you MUST strictly prepend this prefix to the positive prompt: '{prefix}'"
        except:
            pass
            
    messages.append({"role": "user", "content": injected_prompt})
    
    yield "Thinking..."
    
    # Establish MCP connection per request
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # Agent Loop
            max_turns = 5
            for _ in range(max_turns):
                response = await openai_client.chat.completions.create(
                    model=MODEL,
                    messages=messages,
                    # Deliberately NOT using `tools=` to avoid NVIDIA NIM 404 UUID errors
                )
                
                response_content = response.choices[0].message.content
                
                # Check if the LLM made a tool call in the text
                tool_call = extract_tool_call(response_content)
                
                if tool_call and "tool" in tool_call and "args" in tool_call:
                    func_name = tool_call["tool"]
                    func_args = tool_call["args"]
                    
                    yield f"Executing tool: {func_name}..."
                    
                    messages.append({
                        "role": "assistant",
                        "content": response_content
                    })
                    
                    try:
                        # Call the tool over MCP
                        result = await session.call_tool(func_name, arguments=func_args)
                        tool_result_str = result.content[0].text
                    except Exception as e:
                        tool_result_str = f"Error executing tool: {str(e)}"
                        
                    messages.append({
                        "role": "user",
                        "content": f"Tool '{func_name}' returned the following result:\n{tool_result_str}\n\nPlease proceed."
                    })
                else:
                    # Final response
                    yield response_content
                    return
                    
            yield "Max turns reached without final answer."

with gr.Blocks(theme=gr.themes.Monochrome()) as demo:
    gr.Markdown("# 🎨 ComfyUI AI Art Director\nPowered by NVIDIA Nemotron & MCP")
    
    with gr.Row():
        preset_dropdown = gr.Dropdown(
            choices=PRESETS,
            value=PRESETS[0],
            label="Style Preset (Collages)"
        )
        mode_radio = gr.Radio(
            choices=["New Concept", "Create Variation (Same Seed, Enhanced Prompt)"],
            value="New Concept",
            label="Generation Mode"
        )
    
    gr.ChatInterface(
        fn=chat_with_agent,
        additional_inputs=[preset_dropdown, mode_radio],
        description="Describe the image you want to create. The AI will autonomously select the best model, engineer a detailed prompt, and generate the image!",
        examples=[
            ["I want a cinematic, gritty shot of a cyberpunk city at night with neon reflections on wet asphalt."],
            ["A candid, DSLR photography portrait of an elderly man working in a wood shop."],
            ["A fantasy digital painting of a fierce dragon breathing fire, 2.5D illustration style."]
        ]
    )

if __name__ == "__main__":
    print("Starting Gradio MCP Client on http://127.0.0.1:7860")
    demo.launch(server_name="127.0.0.1", server_port=7860)
