#!/usr/bin/env python3
"""
Quick test: generate 2 scenes with deepseek-r1 expanded prompts.
Sends the result video to Telegram.
"""
import sys
import json
import shutil
import zipfile
import subprocess
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from t2v_shorts.prompt_expander import expand_prompt, get_negative_prompt

# Raw short prompts (like storyboard would produce)
RAW_SCENES = [
    "Extreme close-up of a golden retriever's face pressed against a frosted glass door, breath fogging the glass, tail wagging frantically, waiting for owner.",
    "A soldier in uniform walks up the driveway at dusk. The dog explodes through the door, sprinting across the lawn toward him in pure joy.",
]

WANGP_DIR    = Path(r"C:\Users\lijin\.openclaw\workspace\Wan2GP")
WANGP_PYTHON = WANGP_DIR / "venv" / "Scripts" / "python.exe"
OUTPUTS_DIR  = WANGP_DIR / "outputs"
OUT_DIR      = Path(r"C:\Users\lijin\Projects\t2v-shorts-lab\out\test_expanded")
OUT_DIR.mkdir(parents=True, exist_ok=True)


def clear_outputs():
    if OUTPUTS_DIR.exists():
        for f in OUTPUTS_DIR.glob("*.mp4"):
            try: f.unlink()
            except: pass


def create_queue(prompt: str, negative_prompt: str = "") -> Path:
    task = {
        "id": 1,
        "params": {
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "mode": "text2video",
            "model_type": "t2v_1.3B",
            "model_filename": "t2v_1.3B",
            "profile": -1,
            "width": 832,
            "height": 480,
            "num_frames": 81,
            "fps": 24,
            "steps": 50,
            "cfg": 7.5,
            "seed": -1,
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
    queue_file = WANGP_DIR / "test_queue.zip"
    with zipfile.ZipFile(queue_file, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("queue.json", json.dumps([task], indent=2))
    return queue_file


def run_wangp(queue_file: Path, max_wait: int = 900) -> Path | None:
    initial = set(OUTPUTS_DIR.glob("*.mp4")) if OUTPUTS_DIR.exists() else set()

    proc = subprocess.Popen(
        [str(WANGP_PYTHON), str(WANGP_DIR / "wgp.py"), "--process", str(queue_file)],
        cwd=str(WANGP_DIR),
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, encoding="utf-8", errors="replace",
    )

    start = time.time()
    while time.time() - start < max_wait:
        if OUTPUTS_DIR.exists():
            new = set(OUTPUTS_DIR.glob("*.mp4")) - initial
            if new:
                video = sorted(new, key=lambda f: f.stat().st_mtime)[-1]
                time.sleep(2)
                proc.terminate()
                return video
        time.sleep(3)

    proc.terminate()
    return None


def ffmpeg_combine(clips: list, out: Path) -> bool:
    lst = out.parent / "concat.txt"
    lst.write_text("\n".join(f"file '{p.resolve().as_posix()}'" for p in clips), encoding="utf-8")
    r = subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(lst),
        "-c:v", "libx264", "-crf", "18", "-preset", "fast", str(out)
    ], capture_output=True, text=True)
    return out.exists() and out.stat().st_size > 10000


def main():
    neg = get_negative_prompt()
    scene_paths = []

    for i, raw in enumerate(RAW_SCENES, 1):
        print(f"\n{'='*60}")
        print(f"SCENE {i} - RAW ({len(raw)} chars):\n  {raw}")

        # Expand
        expanded = expand_prompt(raw, verbose=True)
        print(f"\nEXPANDED:\n  {expanded[:200]}...\n")

        # Generate
        clear_outputs()
        qf = create_queue(expanded, neg)
        print(f"Running WanGP (steps=50, this takes ~5-10 min)...")
        t0 = time.time()
        result = run_wangp(qf)
        elapsed = time.time() - t0

        if result:
            out = OUT_DIR / f"scene_{i:02d}.mp4"
            shutil.copy(result, out)
            print(f"[OK] Scene {i} done in {elapsed:.0f}s -> {out.name} ({out.stat().st_size//1024} KB)")
            scene_paths.append(out)
        else:
            print(f"[FAIL] Scene {i} failed after {elapsed:.0f}s")

    if not scene_paths:
        print("No scenes generated.")
        sys.exit(1)

    # Combine
    final = OUT_DIR / "test_expanded_output.mp4"
    if len(scene_paths) > 1:
        print("\nCombining scenes...")
        ffmpeg_combine(scene_paths, final)
    else:
        shutil.copy(scene_paths[0], final)

    if final.exists():
        sz = final.stat().st_size
        print(f"\n[DONE] Final output: {final}")
        print(f"   Size: {sz // 1024} KB")
    else:
        print("Combine failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
