from __future__ import annotations

from pathlib import Path
import subprocess


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    clips = sorted((root / "temp" / "scenes").glob("*.mp4"))
    if not clips:
        raise SystemExit("No clips found in temp/scenes")

    out_dir = root / "out"
    out_dir.mkdir(exist_ok=True)

    list_path = out_dir / "concat_list_abs.txt"
    list_path.write_text("\n".join([f"file '{c.as_posix()}'" for c in clips]), encoding="utf-8")

    out_path = out_dir / "shorts_30s_compilation.mp4"

    subprocess.check_call(
        [
            "ffmpeg",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(list_path),
            "-c:v",
            "libx264",
            "-crf",
            "18",
            "-preset",
            "fast",
            str(out_path),
        ]
    )

    print(f"Wrote: {out_path}")


if __name__ == "__main__":
    main()
