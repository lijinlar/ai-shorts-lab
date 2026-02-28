#!/usr/bin/env python3
"""
Batch Generate & Upload Series (WanGP Edition)
Processes multi-video storyboard using WanGP for video generation
"""

import json
import sys
import subprocess
from pathlib import Path
from datetime import datetime
import argparse

# Force UTF-8 output on Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.detach(), encoding='utf-8', errors='replace', line_buffering=True)
    sys.stderr = io.TextIOWrapper(sys.stderr.detach(), encoding='utf-8', errors='replace', line_buffering=True)

# Add parent to path
root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))


def log(msg):
    """Timestamped logging"""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")


def generate_video_with_wangp(storyboard_data, video_data, output_path):
    """
    Generate a single video using WanGP
    
    Args:
        storyboard_data: Full storyboard dict (for metadata)
        video_data: Single video dict with scenes
        output_path: Where to save final video
        
    Returns:
        Path to generated video or None
    """
    log(f"🎬 Generating: {video_data['title']}")
    log(f"   Scenes: {len(video_data['scenes'])}")
    
    # Create temporary storyboard for this single video
    single_video_storyboard = {
        "title": video_data["title"],
        "description": video_data.get("description", ""),
        "tags": storyboard_data.get("tags", []),
        "category": storyboard_data.get("category", "Pets & Animals"),
        "scenes": video_data["scenes"],
    }
    
    # Save temporary storyboard
    temp_storyboard = root / "out" / "temp_storyboard.json"
    temp_storyboard.parent.mkdir(parents=True, exist_ok=True)
    temp_storyboard.write_text(json.dumps(single_video_storyboard, indent=2), encoding='utf-8')
    
    # NOTE: For now, use semi-automated workflow:
    # 1. Run auto_process_wangp.py in one terminal
    # 2. Generate scenes via WanGP UI
    # 3. Run combine_and_upload.py when done
    #
    # This batch script is for future full automation
    generate_script = root / "scripts" / "generate_shorts_wangp.py"
    
    cmd = [
        sys.executable,
        str(generate_script),
        str(temp_storyboard),
        str(output_path)
    ]
    
    log(f"   Running: {generate_script.name}")
    start_time = datetime.now()
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=False,  # Show real-time output
            text=True,
            timeout=3600  # 1 hour timeout for full video generation
        )
        
        duration = (datetime.now() - start_time).total_seconds()
        
        if result.returncode == 0 and Path(output_path).exists():
            log(f"✅ Video generated ({duration:.0f}s): {output_path}")
            return output_path
        else:
            log(f"❌ Generation failed (code {result.returncode})")
            return None
            
    except subprocess.TimeoutExpired:
        log(f"❌ Generation timed out after 1 hour")
        return None
    except Exception as e:
        log(f"❌ Generation error: {e}")
        import traceback
        traceback.print_exc()
        return None


def upload_video(video_path, title, description, tags, category, privacy):
    """
    Upload video to YouTube
    
    Args:
        video_path: Path to video file
        title: Video title
        description: Video description
        tags: List of tags
        category: YouTube category ID
        privacy: public/unlisted/private
        
    Returns:
        Upload result dict or None
    """
    log(f"📤 Uploading: {title}")
    
    upload_script = root / "scripts" / "youtube_upload.py"
    
    tags_csv = ",".join([t.strip() for t in (tags or []) if str(t).strip()])

    cmd = [
        sys.executable,
        str(upload_script),
        "--file", str(video_path),
        "--title", title,
        "--description", description or "",
        "--tags", tags_csv,
        "--privacy", privacy,
        "--category", str(category or "22"),
        "--channel", "dogs",
    ]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600  # 10 minute timeout for upload
        )
        
        if result.returncode == 0:
            # Parse video ID from output
            output = result.stdout
            video_id = None
            
            for line in output.splitlines():
                if "Video id" in line or "watch?v=" in line:
                    # Extract video ID
                    if "v=" in line:
                        video_id = line.split("v=")[-1].strip()
                    elif "Video id" in line:
                        video_id = line.split("'")[-2]
            
            if video_id:
                url = f"https://youtube.com/watch?v={video_id}"
                log(f"✅ Uploaded: {url}")
                return {
                    "title": title,
                    "video_id": video_id,
                    "url": url,
                    "privacy": privacy
                }
            else:
                log(f"⚠️ Upload succeeded but couldn't parse video ID")
                return {
                    "title": title,
                    "video_id": "unknown",
                    "url": "unknown",
                    "privacy": privacy
                }
        else:
            log(f"❌ Upload failed")
            log(f"   Error: {result.stderr[:200]}")
            return None
            
    except subprocess.TimeoutExpired:
        log(f"❌ Upload timed out")
        return None
    except Exception as e:
        log(f"❌ Upload error: {e}")
        return None


def main():
    parser = argparse.ArgumentParser(description="Batch generate and upload videos using WanGP")
    parser.add_argument("--storyboard", required=True, help="Storyboard JSON file")
    parser.add_argument("--privacy", default="public", choices=["public", "unlisted", "private"])
    parser.add_argument("--skip-upload", action="store_true", help="Generate only, don't upload")
    args = parser.parse_args()
    
    storyboard_path = Path(args.storyboard)
    
    if not storyboard_path.exists():
        log(f"❌ Storyboard not found: {storyboard_path}")
        return 1
    
    # Load storyboard
    log(f"📖 Loading storyboard: {storyboard_path.name}")
    storyboard_data = json.loads(storyboard_path.read_text(encoding='utf-8'))
    
    videos = storyboard_data.get("videos", [])
    log(f"   Videos: {len(videos)}")
    log("")
    
    if not videos:
        log("❌ No videos in storyboard")
        return 1
    
    # Process each video
    results = []
    out_dir = root / "out" / "series"
    out_dir.mkdir(parents=True, exist_ok=True)
    
    for i, video_data in enumerate(videos, 1):
        log(f"\n{'='*70}")
        log(f"VIDEO {i}/{len(videos)}")
        log(f"{'='*70}")
        
        # Generate output filename
        safe_title = "".join(c for c in video_data["title"] if c.isalnum() or c in " -_")[:50]
        output_filename = f"video_{i}_{safe_title}.mp4"
        output_path = out_dir / output_filename
        
        # Generate video
        generated_video = generate_video_with_wangp(storyboard_data, video_data, output_path)
        
        if not generated_video:
            log(f"❌ Skipping upload for video {i} (generation failed)")
            results.append({
                "title": video_data["title"],
                "status": "generation_failed",
                "video_id": None,
                "url": None
            })
            continue
        
        # Upload (unless --skip-upload)
        if not args.skip_upload:
            # Tags come from storyboard default (comma-separated)
            default_tags = (storyboard_data.get("default", {}) or {}).get("tags", "")
            tags = [t.strip() for t in str(default_tags).split(",") if t.strip()]

            upload_result = upload_video(
                generated_video,
                video_data["title"],
                video_data.get("description", ""),
                tags,
                (storyboard_data.get("default", {}) or {}).get("category", "22"),  # Pets & Animals
                args.privacy,
            )
            
            if upload_result:
                results.append({
                    **upload_result,
                    "status": "success"
                })
            else:
                results.append({
                    "title": video_data["title"],
                    "status": "upload_failed",
                    "video_id": None,
                    "url": None
                })
        else:
            log(f"⏭️ Skipping upload (--skip-upload)")
            results.append({
                "title": video_data["title"],
                "status": "generated_only",
                "video_id": None,
                "url": None,
                "file": str(generated_video)
            })
    
    # Save results
    results_path = out_dir / "upload_results.json"
    results_path.write_text(json.dumps(results, indent=2), encoding='utf-8')
    log(f"\n💾 Results saved: {results_path}")
    
    # Summary
    log(f"\n{'='*70}")
    log(f"📊 SUMMARY")
    log(f"{'='*70}")
    log(f"Total videos: {len(results)}")
    log(f"Successful: {sum(1 for r in results if r.get('status') == 'success')}")
    log(f"Failed: {sum(1 for r in results if r.get('status') in ['generation_failed', 'upload_failed'])}")
    log(f"{'='*70}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
