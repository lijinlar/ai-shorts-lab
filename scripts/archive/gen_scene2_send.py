#!/usr/bin/env python3
"""Generate scene 2 only (scene 1 exists), combine, send to Telegram."""
import sys, json, shutil, zipfile, subprocess, time
from pathlib import Path

# Force UTF-8
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from t2v_shorts.prompt_expander import expand_prompt, get_negative_prompt

RAW_SCENE_2 = (
    "A soldier in military uniform walks slowly up the driveway at golden hour dusk. "
    "His loyal golden retriever explodes through the front door, sprinting across the lawn "
    "in pure unbridled joy, ears flying, toward the soldier."
)

WANGP_DIR    = Path(r"C:\Users\lijin\.openclaw\workspace\Wan2GP")
WANGP_PYTHON = WANGP_DIR / "venv" / "Scripts" / "python.exe"
OUTPUTS_DIR  = WANGP_DIR / "outputs"
OUT_DIR      = Path(r"C:\Users\lijin\Projects\t2v-shorts-lab\out\test_expanded")
SCENE1       = OUT_DIR / "scene_01.mp4"

def clear_outputs():
    if OUTPUTS_DIR.exists():
        for f in OUTPUTS_DIR.glob("*.mp4"):
            try: f.unlink()
            except: pass

def run_wangp(prompt, neg, max_wait=900):
    task = {"id": 1, "params": {
        "prompt": prompt, "negative_prompt": neg,
        "mode": "text2video", "model_type": "t2v_1.3B", "model_filename": "t2v_1.3B",
        "profile": -1, "width": 832, "height": 480, "num_frames": 81,
        "fps": 24, "steps": 50, "cfg": 7.5, "seed": -1,
        "transformer_quantization": "int8", "transformer_dtype_policy": "auto",
        "vae_quantization": "int8", "loras": [], "loras_multipliers": [], "state": {},
    }, "plugin_data": {}, "prompt": prompt}

    qf = WANGP_DIR / "gen_queue.zip"
    with zipfile.ZipFile(qf, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr("queue.json", json.dumps([task], indent=2))

    initial = set(OUTPUTS_DIR.glob("*.mp4")) if OUTPUTS_DIR.exists() else set()
    proc = subprocess.Popen(
        [str(WANGP_PYTHON), str(WANGP_DIR / "wgp.py"), "--process", str(qf)],
        cwd=str(WANGP_DIR), stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, encoding="utf-8", errors="replace",
    )

    t0 = time.time()
    while time.time() - t0 < max_wait:
        if OUTPUTS_DIR.exists():
            new = set(OUTPUTS_DIR.glob("*.mp4")) - initial
            if new:
                v = sorted(new, key=lambda f: f.stat().st_mtime)[-1]
                time.sleep(2)
                proc.terminate()
                return v, time.time() - t0
        time.sleep(3)

    proc.terminate()
    return None, time.time() - t0


def main():
    neg = get_negative_prompt()

    # Expand scene 2
    print(f"Expanding scene 2 prompt...")
    expanded = expand_prompt(RAW_SCENE_2, verbose=True)
    print(f"\nExpanded ({len(expanded)} chars):\n{expanded}\n")

    # Generate scene 2
    clear_outputs()
    print("Running WanGP for scene 2 (steps=50)...")
    result, elapsed = run_wangp(expanded, neg)

    if not result:
        print("Generation failed!")
        sys.exit(1)

    scene2 = OUT_DIR / "scene_02.mp4"
    shutil.copy(result, scene2)
    print(f"Scene 2 done in {elapsed:.0f}s ({scene2.stat().st_size // 1024} KB)")

    # Combine scene 1 + scene 2
    final = OUT_DIR / "test_final.mp4"
    lst = OUT_DIR / "concat.txt"
    lst.write_text(f"file '{SCENE1.resolve().as_posix()}'\nfile '{scene2.resolve().as_posix()}'", encoding="utf-8")
    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(lst),
        "-c:v", "libx264", "-crf", "18", "-preset", "fast", str(final)
    ], capture_output=True)

    if final.exists():
        print(f"\nFinal: {final} ({final.stat().st_size // 1024} KB)")
        print(f"FINAL_PATH={final}")
    else:
        # Just send scene 2 alone
        shutil.copy(scene2, final)
        print(f"FINAL_PATH={final}")


if __name__ == "__main__":
    main()
