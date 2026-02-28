#!/usr/bin/env python3
"""
Test the optimized SDXL + SVD pipeline
"""

import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from t2v_shorts.config import GenerateRequest
from t2v_shorts.pipeline import run

def main():
    """Test optimized pipeline with a single scene"""
    
    root = Path(__file__).resolve().parents[1]
    out_dir = root / "test_output"
    out_dir.mkdir(exist_ok=True)
    
    # Test prompt: Same golden retriever prompt
    prompt = (
        "A golden retriever running happily through a sunlit meadow, "
        "tail wagging, slow motion, cinematic lighting, high quality, "
        "detailed fur, beautiful natural environment, 4k quality"
    )
    
    req = GenerateRequest(
        text=prompt,
        overlay_text=None,
        seconds=3,
        fps=15,  # Higher FPS for smoother motion
        seed=42,
        backend="svd_optimized",  # Our new optimized backend
        out=str(out_dir / "test_optimized.mp4"),
        width=1080,  # Shorts aspect ratio
        height=1920,
        upscale_4k=False,  # Don't upscale for test
    )
    
    print("=" * 60)
    print("Testing OPTIMIZED SDXL + SVD Pipeline")
    print("=" * 60)
    print(f"\nPrompt: {prompt}")
    print(f"Output: {req.out}")
    print(f"Settings:")
    print(f"  - Backend: svd_optimized")
    print(f"  - Resolution: {req.width}x{req.height}")
    print(f"  - Duration: {req.seconds}s @ {req.fps}fps")
    print(f"  - Seed: {req.seed}")
    print("\nThis will take ~2-3 minutes...")
    print("\nImprovements vs old pipeline:")
    print("  - SDXL (30 steps) instead of SDXL-Turbo (2 steps)")
    print("  - Guidance scale 8.5 (was 0.0)")
    print("  - SVD 25 steps (was default)")
    print("  - FPS 15 (was 6)")
    print("  - Motion 150 (was 120)")
    print("\nStarting generation...\n")
    
    result = run(req)
    
    print("\n" + "=" * 60)
    print("SUCCESS!")
    print("=" * 60)
    print(f"Video saved: {result}")
    print("\nCheck the quality and let me know if we should adjust settings!")
    print("If good -> we'll use this for the full batch generation")

if __name__ == "__main__":
    main()
