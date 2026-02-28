"""
WanGP Integration for YouTube Shorts Pipeline
Generates videos from storyboard using WanGP, adds captions, converts to Shorts format
"""

import sys
import os
import json
import time
import subprocess
import shutil
import glob
from pathlib import Path

# Add Wan2GP to path
from config_loader import get_wangp_dir
WAN2GP_DIR = get_wangp_dir()
sys.path.insert(0, str(WAN2GP_DIR))

def clean_outputs_directory():
    """Clean WanGP outputs directory to prevent picking up old files"""
    outputs_dir = WAN2GP_DIR / "outputs"
    if outputs_dir.exists():
        for file in outputs_dir.glob("*.mp4"):
            try:
                file.unlink()
                print(f"[CLEAN] Deleted old file: {file.name}")
            except Exception as e:
                print(f"[WARN] Could not delete {file.name}: {e}")

def generate_scene_with_wangp(prompt, scene_num, max_retries=2):
    """
    Generate a single scene using WanGP
    
    Args:
        prompt: Ultra-detailed prompt for the scene
        scene_num: Scene number for naming
        max_retries: Number of retry attempts
        
    Returns:
        Path to generated video file or None
    """
    print(f"\n{'='*70}")
    print(f"GENERATING SCENE {scene_num}")
    print(f"{'='*70}")
    print(f"Prompt: {prompt[:100]}...")
    
    # Clean outputs directory before generating
    clean_outputs_directory()
    
    # Import generate_video from WanGP
    from generate_video import generate_video
    
    for attempt in range(max_retries):
        try:
            print(f"\n[ATTEMPT {attempt + 1}/{max_retries}]")
            
            # Generate video
            result = generate_video(prompt)
            
            if result:
                # Find the generated video file
                outputs_dir = WAN2GP_DIR / "outputs"
                video_files = list(outputs_dir.glob("*.mp4"))
                
                if video_files:
                    # Get the most recent file
                    latest_video = max(video_files, key=lambda p: p.stat().st_mtime)
                    print(f"[SUCCESS] Generated: {latest_video}")
                    return latest_video
                else:
                    print(f"[ERROR] No video file found in outputs/")
            else:
                print(f"[ERROR] Generation failed")
                
        except Exception as e:
            print(f"[ERROR] Attempt {attempt + 1} failed: {e}")
            import traceback
            traceback.print_exc()
        
        if attempt < max_retries - 1:
            print(f"[RETRY] Waiting 5 seconds before retry...")
            time.sleep(5)
    
    print(f"[FAIL] All attempts failed for scene {scene_num}")
    return None

def concatenate_scenes(scene_files, output_file):
    """
    Concatenate multiple scene videos into one
    
    Args:
        scene_files: List of video file paths
        output_file: Output file path
    """
    print(f"\n{'='*70}")
    print(f"CONCATENATING {len(scene_files)} SCENES")
    print(f"{'='*70}")
    
    # Create a concat file for FFmpeg
    concat_file = "concat_list.txt"
    with open(concat_file, "w") as f:
        for scene_file in scene_files:
            f.write(f"file '{scene_file}'\n")
    
    # Run FFmpeg concat
    cmd = [
        "ffmpeg",
        "-f", "concat",
        "-safe", "0",
        "-i", concat_file,
        "-c", "copy",
        "-y",
        output_file
    ]
    
    print(f"[CMD] {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        print(f"[SUCCESS] Concatenated video: {output_file}")
        os.remove(concat_file)
        return output_file
    else:
        print(f"[ERROR] Concatenation failed")
        print(result.stderr)
        return None

def add_captions_to_video(input_video, captions, output_video):
    """
    Add text captions to video using FFmpeg drawtext filter
    
    Args:
        input_video: Input video path
        captions: List of {"text": "...", "start": 0.0, "end": 5.0}
        output_video: Output video path
    """
    print(f"\n{'='*70}")
    print(f"ADDING CAPTIONS")
    print(f"{'='*70}")
    
    # Build FFmpeg drawtext filter chain
    filter_parts = []
    for cap in captions:
        # Escape single quotes in text
        text = cap["text"].replace("'", "'\\\\\\''")
        start = cap["start"]
        end = cap["end"]
        
        filter_parts.append(
            f"drawtext=text='{text}':"
            f"fontsize=48:"
            f"fontcolor=white:"
            f"bordercolor=black:"
            f"borderw=3:"
            f"x=(w-text_w)/2:"
            f"y=h-th-80:"
            f"enable='between(t,{start},{end})'"
        )
    
    filter_complex = ",".join(filter_parts)
    
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
    
    print(f"[CMD] Adding {len(captions)} captions...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        print(f"[SUCCESS] Captions added: {output_video}")
        return output_video
    else:
        print(f"[ERROR] Caption failed")
        print(result.stderr[:500])
        return None

def convert_to_shorts_format(input_video, output_video):
    """
    Convert horizontal video to vertical YouTube Shorts format (1080x1920)
    with TikTok-style blurred background
    
    Args:
        input_video: Input video path
        output_video: Output video path
    """
    print(f"\n{'='*70}")
    print(f"CONVERTING TO SHORTS FORMAT")
    print(f"{'='*70}")
    
    # TikTok-style: blur+crop background, overlay original centered
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
    
    print(f"[CMD] Converting to 1080x1920 Shorts format...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        print(f"[SUCCESS] Shorts format: {output_video}")
        # Verify dimensions
        probe_cmd = [
            "ffprobe", "-v", "error",
            "-select_streams", "v:0",
            "-show_entries", "stream=width,height",
            "-of", "csv=s=x:p=0",
            output_video
        ]
        result = subprocess.run(probe_cmd, capture_output=True, text=True)
        dimensions = result.stdout.strip()
        print(f"[VERIFY] Dimensions: {dimensions}")
        return output_video
    else:
        print(f"[ERROR] Conversion failed")
        print(result.stderr[:500])
        return None

def generate_full_video_from_storyboard(storyboard_file, output_file):
    """
    Main pipeline: Generate full video from storyboard JSON
    
    Args:
        storyboard_file: Path to storyboard JSON file
        output_file: Final output video path
        
    Returns:
        Path to final Shorts-ready video
    """
    print(f"\n{'='*70}")
    print(f"WANGP YOUTUBE SHORTS GENERATION PIPELINE")
    print(f"{'='*70}")
    print(f"Storyboard: {storyboard_file}")
    print(f"Output: {output_file}")
    
    # Load storyboard
    with open(storyboard_file, 'r', encoding='utf-8') as f:
        storyboard = json.load(f)
    
    # Get scenes from the storyboard structure
    # The storyboard can have scenes directly or in a nested structure
    scenes = storyboard.get('scenes', [])
    
    # If no scenes at top level, check if it's a single-video storyboard
    if not scenes and 'videos' in storyboard:
        videos = storyboard['videos']
        if videos and len(videos) > 0:
            # Get scenes from first video
            scenes = videos[0].get('scenes', [])
    
    print(f"\n[INFO] Loaded {len(scenes)} scenes")
    
    # Generate each scene
    scene_files = []
    for i, scene in enumerate(scenes, 1):
        prompt = scene.get('prompt', '')
        
        if not prompt:
            print(f"[WARN] Scene {i} has no prompt, skipping")
            continue
        
        video_path = generate_scene_with_wangp(prompt, i)
        
        if video_path:
            scene_files.append(str(video_path))
        else:
            print(f"[ERROR] Failed to generate scene {i}")
            return None
    
    if not scene_files:
        print("[ERROR] No scenes were generated successfully")
        return None
    
    # Concatenate all scenes
    base_name = Path(output_file).stem
    concatenated_video = f"{base_name}_concatenated.mp4"
    
    if not concatenate_scenes(scene_files, concatenated_video):
        return None
    
    # Add captions
    captions = []
    cumulative_time = 0.0
    scene_duration = 5.0  # Each scene is 5 seconds
    
    for i, scene in enumerate(scenes):
        caption_text = scene.get('caption', f'Scene {i+1}')
        captions.append({
            "text": caption_text,
            "start": cumulative_time,
            "end": cumulative_time + scene_duration
        })
        cumulative_time += scene_duration
    
    captioned_video = f"{base_name}_captioned.mp4"
    if not add_captions_to_video(concatenated_video, captions, captioned_video):
        return None
    
    # Convert to Shorts format
    if not convert_to_shorts_format(captioned_video, output_file):
        return None
    
    # Cleanup intermediate files
    try:
        os.remove(concatenated_video)
        os.remove(captioned_video)
        print("[CLEANUP] Removed intermediate files")
    except:
        pass
    
    print(f"\n{'='*70}")
    print(f"✓ PIPELINE COMPLETE")
    print(f"{'='*70}")
    print(f"Final video: {output_file}")
    
    return output_file


if __name__ == "__main__":
    # Fix Windows console encoding
    if sys.platform == 'win32':
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    
    if len(sys.argv) < 3:
        print("Usage: python generate_with_wangp.py <storyboard.json> <output.mp4>")
        sys.exit(1)
    
    storyboard_file = sys.argv[1]
    output_file = sys.argv[2]
    
    result = generate_full_video_from_storyboard(storyboard_file, output_file)
    
    if result:
        print(f"\nSUCCESS! Video ready for upload: {result}")
        sys.exit(0)
    else:
        print(f"\nFAILED to generate video")
        sys.exit(1)
