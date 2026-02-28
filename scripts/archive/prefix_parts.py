from __future__ import annotations

import json
from pathlib import Path

p = Path(__file__).resolve().parents[1] / "storyboards" / "series_2026-02-12_tearjerker.json"
data = json.loads(p.read_text(encoding="utf-8"))

videos = data["videos"]
for i, v in enumerate(videos, start=1):
    base = v["title"]
    if "Part" in base:
        continue
    v["title"] = f"Part {i}/10 — {base}"

p.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
print("Updated titles with part numbers")
