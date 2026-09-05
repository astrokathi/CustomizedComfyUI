# ComfyUI Model Configuration & Parameter Reference Guide (`context.md`)

This reference manual documents optimal operational ranges, standard default values, architectural constraints, and configuration parameters across five prominent Stable Diffusion checkpoints:
1. **Stable Diffusion 1.5 Base** (`v1-5-pruned-emaonly.safetensors`)
2. **DreamShaper 8** (`Dreamshaper_8_pruned.safetensors`)
3. **DreamShaper XL** (`DreamShaperXL_Turbo_v2.safetensors` / Standard / Lightning)
4. **Juggernaut XL** (`Juggernaut-XL_v9.safetensors` / RunDiffusion Photo2)
5. **RealVisXL v5.0** (`RealVisXL_V5.0.safetensors` / Lightning)

---

## 1. Master Parameter Matrix

The table below provides an at-a-glance comparison across all five models.

| Configuration Field | SD 1.5 Base | DreamShaper 8 | DreamShaper XL (Standard) | Juggernaut XL (v9) | RealVisXL (v5.0) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Base Architecture** | SD 1.5 | SD 1.5 | SDXL 1.0 | SDXL 1.0 | SDXL 1.0 |
| **Model Size** | ~4.27 GB | ~2.13 GB | ~6.62 GB | ~6.62 GB | ~6.62 GB |
| **Text Encoder** | CLIP ViT-L/14 | CLIP ViT-L/14 | Dual CLIP (ViT-L + OpenCLIP bigG) | Dual CLIP (ViT-L + OpenCLIP bigG) | Dual CLIP (ViT-L + OpenCLIP bigG) |
| **Native Base Res** | 512 × 512 | 512 × 512 | 1024 × 1024 | 1024 × 1024 | 1024 × 1024 |
| **Steps (Default)** | 25 | 28 | 30 | 32 | 30 |
| **Steps (Optimal Range)**| 20 – 35 | 25 – 35 | 25 – 35 | 28 – 35 | 28 – 35 |
| **Steps (Lightning/Turbo)**| N/A | N/A | 6 – 8 (Turbo / Lightning) | 4 – 6 (Lightning) | 4 – 6 (Lightning) |
| **CFG Scale (Default)** | 7.5 | 6.5 | 5.5 | 4.5 | 4.5 |
| **CFG Scale (Safe Range)** | 6.5 – 8.5 | 5.5 – 7.5 | 4.5 – 6.5 | 3.5 – 5.5 | 3.5 – 5.5 |
| **Primary Sampler** | `euler_ancestral` / `dpmpp_2m` | `dpmpp_2m` | `dpmpp_2m` | `dpmpp_2m_sde` | `dpmpp_2m_sde` |
| **Secondary Sampler** | `ddim` | `euler_ancestral` | `euler_ancestral` | `dpmpp_2m` | `dpmpp_2m` |
| **Scheduler** | `karras` or `normal` | `karras` | `karras` | `karras` | `karras` |
| **CLIP Skip** | 1 (or 2 for anime) | 1 or 2 | 1 (Standard) | 1 (Standard) | 1 (Standard) |
| **Negative Dependency** | Heavy | Moderate to Heavy | Low to Moderate | Low | Very Low |
| **Ideal Orientation** | 1:1 Square, 2:3 Portrait | 2:3 Portrait, 1:1 Square | 3:4 / 2:3 Portrait, 1:1 Square | 16:9 / 21:9 Widescreen | 2:3 / 3:4 Vertical Portrait |

---

## 2. In-Depth Parameter Breakdown & Valid Ranges

Every generation parameter in ComfyUI modifies latent noise progression and manifold convergence. Understanding the bounds of each parameter avoids common failure modes.

### 2.1 Sampling Steps (`steps`)
Controls how many iterations the denoising U-Net performs on the latent space.
* **Theoretical System Range:** `1` to `10,000`
* **Practical Functional Range:**
  * **Standard SD 1.5 / SDXL:** `15` to `50`
  * **Distilled / Turbo / Lightning:** `4` to `8`
* **Under-stepping (< 15 steps standard):** Retains residual Gaussian noise, produces murky low-contrast blobs, incomplete textures, and smudged anatomy.
* **Over-stepping (> 45 steps standard):** Wastes GPU compute time with zero noticeable aesthetic gain; may cause micro-contrasting artifacts or burnt edges.

### 2.2 Classifier-Free Guidance (`cfg`)
Governs the mathematical pull of your prompt vectors relative to unconditional (negative) baseline noise.
$$\epsilon_{	ext{pred}} = \epsilon_{	ext{uncond}} + 	ext{cfg} 	imes (\epsilon_{	ext{cond}} - \epsilon_{	ext{uncond}})$$
* **Theoretical System Range:** `0.0` to `100.0`
* **Practical Functional Range:**
  * **SD 1.5 Base:** `6.0` to `9.0` (Native models need higher CFG to adhere to prompts)
  * **SD 1.5 Fine-tunes (DreamShaper 8):** `5.5` to `7.5`
  * **SDXL Fine-tunes (DSXL, Juggernaut, RealVis):** `3.5` to `6.0`
  * **Lightning / Turbo Models:** `1.5` to `2.5`
* **Under-setting (< 3.0 on standard models):** Latents drift freely, ignoring textual directives and producing washed-out, dreamlike, or irrelevant imagery.
* **Over-setting (> 8.0 on SDXL / > 10.0 on SD 1.5):** Results in "CFG burn" (oversaturated colors, high contrast, pitch-black shadows, rainbow edge halos, and unnatural plastic skin).

### 2.3 Samplers (`sampler_name`)
Determines the numerical ODE/SDE solver used to step through latent diffusion.
* `euler`: Simple, fast, deterministic. Standard baseline for rapid prototyping.
* `euler_ancestral` (`euler_a`): Adds stochastic noise at each step. Excellent for artistic drift, hair details, and fantasy illustrations. Never fully converges (will change output if step count changes).
* `dpmpp_2m`: Second-order multi-step deterministic solver. Highly stable, razor-sharp details, converges reliably around 25–30 steps. Best all-rounder.
* `dpmpp_2m_sde`: Stochastic differential equation variant. Slower per step, but excels at rendering realistic skin pores, eye reflections, and natural atmospheric depth in photorealistic models.
* `dpmpp_sde`: High quality, but requires more compute time per step.
* `ddim`: Classic deterministic sampler; useful for latent interpolation and consistent img2img.

### 2.4 Schedulers (`scheduler`)
Controls the noise variance reduction schedule across steps.
* `karras`: Dynamically groups noise levels toward lower sigma values where visual features form. Delivers superior sharpness and contrast compared to linear schedules. **Standard recommendation across all models.**
* `normal`: Linear beta schedule. Standard for base SD 1.5, but often softer than Karras.
* `exponential`: Rapidly decays noise. Good for specialized high-step counts.
* `sgm_uniform`: Standard schedule matching the original Stability AI SDXL training config.
* `simple`: Linear step progression; standard for FLUX and distilled models.

### 2.5 Latent Dimensions & Resolution
Latent dimensions define the shape of the initial empty tensor:
$$	ext{Latent Shape} = \left(	ext{Batch Size}, 4, rac{	ext{Height}}{8}, rac{	ext{Width}}{8}ight)$$
* **Dimension Rule:** Width and Height **must be divisible by 64** (due to the 8× downsampling factor of the Autoencoder and internal U-Net block pooling).
* **SD 1.5 Native Training Res:** `512 × 512` (Total pixels: ~262,144). Going above 768px in a single pass causes duplicated bodies, two-headed figures, and distorted anatomy.
* **SDXL Native Training Res:** `1024 × 1024` (Total pixels: ~1,048,576). SDXL models use multiple resolution buckets during training.

---

## 3. Detailed Model Specifications

### 3.1 Stable Diffusion 1.5 Base
* **File Identifier:** `v1-5-pruned-emaonly.safetensors`
* **Architecture:** SD 1.5 (Latent Diffusion Model)
* **VRAM Footprint:** ~4–6 GB
* **Target Aesthetic:** Unbiased baseline. Requires strong stylization tokens to produce polished results.

#### Operational Parameter Matrix
| Parameter | Default Value | Valid Safe Range | Extreme / Experimental |
| :--- | :--- | :--- | :--- |
| **Steps** | `25` | `20 – 35` | `15 – 50` |
| **CFG Scale** | `7.5` | `6.5 – 8.5` | `5.0 – 12.0` |
| **Sampler** | `euler_ancestral` | `dpmpp_2m`, `euler_a`, `ddim` | `dpmpp_sde` |
| **Scheduler** | `normal` | `karras`, `normal` | `exponential` |
| **Width × Height** | `512 × 512` | `512×512`, `512×768`, `768×512` | Max single-pass: `768 × 768` |
| **CLIP Skip** | `1` | `1` | `2` |

#### Prompting Behavior & Syntax
* **Required Prompt Density:** High. Needs explicit guidance for camera, lighting, and medium.
* **Effective Keywords:** `masterpiece`, `highly detailed`, `studio photography`, `dramatic lighting`, `8k resolution`.
* **Negative Prompting:** **Mandatory**. Without negative prompts, SD 1.5 defaults to LAION-5B average aesthetics (blurry, watermarked, distorted hands).

---

### 3.2 DreamShaper 8
* **File Identifier:** `Dreamshaper_8_pruned.safetensors`
* **Architecture:** SD 1.5 Fine-tune (Lykon)
* **VRAM Footprint:** ~4–6 GB
* **Target Aesthetic:** 2.5D illustration, fantasy portraits, digital concept art, vibrant stylized photography.

#### Operational Parameter Matrix
| Parameter | Default Value | Valid Safe Range | Extreme / Experimental |
| :--- | :--- | :--- | :--- |
| **Steps** | `28` | `25 – 35` | `20 – 45` |
| **CFG Scale** | `6.5` | `5.5 – 7.5` | `4.5 – 8.5` *(burns > 8.0)* |
| **Sampler** | `dpmpp_2m` | `dpmpp_2m`, `euler_ancestral` | `dpmpp_sde_gpu` |
| **Scheduler** | `karras` | `karras` | `normal` |
| **Width × Height** | `512 × 768` | `512×512`, `512×768`, `768×512` | Max single-pass: `640 × 896` |
| **CLIP Skip** | `1` | `1` or `2` | `2` |

#### Composition & Aspect Ratios
* **Portrait (3:2 / 2:3):** `512 × 768` — Optimal for character concepts, cosplay, fantasy avatars.
* **Square (1:1):** `512 × 512` — Best for icons, close-up portraits, centered monsters.
* **Landscape (3:2):** `768 × 512` — Best for magical vistas, environments, sci-fi vehicles.

---

### 3.3 DreamShaper XL (DSXL)
* **File Identifier:** `DreamShaperXL_Turbo_v2.safetensors` / `DreamShaperXL_1-0.safetensors`
* **Architecture:** SDXL 1.0 (Dual CLIP: ViT-L + OpenCLIP bigG)
* **VRAM Footprint:** ~8–12 GB (Run in `--lowvram` or `--medvram` if < 8 GB)
* **Target Aesthetic:** High-resolution digital painting, semi-realistic character art, video game assets.

#### Operational Parameter Matrix
| Parameter | Standard SDXL Profile | Turbo / Lightning Profile |
| :--- | :--- | :--- |
| **Steps** | `30` (Range: `25 – 35`) | `6` (Range: `4 – 8`) |
| **CFG Scale** | `5.5` (Range: `4.5 – 6.5`) | `2.0` (Range: `1.5 – 2.5`) |
| **Sampler** | `dpmpp_2m` or `euler_ancestral` | `euler` or `dpmpp_2m` |
| **Scheduler** | `karras` | `karras` or `simple` |
| **Native Base Res** | `1024 × 1024` | `1024 × 1024` |
| **CLIP Skip** | `1` | `1` |

#### Native SDXL Latent Buckets
* **Square (1:1):** `1024 × 1024`
* **Portrait (3:4):** `896 × 1152`
* **Tall Portrait (2:3):** `832 × 1216`
* **Landscape (4:3):** `1152 × 896`
* **Wide Landscape (16:9):** `1344 × 768`

---

### 3.4 Juggernaut XL (v9 / RunDiffusion)
* **File Identifier:** `Juggernaut-XL_v9.safetensors`
* **Architecture:** SDXL 1.0 Fine-tune
* **VRAM Footprint:** ~8–12 GB
* **Target Aesthetic:** Cinematic realism, movie frames, gritty lighting, architectural depth, hard-surface mechanical props.

#### Operational Parameter Matrix
| Parameter | Standard Profile | Lightning 4-Step Profile |
| :--- | :--- | :--- |
| **Steps** | `32` (Range: `28 – 38`) | `5` (Range: `4 – 6`) |
| **CFG Scale** | `4.5` (Range: `3.5 – 5.5`) | `1.5 – 2.0` |
| **Sampler** | `dpmpp_2m_sde` or `dpmpp_2m` | `dpmpp_2m_sde` or `euler` |
| **Scheduler** | `karras` | `karras` or `sgm_uniform` |
| **Optimal Orientation** | Widescreen landscape / Anamorphic | Widescreen landscape |
| **CLIP Skip** | `1` | `1` |

#### Aspect Ratio & Composition Strengths
* **Cinematic Movie Still (16:9):** `1344 × 768` — Incredible environmental depth and lighting contrast.
* **Cinemascope / Anamorphic (21:9):** `1536 × 640` — Expansive horizon lines, sprawling cyberpunk streets.
* **Photography Standard (3:2):** `1216 × 832` — Exterior architectural shots, vehicle modeling.
* **Dramatic Portrait (3:4):** `896 × 1152` — Chiaroscuro headshots, military gear, weathered characters.

---

### 3.5 RealVisXL (v5.0)
* **File Identifier:** `RealVisXL_V5.0.safetensors`
* **Architecture:** SDXL 1.0 Photorealism Fine-tune
* **VRAM Footprint:** ~8–12 GB
* **Target Aesthetic:** DSLR camera fidelity, unedited candid photography, realistic human skin textures, zero AI plastic sheen.

#### Operational Parameter Matrix
| Parameter | Standard Profile | Lightning Profile |
| :--- | :--- | :--- |
| **Steps** | `30` (Range: `28 – 35`) | `6` (Range: `4 – 8`) |
| **CFG Scale** | `4.5` (Range: `3.5 – 5.5`) | `1.5 – 2.0` |
| **Sampler** | `dpmpp_2m_sde` | `dpmpp_2m_sde` |
| **Scheduler** | `karras` | `karras` |
| **Optimal Orientation** | Vertical Portrait (2:3 and 3:4) | Vertical Portrait |
| **CLIP Skip** | `1` | `1` |

#### Composition & Best Framing
* **Fashion & Headshot (3:4):** `896 × 1152` — Natural facial symmetry, iris depth, skin pores.
* **Full-Body Portrait (2:3):** `832 × 1216` — Natural clothing drape, balanced feet/hand rendering.
* **Documentary Landscape (4:3):** `1152 × 896` — Street photography, environmental documentary shots.

---

## 4. Universal Prompting Reference

### 4.1 Master "Set-and-Forget" Negative Prompts

#### Universal SD 1.5 Negative Prompt (for Base 1.5 & DreamShaper 8)
```text
(worst quality, low quality:1.3), lowres, blurry, bad anatomy, bad hands, missing fingers, extra fingers, mutated hands, poorly drawn face, mutation, deformed, disfigured, extra limbs, cloned face, gross proportions, watermark, text, signature, jpeg artifacts
```

#### Universal SDXL Negative Prompt (for DSXL, Juggernaut XL, RealVisXL)
```text
(worst quality, low quality:1.3), blurry, bad anatomy, bad hands, missing fingers, mutated hands, deformed, disfigured, watermark, text
```
*(Note: SDXL requires far fewer negative tokens. Bloating the negative prompt degrades composition and burns dynamic range.)*

---

### 4.2 Positive Prompt Architecture Blueprint

To achieve consistent results across checkpoints, order your prompt tokens hierarchically:

```text
[Subject & Core Action] + [Clothing & Physical Detail] + [Environment & Setting] + [Lighting & Atmosphere] + [Camera Gear & Film Stock / Medium]
```

#### Cross-Model Prompt Translation Example

* **For DreamShaper 8 / DreamShaper XL:**
  ```text
  portrait of an arcane battlemage casting a frost spell, glowing icy runes orbiting hands, intricate leather and silver armor, swirling blizzard in background, dramatic blue rim light, digital concept art, trending on ArtStation, sharp focus
  ```

* **For Juggernaut XL:**
  ```text
  cinematic film still, a solitary bounty hunter walking through a dystopian rain-soaked alley, dirty neon reflections on wet asphalt, volumetric steam from storm grates, 35mm film, anamorphic lens, shallow depth of field, dramatic shadows, Arri Alexa cinematography
  ```

* **For RealVisXL v5.0:**
  ```text
  candid 35mm street portrait of an elderly carpenter smiling warmly in his sunlit workshop, sawdust in air, worn denim apron, natural skin wrinkles, fine grey hair, captured on Sony A7IV, 85mm f/1.4 lens, natural window light, authentic color grading
  ```

---

## 5. Troubleshooting & Configuration Error Matrix

| Symptom | Root Cause | Exact Solution |
| :--- | :--- | :--- |
| **Two heads, stacked bodies, or duplicate limbs** | Latent dimension exceeds native training resolution. | For SD 1.5: Keep initial pass to `512×512` or `512×768`. Use Latent Hires Fix to upscale. For SDXL: Use standard buckets (e.g. `1024×1024`, `896×1152`). |
| **Burned colors, excessive contrast, green/magenta fringe** | CFG Scale is configured too high. | Lower CFG. On SDXL, drop CFG to `4.0 – 5.5`. On Lightning/Turbo models, drop CFG to `1.5 – 2.0`. |
| **Plastic, smooth, doll-like skin** | Over-prompting "photorealistic" tokens or running high CFG on RealVisXL. | Strip buzzwords like `photorealistic, hyperdetailed, 8k`. Switch sampler to `dpmpp_2m_sde`, scheduler to `karras`, and CFG to `4.5`. |
| **Pure static / noise output** | Running Turbo/Lightning model with standard step count/CFG, or incompatible scheduler. | Check model type. If using Lightning checkpoint, set steps to `4–6` and CFG to `1.5–2.0`. |
| **Black screen or `NaN` error during generation** | VAE fp16 overflow or VRAM exhaustion. | Run ComfyUI with `--fp16-vae` or add a dedicated `Load VAE` node using `sdxl_vae.safetensors` / `vae-ft-mse-840000-ema-pruned.safetensors`. |
| **Muddy textures and lack of fine details** | Sampler under-stepping or using linear `normal` scheduler on low steps. | Set scheduler to `karras` and ensure steps are at least `28` for standard models. |

---

*Generated for ComfyUI local workflow deployment.*
