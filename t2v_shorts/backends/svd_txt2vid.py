from __future__ import annotations

from pathlib import Path
from typing import Optional

import torch

from .types import VideoBackend


class SvdTxt2VidBackend(VideoBackend):
    """Text->(image)->video using SDXL-Turbo + Stable Video Diffusion (SVD-XT).

    Why:
    - CogVideoX is too VRAM-hungry on ~16GB GPUs.
    - This path is much more likely to run locally, while still producing realistic-ish motion.

    Models:
    - Text->image: stabilityai/sdxl-turbo
    - Image->video: stabilityai/stable-video-diffusion-img2vid-xt

    Notes:
    - We generate a single keyframe at 1024x576 (SVD expects 1024x576).
    - Output is short (usually 25 frames @ 7 fps ~ 3.5s). Longer = more VRAM.
    """

    name = "svd"

    def __init__(
        self,
        t2i_model_id: str = "stabilityai/sdxl-turbo",
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

        # SVD uses 1024x576 conditioning (landscape). We'll generate in that and later scale/crop.
        cond_w, cond_h = 1024, 576

        # keep compute bounded
        fps_run = 6
        num_frames = max(6, int(3 * fps_run))  # default ~3s; caller can request longer but we cap below

        generator = None
        if seed is not None:
            generator = torch.Generator(device="cuda").manual_seed(int(seed))

        # 1) Text -> image (SDXL-Turbo)
        t2i = StableDiffusionXLPipeline.from_pretrained(
            self.t2i_model_id,
            torch_dtype=torch.float16,
            variant="fp16",
        )
        try:
            t2i.enable_model_cpu_offload()
        except Exception:
            t2i = t2i.to("cuda")

        # NOTE: SDXL CLIP text encoder effectively caps at 77 tokens; keep prompts concise.
        image = t2i(
            prompt=prompt,
            num_inference_steps=2,
            guidance_scale=0.0,
            width=cond_w,
            height=cond_h,
            generator=generator,
        ).images[0]

        # 2) Image -> video (SVD-XT)
        pipe = StableVideoDiffusionPipeline.from_pretrained(
            self.i2v_model_id,
            torch_dtype=torch.float16,
            variant="fp16",
        )
        try:
            pipe.enable_model_cpu_offload()
        except Exception:
            pipe = pipe.to("cuda")

        # motion_bucket_id controls motion magnitude (higher -> more motion)
        # seconds/fps from request, but cap to keep VRAM predictable
        req_seconds = float(seconds)
        if req_seconds > 3:
            req_seconds = 3.0
        req_fps = int(fps)
        if req_fps > fps_run:
            req_fps = fps_run

        num_frames = max(6, int(req_seconds * req_fps))

        frames = pipe(
            image,
            num_frames=num_frames,
            fps=req_fps,
            motion_bucket_id=120,
            noise_aug_strength=0.02,
            decode_chunk_size=4,
            generator=generator,
        ).frames[0]

        fps_run = req_fps

        out_path.parent.mkdir(parents=True, exist_ok=True)
        export_to_video(frames, str(out_path), fps=fps_run)
