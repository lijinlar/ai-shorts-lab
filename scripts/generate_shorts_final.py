#!/usr/bin/env python3
"""
WanGP Shorts Generator - Scene by Scene
Uses the proven Feb 16 method: generate scenes individually, then combine
"""

import sys
import os
import json
import subprocess
import time
import shutil
from pathlib import Path

# Import the scene generator
root = Path(__file__).parent.parent
sys.path.insert(0, str(root / "scripts"))

# UTF-8 - do after imports
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.detach(), encoding='utf-8', errors='replace', line_buffering=True)
    sys.stderr = io.TextIOWrapper(sys.stderr.detach(), encoding='utf-8', errors='replace', line_buffering=True)

from wangp_generate_scene import generate_scene

def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}")

def concatenate_videos(video_files, output):
    """Concatenate videos with FFmpeg"""
    log(f"Concatenating {len(video_files)} videos...")
    
    concat_file = "concat_list.txt"
    with open(concat_file, "w") as f:
        for v in video_files:
            f.write(f"file '{v}'\n")
    
    cmd = ["ffmpeg", "-f", "concat", "-safe", "0", "-i", concat_file,
           "-c", "copy", "-y", output]
    
    result = subprocess.run(cmd, capture_output=True)
    
    try:
        os.remove(concat_file)
    except:
        pass
    
    if result.returncode == 0:
        log(f"  Success: {output}")
        return output
    else:
        log(f"  Failed")
        return None

def add_captions(input_video, captions, output_video):
    """Add captions with FFmpeg"""
    log(f"Adding {len(captions)} captions...")
    
    filters = []
    for cap in captions:
        text = cap["text"].replace("'", "").replace('"', '')
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
        log(f"  Success: {output_video}")
        return output_video
    return None

def convert_to_shorts(input_video, output_video):
    """Convert to 1080x1920 Shorts format"""
    log("Converting to Shorts format (1080x1920)...")
    
    filter_complex = (
        "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,"
        "crop=1080:1920,boxblur=30:5[bg];"
        "[0:v]scale=1080:-1[fg];"
        "[bg][fg]overlay=(W-w)/2:(H-h)/2"
    )
    
    cmd = ["ffmpeg", "-i", input_video, "-filter_complex", filter_complex,
           "-c:v", "libx264", "-preset", "medium", "-crf", "23",
           "-c:a", "copy", "-y", output_video]
    
    result = subprocess.run(cmd, capture_output=True)
    
    if result.returncode == 0:
        log(f"  Success: {output_video}")
        return output_video
    return None

def main():
    if len(sys.argv) < 3:
        print("Usage: python generate_shorts_final.py <storyboard.json> <output.mp4>")
        sys.exit(1)
    
    storyboard_file = sys.argv[1]
    output_file = sys.argv[2]
    
    log("="*60)
    log("WanGP Shorts Generator (Scene-by-Scene Method)")
    log("="*60)
    log(f"Storyboard: {storyboard_file}")
    log(f"Output: {output_file}")
    log("")
    
    # Load storyboard
    with open(storyboard_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Get scenes
    scenes = data.get('scenes', [])
    if not scenes and 'videos' in data:
        videos = data['videos']
        if videos:
            scenes = videos[0].get('scenes', [])
    
    if not scenes:
        log("ERROR: No scenes in storyboard")
        sys.exit(1)
    
    log(f"Scenes: {len(scenes)}")
    log("")
    
    # Generate each scene
    scene_files = []
    for i, scene in enumerate(scenes, 1):
        prompt = scene.get('prompt', '')
        if not prompt:
            log(f"Scene {i}: No prompt, skipping")
            continue
        
        log(f"Scene {i}/{len(scenes)}:")
        log(f"  {prompt[:60]}...")
        
        video = generate_scene(prompt, max_wait=600)
        
        if video:
            # Copy to permanent location
            safe_path = f"scene_{i}.mp4"
            shutil.copy(video, safe_path)
            scene_files.append(safe_path)
            log(f"  Saved: {safe_path}")
            log("")
        else:
            log(f"  FAILED - Stopping pipeline")
            sys.exit(1)
    
    if not scene_files:
        log("ERROR: No scenes generated")
        sys.exit(1)
    
    log("")
    
    # Concatenate
    base = Path(output_file).stem
    concat_video = f"{base}_concat.mp4"
    if not concatenate_videos(scene_files, concat_video):
        sys.exit(1)
    
    # Captions
    captions = []
    t = 0.0
    for i, scene in enumerate(scenes):
        captions.append({
            "text": scene.get('caption', f'Scene {i+1}'),
            "start": t,
            "end": t + 5.0
        })
        t += 5.0
    
    captioned_video = f"{base}_captioned.mp4"
    if not add_captions(concat_video, captions, captioned_video):
        sys.exit(1)
    
    # Convert to Shorts
    if not convert_to_shorts(captioned_video, output_file):
        sys.exit(1)
    
    # Cleanup
    try:
        for f in scene_files + [concat_video, captioned_video]:
            os.remove(f)
        log("Cleanup complete")
    except:
        pass
    
    log("")
    log("="*60)
    log(f"SUCCESS: {output_file}")
    size_mb = Path(output_file).stat().st_size / (1024*1024)
    log(f"Size: {size_mb:.1f} MB")
    log("="*60)
    
    sys.exit(0)

if __name__ == "__main__":
    main()
