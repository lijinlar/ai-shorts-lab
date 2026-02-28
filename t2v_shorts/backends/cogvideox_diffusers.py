from __future__ import annotations

from pathlib import Path

import torch


class CogVideoXDiffusersBackend:
    """CogVideoX via HuggingFace diffusers.

    Notes:
    - Requires CUDA-enabled torch.
    - 5B model can OOM on consumer GPUs; we auto-fallback to 2B + smaller res.
    """

    name = "cogvideox"

    def __init__(self, model_id: str = "THUDM/CogVideoX-2b", fallback_model_id: str = "THUDM/CogVideoX-2b"):
        # Default to 2B for RTX 5070 Ti-class VRAM. You can override to 5B later.
        self.model_id = model_id
        self.fallback_model_id = fallback_model_id

    def generate(
        self,
        *,
        prompt: str,
        seconds: int,
        fps: int,
        width: int,
        height: int,
        seed: int | None,
        out_path: Path,
    ) -> None:
        if not torch.cuda.is_available():
            raise RuntimeError(
                "CUDA torch not available. Install a CUDA-enabled torch build, then retry."
            )

        # Lazy import to keep base installs light
        from diffusers import CogVideoXPipeline
        import imageio.v3 as iio

        device = torch.device("cuda")

        def _load(model_id: str) -> CogVideoXPipeline:
            pipe = CogVideoXPipeline.from_pretrained(
                model_id,
                torch_dtype=torch.float16,
            )
            # memory savers
            for fn in ("enable_attention_slicing", "enable_vae_tiling"):
                try:
                    getattr(pipe, fn)()
                except Exception:
                    pass
            # Best-effort VRAM reduction (may slow down). Prefer sequential offload.
            for fn in ("enable_sequential_cpu_offload", "enable_model_cpu_offload"):
                try:
                    getattr(pipe, fn)()
                    return pipe
                except Exception:
                    pass
            return pipe.to(device)

        def _run(pipe: CogVideoXPipeline, w: int, h: int, steps: int, run_fps: int, run_seconds: float):
            # Hard caps to protect VRAM
            run_fps = max(4, min(int(run_fps), 12))
            run_seconds = float(max(1.0, min(float(run_seconds), 3.0)))
            steps = max(10, min(int(steps), 25))

            num_frames = int(run_seconds * run_fps)
            generator = None
            if seed is not None:
                generator = torch.Generator(device=device).manual_seed(int(seed))
            return pipe(
                prompt=prompt,
                num_frames=num_frames,
                height=h,
                width=w,
                generator=generator,
                num_inference_steps=steps,
            )

        # First attempt: primary model
        pipe = _load(self.model_id)

        try:
            result = _run(pipe, width, height, steps=25, run_fps=fps, run_seconds=seconds)
        except RuntimeError as e:
            msg = str(e).lower()
            oom = ("out of memory" in msg) or ("cuda" in msg and "memory" in msg)
            if not oom:
                raise

            # Cleanup and fallback
            try:
                del pipe
            except Exception:
                pass
            try:
                torch.cuda.empty_cache()
            except Exception:
                pass

            # Aggressive fallback: smaller model + smaller res + fewer frames/steps
            w2 = min(width, 448)
            h2 = min(height, 800)

            pipe = _load(self.fallback_model_id)
            result = _run(pipe, w2, h2, steps=12, run_fps=min(fps, 6), run_seconds=min(seconds, 1.5))

        frames = result.frames
        out_path.parent.mkdir(parents=True, exist_ok=True)

        iio.imwrite(
            out_path,
            frames,
            fps=fps,
            codec="libx264",
            pixelformat="yuv420p",
        )
