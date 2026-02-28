from __future__ import annotations

import gc
import json
import random
import subprocess
from pathlib import Path

import sys

# Force UTF-8 output on Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from t2v_shorts.config import GenerateRequest
from t2v_shorts.pipeline import run
try:
    from t2v_shorts.prompt_expander import expand_prompt
    EXPAND_PROMPTS = True
    print("[pipeline] Prompt expander loaded ✓")
except ImportError:
    EXPAND_PROMPTS = False
    print("[pipeline] Prompt expander not found — using raw prompts")

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False


def concat_scenes(scene_paths: list[Path], out_path: Path) -> None:
    root = Path(__file__).resolve().parents[1]
    out_path.parent.mkdir(parents=True, exist_ok=True)

    abs_clips = [p.resolve() for p in scene_paths]
    lst = out_path.parent / (out_path.stem + "_concat_list.txt")
    lst.write_text("\n".join([f"file '{p.as_posix()}'" for p in abs_clips]), encoding="utf-8")

    # Run ffmpeg and check output file exists (ignore fontconfig warnings)
    result = subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(lst),
            "-c:v",
            "libx264",
            "-crf",
            "18",
            "-preset",
            "fast",
            str(out_path),
        ],
        capture_output=True,
        text=True,
    )
    
    # Check if output file was created successfully (ignore exit code due to fontconfig warnings)
    if not out_path.exists() or out_path.stat().st_size < 1000:
        print(f"FFmpeg STDOUT:\n{result.stdout}")
        print(f"FFmpeg STDERR:\n{result.stderr}")
        raise RuntimeError(f"Concatenation failed - output file missing or too small: {out_path}")


def upload(video_path: Path, *, title: str, description: str, tags: str, privacy: str) -> str:
    root = Path(__file__).resolve().parents[1]
    cmd = [
        str(root / ".venv" / "Scripts" / "python"),
        str(root / "scripts" / "youtube_upload.py"),
        "--file",
        str(video_path),
        "--title",
        title,
        "--description",
        description,
        "--tags",
        tags,
        "--privacy",
        privacy,
    ]
    out = subprocess.check_output(cmd, text=True, encoding="utf-8", errors="replace")
    # last URL line
    for line in out.splitlines()[::-1]:
        if line.startswith("URL:"):
            return line.replace("URL:", "").strip()
    return out.strip()


def main() -> None:
    root = Path(__file__).resolve().parents[1]

    storyboard_path = root / "storyboards" / "series_2026-02-12_tearjerker.json"
    privacy = "public"  # user requested

    # lightweight arg parsing to avoid extra deps
    argv = sys.argv[1:]
    if "--storyboard" in argv:
        i = argv.index("--storyboard")
        storyboard_path = Path(argv[i + 1])
        if not storyboard_path.is_absolute():
            storyboard_path = (root / storyboard_path).resolve()
    if "--privacy" in argv:
        i = argv.index("--privacy")
        privacy = argv[i + 1]

    data = json.loads(storyboard_path.read_text(encoding="utf-8"))

    default = data["default"]
    videos = data["videos"]

    out_dir = root / "out" / "series"
    out_dir.mkdir(parents=True, exist_ok=True)

    temp_root = root / "temp" / "series"
    temp_root.mkdir(parents=True, exist_ok=True)

    results = []

    for idx, v in enumerate(videos, start=1):
        slug = v["slug"]
        title = v["title"]
        desc = v.get("description", "")
        tags = default.get("tags", "")

        print(f"\n=== [{idx}/{len(videos)}] {slug} ===")

        scene_dir = temp_root / slug
        if scene_dir.exists():
            # keep and overwrite
            pass
        scene_dir.mkdir(parents=True, exist_ok=True)

        scene_paths: list[Path] = []
        for si, s in enumerate(v["scenes"], start=1):
            seed = random.randint(1, 2**31 - 1)
            scene_out = scene_dir / f"scene_{si:02d}.mp4"

            seconds = int(s.get("seconds") or default["sceneSeconds"])

            # ── Prompt expansion ──────────────────────────────────────────
            raw_prompt = s["prompt"]
            if EXPAND_PROMPTS:
                print(f"  [expand] Scene {si}: {raw_prompt[:60]}...")
                expanded_prompt = expand_prompt(raw_prompt, verbose=False)
                print(f"  [expand] → {len(expanded_prompt)} chars")
            else:
                expanded_prompt = raw_prompt

            req = GenerateRequest(
                text=expanded_prompt,
                overlay_text=s.get("caption") or None,
                seconds=seconds,
                fps=int(default["fps"]),
                seed=seed,
                backend=default["backend"],
                out=str(scene_out),
                width=int(default["width"]),
                height=int(default["height"]),
                upscale_4k=bool(default["upscale4k"]),
            )
            print(f"  - scene {si}/10 seed={seed}")
            try:
                run(req)
                scene_paths.append(scene_out)
            except Exception as e:
                print(f"ERROR generating scene {si}: {type(e).__name__}: {e}")
                raise
            
            # GPU memory cleanup after each scene
            if TORCH_AVAILABLE and torch.cuda.is_available():
                torch.cuda.empty_cache()
                torch.cuda.synchronize()
                mem_allocated = torch.cuda.memory_allocated() / 1e9
                mem_reserved = torch.cuda.memory_reserved() / 1e9
                print(f"    GPU cleared: {mem_allocated:.2f}GB allocated, {mem_reserved:.2f}GB reserved")

        final_path = out_dir / f"{slug}.mp4"
        print("Concatenating ->", final_path)
        concat_scenes(scene_paths, final_path)

        print("Uploading -> public")
        url = upload(final_path, title=title, description=desc, tags=tags, privacy=privacy)
        print("Uploaded:", url)
        results.append({"slug": slug, "title": title, "url": url})
        
        # GPU memory cleanup between videos
        if TORCH_AVAILABLE and torch.cuda.is_available():
            print(f"Clearing GPU memory before next video...")
            torch.cuda.empty_cache()
            torch.cuda.synchronize()
            gc.collect()
            mem_allocated = torch.cuda.memory_allocated() / 1e9
            mem_reserved = torch.cuda.memory_reserved() / 1e9
            print(f"  GPU memory: {mem_allocated:.2f}GB allocated, {mem_reserved:.2f}GB reserved")

    summary_path = out_dir / "upload_results.json"
    summary_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print("\nSaved summary:", summary_path)


if __name__ == "__main__":
    main()
