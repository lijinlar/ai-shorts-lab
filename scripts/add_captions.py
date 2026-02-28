"""
Add captions to video using FFmpeg drawtext
"""
import subprocess
import sys
from pathlib import Path

captions = [
    {"start": 0, "end": 5, "text": "Day 47 in the shelter... 😢"},
    {"start": 5, "end": 10, "text": "Nobody wants me anymore 💔"},
    {"start": 10, "end": 15, "text": "Wait... someone's coming?"},
    {"start": 15, "end": 20, "text": "Is this... real? 🥺"},
    {"start": 20, "end": 25, "text": "They chose ME?! 😳"},
    {"start": 25, "end": 30, "text": "Best day EVER! ❤️"},
    {"start": 30, "end": 35, "text": "Going home with my family! 🐕"},
    {"start": 35, "end": 40, "text": "From rescue to forever home 🏡✨"},
]

input_video = Path(r"C:\Users\lijin\Projects\t2v-shorts-lab\out\shelter_dog_40s_FIXED.mp4")
output_video = Path(r"C:\Users\lijin\Projects\t2v-shorts-lab\out\shelter_dog_40s_WITH_CAPTIONS.mp4")

# Build drawtext filters
filters = []
for cap in captions:
    # Escape single quotes and colons in text
    text = cap["text"].replace("'", "'\\\\\\''").replace(":", "\\:")
    
    # Create drawtext filter with enable condition for timing
    filter_str = (
        f"drawtext="
        f"text='{text}':"
        f"fontfile='C\\:/Windows/Fonts/arial.ttf':"
        f"fontsize=32:"
        f"fontcolor=white:"
        f"borderw=3:"
        f"bordercolor=black:"
        f"x=(w-text_w)/2:"
        f"y=h-th-40:"
        f"enable='between(t,{cap['start']},{cap['end']})'"
    )
    filters.append(filter_str)

# Combine all filters
vf = ",".join(filters)

cmd = [
    "ffmpeg",
    "-i", str(input_video),
    "-vf", vf,
    "-c:a", "copy",
    "-y",
    str(output_video)
]

print("Adding captions...")
result = subprocess.run(cmd, capture_output=True, text=True)

if result.returncode == 0:
    print(f"Success: {output_video}")
    print(f"Size: {output_video.stat().st_size / 1_000_000:.1f} MB")
else:
    print(f"Failed:")
    print(result.stderr)
    sys.exit(1)
