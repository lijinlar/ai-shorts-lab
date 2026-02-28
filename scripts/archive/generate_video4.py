"""Generate video 4: 15-year shelter dog"""

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
storyboard_path = Path("C:/Users/lijin/Projects/t2v-shorts-lab/storyboards/series_2026-02-17_dogs_emotional_DATADRIVEN.json")
data = json.loads(storyboard_path.read_text(encoding='utf-8'))
video_data = data["videos"][3]  # Senior dog (index 3)

print(f"\nGenerating: {video_data['title']}")
print(f"Scenes: {len(video_data['scenes'])}\n")

# Generate scenes
wangp_outputs = wangp_dir / "outputs"
temp_dir = Path("C:/Users/lijin/Projects/t2v-shorts-lab/temp/senior-dog")
temp_dir.mkdir(parents=True, exist_ok=True)

scene_files = []
for i, scene in enumerate(video_data["scenes"], 1):
    print(f"[Scene {i}/{len(video_data['scenes'])}] {scene['caption']}")
    
    result = generate_video(scene["prompt"], output_dir=str(wangp_outputs))
    if not result:
        print(f"ERROR: Scene {i} failed!")
        sys.exit(1)
    
    # Find latest video
    output_files = sorted(wangp_outputs.glob("*.mp4"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not output_files:
        print(f"ERROR: No video found for scene {i}")
        sys.exit(1)
    
    # Copy to temp
    scene_file = temp_dir / f"scene_{i:02d}.mp4"
    scene_file.write_bytes(output_files[0].read_bytes())
    scene_files.append(scene_file)
    output_files[0].unlink()
    
    print(f"✓ Scene {i} saved\n")
    time.sleep(2)

print(f"✓ All {len(scene_files)} scenes generated!")

# Combine scenes
out_dir = Path("C:/Users/lijin/Projects/t2v-shorts-lab/out")
combined_path = out_dir / "senior-dog_combined.mp4"

concat_file = combined_path.parent / "senior-dog_concat.txt"
concat_file.write_text("\n".join([f"file '{f.absolute().as_posix()}'" for f in scene_files]))

subprocess.run([
    "ffmpeg", "-y", "-f", "concat", "-safe", "0",
    "-i", str(concat_file),
    "-c:v", "libx264", "-crf", "18", "-preset", "fast",
    str(combined_path)
], capture_output=True, check=True)

print(f"✓ Combined: {combined_path}")

# Add captions
captioned_path = out_dir / "senior-dog_captioned.mp4"
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
print(f"\n✓ COMPLETE! Ready to upload.")
print(f"\nUpload command:")
print(f'python scripts/youtube_upload.py --file "{captioned_path}" --title "{video_data["title"]}" --description "{video_data["description"]}" --privacy public')
