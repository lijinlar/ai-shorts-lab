from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from t2v_shorts.config import GenerateRequest
from t2v_shorts.pipeline import run

req = GenerateRequest(
    text="Cinematic mall corridor in UAE, warm lights, a small child standing alone looking scared, shallow depth of field, realistic, cinematic lens",
    overlay_text="He could not find his mom.\nما قدر يلقى أمه.",
    seconds=3,
    fps=8,
    backend="svd",
    out="out/_test_overlay_ar.mp4",
    width=1080,
    height=1920,
    upscale_4k=False,
)

print(run(req))
