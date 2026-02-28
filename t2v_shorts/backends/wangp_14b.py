"""
WanGP 14B Backend — Wan2.1 Text-to-Video 14B (int8 quantized)
Drops into the t2v_shorts pipeline as a proper VideoBackend.
"""
from __future__ import annotations

import json
import shutil
import time
import zipfile
import subprocess
from pathlib import Path

WANGP_DIR = Path(r"C:\Users\lijin\.openclaw\workspace\Wan2GP")
WANGP_PYTHON = WANGP_DIR / "venv" / "Scripts" / "python.exe"
OUTPUTS_DIR = WANGP_DIR / "outputs"


class WanGP14BBackend:
    name = "wangp"

    def generate(
        self,
        *,
        prompt: str,
        seconds: int,
        fps: int,
        width: int,
        height: int,
        seed: int | None = None,
        out_path: Path,
        negative_prompt: str = "",
        steps: int = 50,
        cfg: float = 7.5,
    ) -> None:
        num_frames = min(seconds * fps, 121)  # WanGP cap

        task = {
            "id": 1,
            "params": {
                "prompt": prompt,
                "negative_prompt": negative_prompt,
                "mode": "text2video",
                "model_type": "t2v_1.3B",
                "model_filename": "t2v_1.3B",
                "profile": -1,
                "width": width,
                "height": height,
                "num_frames": num_frames,
                "fps": fps,
                "steps": steps,
                "cfg": cfg,
                "seed": seed if seed is not None else -1,
                "transformer_quantization": "int8",
                "transformer_dtype_policy": "auto",
                "vae_quantization": "int8",
                "loras": [],
                "loras_multipliers": [],
                "state": {},
            },
            "plugin_data": {},
            "prompt": prompt,
        }

        # Write queue zip
        queue_file = WANGP_DIR / f"queue_{int(time.time())}.zip"
        with zipfile.ZipFile(queue_file, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("queue.json", json.dumps([task], indent=2))

        # Clear previous outputs
        if OUTPUTS_DIR.exists():
            for f in OUTPUTS_DIR.glob("*.mp4"):
                try:
                    f.unlink()
                except Exception:
                    pass

        initial = set(OUTPUTS_DIR.glob("*.mp4")) if OUTPUTS_DIR.exists() else set()

        proc = subprocess.Popen(
            [str(WANGP_PYTHON), str(WANGP_DIR / "wgp.py"), "--process", str(queue_file)],
            cwd=str(WANGP_DIR),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
        )

        # Stream output + watch for result
        max_wait = 1800  # 30 min
        t0 = time.time()
        result_video = None

        while time.time() - t0 < max_wait:
            # Check for new video
            if OUTPUTS_DIR.exists():
                new = set(OUTPUTS_DIR.glob("*.mp4")) - initial
                if new:
                    result_video = sorted(new, key=lambda f: f.stat().st_mtime)[-1]
                    time.sleep(2)  # Let write finish
                    break

            # Print progress
            line = proc.stdout.readline()
            if line:
                print(f"  [wangp] {line.rstrip()}", flush=True)
            else:
                time.sleep(1)

        proc.terminate()
        try:
            queue_file.unlink()
        except Exception:
            pass

        if not result_video:
            raise RuntimeError(f"WanGP 14B generation timed out after {max_wait}s")

        out_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(result_video, out_path)
        print(f"  [wangp] Saved {out_path.name} ({out_path.stat().st_size // 1024} KB)")
