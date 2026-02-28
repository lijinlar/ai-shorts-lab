"""
Generate 40-second video with properly detailed prompts
Fixed version that ensures only NEW videos are used
"""
import json
import sys
import subprocess
import shutil
import time
from pathlib import Path
from datetime import datetime

# Force UTF-8
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

WANGP_DIR = Path(r"C:\Users\lijin\.openclaw\workspace\Wan2GP")
WANGP_PYTHON = WANGP_DIR / "venv" / "Scripts" / "python.exe"
WANGP_OUTPUTS = WANGP_DIR / "outputs"

# Ultra-detailed prompts with DOG as the PRIMARY subject
DETAILED_SCENES = [
    {
        "prompt": """Close-up shot of a brown and white mixed-breed shelter dog sitting alone behind chain-link fence bars in a concrete kennel. The DOG is the sole subject, head down with sad eyes looking directly at camera. Gray concrete walls surround the DOG. Harsh fluorescent lighting casts shadows on the DOG's fur. Medium shot framed from outside the kennel looking in at the DOG. Sharp focus on the DOG's expressive brown eyes and drooping ears. High dynamic range captures every detail of the DOG's sad expression. No humans visible.""",
        "seconds": 5
    },
    {
        "prompt": """Medium close-up of the same brown and white shelter DOG now lying curled up on a thin blue blanket in the kennel corner. The DOG is the only subject - eyes slowly closing in defeat. The DOG's body language shows complete hopelessness. Soft focus background with sharp focus on the DOG's face and paws. Muted colors emphasizing the somber mood. The DOG fills most of the frame. Natural melancholic lighting. No people in shot.""",
        "seconds": 5
    },
    {
        "prompt": """Wide angle shot showing the brown and white shelter DOG in full body view inside the kennel as a blurred human figure approaches from behind. The DOG's ears perk up slightly - DOG is main focus in foreground. Metal kennel door visible on right side of frame. The DOG looks cautiously toward the approaching shadow. Fluorescent lights reflect off metal surfaces. The DOG remains the primary subject with person intentionally out of focus. Documentary-style natural cinematography.""",
        "seconds": 5
    },
    {
        "prompt": """Eye-level medium shot of the brown and white shelter DOG looking up hopefully as kennel door swings open. The DOG is centered in frame, front and center. A human hand extends into frame from side reaching toward the DOG. Warm sunlight streams through window creating a glow around the DOG. Shallow depth of field - the DOG's face is razor sharp, everything else slightly soft. The DOG's expression changes from fear to cautious hope. High dynamic range captures light in the DOG's eyes.""",
        "seconds": 5
    },
    {
        "prompt": """Medium shot of the brown and white shelter DOG cautiously entering bright adoption room. The DOG is the star of the shot, centered and in sharp focus. Blurred happy family visible in background - DOG in foreground. The DOG freezes mid-step, one paw raised. The DOG's tail begins slow wag motion. Warm natural window light illuminates the DOG's golden-brown fur. The DOG's surprised expression clearly visible. Shallow depth of field keeps attention on the DOG.""",
        "seconds": 5
    },
    {
        "prompt": """Close-up shot focused entirely on the brown and white DOG's face and upper body as the DOG receives gentle pets. The DOG is the exclusive subject - camera stays on the DOG's joyful expression. The DOG's tail wagging rapidly (visible in frame). The DOG's mouth open in happy pant with tongue out. Multiple human hands visible at edges of frame but the DOG is center stage. The DOG's eyes bright and excited. Warm golden hour lighting on the DOG's fur. Every detail of the DOG's happy face crystal clear.""",
        "seconds": 5
    },
    {
        "prompt": """Close-up following shot of the brown and white shelter DOG walking proudly with new family. The DOG is the main subject in center frame wearing a bright new red collar. Camera tracks alongside the DOG at DOG's eye level. The DOG's head held high, tail wagging energetically. The DOG's confident stride. Blurred human legs visible but DOG dominates the composition. Bright blue sky and sunshine creating perfect lighting on the DOG. The DOG's transformation from sad to happy clearly visible. High dynamic range, cinematic quality focused on the DOG.""",
        "seconds": 5
    },
    {
        "prompt": """Final wide establishing shot of the brown and white DOG walking away from shelter building with family. The DOG is prominent in lower center of frame. The DOG's silhouette clear against bright sunny background. The DOG's tail high and wagging. New red collar visible on the DOG. Beautiful blue sky with white fluffy clouds above. The DOG and family walking toward camera-left. Uplifting cinematography with the DOG as the hero. Golden sunlight backlighting the DOG. Perfect happy ending composition with the DOG as focal point.""",
        "seconds": 5
    }
]

def clean_wangp_outputs():
    """Remove all existing videos from WanGP outputs directory"""
    if WANGP_OUTPUTS.exists():
        for mp4 in WANGP_OUTPUTS.glob("*.mp4"):
            try:
                mp4.unlink()
                print(f"  Cleaned: {mp4.name}")
            except Exception as e:
                print(f"  Could not delete {mp4.name}: {e}")

def generate_single_scene(prompt: str, scene_num: int) -> Path:
    """Generate ONE scene and return its path"""
    print(f"\n{'='*80}")
    print(f"GENERATING SCENE {scene_num}/8")
    print(f"{'='*80}")
    print(f"Prompt preview: {prompt[:120]}...")
    
    # Clean outputs before generation
    print("\nCleaning old videos...")
    clean_wangp_outputs()
    
    # Generate using WanGP
    print("\nStarting generation...")
    cmd = [str(WANGP_PYTHON), str(WANGP_DIR / "generate_video.py"), prompt]
    
    result = subprocess.run(
        cmd,
        cwd=str(WANGP_DIR),
        capture_output=True,
        text=True,
        timeout=600
    )
    
    if result.returncode != 0 or "[SUCCESS]" not in result.stdout:
        print(f"FAILED:\n{result.stdout}\n{result.stderr}")
        return None
    
    # Wait a moment for file to be written
    time.sleep(3)
    
    # Find the newly generated video (should be the ONLY one)
    videos = list(WANGP_OUTPUTS.glob("*.mp4"))
    
    if not videos:
        print("ERROR: No video file found after generation!")
        return None
    
    if len(videos) > 1:
        print(f"WARNING: Found {len(videos)} videos, using most recent")
        video = max(videos, key=lambda p: p.stat().st_mtime)
    else:
        video = videos[0]
    
    print(f"SUCCESS: {video.name}")
    return video

def main():
    root = Path(__file__).resolve().parents[1]
    temp_dir = root / "temp" / "shelter_dog_fixed"
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    scene_paths = []
    
    # Generate each scene
    for i, scene in enumerate(DETAILED_SCENES, start=1):
        scene_file = temp_dir / f"scene_{i:02d}.mp4"
        
        # Skip if exists and valid
        if scene_file.exists() and scene_file.stat().st_size > 500000:
            print(f"\nScene {i}/8: Already exists ({scene_file.stat().st_size} bytes)")
            scene_paths.append(scene_file)
            continue
        
        # Generate new
        generated = generate_single_scene(scene["prompt"], i)
        
        if not generated:
            print(f"\nABORTED: Scene {i} failed")
            return None
        
        # Move to final location
        shutil.move(str(generated), str(scene_file))
        print(f"Saved: {scene_file}")
        scene_paths.append(scene_file)
        
        # Brief pause between generations
        if i < len(DETAILED_SCENES):
            time.sleep(2)
    
    # Concatenate
    print(f"\n{'='*80}")
    print("CONCATENATING 8 SCENES...")
    print(f"{'='*80}")
    
    final_output = root / "out" / "shelter_dog_40s_FIXED.mp4"
    final_output.parent.mkdir(parents=True, exist_ok=True)
    
    # Create concat file
    concat_list = temp_dir / "concat.txt"
    concat_list.write_text(
        "\n".join([f"file '{p.as_posix()}'" for p in scene_paths]),
        encoding="utf-8"
    )
    
    # Run FFmpeg
    subprocess.run(
        [
            "ffmpeg", "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", str(concat_list),
            "-c:v", "libx264",
            "-crf", "18",
            "-preset", "fast",
            str(final_output)
        ],
        check=True,
        capture_output=True
    )
    
    print(f"\n{'='*80}")
    print(f"COMPLETE!")
    print(f"{'='*80}")
    print(f"Output: {final_output}")
    print(f"Size: {final_output.stat().st_size / 1_000_000:.1f} MB")
    
    return str(final_output)

if __name__ == "__main__":
    result = main()
    sys.exit(0 if result else 1)
