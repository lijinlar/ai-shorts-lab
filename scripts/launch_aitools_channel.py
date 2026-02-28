"""
Launch AI Tools Daily channel - First 4 videos
Using WanGP for generation, youtube_token_finance.json for upload
"""

import sys
import io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import time
import json
import subprocess
from pathlib import Path

wangp_dir = Path(r"C:\Users\lijin\.openclaw\workspace\Wan2GP")
sys.path.insert(0, str(wangp_dir))
from generate_video import generate_video

# Load storyboard
storyboard_path = Path("C:/Users/lijin/Projects/t2v-shorts-lab/storyboards/series_2026-02-17_aitools.json")
data = json.loads(storyboard_path.read_text(encoding='utf-8'))

print("\n" + "="*70)
print("🚀 LAUNCHING AI TOOLS DAILY CHANNEL")
print("="*70)
print(f"Videos to create: {len(data['videos'])}")
print(f"Channel: AI Tools Daily (UChmoxeUgszJP1_iC7nbce9Q)")
print(f"Token: youtube_token_finance.json")
print("="*70 + "\n")

uploaded_videos = []

for video_idx, video_data in enumerate(data["videos"], 1):
    print(f"\n{'='*70}")
    print(f"VIDEO {video_idx}/{len(data['videos'])}: {video_data['title']}")
    print(f"{'='*70}\n")
    
    # Generate scenes
    wangp_outputs = wangp_dir / "outputs"
    temp_dir = Path("C:/Users/lijin/Projects/t2v-shorts-lab/temp") / video_data['slug']
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    scene_files = []
    for i, scene in enumerate(video_data["scenes"], 1):
        print(f"[Scene {i}/{len(video_data['scenes'])}] {scene['caption']}")
        
        result = generate_video(scene["prompt"], output_dir=str(wangp_outputs))
        if not result:
            print(f"ERROR: Scene {i} failed!")
            continue
        
        # Find latest video
        output_files = sorted(wangp_outputs.glob("*.mp4"), key=lambda p: p.stat().st_mtime, reverse=True)
        if not output_files:
            print(f"ERROR: No video found for scene {i}")
            continue
        
        # Copy to temp
        scene_file = temp_dir / f"scene_{i:02d}.mp4"
        scene_file.write_bytes(output_files[0].read_bytes())
        scene_files.append(scene_file)
        output_files[0].unlink()
        
        print(f"✓ Scene {i} saved")
        time.sleep(2)
    
    if len(scene_files) != len(video_data["scenes"]):
        print(f"⚠️ WARNING: Only {len(scene_files)}/{len(video_data['scenes'])} scenes generated")
    
    print(f"\n✓ All {len(scene_files)} scenes generated!")
    
    # Combine scenes
    out_dir = Path("C:/Users/lijin/Projects/t2v-shorts-lab/out/aitools")
    out_dir.mkdir(parents=True, exist_ok=True)
    combined_path = out_dir / f"{video_data['slug']}_combined.mp4"
    
    concat_file = combined_path.parent / f"{video_data['slug']}_concat.txt"
    concat_file.write_text("\n".join([f"file '{f.absolute().as_posix()}'" for f in scene_files]))
    
    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", str(concat_file),
        "-c:v", "libx264", "-crf", "18", "-preset", "fast",
        str(combined_path)
    ], capture_output=True, check=True)
    
    print(f"✓ Combined: {combined_path}")
    
    # Add captions
    captioned_path = out_dir / f"{video_data['slug']}_captioned.mp4"
    scene_duration = 5.0
    filters = []
    
    for i, scene in enumerate(video_data["scenes"]):
        caption = scene["caption"].replace("'", "'\\\\\\''").replace(":", "\\:")
        start = i * scene_duration
        end = start + scene_duration
        
        filters.append(
            f"drawtext=text='{caption}':"
            f"fontfile=/Windows/Fonts/arial.ttf:fontsize=48:fontcolor=white:"
            f"borderw=3:bordercolor=black:"
            f"x=(w-text_w)/2:y=h-th-80:"
            f"enable='between(t,{start},{end})'"
        )
    
    filter_complex = ",".join(filters)
    
    subprocess.run([
        "ffmpeg", "-y", "-i", str(combined_path),
        "-vf", filter_complex,
        "-c:v", "libx264", "-crf", "18", "-preset", "fast",
        "-c:a", "copy",
        str(captioned_path)
    ], capture_output=True, check=True)
    
    print(f"✓ Captions added: {captioned_path}")
    
    # Upload to AI Tools Daily channel (using finance token)
    print(f"\n📤 Uploading to AI Tools Daily...")
    
    upload_result = subprocess.run([
        sys.executable,
        "scripts/youtube_upload.py",
        "--file", str(captioned_path),
        "--title", video_data["title"],
        "--description", video_data["description"],
        "--privacy", "public",
        "--channel", "finance"  # Use youtube_token_finance.json (AI Tools Daily)
    ], capture_output=True, text=True, cwd=Path.cwd())
    
    # Extract URL from output
    url = None
    for line in upload_result.stdout.split('\n'):
        if 'URL:' in line or 'youtube.com/watch' in line:
            url = line.split('URL:')[-1].strip() if 'URL:' in line else line.strip()
            break
    
    if url:
        print(f"✅ UPLOADED: {url}")
        uploaded_videos.append({
            "title": video_data["title"],
            "url": url,
            "slug": video_data["slug"]
        })
    else:
        print(f"⚠️ Upload may have succeeded but couldn't extract URL")
        print(upload_result.stdout)
    
    print(f"\n✓ VIDEO {video_idx} COMPLETE!\n")

print("\n" + "="*70)
print("🎉 AI TOOLS DAILY CHANNEL LAUNCHED!")
print("="*70)
print(f"Videos uploaded: {len(uploaded_videos)}/4")
print("\nURLs:")
for v in uploaded_videos:
    print(f"  • {v['title']}")
    print(f"    {v['url']}\n")

print("Channel: https://www.youtube.com/@AIToolsDaily")
print("="*70)
