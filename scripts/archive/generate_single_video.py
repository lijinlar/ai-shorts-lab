from __future__ import annotations

import gc
import json
import random
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from t2v_shorts.config import GenerateRequest
from t2v_shorts.pipeline import run

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False


def concat_scenes(scene_paths: list[Path], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    abs_clips = [p.resolve() for p in scene_paths]
    lst = out_path.parent / (out_path.stem + "_concat_list.txt")
    lst.write_text("\n".join([f"file '{p.as_posix()}'" for p in abs_clips]), encoding="utf-8")

    subprocess.check_call(
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
        ]
    )


def main() -> None:
    root = Path(__file__).resolve().parents[1]

    # Parse args
    argv = sys.argv[1:]
    if len(argv) < 2:
        print("Usage: python generate_single_video.py --storyboard <file> --video-index <0-5>")
        sys.exit(1)

    storyboard_path = None
    video_index = 0

    if "--storyboard" in argv:
        i = argv.index("--storyboard")
        storyboard_path = Path(argv[i + 1])
        if not storyboard_path.is_absolute():
            storyboard_path = (root / storyboard_path).resolve()
    
    if "--video-index" in argv:
        i = argv.index("--video-index")
        video_index = int(argv[i + 1])

    if not storyboard_path:
        print("ERROR: --storyboard required")
        sys.exit(1)

    data = json.loads(storyboard_path.read_text(encoding="utf-8"))
    default = data["default"]
    videos = data["videos"]

    if video_index < 0 or video_index >= len(videos):
        print(f"ERROR: video-index must be 0-{len(videos)-1}")
        sys.exit(1)

    v = videos[video_index]
    slug = v["slug"]
    title = v["title"]

    print(f"\n=== Generating video {video_index + 1}/{len(videos)}: {slug} ===")

    temp_root = root / "temp" / "series"
    out_dir = root / "out" / "series"
    out_dir.mkdir(parents=True, exist_ok=True)

    scene_dir = temp_root / slug
    scene_dir.mkdir(parents=True, exist_ok=True)

    scene_paths: list[Path] = []
    for si, s in enumerate(v["scenes"], start=1):
        seed = random.randint(1, 2**31 - 1)
        scene_out = scene_dir / f"scene_{si:02d}.mp4"

        seconds = int(s.get("seconds") or default["sceneSeconds"])
        req = GenerateRequest(
            text=s["prompt"],
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
        print(f"  - scene {si}/{len(v['scenes'])} seed={seed}")
        
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
            gc.collect()
            mem_allocated = torch.cuda.memory_allocated() / 1e9
            mem_reserved = torch.cuda.memory_reserved() / 1e9
            print(f"    GPU cleared: {mem_allocated:.2f}GB allocated, {mem_reserved:.2f}GB reserved")

    final_path = out_dir / f"{slug}.mp4"
    print("Concatenating ->", final_path)
    concat_scenes(scene_paths, final_path)

    print(f"DONE Video saved: {final_path}")
    print(f"   Title: {title}")


if __name__ == "__main__":
    main()
