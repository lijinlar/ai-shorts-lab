"""
Generate scenes individually using WanGP, then concatenate
"""
import json
import sys
import subprocess
from pathlib import Path

# Force UTF-8
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

WANGP_DIR = Path(r"C:\Users\lijin\.openclaw\workspace\Wan2GP")
WANGP_PYTHON = WANGP_DIR / "venv" / "Scripts" / "python.exe"

def generate_scene(prompt: str, scene_num: int, total_scenes: int):
    """Generate a single scene using WanGP CLI"""
    print(f"\n{'='*70}")
    print(f"Scene {scene_num}/{total_scenes}")
    print(f"{'='*70}")
    print(f"Prompt: {prompt[:100]}...")
    
    # Use the generate_video.py script
    cmd = [
        str(WANGP_PYTHON),
        str(WANGP_DIR / "generate_video.py"),
        prompt
    ]
    
    result = subprocess.run(cmd, cwd=str(WANGP_DIR), capture_output=True, text=True, timeout=600)
    
    if result.returncode == 0 and "[SUCCESS]" in result.stdout:
        print(f"✓ Scene {scene_num} generated successfully")
        return True
    else:
        print(f"✗ Scene {scene_num} failed")
        print(f"Output: {result.stdout}")
        print(f"Error: {result.stderr}")
        return False

def find_latest_video(wangp_output_dir: Path):
    """Find the most recently created video"""
    videos = sorted(wangp_output_dir.glob("*.mp4"), key=lambda p: p.stat().st_mtime, reverse=True)
    return videos[0] if videos else None

def concat_scenes(scene_paths: list, output_path: Path):
    """Concatenate scenes using ffmpeg"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Create concat list
    concat_list = output_path.parent / "concat_list.txt"
    concat_list.write_text(
        "\n".join([f"file '{p.as_posix()}'" for p in scene_paths]),
        encoding="utf-8"
    )
    
    cmd = [
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(concat_list),
        "-c:v", "libx264",
        "-crf", "18",
        "-preset", "fast",
        str(output_path)
    ]
    
    subprocess.run(cmd, check=True, capture_output=True)
    print(f"\n✓ Concatenated to: {output_path}")

def main():
    root = Path(__file__).resolve().parents[1]
    storyboard_path = root / "storyboards" / "series_2026-02-16_test_40s.json"
    
    data = json.loads(storyboard_path.read_text(encoding="utf-8"))
    video = data["videos"][0]
    scenes = video["scenes"]
    
    wangp_output = WANGP_DIR / "outputs"
    temp_dir = root / "temp" / "series" / video["slug"]
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    scene_paths = []
    
    for i, scene in enumerate(scenes, start=1):
        scene_file = temp_dir / f"scene_{i:02d}.mp4"
        
        # Skip if already exists and valid
        if scene_file.exists() and scene_file.stat().st_size > 100000:
            print(f"\n✓ Scene {i}/{len(scenes)} already exists: {scene_file.name}")
            scene_paths.append(scene_file)
            continue
        
        # Generate new scene
        success = generate_scene(scene["prompt"], i, len(scenes))
        
        if not success:
            print(f"Failed to generate scene {i}, aborting")
            return False
        
        # Find and move the generated video
        import time
        time.sleep(2)
        
        latest = find_latest_video(wangp_output)
        if latest:
            import shutil
            shutil.move(str(latest), str(scene_file))
            print(f"✓ Moved to: {scene_file}")
            scene_paths.append(scene_file)
        else:
            print(f"✗ Could not find generated video")
            return False
    
    # Concatenate all scenes
    final_output = root / "out" / "series" / f"{video['slug']}.mp4"
    concat_scenes(scene_paths, final_output)
    
    print(f"\n{'='*70}")
    print(f"✓ COMPLETE: {final_output}")
    print(f"{'='*70}")
    
    return str(final_output)

if __name__ == "__main__":
    result = main()
    if result:
        print(f"\nFinal video: {result}")
