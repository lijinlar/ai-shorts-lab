"""
Generate remaining 2 videos for Feb 17 using WanGP
Video 3: Pregnant rescue dog
Video 4: 15-year shelter dog
"""

import sys
import io

# Force UTF-8 output on Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import time
import json
import subprocess
from pathlib import Path

# Add WanGP to path
wangp_dir = Path(r"C:\Users\lijin\.openclaw\workspace\Wan2GP")
sys.path.insert(0, str(wangp_dir))

# Import WanGP video generation
from generate_video import generate_video

def generate_video_from_scenes(video_data, output_name):
    """Generate a complete video from scene prompts"""
    
    scenes = video_data["scenes"]
    title = video_data["title"]
    
    print(f"\n{'='*70}")
    print(f"Generating: {title}")
    print(f"Scenes: {len(scenes)}")
    print(f"{'='*70}\n")
    
    # WanGP outputs directory
    wangp_outputs = wangp_dir / "outputs"
    
    # Temp directory for this video's scenes
    temp_dir = Path("C:/Users/lijin/Projects/t2v-shorts-lab/temp") / output_name
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    scene_files = []
    
    for i, scene in enumerate(scenes, 1):
        prompt = scene["prompt"]
        caption = scene["caption"]
        
        print(f"\n[Scene {i}/{len(scenes)}]")
        print(f"Prompt: {prompt[:80]}...")
        print(f"Caption: {caption}")
        
        # Generate video using WanGP
        print("Generating with WanGP...")
        result = generate_video(prompt, output_dir=str(wangp_outputs))
        
        if not result:
            print(f"ERROR: Scene {i} generation failed!")
            return None
        
        # Find the generated video (latest file in outputs)
        # WanGP saves to outputs/ with timestamp
        output_files = sorted(wangp_outputs.glob("*.mp4"), key=lambda p: p.stat().st_mtime, reverse=True)
        
        if not output_files:
            print(f"ERROR: No video file found for scene {i}")
            return None
        
        latest_video = output_files[0]
        
        # Copy to temp with scene number
        scene_file = temp_dir / f"scene_{i:02d}.mp4"
        scene_file.write_bytes(latest_video.read_bytes())
        scene_files.append(scene_file)
        
        print(f"✓ Scene {i} saved: {scene_file.name}")
        
        # Clean up WanGP output to avoid picking wrong file next time
        latest_video.unlink()
        
        # Small delay between scenes
        time.sleep(2)
    
    print(f"\n✓ All {len(scenes)} scenes generated!")
    return scene_files


def combine_scenes(scene_files, output_path):
    """Combine scene files into one video using FFmpeg"""
    
    print(f"\nCombining {len(scene_files)} scenes...")
    
    # Create concat file
    concat_file = output_path.parent / f"{output_path.stem}_concat.txt"
    concat_file.write_text("\n".join([f"file '{f.absolute().as_posix()}'" for f in scene_files]))
    
    # FFmpeg concat
    cmd = [
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(concat_file),
        "-c:v", "libx264",
        "-crf", "18",
        "-preset", "fast",
        str(output_path)
    ]
    
    subprocess.run(cmd, capture_output=True, check=True)
    
    if output_path.exists():
        print(f"✓ Combined video: {output_path}")
        return output_path
    else:
        print("ERROR: Failed to combine scenes")
        return None


def add_captions_to_video(video_path, scenes_data, output_path):
    """Add captions using FFmpeg drawtext"""
    
    print("\nAdding captions...")
    
    # Each scene is 5 seconds (WanGP default 121 frames @ 24fps ≈ 5s)
    scene_duration = 5.0
    
    # Build filter complex for all captions
    filters = []
    for i, scene in enumerate(scenes_data):
        caption = scene["caption"]
        start_time = i * scene_duration
        end_time = start_time + scene_duration
        
        # Escape special characters for FFmpeg
        caption_escaped = caption.replace("'", "'\\\\\\''").replace(":", "\\:")
        
        filters.append(
            f"drawtext=text='{caption_escaped}':"
            f"fontfile=/Windows/Fonts/arial.ttf:fontsize=48:fontcolor=white:"
            f"borderw=3:bordercolor=black:"
            f"x=(w-text_w)/2:y=h-th-80:"
            f"enable='between(t,{start_time},{end_time})'"
        )
    
    filter_complex = ",".join(filters)
    
    cmd = [
        "ffmpeg", "-y",
        "-i", str(video_path),
        "-vf", filter_complex,
        "-c:v", "libx264",
        "-crf", "18",
        "-preset", "fast",
        "-c:a", "copy",
        str(output_path)
    ]
    
    subprocess.run(cmd, capture_output=True, check=True)
    
    if output_path.exists():
        print(f"✓ Captions added: {output_path}")
        return output_path
    else:
        print("ERROR: Failed to add captions")
        return None


def convert_to_shorts_format(video_path, output_path):
    """Convert to 1080x1920 Shorts format with blurred background"""
    
    print("\nConverting to Shorts format (1080x1920)...")
    
    # Scale original to 1080 width, blur and crop background for top/bottom
    filter_complex = (
        "[0:v]scale=1080:-1,setsar=1[main];"
        "[0:v]scale=1080:-1,boxblur=20[bg];"
        "[bg]crop=1080:1920[bgcrop];"
        "[bgcrop][main]overlay=(W-w)/2:(H-h)/2"
    )
    
    cmd = [
        "ffmpeg", "-y",
        "-i", str(video_path),
        "-filter_complex", filter_complex,
        "-c:v", "libx264",
        "-crf", "18",
        "-preset", "fast",
        "-c:a", "copy",
        str(output_path)
    ]
    
    subprocess.run(cmd, capture_output=True, check=True)
    
    if output_path.exists():
        print(f"✓ Shorts format: {output_path}")
        return output_path
    else:
        print("ERROR: Failed to convert to Shorts format")
        return None


if __name__ == "__main__":
    # Load storyboard
    storyboard_path = Path("C:/Users/lijin/Projects/t2v-shorts-lab/storyboards/series_2026-02-17_dogs_emotional_DATADRIVEN.json")
    data = json.loads(storyboard_path.read_text(encoding='utf-8'))
    
    # Videos 3 and 4 (index 2 and 3)
    videos_to_generate = [
        (data["videos"][2], "abandoned-pregnant-dog"),
        (data["videos"][3], "senior-dog-adopted")
    ]
    
    out_dir = Path("C:/Users/lijin/Projects/t2v-shorts-lab/out")
    out_dir.mkdir(parents=True, exist_ok=True)
    
    results = []
    
    for video_data, slug in videos_to_generate:
        print(f"\n{'='*70}")
        print(f"VIDEO: {slug}")
        print(f"{'='*70}")
        
        # Step 1: Generate scenes
        scene_files = generate_video_from_scenes(video_data, slug)
        if not scene_files:
            print(f"✗ FAILED: {slug}")
            continue
        
        # Step 2: Combine scenes
        combined_path = out_dir / f"{slug}_combined.mp4"
        if not combine_scenes(scene_files, combined_path):
            print(f"✗ FAILED: {slug}")
            continue
        
        # Step 3: Add captions
        captioned_path = out_dir / f"{slug}_captioned.mp4"
        if not add_captions_to_video(combined_path, video_data["scenes"], captioned_path):
            print(f"✗ FAILED: {slug}")
            continue
        
        # Step 4: Convert to Shorts format
        final_path = out_dir / f"{slug}_FINAL_SHORTS.mp4"
        if not convert_to_shorts_format(captioned_path, final_path):
            print(f"✗ FAILED: {slug}")
            continue
        
        results.append({
            "slug": slug,
            "title": video_data["title"],
            "file": final_path
        })
        
        print(f"\n✓ COMPLETE: {slug}")
        print(f"   Final file: {final_path}")
    
    print(f"\n{'='*70}")
    print("SUMMARY")
    print(f"{'='*70}")
    print(f"Successful: {len(results)}/{len(videos_to_generate)}")
    
    for r in results:
        print(f"\n{r['title']}")
        print(f"  File: {r['file']}")
    
    if len(results) == len(videos_to_generate):
        print("\n✓ All videos ready for upload!")
        print("\nUpload with:")
        for r in results:
            print(f"\npython scripts/youtube_upload.py \\")
            print(f"  --file \"{r['file']}\" \\")
            print(f"  --title \"{r['title']}\" \\")
            print(f"  --description \"...\" \\")
            print(f"  --privacy public")
