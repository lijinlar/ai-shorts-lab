from __future__ import annotations

import subprocess
from pathlib import Path


class StubBackend:
    name = "stub"

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
        """Creates a placeholder video with the prompt burned in.

        Useful to test the pipeline without heavy models.
        """
        out_path.parent.mkdir(parents=True, exist_ok=True)

        txt = prompt.replace("'", "\\'")
        cmd = [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            f"color=c=black:s={width}x{height}:d={seconds}:r={fps}",
            "-vf",
            f"drawtext=text='{txt}':fontcolor=white:fontsize=36:x=40:y=H/2",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            str(out_path),
        ]
        subprocess.check_call(cmd)
