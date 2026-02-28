#!/usr/bin/env python3
"""
WanGP Auto-Processor
Monitors WanGP outputs folder and automatically processes new videos
Semi-automated: You generate via UI, this handles the rest
"""

import sys
import os
import time
import shutil
import subprocess
from pathlib import Path
from datetime import datetime

# UTF-8
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.detach(), encoding='utf-8', errors='replace', line_buffering=True)

from config_loader import get_wangp_dir
WAN2GP_OUTPUTS = get_wangp_dir() / "outputs"
PROCESSED_DIR = Path("out/processed_scenes")
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def get_new_videos():
    """Find videos that haven't been processed yet"""
    if not WAN2GP_OUTPUTS.exists():
        return []
    
    all_videos = list(WAN2GP_OUTPUTS.glob("*.mp4"))
    processed_marker = PROCESSED_DIR / ".processed_list.txt"
    
    # Load list of processed videos
    processed = set()
    if processed_marker.exists():
        processed = set(processed_marker.read_text().splitlines())
    
    # Find new ones
    new_videos = [v for v in all_videos if v.name not in processed]
    return new_videos

def mark_as_processed(video_name):
    """Mark a video as processed"""
    marker = PROCESSED_DIR / ".processed_list.txt"
    with open(marker, "a") as f:
        f.write(f"{video_name}\n")

def process_video(video_path, scene_num):
    """
    Copy and rename video for processing
    
    Args:
        video_path: Source video
        scene_num: Scene number
        
    Returns:
        Path to processed scene or None
    """
    output_path = PROCESSED_DIR / f"scene_{scene_num:02d}.mp4"
    
    try:
        shutil.copy(video_path, output_path)
        log(f"  Scene {scene_num}: Saved as {output_path.name}")
        return output_path
    except Exception as e:
        log(f"  Scene {scene_num}: ERROR - {e}")
        return None

def main():
    log("="*60)
    log("WanGP Auto-Processor - Monitoring Mode")
    log("="*60)
    log(f"Watching: {WAN2GP_OUTPUTS}")
    log(f"Output: {PROCESSED_DIR}")
    log("")
    log("Instructions:")
    log("1. Open http://localhost:7860")
    log("2. Generate scenes one by one")
    log("3. This script will auto-process them")
    log("4. Press Ctrl+C when done")
    log("")
    
    scene_counter = 1
    processed_videos = []
    
    try:
        while True:
            new_videos = get_new_videos()
            
            if new_videos:
                for video in new_videos:
                    log(f"New video detected: {video.name}")
                    
                    # Wait a moment for file to finish writing
                    time.sleep(2)
                    
                    # Process it
                    processed = process_video(video, scene_counter)
                    
                    if processed:
                        processed_videos.append(processed)
                        mark_as_processed(video.name)
                        scene_counter += 1
                        log(f"  Total scenes processed: {len(processed_videos)}")
                    
                    log("")
            
            time.sleep(3)  # Check every 3 seconds
            
    except KeyboardInterrupt:
        log("")
        log("="*60)
        log(f"Stopped - {len(processed_videos)} scenes processed")
        log("="*60)
        
        if processed_videos:
            log("\nProcessed scenes:")
            for i, scene in enumerate(processed_videos, 1):
                log(f"  {i}. {scene.name}")
            
            log(f"\nTo combine into Shorts:")
            log(f"python scripts/combine_and_upload.py")
        else:
            log("\nNo scenes were processed")
        
        return 0

if __name__ == "__main__":
    sys.exit(main())
