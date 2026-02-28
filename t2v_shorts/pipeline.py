from __future__ import annotations

import os
import subprocess
from pathlib import Path

from .config import GenerateRequest
from .backends.registry import get_backend


def ensure_parent(path: str) -> Path:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def ffmpeg_fit(
    in_path: Path,
    out_path: Path,
    *,
    width: int,
    height: int,
    mode: str = "pad",
    overlay_text: str | None = None,
) -> None:
    """Fit video to exact WxH.

    mode:
      - "pad": preserve entire frame (no zoom), add letterbox/pillarbox as needed
      - "crop": fill frame (zoom) then center-crop

    For SVD (which is 16:9 / landscape), "pad" avoids heavy zoom and quality loss.
    """
    if mode == "crop":
        vf = f"scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height}"
    elif mode == "blur":
        # Full-frame vertical with blurred background + sharp foreground (no ugly zoom crop).
        # 1) bg: scale to fill, blur
        # 2) fg: scale to fit, overlay centered
        vf = (
            f"[0:v]scale={width}:{height}:force_original_aspect_ratio=increase,"
            f"crop={width}:{height},gblur=sigma=30[bg];"
            f"[0:v]scale={width}:{height}:force_original_aspect_ratio=decrease[fg];"
            f"[bg][fg]overlay=(W-w)/2:(H-h)/2"
        )
    else:
        vf = (
            f"scale={width}:{height}:force_original_aspect_ratio=decrease,"
            f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2"
        )
    font_name = os.environ.get("T2V_SHORTS_FONT_NAME", "Arial")

    def _text_filter(textfile: Path) -> str:
        # Bottom-center captions (safe: use textfile to avoid quoting/escaping user text)
        # Use font name (avoids Windows drive-letter escaping issues).
        txt_p = textfile.as_posix()

        return (
            "drawtext="
            f"font={font_name}:"
            f"textfile={txt_p}:"
            "reload=0:"
            "fontsize=64:"
            "fontcolor=white:"
            "borderw=4:"
            "bordercolor=black:"
            "x=(w-text_w)/2:"
            "y=h*0.78"
        )

    textfile = None
    if overlay_text:
        textfile = out_path.parent / (out_path.stem + "_caption.txt")
        textfile.parent.mkdir(parents=True, exist_ok=True)
        textfile.write_text(overlay_text, encoding="utf-8")

    if mode == "blur":
        graph = vf
        if textfile:
            graph = graph + "," + _text_filter(textfile)
        graph = graph + "[v]"

        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            str(in_path),
            "-filter_complex",
            graph,
            "-map",
            "[v]",
            "-c:v",
            "libx264",
            "-crf",
            "18",
            "-preset",
            "slow",
            str(out_path),
        ]
        
        # Run ffmpeg and check output exists (ignore exit code due to fontconfig warnings on Windows)
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if not out_path.exists() or out_path.stat().st_size < 1000:
            raise RuntimeError(f"FFmpeg failed - output missing or too small: {out_path}\nSTDERR: {result.stderr}")
        
        return  # Early return for blur mode
    else:
        vf2 = vf
        if textfile:
            vf2 = vf2 + "," + _text_filter(textfile)

        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            str(in_path),
            "-vf",
            vf2,
            "-c:v",
            "libx264",
            "-crf",
            "18",
            "-preset",
            "slow",
            str(out_path),
        ]

    # Run ffmpeg and check output exists (ignore exit code due to fontconfig warnings on Windows)
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if not out_path.exists() or out_path.stat().st_size < 1000:
        raise RuntimeError(f"FFmpeg failed - output missing or too small: {out_path}\nSTDERR: {result.stderr}")


def ffmpeg_scale_to_4k(in_path: Path, out_path: Path) -> None:
    # 4K vertical: 2160x3840
    ffmpeg_fit(in_path, out_path, width=2160, height=3840)


def run(req: GenerateRequest, *, dry_run: bool = False) -> Path:
    out_path = ensure_parent(req.out)

    backend = get_backend(req.backend)
    if dry_run:
        print("DRY RUN")
        print("backend:", backend.name)
        print(req.model_dump())
        return out_path

    tmp_dir = Path("temp")
    tmp_dir.mkdir(exist_ok=True)
    base_video = tmp_dir / "base.mp4"

    # 1) generate base video
    backend.generate(
        prompt=req.text,
        seconds=req.seconds,
        fps=req.fps,
        width=req.width,
        height=req.height,
        seed=req.seed,
        out_path=base_video,
    )

    # 2) fit to requested WxH (center-crop) for Shorts aspect ratio
    fitted = tmp_dir / "fit.mp4"
    ffmpeg_fit(
        base_video,
        fitted,
        width=req.width,
        height=req.height,
        mode="blur",
        overlay_text=req.overlay_text,
    )

    # 3) optional 4K upscale (still cropped vertical)
    final_video = fitted
    if req.upscale_4k:
        up = tmp_dir / "up4k.mp4"
        ffmpeg_scale_to_4k(fitted, up)
        final_video = up

    # 4) copy to output
    out_path.write_bytes(final_video.read_bytes())

    # cleanup left intentionally for inspection
    return out_path
