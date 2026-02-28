"""
Prompt Expander — WanGP Cinematic Quality Booster
==================================================
Takes short storyboard scene descriptions and expands them into
full cinematic prompts that match WanGP web-UI quality.

Uses Ollama (llama3.1:8b) locally — no API key, no cost.
Falls back to template-based expansion if Ollama is unavailable.
"""

from __future__ import annotations

import json
import re
import urllib.request
import urllib.error
from typing import Optional

# ── Quality suffixes (always appended) ────────────────────────────────────────

CINEMATIC_SUFFIX = (
    "cinematic 4K ultra-realistic, photorealistic, professional cinema camera, "
    "shallow depth of field, warm golden emotional lighting, smooth slow motion, "
    "sharp focus, film grain, high dynamic range, color graded"
)

NEGATIVE_PROMPT = (
    "cartoon, anime, illustration, painting, blurry, low quality, watermark, "
    "text overlay, ugly, deformed, noisy, pixelated, overexposed, flat lighting"
)

# ── System prompt for LLM expansion ───────────────────────────────────────────

SYSTEM_PROMPT = """You are a professional video director writing prompts for an AI video generator (WanGP/Wan2.1).

Your job: take a SHORT scene description and expand it into a DETAILED cinematic prompt.

Rules:
- Output ONLY the expanded prompt — no preamble, no explanation, no quotes
- Length: 60-100 words
- Always include: specific camera angle, lighting type, emotional tone, motion description
- Always end with quality keywords: "cinematic 4K, ultra-realistic, photorealistic, shallow depth of field, warm emotional lighting, smooth motion"
- Keep the core action/subject from the original
- Be specific about what we SEE (not what we feel abstractly)
- Style: emotional dog content (reunions, rescues, transformations)

Example input:  "Soldier steps inside with duffel bag. Dog rushes forward."
Example output: "Medium wide shot: A US Army soldier in camouflage uniform pushes open the front door, worn duffel bag slung over his shoulder. A golden retriever freezes for one heartbeat then bursts forward across polished hardwood, paws scrambling with pure joy. Slow-motion impact as soldier drops to his knees with arms open wide. Cinematic 4K, ultra-realistic, photorealistic, shallow depth of field, warm golden indoor lighting, smooth slow motion."
"""

# ── Ollama client ──────────────────────────────────────────────────────────────

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
OLLAMA_MODEL = "deepseek-r1:32b"  # production model


def _ollama_available() -> bool:
    try:
        req = urllib.request.Request("http://127.0.0.1:11434/api/tags", method="GET")
        with urllib.request.urlopen(req, timeout=3):
            return True
    except Exception:
        return False


def _expand_via_ollama(short_prompt: str) -> Optional[str]:
    """Call Ollama llama3.1:8b to expand the prompt."""
    payload = json.dumps({
        "model": OLLAMA_MODEL,
        "prompt": f"{SYSTEM_PROMPT}\n\nExpand this scene:\n{short_prompt}",
        "stream": False,
        "think": False,  # Disable deepseek-r1 chain-of-thought — we need speed not reasoning
        "options": {
            "temperature": 0.7,
            "num_predict": 300,
            "stop": ["Example input:", "Example output:", "Note:", "---"],
        }
    }).encode()

    try:
        req = urllib.request.Request(
            OLLAMA_URL,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=300) as resp:  # 5 min — deepseek-r1:32b cold start
            result = json.loads(resp.read())
            text = result.get("response", "").strip()
            # Strip deepseek-r1 <think>...</think> reasoning blocks
            text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()
            # Strip any accidental quotes
            text = text.strip('"').strip("'").strip()
            return text if len(text) > 50 else None
    except Exception as e:
        print(f"[expander] Ollama call failed: {e}")
        return None


# ── Template-based fallback ────────────────────────────────────────────────────

# Camera angle pool — cycle through for variety
_CAMERA_ANGLES = [
    "Extreme close-up",
    "Close-up",
    "Medium close-up",
    "Medium shot",
    "Medium wide shot",
    "Wide shot",
    "Low angle medium shot",
    "Overhead close-up",
    "Slow-motion medium shot",
]

_LIGHTING = [
    "warm golden indoor lighting",
    "soft afternoon sunlight streaming through windows",
    "warm sunset backlighting",
    "gentle diffused daylight, warm tones",
    "cinematic warm amber light",
]

_QUALITY_TAIL = (
    "Cinematic 4K, ultra-realistic, photorealistic, shallow depth of field, "
    "smooth slow motion, sharp focus, high dynamic range, emotional realism."
)

_angle_idx = 0

def _expand_via_template(short_prompt: str) -> str:
    """Deterministic template expansion — always works, no LLM needed."""
    global _angle_idx

    # Strip existing camera/scene labels like "Hook (first 2 seconds):"
    cleaned = re.sub(r"^(Hook|Scene|Shot|Wide|Close|Medium)\s*[^:]*:\s*", "", short_prompt, flags=re.IGNORECASE).strip()

    # Pick angle + lighting (cycle for variety)
    angle = _CAMERA_ANGLES[_angle_idx % len(_CAMERA_ANGLES)]
    light = _LIGHTING[_angle_idx % len(_LIGHTING)]
    _angle_idx += 1

    expanded = f"{angle}: {cleaned} {light}. {_QUALITY_TAIL}"
    return expanded


# ── Public API ─────────────────────────────────────────────────────────────────

def expand_prompt(
    short_prompt: str,
    *,
    use_llm: bool = True,
    verbose: bool = False,
) -> str:
    """
    Expand a short scene description into a full cinematic WanGP prompt.

    Args:
        short_prompt:  The raw scene description from the storyboard.
        use_llm:       Try Ollama first (falls back to template if unavailable).
        verbose:       Print expansion details.

    Returns:
        Full cinematic prompt string ready for WanGP.
    """
    if verbose:
        print(f"[expander] Input ({len(short_prompt)} chars): {short_prompt[:80]}...")

    expanded: Optional[str] = None

    if use_llm and _ollama_available():
        expanded = _expand_via_ollama(short_prompt)
        if expanded and verbose:
            print(f"[expander] LLM expanded ({len(expanded)} chars)")
    
    if not expanded:
        expanded = _expand_via_template(short_prompt)
        if verbose:
            print(f"[expander] Template expanded ({len(expanded)} chars)")

    # Avoid duplicate quality keywords if LLM already included them
    lower = expanded.lower()
    if "cinematic 4k" in lower or "ultra-realistic" in lower:
        result = expanded  # LLM already added quality keywords — don't double-append
    else:
        result = expanded.rstrip(". ") + ". " + CINEMATIC_SUFFIX
    
    if verbose:
        print(f"[expander] Final ({len(result)} chars): {result[:120]}...")

    return result


def get_negative_prompt() -> str:
    """Return the standard negative prompt for WanGP."""
    return NEGATIVE_PROMPT


# ── CLI test ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    test_prompts = [
        "Hook (first 2 seconds): Extreme close-up of a dog's mouth holding a scuffed yellow tennis ball, tail wagging fast.",
        "A Navy SEAL in uniform steps inside with a duffel bag. The dog freezes for one heartbeat, then rushes forward.",
        "Close-up: The SEAL kneels, crying, hugging the dog tight.",
        "Final shot: Outside at sunrise, the SEAL throws the tennis ball and the dog sprints after it, joyful.",
    ]

    if len(sys.argv) > 1:
        test_prompts = [" ".join(sys.argv[1:])]

    print("=== Prompt Expander Test ===\n")
    ollama_ok = _ollama_available()
    print(f"Ollama available: {ollama_ok}")
    print(f"Model: {OLLAMA_MODEL}\n")

    for i, p in enumerate(test_prompts, 1):
        print(f"--- Scene {i} ---")
        print(f"IN:  {p}")
        result = expand_prompt(p, verbose=True)
        print(f"OUT: {result}")
        print()
