#!/usr/bin/env python3
"""
Single Scene Generator for WanGP
Generates one scene at a time - the method that worked on Feb 16
"""

import sys
import os
import json
import zipfile
import subprocess
import time
import shutil
from pathlib import Path

# UTF-8 encoding - safe version
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.detach(), encoding='utf-8', errors='replace', line_buffering=True)
    sys.stderr = io.TextIOWrapper(sys.stderr.detach(), encoding='utf-8', errors='replace', line_buffering=True)

from config_loader import get_wangp_dir
WAN2GP_DIR = get_wangp_dir()
WANGP_PYTHON = WAN2GP_DIR / "venv" / "Scripts" / "python.exe"
OUTPUTS_DIR = WAN2GP_DIR / "outputs"

# Add project root for imports
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
try:
    from t2v_shorts.prompt_expander import expand_prompt, get_negative_prompt
    EXPANDER_AVAILABLE = True
except ImportError:
    EXPANDER_AVAILABLE = False
    print("[wangp] Warning: prompt_expander not available, using raw prompts")

def clean_outputs():
    """Delete all videos in outputs"""
    if OUTPUTS_DIR.exists():
        for f in OUTPUTS_DIR.glob("*.mp4"):
            try:
                f.unlink()
            except:
                pass

def create_single_scene_queue(prompt, negative_prompt=""):
    """Create a queue.json for one scene using Wan2.1 14B model."""
    task = {
        "id": 1,
        "params": {
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "mode": "text2video",
            "model_type": "t2v_1.3B",
            "model_filename": "t2v_1.3B",
            "profile": -1,
            "width": 832,
            "height": 480,
            "num_frames": 81,
            "fps": 24,
            "steps": 50,
            "cfg": 7.5,
            "seed": -1,
            "transformer_quantization": "int8",
            "transformer_dtype_policy": "auto",
            "vae_quantization": "int8",
            "loras": [],
            "loras_multipliers": [],
            "state": {},
        },
        "plugin_data": {},
        "prompt": prompt,
    }
    return [task]

def generate_scene(prompt, max_wait=600, expand=True):
    """
    Generate one scene with WanGP

    Args:
        prompt:   Generation prompt (short storyboard description or full cinematic)
        max_wait: Max seconds to wait
        expand:   Auto-expand short prompts using LLM (default True)

    Returns:
        Path to generated video or None
    """
    # ── Prompt expansion ──────────────────────────────────────────────────────
    original_prompt = prompt
    negative_prompt = ""
    if expand and EXPANDER_AVAILABLE:
        print(f"[expand] Expanding prompt ({len(prompt)} chars)...")
        prompt = expand_prompt(prompt, verbose=True)
        negative_prompt = get_negative_prompt()
        print(f"[expand] → {len(prompt)} chars")
    
    print(f"Generating scene...")
    print(f"Prompt ({len(prompt)} chars): {prompt[:120]}...")
    
    # Clean outputs first
    clean_outputs()
    
    # Create queue file
    queue_data = create_single_scene_queue(prompt, negative_prompt=negative_prompt)
    queue_file = WAN2GP_DIR / "temp_queue.zip"
    
    with zipfile.ZipFile(queue_file, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("queue.json", json.dumps(queue_data, indent=2))
    
    print(f"Created queue: {queue_file}")
    
    # Run WanGP with --process
    cmd = [
        str(WANGP_PYTHON),
        str(WAN2GP_DIR / "wgp.py"),
        "--process", str(queue_file)
    ]
    
    print(f"Starting WanGP...")
    
    # Start process
    process = subprocess.Popen(
        cmd,
        cwd=str(WAN2GP_DIR),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding='utf-8',
        errors='replace'
    )
    
    # Wait for video to appear
    start_time = time.time()
    initial_files = set(OUTPUTS_DIR.glob("*.mp4")) if OUTPUTS_DIR.exists() else set()
    
    while time.time() - start_time < max_wait:
        # Check for new video files
        if OUTPUTS_DIR.exists():
            current_files = set(OUTPUTS_DIR.glob("*.mp4"))
            new_files = current_files - initial_files
            
            if new_files:
                # Found a video!
                video = list(new_files)[0]
                time.sleep(2)  # Let it finish writing
                
                # Kill the process
                process.terminate()
                time.sleep(1)
                if process.poll() is None:
                    process.kill()
                
                # Clean up queue file
                try:
                    queue_file.unlink()
                except:
                    pass
                
                print(f"SUCCESS: {video.name} ({video.stat().st_size / (1024*1024):.1f} MB)")
                return video
        
        time.sleep(2)
    
    # Timeout
    process.terminate()
    time.sleep(1)
    if process.poll() is None:
        process.kill()
    
    print("TIMEOUT: No video generated")
    return None

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python wangp_generate_scene.py <prompt> <output.mp4>")
        sys.exit(1)
    
    prompt = sys.argv[1]
    output = sys.argv[2]
    
    result = generate_scene(prompt)
    
    if result:
        shutil.copy(result, output)
        print(f"Saved to: {output}")
        sys.exit(0)
    else:
        print("Failed")
        sys.exit(1)
