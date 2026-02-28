# WAN 2.2 Setup for 16GB VRAM

## Goal
Replace SDXL-Turbo + SVD pipeline with WAN 2.2 for better video generation quality.

## Model Selection: 5B (16GB VRAM Optimized)

### Required Files

**1. Text Encoder (1.4GB)**
- File: `umt5_xxl_fp8_e4m3fn_scaled.safetensors`
- Location: `ComfyUI/models/text_encoders/`
- Download: https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/tree/main/split_files/text_encoders

**2. VAE (116MB)**
- File: `wan2.2_vae.safetensors`
- Location: `ComfyUI/models/vae/`
- Download: https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/blob/main/split_files/vae/wan2.2_vae.safetensors

**3. Diffusion Model (9.8GB)**
- File: `wan2.2_ti2v_5B_fp16.safetensors`
- Location: `ComfyUI/models/diffusion_models/`
- Download: https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/blob/main/split_files/diffusion_models/wan2.2_ti2v_5B_fp16.safetensors

**Total Download: ~11.3GB**

## Setup Steps

1. ✅ Clone ComfyUI
2. ✅ Install dependencies (requirements.txt)
3. ✅ Create model directories
4. ✅ Download models (HuggingFace CLI - 11.3GB total)
5. ✅ Download workflow JSON
6. ⏳ Start ComfyUI server and test generation
7. ⏳ Integrate into batch_generate_upload_series.py as **--pipeline=wan22** option

## Workflow Files

- Text-to-video: https://comfyanonymous.github.io/ComfyUI_examples/wan22/text_to_video_wan22_5B.json
- Image-to-video: https://comfyanonymous.github.io/ComfyUI_examples/wan22/image_to_video_wan22_5B.json

## Integration Strategy

**IMPORTANT: Current SDXL-Turbo + SVD pipeline stays as FALLBACK!**

**Dual-Pipeline Architecture:**
```bash
# Current pipeline (default, proven to work)
python batch_generate_upload_series.py --storyboard ... 

# WAN 2.2 pipeline (new, experimental)
python batch_generate_upload_series.py --storyboard ... --pipeline=wan22
```

**Option 1: ComfyUI API Mode** ⭐ RECOMMENDED
- Run ComfyUI server in background (once, persistent)
- Send API requests from Python script
- More stable, easier debugging
- Clean separation between pipelines

**Option 2: Direct Python Integration**
- Import ComfyUI nodes directly
- Faster, no server overhead
- Requires careful dependency management
- Risk of conflicts with existing pipeline

**Selected: Option 1** (ComfyUI API mode for safety)

## VRAM Considerations (16GB)

- 5B model: ~10GB VRAM during inference
- Leaves ~6GB for other processes
- Should handle 512x512 -> video smoothly
- May struggle with 768x768 (test required)

## Current Status (2026-02-14 21:30)

✅ **Completed:**
- ComfyUI installed at `C:\Users\lijin\Projects\ComfyUI`
- All dependencies installed (torch, comfyui packages, etc.)
- WAN 2.2 5B models downloaded and placed correctly:
  - Diffusion: `wan2.2_ti2v_5B_fp16.safetensors` (9.31GB)
  - Text Encoder: `umt5_xxl_fp8_e4m3fn_scaled.safetensors` (6.27GB)
  - VAE: `wan2.2_vae.safetensors` (1.31GB)
- Workflow JSON downloaded
- Test script created (`scripts/test_wan22.py`) - all models verified

⏳ **Next Steps:**
1. Start ComfyUI server: `cd C:\Users\lijin\Projects\ComfyUI && python main.py --listen 127.0.0.1 --port 8188`
2. Test basic text-to-video generation via API
3. Benchmark VRAM usage with 512x512 generation
4. Create WAN 2.2 integration in `batch_generate_upload_series.py` with `--pipeline=wan22` flag
5. Run side-by-side comparison (SDXL+SVD vs WAN 2.2)
6. If WAN 2.2 performs better → make it default, keep SDXL+SVD as fallback
