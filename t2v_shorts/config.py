from __future__ import annotations

from pydantic import BaseModel, Field


class GenerateRequest(BaseModel):
    text: str
    overlay_text: str | None = None
    seconds: int = Field(default=6, ge=1, le=20)
    fps: int = Field(default=24, ge=8, le=60)
    seed: int | None = None
    backend: str = Field(default="cogvideox")

    # output
    out: str = "out/out.mp4"

    # quality knobs
    width: int = 768
    height: int = 1344  # 9:16-ish base

    # post
    upscale_4k: bool = True
    interpolate: bool = False
