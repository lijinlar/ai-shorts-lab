from __future__ import annotations

import random
import subprocess
from pathlib import Path

import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from t2v_shorts.config import GenerateRequest
from t2v_shorts.pipeline import run


def ffmpeg_concat(inputs: list[Path], out_path: Path) -> None:
    """Concat scenes robustly using an absolute-path list (fixes ffmpeg relative path issues)."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = out_path.parent / "concat_list_abs.txt"

    root = Path(__file__).resolve().parents[1]
    abs_inputs = [(root / p).resolve() if not p.is_absolute() else p.resolve() for p in inputs]

    tmp.write_text("\n".join([f"file '{p.as_posix()}'" for p in abs_inputs]), encoding="utf-8")

    cmd = [
        "ffmpeg",
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        str(tmp),
        "-c:v",
        "libx264",
        "-crf",
        "18",
        "-preset",
        "fast",
        str(out_path),
    ]
    subprocess.check_call(cmd)


def main() -> None:
    # Simple mini-story: stray cat finds a cozy home (10 scenes x ~3s)
    prompts = [
        "Cinematic street at night in Dubai, a small stray cat under neon lights, shallow depth of field, realistic, cinematic lens",
        "Extreme close-up of the cat's face looking up, big reflective eyes, realistic fur detail, soft bokeh lights, cinematic",
        "The cat cautiously walks along a wet sidewalk with reflections, realistic motion, cinematic lighting, slow camera follow",
        "A kind human crouches down and offers food to the cat, warm streetlight, cinematic, realistic",
        "The cat eats, then slowly trusts and rubs against the human's hand, intimate close-up, gentle movement, cinematic",
        "The human carries the cat in a hoodie pocket while walking, cozy vibe, cinematic, realistic",
        "Inside a small apartment, the cat explores a living room, warm lamp light, cinematic, slow camera pan",
        "The cat plays with a small toy on the floor, playful motion, cinematic, realistic",
        "The cat curls up on a couch and falls asleep, soft warm lighting, close-up, shallow depth of field, cinematic",
        "Morning sunlight through a window, the cat wakes up and stretches, peaceful, cinematic, realistic",
    ]

    overlays = [
        "He was shaking in the rain…",
        "I couldn't walk away.",
        "He didn't trust me.",
        "One step closer.",
        "Okay… we're friends.",
        "Let's get you home.",
        "New place. New life.",
        "He learned to play.",
        "Finally… safe.",
        "Name him? Comment below.",
    ]

    out_dir = Path("out")
    out_dir.mkdir(exist_ok=True)

    scenes_dir = Path("temp") / "scenes"
    scenes_dir.mkdir(parents=True, exist_ok=True)

    scene_seconds = 3
    n_scenes = 10  # 10*3 = 30s

    clips: list[Path] = []

    for i in range(n_scenes):
        seed = random.randint(1, 2**31 - 1)
        out_path = scenes_dir / f"scene_{i:02d}.mp4"
        text = prompts[i % len(prompts)]
        caption = overlays[i % len(overlays)]

        req = GenerateRequest(
            text=text,
            overlay_text=caption,
            seconds=scene_seconds,
            fps=8,
            seed=seed,
            backend="svd",
            out=str(out_path),
            width=1080,
            height=1920,
            upscale_4k=False,
        )

        print(f"[scene {i+1}/{n_scenes}] seed={seed} -> {out_path}")
        run(req)
        clips.append(out_path)

    final_path = out_dir / "shorts_30s_compilation.mp4"
    print("Concatenating ->", final_path)
    ffmpeg_concat(clips, final_path)
    print("Wrote:", final_path)


if __name__ == "__main__":
    main()
