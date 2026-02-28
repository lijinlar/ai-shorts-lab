#!/usr/bin/env python3
"""
Simple WanGP Shorts Generator - Scene by Scene Method
Uses the exact approach that worked on Feb 16 - individual scene generation
"""

import sys
import os
import json
import subprocess
import time
import shutil
import glob
from pathlib import Path

# Force UTF-8
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

WAN2GP_DIR = Path(r"C:\Users\lijin\.openclaw\workspace\Wan2GP")
WANGP_PYTHON = WAN2GP_DIR / "venv" / "Scripts" / "python.exe"
WANGP_SCRIPT = WAN2GP_DIR / "wgp.py"
OUTPUTS_DIR = WAN2GP_DIR / "outputs"

def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}")

def clean_outputs():
    """Delete all MP4 files in outputs directory"""
    if OUTPUTS_DIR.exists():
        for f in OUTPUTS_DIR.glob("*.mp4"):
            try:
                f.unlink()
                log(f"Cleaned: {f.name}")
            except Exception as e:
                log(f"Warning: Could not delete {f.name}: {e}")

def wait_for_new_video(timeout=600):
    """
    Wait for a new video to appear in outputs directory
    
    Args:
        timeout: Max seconds to wait
        
    Returns:
        Path to new video or None
    """
    start_time = time.time()
    initial_files = set(OUTPUTS_DIR.glob("*.mp4")) if OUTPUTS_DIR.exists() else set()
    
    log(f"Waiting for video generation (timeout: {timeout}s)...")
    
    while time.time() - start_time < timeout:
        if OUTPUTS_DIR.exists():
            current_files = set(OUTPUTS_DIR.glob("*.mp4"))
            new_files = current_files - initial_files
            
            if new_files:
                # Found a new file
                new_file = list(new_files)[0]
                # Wait a bit to ensure file is fully written
                time.sleep(2)
                log(f"Found new video: {new_file.name}")
                return new_file
        
        time.sleep(2)  # Check every 2 seconds
    
    log("Timeout waiting for video")
    return None

def generate_scene_direct(prompt, scene_num):
    """
    Generate one scene by directly invoking WanGP generation
    Uses the method that worked on Feb 16
    
    Args:
        prompt: Video generation prompt
        scene_num: Scene number
        
    Returns:
        Path to generated video or None
    """
    log(f"="*60)
    log(f"Scene {scene_num}: Starting generation")
    log(f"="*60)
    log(f"Prompt: {prompt[:80]}...")
    
    # Clean outputs directory first
    clean_outputs()
    
    # Create a simple Python script that calls WanGP generation directly
    generate_script = f"""
import sys
sys.path.insert(0, r'{WAN2GP_DIR}')
import wgp

# Generate video with the exact settings that worked
prompt = {repr(prompt)}

# Call WanGP's internal generation function
# This is the approach that worked on Feb 16
try:
    # Generate using WanGP's text2video function
    result = wgp.text2video_generate(
        prompt=prompt,
        width=832,
        height=480,
        num_frames=121,
        fps=24,
        steps=30,
        cfg=7.0,
        seed=-1,
        model='wan2.1',
        profile='default'
    )
    print(f"Generated: {{result}}")
except Exception as e:
    print(f"Error: {{e}}")
    import traceback
    traceback.print_exc()
"""
    
    # Save the generation script
    gen_script_path = "temp_generate.py"
    with open(gen_script_path, "w", encoding="utf-8") as f:
        f.write(generate_script)
    
    # Run the generation script
    cmd = [str(WANGP_PYTHON), gen_script_path]
    
    log("Starting generation process...")
    
    try:
        # Start the process
        process = subprocess.Popen(
            cmd,
            cwd=str(WAN2GP_DIR),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding='utf-8',
            errors='replace'
        )
        
        # Wait for video to appear (with timeout)
        video_path = wait_for_new_video(timeout=600)  # 10 minute timeout
        
        # Terminate the process if it's still running
        if process.poll() is None:
            process.terminate()
            time.sleep(1)
            if process.poll() is None:
                process.kill()
        
        # Clean up
        try:
            os.remove(gen_script_path)
        except:
            pass
        
        if video_path and video_path.exists():
            log(f"SUCCESS: {video_path.name} ({video_path.stat().st_size / (1024*1024):.1f} MB)")
            return video_path
        else:
            log("FAILED: No video file generated")
            return None
            
    except Exception as e:
        log(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return None

def concatenate_videos(video_files, output):
    """Concatenate videos using FFmpeg"""
    log(f"Concatenating {len(video_files)} videos...")
    
    # Create concat list
    concat_file = "concat_list.txt"
    with open(concat_file, "w") as f:
        for video in video_files:
            f.write(f"file '{video}'\n")
    
    cmd = [
        "ffmpeg", "-f", "concat", "-safe", "0",
        "-i", concat_file, "-c", "copy", "-y", output
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    try:
        os.remove(concat_file)
    except:
        pass
    
    if result.returncode == 0:
        log(f"Concatenated: {output}")
        return output
    else:
        log(f"Concat failed: {result.stderr[:200]}")
        return None

def add_captions(input_video, captions, output_video):
    """Add captions using FFmpeg drawtext"""
    log(f"Adding {len(captions)} captions...")
    
    # Build filter
    filters = []
    for cap in captions:
        # Remove problematic characters
        text = cap["text"].replace("'", "").replace('"', '').replace('\\', '')
        filters.append(
            f"drawtext=text='{text}':fontsize=48:fontcolor=white:"
            f"bordercolor=black:borderw=3:x=(w-text_w)/2:y=h-th-80:"
            f"enable='between(t,{cap['start']},{cap['end']})'"
        )
    
    filter_str = ",".join(filters)
    
    cmd = [
        "ffmpeg", "-i", input_video, "-vf", filter_str,
        "-c:v", "libx264", "-preset", "medium", "-crf", "23",
        "-c:a", "copy", "-y", output_video
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        log(f"Captions added: {output_video}")
        return output_video
    else:
        log(f"Caption failed: {result.stderr[:200]}")
        return None

def convert_to_shorts(input_video, output_video):
    """Convert to 1080x1920 Shorts format with blurred background"""
    log("Converting to Shorts format (1080x1920)...")
    
    filter_complex = (
        "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,"
        "crop=1080:1920,boxblur=30:5[bg];"
        "[0:v]scale=1080:-1[fg];"
        "[bg][fg]overlay=(W-w)/2:(H-h)/2"
    )
    
    cmd = [
        "ffmpeg", "-i", input_video, "-filter_complex", filter_complex,
        "-c:v", "libx264", "-preset", "medium", "-crf", "23",
        "-c:a", "copy", "-y", output_video
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        log(f"Shorts format: {output_video}")
        return output_video
    else:
        log(f"Conversion failed: {result.stderr[:200]}")
        return None

def main():
    if len(sys.argv) < 3:
        print("Usage: python generate_shorts_simple.py <storyboard.json> <output.mp4>")
        sys.exit(1)
    
    storyboard_file = sys.argv[1]
    output_file = sys.argv[2]
    
    log("="*60)
    log("WanGP YouTube Shorts Generator (Simple Method)")
    log("="*60)
    log(f"Storyboard: {storyboard_file}")
    log(f"Output: {output_file}")
    
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
    
    log(f"Total scenes: {len(scenes)}")
    log("")
    
    # Generate each scene
    scene_files = []
    for i, scene in enumerate(scenes, 1):
        prompt = scene.get('prompt', '')
        if not prompt:
            log(f"Scene {i}: No prompt, skipping")
            continue
        
        video = generate_scene_direct(prompt, i)
        
        if video:
            # Copy to permanent location
            safe_path = f"scene_{i}.mp4"
            shutil.copy(video, safe_path)
            scene_files.append(safe_path)
            log("")
        else:
            log(f"Scene {i}: FAILED")
            log("Stopping pipeline")
            sys.exit(1)
    
    if not scene_files:
        log("ERROR: No scenes generated")
        sys.exit(1)
    
    # Concatenate scenes
    base = Path(output_file).stem
    concat_video = f"{base}_concat.mp4"
    if not concatenate_videos(scene_files, concat_video):
        sys.exit(1)
    
    # Add captions
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
    
    # Convert to Shorts format
    if not convert_to_shorts(captioned_video, output_file):
        sys.exit(1)
    
    # Cleanup intermediate files
    try:
        for f in scene_files + [concat_video, captioned_video]:
            os.remove(f)
        log("Cleanup complete")
    except:
        pass
    
    log("")
    log("="*60)
    log(f"SUCCESS: {output_file}")
    log(f"File size: {Path(output_file).stat().st_size / (1024*1024):.1f} MB")
    log("="*60)
    
    sys.exit(0)

if __name__ == "__main__":
    main()
