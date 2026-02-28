"""
Launch ALL 3 new channels - 12 videos total
- AI Tools Daily: 4 videos
- Finance Freedom: 4 videos  
- Sleep Sounds Haven: 4 videos
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

from config_loader import get_wangp_dir, get_project_root
ROOT = get_project_root()
wangp_dir = get_wangp_dir()
sys.path.insert(0, str(wangp_dir))
from generate_video import generate_video

# Channel configurations
CHANNELS = [
    {
        'name': 'AI Tools Daily',
        'token': 'aitools',
        'storyboard': 'storyboards/series_2026-02-17_aitools.json',
        'output_dir': 'out/aitools'
    },
    {
        'name': 'Finance Freedom',
        'token': 'finance',
        'storyboard': 'storyboards/series_2026-02-17_finance.json',
        'output_dir': 'out/finance'
    },
    {
        'name': 'Sleep Sounds Haven',
        'token': 'sleepsounds',
        'storyboard': 'storyboards/series_2026-02-17_sleepsounds.json',
        'output_dir': 'out/sleepsounds'
    }
]

def generate_and_upload_video(video_data, channel_token, output_dir):
    """Generate one video and upload to specified channel"""
    
    print(f"\n{'='*70}")
    print(f"VIDEO: {video_data['title']}")
    print(f"{'='*70}\n")
    
    # Generate scenes
    wangp_outputs = wangp_dir / "outputs"
    temp_dir = ROOT / "temp" / video_data['slug']
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    scene_files = []
    for i, scene in enumerate(video_data["scenes"], 1):
        print(f"[Scene {i}/{len(video_data['scenes'])}] {scene['caption']}")
        
        result = generate_video(scene["prompt"], output_dir=str(wangp_outputs))
        if not result:
            print(f"ERROR: Scene {i} failed!")
            continue
        
        output_files = sorted(wangp_outputs.glob("*.mp4"), key=lambda p: p.stat().st_mtime, reverse=True)
        if not output_files:
            print(f"ERROR: No video found for scene {i}")
            continue
        
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
    out_dir = Path(output_dir)
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
    
    # Upload
    print(f"\n📤 Uploading...")
    
    upload_result = subprocess.run([
        sys.executable,
        "scripts/youtube_upload.py",
        "--file", str(captioned_path),
        "--title", video_data["title"],
        "--description", video_data["description"],
        "--privacy", "public",
        "--channel", channel_token
    ], capture_output=True, text=True, cwd=Path.cwd())
    
    url = None
    for line in upload_result.stdout.split('\n'):
        if 'URL:' in line or 'youtube.com/watch' in line:
            url = line.split('URL:')[-1].strip() if 'URL:' in line else line.strip()
            break
    
    if url:
        print(f"✅ UPLOADED: {url}")
        return {
            "title": video_data["title"],
            "url": url,
            "slug": video_data["slug"]
        }
    else:
        print(f"⚠️ Upload may have succeeded but couldn't extract URL")
        return None

# Main execution
print("\n" + "="*70)
print("🚀 LAUNCHING 3 NEW YOUTUBE CHANNELS")
print("="*70)
print("Total videos to generate: 12")
print("Estimated time: 2-3 hours")
print("="*70 + "\n")

all_results = {}

for channel in CHANNELS:
    print(f"\n{'#'*70}")
    print(f"# CHANNEL: {channel['name']}")
    print(f"# Token: {channel['token']}")
    print(f"{'#'*70}\n")
    
    # Load storyboard
    storyboard_path = Path(channel['storyboard'])
    data = json.loads(storyboard_path.read_text(encoding='utf-8'))
    
    channel_results = []
    
    for video_idx, video_data in enumerate(data["videos"], 1):
        print(f"\n[Video {video_idx}/4]")
        result = generate_and_upload_video(video_data, channel['token'], channel['output_dir'])
        if result:
            channel_results.append(result)
    
    all_results[channel['name']] = channel_results
    
    print(f"\n✅ {channel['name']}: {len(channel_results)}/4 videos uploaded!")

# Final summary
print("\n" + "="*70)
print("🎉 ALL CHANNELS LAUNCHED!")
print("="*70)

for channel_name, results in all_results.items():
    print(f"\n{channel_name}: {len(results)} videos")
    for r in results:
        print(f"  • {r['title']}")
        print(f"    {r['url']}")

print("\n" + "="*70)
print("Total videos uploaded: " + str(sum(len(r) for r in all_results.values())) + "/12")
print("="*70)
