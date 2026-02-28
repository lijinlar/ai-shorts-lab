from __future__ import annotations

import argparse
import json
import random
import subprocess
from pathlib import Path

import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from t2v_shorts.config import GenerateRequest
from t2v_shorts.pipeline import run


def concat_scenes(scene_paths: list[Path], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    lst = out_path.parent / (out_path.stem + "_concat_list.txt")
    lst.write_text("\n".join([f"file '{p.resolve().as_posix()}'" for p in scene_paths]), encoding="utf-8")

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
    for line in out.splitlines()[::-1]:
        if line.startswith("URL:"):
            return line.replace("URL:", "").strip()
    return out.strip()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--storyboard", required=True)
    ap.add_argument("--privacy", default="public", choices=["public", "unlisted", "private"])
    args = ap.parse_args()

    root = Path(__file__).resolve().parents[1]
    sb_path = Path(args.storyboard)
    if not sb_path.is_absolute():
        sb_path = (root / sb_path).resolve()

    sb = json.loads(sb_path.read_text(encoding="utf-8"))

    default = sb["default"]
    scenes = sb["scenes"]

    slug = sb.get("slug", "video")
    title = sb["title"]
    desc = sb.get("description", "")
    tags = sb.get("tags", "")

    temp_dir = root / "temp" / "single" / slug
    temp_dir.mkdir(parents=True, exist_ok=True)

    scene_paths: list[Path] = []
    for i, s in enumerate(scenes, start=1):
        seed = random.randint(1, 2**31 - 1)
        out_scene = temp_dir / f"scene_{i:02d}.mp4"

        # Allow variable per-scene durations (e.g., 2s, 3s, etc.)
        scene_seconds = int(s.get("seconds") or default["sceneSeconds"])

        req = GenerateRequest(
            text=s["prompt"],
            overlay_text=s.get("caption") or None,
            seconds=scene_seconds,
            fps=int(default["fps"]),
            seed=seed,
            backend=default["backend"],
            out=str(out_scene),
            width=int(default["width"]),
            height=int(default["height"]),
            upscale_4k=bool(default.get("upscale4k", False)),
        )
        print(f"scene {i}/{len(scenes)} ({scene_seconds}s) seed={seed}")
        run(req)
        scene_paths.append(out_scene)

    final = root / "out" / f"{slug}.mp4"
    print("Concatenating ->", final)
    concat_scenes(scene_paths, final)

    print(f"Uploading -> {args.privacy}")
    url = upload(final, title=title, description=desc, tags=tags, privacy=args.privacy)
    print("Uploaded:", url)


if __name__ == "__main__":
    main()
