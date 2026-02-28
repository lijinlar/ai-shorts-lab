#!/usr/bin/env python3
"""
Combine Processed Scenes into YouTube Short
Takes processed scenes from auto_process_wangp.py and creates final video
"""

import sys
import os
import json
import subprocess
from pathlib import Path
from datetime import datetime

# UTF-8
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.detach(), encoding='utf-8', errors='replace', line_buffering=True)

PROCESSED_DIR = Path("out/processed_scenes")

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def get_processed_scenes():
    """Get all processed scene files"""
    if not PROCESSED_DIR.exists():
        return []
    
    scenes = sorted(PROCESSED_DIR.glob("scene_*.mp4"))
    return scenes

def concatenate(scenes, output):
    """Concatenate videos"""
    log(f"Concatenating {len(scenes)} scenes...")
    
    concat_file = "concat_list.txt"
    with open(concat_file, "w") as f:
        for scene in scenes:
            f.write(f"file '{scene.absolute()}'\n")
    
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
    """Add captions"""
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
    """Convert to 1080x1920"""
    log("Converting to Shorts format...")
    
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
    log("="*60)
    log("Combine & Upload YouTube Short")
    log("="*60)
    
    # Get processed scenes
    scenes = get_processed_scenes()
    
    if not scenes:
        log("ERROR: No processed scenes found")
        log(f"Expected location: {PROCESSED_DIR}")
        return 1
    
    log(f"Found {len(scenes)} scenes:")
    for scene in scenes:
        size_mb = scene.stat().st_size / (1024*1024)
        log(f"  - {scene.name} ({size_mb:.1f} MB)")
    
    log("")
    
    # Concatenate
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    concat_video = f"out/video_{timestamp}_concat.mp4"
    if not concatenate(scenes, concat_video):
        return 1
    
    # Captions (simple for now - one per scene)
    captions = []
    t = 0.0
    for i in range(len(scenes)):
        captions.append({
            "text": f"Scene {i+1}",
            "start": t,
            "end": t + 5.0
        })
        t += 5.0
    
    captioned_video = f"out/video_{timestamp}_captioned.mp4"
    if not add_captions(concat_video, captions, captioned_video):
        return 1
    
    # Convert to Shorts
    final_video = f"out/video_{timestamp}_FINAL.mp4"
    if not convert_to_shorts(captioned_video, final_video):
        return 1
    
    # Cleanup intermediate files
    try:
        os.remove(concat_video)
        os.remove(captioned_video)
    except:
        pass
    
    log("")
    log("="*60)
    log(f"SUCCESS: {final_video}")
    size_mb = Path(final_video).stat().st_size / (1024*1024)
    log(f"Size: {size_mb:.1f} MB")
    log("="*60)
    log("")
    log("To upload to YouTube:")
    log(f'python scripts/youtube_upload.py --file "{final_video}" --title "..." --description "..." --keywords "shorts" --privacyStatus public')
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
