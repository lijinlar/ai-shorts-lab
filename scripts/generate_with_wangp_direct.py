"""
WanGP Direct Integration for YouTube Shorts
Generates videos by calling WanGP server API (Gradio interface)
This avoids the problematic --process batch mode
"""

import sys
import os
import json
import time
import subprocess
from pathlib import Path
import shutil
import glob

# Force UTF-8 on Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from config_loader import get_wangp_dir
WAN2GP_DIR = get_wangp_dir()
OUTPUTS_DIR = WAN2GP_DIR / "outputs"

def ensure_wangp_server_running():
    """Check if WanGP server is running, start if needed"""
    import requests
    
    try:
        response = requests.get("http://localhost:7860", timeout=2)
        if response.status_code == 200:
            print("[INFO] WanGP server already running")
            return True
    except:
        pass
    
    print("[INFO] Starting WanGP server...")
    
    # Start server in background
    wangp_python = WAN2GP_DIR / "venv" / "Scripts" / "python.exe"
    cmd = [
        str(wangp_python),
        str(WAN2GP_DIR / "wgp.py"),
        "--profile", "1"
    ]
    
    process = subprocess.Popen(
        cmd,
        cwd=str(WAN2GP_DIR),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    
    # Wait for server to start (max 60 seconds)
    for i in range(60):
        time.sleep(1)
        try:
            response = requests.get("http://localhost:7860", timeout=1)
            if response.status_code == 200:
                print("[INFO] WanGP server started successfully")
                return True
        except:
            pass
    
    print("[ERROR] Failed to start WanGP server")
    return False


def clean_outputs_directory():
    """Clean WanGP outputs directory"""
    if OUTPUTS_DIR.exists():
        for file in OUTPUTS_DIR.glob("*.mp4"):
            try:
                file.unlink()
                print(f"[CLEAN] Deleted: {file.name}")
            except Exception as e:
                print(f"[WARN] Could not delete {file.name}: {e}")


def generate_scene_via_api(prompt, scene_num):
    """
    Generate a single scene using WanGP Gradio API
    
    Args:
        prompt: Video generation prompt
        scene_num: Scene number for logging
        
    Returns:
        Path to generated video or None
    """
    from gradio_client import Client
    
    print(f"\n{'='*70}")
    print(f"GENERATING SCENE {scene_num}")
    print(f"{'='*70}")
    print(f"Prompt: {prompt[:100]}...")
    
    # Clean outputs before generating
    clean_outputs_directory()
    
    try:
        client = Client("http://localhost:7860")
        
        # Call the generate function
        # API parameters from earlier testing
        result = client.predict(
            prompt=prompt,  # Main prompt
            api_name="/generate"  # Check actual API name
        )
        
        # Find generated video
        video_files = list(OUTPUTS_DIR.glob("*.mp4"))
        if video_files:
            latest = max(video_files, key=lambda p: p.stat().st_mtime)
            print(f"[SUCCESS] Generated: {latest.name}")
            return latest
        else:
            print(f"[ERROR] No output file found")
            return None
            
    except Exception as e:
        print(f"[ERROR] Generation failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def concatenate_scenes(scene_files, output_file):
    """Concatenate multiple videos"""
    print(f"\n{'='*70}")
    print(f"CONCATENATING {len(scene_files)} SCENES")
    print(f"{'='*70}")
    
    # Create concat list
    concat_file = "concat_list.txt"
    with open(concat_file, "w") as f:
        for scene in scene_files:
            f.write(f"file '{scene}'\n")
    
    cmd = [
        "ffmpeg",
        "-f", "concat",
        "-safe", "0",
        "-i", concat_file,
        "-c", "copy",
        "-y",
        output_file
    ]
    
    result = subprocess.run(cmd, capture_output=True)
    
    if result.returncode == 0:
        print(f"[SUCCESS] Concatenated: {output_file}")
        os.remove(concat_file)
        return output_file
    else:
        print(f"[ERROR] FFmpeg concat failed")
        return None


def add_captions(input_video, captions, output_video):
    """Add text captions using FFmpeg"""
    print(f"\n{'='*70}")
    print(f"ADDING {len(captions)} CAPTIONS")
    print(f"{'='*70}")
    
    # Build filter
    filters = []
    for cap in captions:
        text = cap["text"].replace("'", "'\\\\\\''")
        filters.append(
            f"drawtext=text='{text}':"
            f"fontsize=48:fontcolor=white:bordercolor=black:borderw=3:"
            f"x=(w-text_w)/2:y=h-th-80:"
            f"enable='between(t,{cap['start']},{cap['end']})'"
        )
    
    filter_complex = ",".join(filters)
    
    cmd = [
        "ffmpeg",
        "-i", input_video,
        "-vf", filter_complex,
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "23",
        "-c:a", "copy",
        "-y",
        output_video
    ]
    
    result = subprocess.run(cmd, capture_output=True)
    
    if result.returncode == 0:
        print(f"[SUCCESS] Captions added: {output_video}")
        return output_video
    else:
        print(f"[ERROR] Caption failed")
        return None


def convert_to_shorts(input_video, output_video):
    """Convert to 1080x1920 Shorts format with blurred background"""
    print(f"\n{'='*70}")
    print(f"CONVERTING TO SHORTS FORMAT (1080x1920)")
    print(f"{'='*70}")
    
    filter_complex = (
        "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,"
        "crop=1080:1920,"
        "boxblur=30:5[bg];"
        "[0:v]scale=1080:-1[fg];"
        "[bg][fg]overlay=(W-w)/2:(H-h)/2"
    )
    
    cmd = [
        "ffmpeg",
        "-i", input_video,
        "-filter_complex", filter_complex,
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "23",
        "-c:a", "copy",
        "-y",
        output_video
    ]
    
    result = subprocess.run(cmd, capture_output=True)
    
    if result.returncode == 0:
        print(f"[SUCCESS] Shorts format: {output_video}")
        return output_video
    else:
        print(f"[ERROR] Conversion failed")
        return None


def main():
    if len(sys.argv) < 3:
        print("Usage: python generate_with_wangp_direct.py <storyboard.json> <output.mp4>")
        sys.exit(1)
    
    storyboard_file = sys.argv[1]
    output_file = sys.argv[2]
    
    print(f"\n{'='*70}")
    print(f"WANGP YOUTUBE SHORTS PIPELINE (DIRECT API)")
    print(f"{'='*70}")
    print(f"Storyboard: {storyboard_file}")
    print(f"Output: {output_file}")
    print(f"{'='*70}\n")
    
    # Load storyboard
    with open(storyboard_file, 'r', encoding='utf-8') as f:
        storyboard = json.load(f)
    
    # Get scenes
    scenes = storyboard.get('scenes', [])
    if not scenes and 'videos' in storyboard:
        videos = storyboard['videos']
        if videos:
            scenes = videos[0].get('scenes', [])
    
    if not scenes:
        print("[ERROR] No scenes in storyboard")
        sys.exit(1)
    
    print(f"[INFO] Loaded {len(scenes)} scenes\n")
    
    # Ensure server is running
    if not ensure_wangp_server_running():
        print("[ERROR] Could not start WanGP server")
        sys.exit(1)
    
    # Generate each scene
    scene_files = []
    for i, scene in enumerate(scenes, 1):
        prompt = scene.get('prompt', '')
        if not prompt:
            print(f"[WARN] Scene {i} has no prompt")
            continue
        
        video_path = generate_scene_via_api(prompt, i)
        if video_path:
            # Copy to permanent location
            permanent_path = f"scene_{i}.mp4"
            shutil.copy(video_path, permanent_path)
            scene_files.append(permanent_path)
        else:
            print(f"[ERROR] Scene {i} failed")
            sys.exit(1)
    
    if not scene_files:
        print("[ERROR] No scenes generated")
        sys.exit(1)
    
    # Concatenate
    base = Path(output_file).stem
    concat_video = f"{base}_concat.mp4"
    if not concatenate_scenes(scene_files, concat_video):
        sys.exit(1)
    
    # Captions
    captions = []
    time_offset = 0.0
    for i, scene in enumerate(scenes):
        captions.append({
            "text": scene.get('caption', f'Scene {i+1}'),
            "start": time_offset,
            "end": time_offset + 5.0
        })
        time_offset += 5.0
    
    caption_video = f"{base}_captions.mp4"
    if not add_captions(concat_video, captions, caption_video):
        sys.exit(1)
    
    # Convert to Shorts
    if not convert_to_shorts(caption_video, output_file):
        sys.exit(1)
    
    # Cleanup
    try:
        for f in scene_files + [concat_video, caption_video]:
            os.remove(f)
    except:
        pass
    
    print(f"\n{'='*70}")
    print(f"SUCCESS! Video ready: {output_file}")
    print(f"{'='*70}\n")
    
    sys.exit(0)


if __name__ == "__main__":
    main()
