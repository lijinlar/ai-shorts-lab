from __future__ import annotations

from pathlib import Path
from typing import Optional

import torch

from .types import VideoBackend


class SvdOptimizedBackend(VideoBackend):
    """OPTIMIZED Text->(image)->video using SDXL + Stable Video Diffusion (SVD-XT).

    Key improvements over svd_txt2vid:
    - Full SDXL instead of SDXL-Turbo (30 steps vs 2 steps)
    - Guidance scale enabled (8.5 for better prompt following)
    - Higher FPS (15 instead of 6)
    - More SVD inference steps (default 25)
    - Better motion settings
    - Higher quality decode
    
    Models:
    - Text->image: stabilityai/stable-diffusion-xl-base-1.0 (not Turbo!)
    - Image->video: stabilityai/stable-video-diffusion-img2vid-xt
    """

    name = "svd_optimized"

    def __init__(
        self,
        t2i_model_id: str = "stabilityai/stable-diffusion-xl-base-1.0",
        i2v_model_id: str = "stabilityai/stable-video-diffusion-img2vid-xt",
    ):
        self.t2i_model_id = t2i_model_id
        self.i2v_model_id = i2v_model_id

    def generate(
        self,
        prompt: str,
        seconds: int,
        fps: int,
        width: int,
        height: int,
        seed: Optional[int],
        out_path: Path,
        **kwargs,
    ) -> None:
        from diffusers import StableDiffusionXLPipeline, StableVideoDiffusionPipeline
        from diffusers.utils import export_to_video

        # SVD works best at 1024x576 (landscape)
        # We'll generate there then post-process to vertical if needed
        cond_w, cond_h = 1024, 576

        # Better defaults for quality
        fps_run = 15  # Increased from 6
        num_inference_steps_t2i = 30  # Increased from 2
        guidance_scale = 8.5  # Enabled (was 0.0)
        num_inference_steps_i2v = 25  # SVD steps for smoother motion

        generator = None
        if seed is not None:
            generator = torch.Generator(device="cuda").manual_seed(int(seed))

        print(f"  [OPTIMIZED] Generating keyframe with SDXL (30 steps, guidance=8.5)...")
        
        # 1) Text -> image (Full SDXL, not Turbo!)
        t2i = StableDiffusionXLPipeline.from_pretrained(
            self.t2i_model_id,
            torch_dtype=torch.float16,
            variant="fp16",
            use_safetensors=True,
        )
        
        try:
            t2i.enable_model_cpu_offload()
        except Exception:
            t2i = t2i.to("cuda")

        # Enhanced negative prompt for better quality
        negative_prompt = (
            "blurry, low quality, distorted, ugly, deformed, watermark, "
            "text, logo, signature, out of focus, bad anatomy, worst quality"
        )

        # High-quality image generation
        image = t2i(
            prompt=prompt,
            negative_prompt=negative_prompt,
            num_inference_steps=num_inference_steps_t2i,
            guidance_scale=guidance_scale,
            width=cond_w,
            height=cond_h,
            generator=generator,
        ).images[0]

        # Save intermediate image for inspection
        keyframe_path = out_path.parent / (out_path.stem + "_keyframe.jpg")
        image.save(keyframe_path, quality=95)
        print(f"  [OPTIMIZED] Keyframe saved: {keyframe_path}")

        # Free up VRAM before SVD
        del t2i
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

        print(f"  [OPTIMIZED] Animating with SVD-XT (25 steps, motion=150, fps=15)...")
        
        # 2) Image -> video (SVD-XT with better settings)
        pipe = StableVideoDiffusionPipeline.from_pretrained(
            self.i2v_model_id,
            torch_dtype=torch.float16,
            variant="fp16",
        )
        
        try:
            pipe.enable_model_cpu_offload()
        except Exception:
            pipe = pipe.to("cuda")

        # Calculate frames based on request (cap at 5 seconds for VRAM)
        req_seconds = min(float(seconds), 5.0)
        num_frames = max(14, min(int(req_seconds * fps_run), 75))  # 14-75 frames

        # Higher motion_bucket_id = more motion (default is 127, we'll use 140 - safer)
        # Lower noise_aug_strength = sharper (default 0.02)
        # REDUCED STEPS from 25 to 15 to avoid crash at step 4-5
        frames = pipe(
            image,
            num_frames=num_frames + 3,  # Generate extra frames to trim glitchy end
            num_inference_steps=15,  # REDUCED from 25 - was crashing at step 4-5
            fps=fps_run,
            motion_bucket_id=127,  # Default (was 140)
            noise_aug_strength=0.02,  # Default (was 0.015)
            decode_chunk_size=4,  # REDUCED from 8 - less VRAM pressure
            generator=generator,
        ).frames[0]

        # Trim last 3 frames to remove end glitches (common SVD issue)
        frames = frames[:-3]

        print(f"  [OPTIMIZED] Generated {len(frames)} frames @ {fps_run}fps = {len(frames)/fps_run:.2f}s (trimmed end glitch)")

        # Export video
        out_path.parent.mkdir(parents=True, exist_ok=True)
        export_to_video(frames, str(out_path), fps=fps_run)
        
        print(f"  [OPTIMIZED] Video saved: {out_path}")
