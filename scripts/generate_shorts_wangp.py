#!/usr/bin/env python3
"""
Simple WanGP Shorts Generator
Uses the proven individual scene generation method from Feb 16 testing
"""

import sys
import os
import json
import subprocess
import time
import shutil
from pathlib import Path

# Force UTF-8
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.detach(), encoding='utf-8', errors='replace', line_buffering=True)
    sys.stderr = io.TextIOWrapper(sys.stderr.detach(), encoding='utf-8', errors='replace', line_buffering=True)

from config_loader import get_wangp_dir
WAN2GP_DIR = get_wangp_dir()
WANGP_PYTHON = WAN2GP_DIR / "venv" / "Scripts" / "python.exe"
OUTPUTS_DIR = WAN2GP_DIR / "outputs"

def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}")

def clean_outputs():
    """Delete all videos in outputs directory"""
    if OUTPUTS_DIR.exists():
        for f in OUTPUTS_DIR.glob("*.mp4"):
            try:
                f.unlink()
            except:
                pass

def create_queue_json(prompt, *, width, height, num_frames, fps, steps=20, cfg=6.5, seed=-1):
    """Create a single-task queue JSON for WanGP --process mode.

    Allow low-VRAM overrides via env:
      - WANGP_MODEL_TYPE (e.g. t2v_1.3B)
      - WANGP_STEPS (e.g. 8-20)
      - WANGP_CFG (e.g. 1-7)
    """
    model_type = os.environ.get("WANGP_MODEL_TYPE", "t2v")
    steps = int(os.environ.get("WANGP_STEPS", str(steps)))
    cfg = float(os.environ.get("WANGP_CFG", str(cfg)))

    task = {
        "id": 1,
        "params": {
            "prompt": prompt,
            "mode": "text2video",
            "model_type": model_type,
            "width": int(width),
            "height": int(height),
            "num_frames": int(num_frames),
            "fps": int(fps),
            "steps": int(steps),
            "cfg": float(cfg),
            "seed": int(seed),
        },
    }
    return [task]

def generate_scene(prompt, scene_num, *, width, height, num_frames, fps, max_retries=2):
    """
    Generate one scene using WanGP
    
    Returns: Path to generated video or None
    """
    log(f"Scene {scene_num}: Generating...")
    
    for attempt in range(max_retries):
        # Clean outputs before generation
        clean_outputs()
        
        # Create queue file
        import zipfile
        queue_data = create_queue_json(prompt, width=width, height=height, num_frames=num_frames, fps=fps)
        queue_file = str(WAN2GP_DIR / "temp_queue.zip")
        
        with zipfile.ZipFile(queue_file, 'w') as zf:
            zf.writestr("queue.json", json.dumps(queue_data, indent=2))
        
        # Run WanGP in --process mode
        cmd = [
            str(WANGP_PYTHON),
            str(WAN2GP_DIR / "wgp.py"),
            "--process", queue_file
        ]
        
        log(f"  Attempt {attempt + 1}/{max_retries}...")
        
        try:
            result = subprocess.run(
                cmd,
                cwd=str(WAN2GP_DIR),
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout per scene
            )
            
            # Find generated video
            videos = list(OUTPUTS_DIR.glob("*.mp4"))
            if videos:
                latest = max(videos, key=lambda p: p.stat().st_mtime)
                log(f"  SUCCESS: {latest.name}")
                os.remove(queue_file)
                return latest
            else:
                log(f"  No output file (attempt {attempt + 1})")
                if result.stdout:
                    tail = "\n".join(result.stdout.splitlines()[-30:])
                    log("  --- WanGP stdout (tail) ---")
                    print(tail)
                if result.stderr:
                    tail = "\n".join(result.stderr.splitlines()[-30:])
                    log("  --- WanGP stderr (tail) ---")
                    print(tail)
                
        except subprocess.TimeoutExpired:
            log(f"  Timeout (attempt {attempt + 1})")
        except Exception as e:
            log(f"  Error: {e}")
        
        if attempt < max_retries - 1:
            time.sleep(3)
    
    log(f"  FAILED after {max_retries} attempts")
    return None

def concatenate_videos(video_files, output):
    """Concatenate multiple videos with FFmpeg"""
    log(f"Concatenating {len(video_files)} videos...")
    
    concat_list = "concat.txt"
    with open(concat_list, "w") as f:
        for vid in video_files:
            f.write(f"file '{vid}'\n")
    
    cmd = ["ffmpeg", "-f", "concat", "-safe", "0", "-i", concat_list,
           "-c", "copy", "-y", output]
    
    result = subprocess.run(cmd, capture_output=True)
    os.remove(concat_list)
    
    if result.returncode == 0:
        log(f"  Concatenated: {output}")
        return output
    else:
        log(f"  Concat failed")
        return None

def add_captions(input_video, captions, output_video):
    """Add captions with FFmpeg drawtext"""
    log(f"Adding {len(captions)} captions...")
    
    filters = []
    for cap in captions:
        text = cap["text"].replace("'", "").replace('"', '')  # Remove quotes
        filters.append(
            f"drawtext=text='{text}':fontsize=48:fontcolor=white:"
            f"bordercolor=black:borderw=3:x=(w-text_w)/2:y=h-th-80:"
            f"enable='between(t,{cap['start']},{cap['end']})'"
        )
    
    filter_str = ",".join(filters)
    
    cmd = ["ffmpeg", "-i", input_video, "-vf", filter_str,
           "-c:v", "libx264", "-preset", "medium", "-crf", "23",
           "-c:a", "copy", "-y", output_video]
    
    result = subprocess.run(cmd, capture_output=True)
    
    if result.returncode == 0:
        log(f"  Captions added: {output_video}")
        return output_video
    return None

def convert_to_shorts(input_video, output_video):
    """Convert any video to YouTube Shorts portrait format (1080x1920, 9:16).

    WanGP outputs landscape (832x480). This function converts it to portrait
    using a blurred background + centered foreground approach (TikTok style).
    Works correctly for both landscape AND portrait inputs.
    """
    log("Converting to Shorts portrait format (1080x1920)...")

    # Blur background fills top/bottom; original video centered in the middle.
    # This is the proven approach used for shelter_dog shorts (correct 1080x1920).
    cmd = [
        "ffmpeg", "-i", input_video,
        "-filter_complex",
        (
            "[0:v]scale=1080:-1,boxblur=30:5,"
            "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920[bg];"
            "[0:v]scale=1080:-1[fg];"
            "[bg][fg]overlay=0:(H-h)/2"
        ),
        "-c:v", "libx264", "-preset", "medium", "-crf", "23",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "128k",
        "-y", output_video,
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode == 0:
        from pathlib import Path as _Path
        size_mb = _Path(output_video).stat().st_size / 1_000_000
        log(f"  Shorts ready: {output_video} ({size_mb:.1f} MB, 1080x1920)")
        return output_video

    log("  Conversion failed")
    if result.stderr:
        log("  --- ffmpeg stderr (tail) ---")
        print("\n".join(result.stderr.splitlines()[-30:]))
    return None

def main():
    if len(sys.argv) < 3:
        print("Usage: python generate_shorts_wangp.py <storyboard.json> <output.mp4>")
        sys.exit(1)
    
    storyboard_file = sys.argv[1]
    output_file = sys.argv[2]
    
    log("="*60)
    log("WanGP YouTube Shorts Generator")
    log("="*60)
    log(f"Storyboard: {storyboard_file}")
    log(f"Output: {output_file}")
    
    # Load storyboard
    with open(storyboard_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Defaults (support both single-video and series storyboards)
    defaults = data.get('default', {}) if isinstance(data, dict) else {}
    scene_seconds = float(defaults.get('sceneSeconds', 3))
    fps = int(defaults.get('fps', 24))
    width = int(defaults.get('width', 480))
    height = int(defaults.get('height', 832))
    num_frames = int(scene_seconds * fps) + 1  # WanGP expects frame count

    log(f"Render: {width}x{height} @ {fps}fps, {scene_seconds:.1f}s/scene ({num_frames} frames)")

    # Get scenes
    scenes = data.get('scenes', [])
    if not scenes and 'videos' in data:
        videos = data['videos']
        if videos:
            scenes = videos[0].get('scenes', [])
    
    if not scenes:
        log("ERROR: No scenes in storyboard")
        sys.exit(1)
    
    log(f"Scenes to generate: {len(scenes)}")
    log("")
    
    # Generate scenes
    scene_files = []
    for i, scene in enumerate(scenes, 1):
        prompt = scene.get('prompt', '')
        if not prompt:
            log(f"Scene {i}: No prompt, skipping")
            continue
        
        video = generate_scene(prompt, i, width=width, height=height, num_frames=num_frames, fps=fps)
        if video:
            # Copy to safe location
            safe_path = f"scene_{i}.mp4"
            shutil.copy(video, safe_path)
            scene_files.append(safe_path)
        else:
            log(f"Scene {i}: Generation failed")
            sys.exit(1)
    
    if not scene_files:
        log("ERROR: No scenes generated")
        sys.exit(1)
    
    log("")
    
    # Concatenate
    base = Path(output_file).stem
    concat = f"{base}_concat.mp4"
    if not concatenate_videos(scene_files, concat):
        sys.exit(1)
    
    # Captions
    captions = []
    t = 0.0
    for i, scene in enumerate(scenes):
        captions.append({
            "text": scene.get('caption', f'Scene {i+1}'),
            "start": t,
            "end": t + scene_seconds
        })
        t += scene_seconds
    
    captioned = f"{base}_captioned.mp4"
    if not add_captions(concat, captions, captioned):
        sys.exit(1)
    
    # Convert
    if not convert_to_shorts(captioned, output_file):
        sys.exit(1)
    
    # Cleanup
    try:
        for f in scene_files + [concat, captioned]:
            os.remove(f)
        log("Cleanup complete")
    except:
        pass
    
    log("")
    log("="*60)
    log(f"SUCCESS: {output_file}")
    log("="*60)
    
    sys.exit(0)

if __name__ == "__main__":
    main()
