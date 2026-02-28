from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

from .types import VideoBackend
from .stub import StubBackend


_BACKENDS: Dict[str, VideoBackend] = {
    "stub": StubBackend(),
}


def try_register_optional_backends() -> None:
    # Import-only registration to keep installs flexible.
    try:
        from .cogvideox_diffusers import CogVideoXDiffusersBackend

        _BACKENDS.setdefault("cogvideox", CogVideoXDiffusersBackend())
    except Exception:
        pass

    try:
        from .svd_txt2vid import SvdTxt2VidBackend

        _BACKENDS.setdefault("svd", SvdTxt2VidBackend())
    except Exception:
        pass

    try:
        from .svd_optimized import SvdOptimizedBackend

        _BACKENDS.setdefault("svd_optimized", SvdOptimizedBackend())
    except Exception:
        pass

    try:
        from .wangp_14b import WanGP14BBackend

        _BACKENDS.setdefault("wangp", WanGP14BBackend())
    except Exception:
        pass


def get_backend(name: str) -> VideoBackend:
    try_register_optional_backends()
    if name not in _BACKENDS:
        raise ValueError(f"Unknown backend '{name}'. Available: {sorted(_BACKENDS.keys())}")
    return _BACKENDS[name]
