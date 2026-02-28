from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


class VideoBackend(Protocol):
    name: str

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
    ) -> None: ...
