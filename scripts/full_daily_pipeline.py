#!/usr/bin/env python3
"""
Full Daily YouTube Automation Pipeline
- Analytics & strategy
- Storyboard validation/selection
- Video generation (GPU-optimized)
- YouTube upload
- Results reporting
"""

import json
import sys
import subprocess
from pathlib import Path
from datetime import datetime, timedelta

# Force UTF-8 output on Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.detach(), encoding='utf-8', errors='replace', line_buffering=True)
    sys.stderr = io.TextIOWrapper(sys.stderr.detach(), encoding='utf-8', errors='replace', line_buffering=True)

# Add parent to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def log(msg):
    """Timestamped logging"""
    # Remove emojis for Windows console compatibility
    safe_msg = msg.encode('ascii', 'ignore').decode('ascii')
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {safe_msg}")


def analyze_performance():
    """Quick analytics check"""
    log("📊 Running analytics...")
    
    root = Path(__file__).resolve().parents[1]
    analytics_script = root / "scripts" / "youtube_analytics_report.py"
    
    try:
        result = subprocess.run(
            [sys.executable, str(analytics_script)],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        # Parse key metrics from output
        output = result.stdout
        
        # Look for top performers in output
        log("✅ Analytics complete")
        
        # Return strategy based on recent performance
        # TODO: Parse actual analytics data
        strategy = {
            "content_type": "dogs_emotional",  # Based on 597-view winner
            "video_count": 4,  # Target for the day
            "upload_spacing_hours": 4,  # 2 PM, 6 PM, 10 PM, 2 AM
        }
        
        return strategy
        
    except Exception as e:
        log(f"⚠️ Analytics failed: {e}")
        # Fallback strategy
        return {
            "content_type": "dogs_emotional",
            "video_count": 2,  # Conservative fallback
            "upload_spacing_hours": 6,
        }


def get_todays_storyboard():
    """Find or validate today's storyboard"""
    root = Path(__file__).resolve().parents[1]
    date_str = datetime.now().strftime("%Y-%m-%d")
    
    # Look for data-driven storyboard first
    storyboard_candidates = [
        root / "storyboards" / f"series_{date_str}_dogs_emotional_DATADRIVEN.json",
        root / "storyboards" / f"series_{date_str}_dogs_emotional.json",
        root / "storyboards" / f"series_{date_str}_funny_pets.json",
    ]
    
    for path in storyboard_candidates:
        if path.exists():
            log(f"✅ Found storyboard: {path.name}")
            return path
    
    # No storyboard found
    log("❌ No storyboard for today!")
    log(f"   Expected: series_{date_str}_*.json")
    log("   Create one first or use --storyboard flag")
    return None


def run_batch_generation(storyboard_path, privacy="public"):
    """Execute video generation and upload"""
    root = Path(__file__).resolve().parents[1]
    # Use Wan2.x (wangp) generation script
    batch_script = root / "scripts" / "batch_generate_upload_series_wangp.py"
    
    log(f"🎬 Starting batch generation...")
    log(f"   Storyboard: {storyboard_path.name}")
    log(f"   Privacy: {privacy}")
    
    # Load storyboard to show video count
    data = json.loads(storyboard_path.read_text(encoding="utf-8"))
    video_count = len(data["videos"])
    total_scenes = sum(len(v["scenes"]) for v in data["videos"])
    
    log(f"   Videos: {video_count}")
    log(f"   Total scenes: {total_scenes}")
    log(f"   Estimated time: {total_scenes * 3} minutes")
    
    start_time = datetime.now()
    
    try:
        # Run batch generation with real-time output
        process = subprocess.Popen(
            [
                sys.executable,
                str(batch_script),
                "--storyboard",
                str(storyboard_path),
                "--privacy",
                privacy,
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding='utf-8',
            errors='replace',
            bufsize=1,
        )
        
        # Stream output
        for line in process.stdout:
            print(line, end='')
        
        process.wait()
        
        if process.returncode != 0:
            log(f"❌ Generation failed with code {process.returncode}")
            return None
        
        duration = datetime.now() - start_time
        log(f"✅ Generation complete ({duration.total_seconds():.0f}s)")
        
        # Parse results
        results_path = root / "out" / "series" / "upload_results.json"
        if results_path.exists():
            results = json.loads(results_path.read_text())
            return results
        else:
            log("⚠️ No upload_results.json found")
            return []
        
    except Exception as e:
        log(f"❌ Generation error: {e}")
        import traceback
        traceback.print_exc()
        return None


def generate_report(strategy, results, duration_seconds):
    """Create final report"""
    log("=" * 70)
    log("📋 DAILY AUTOMATION REPORT")
    log("=" * 70)
    
    log(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    log(f"Duration: {duration_seconds:.0f}s ({duration_seconds/60:.1f} minutes)")
    log("")
    
    if results:
        log(f"✅ Successfully uploaded {len(results)} videos:")
        for r in results:
            log(f"   • {r['title']}")
            log(f"     {r['url']}")
        log("")
        
        # Calculate next upload times (for manual scheduling or future automation)
        spacing = strategy.get('upload_spacing_hours', 4)
        now = datetime.now()
        log(f"📅 Suggested upload schedule ({spacing}h spacing):")
        for i, r in enumerate(results):
            upload_time = now + timedelta(hours=i * spacing)
            log(f"   {upload_time.strftime('%I:%M %p')} - {r['title']}")
        
    else:
        log("❌ No videos uploaded")
    
    log("=" * 70)
    
    return {
        "date": datetime.now().isoformat(),
        "duration_seconds": duration_seconds,
        "strategy": strategy,
        "results": results or [],
    }


def main():
    """Main automation workflow"""
    
    # Parse args
    import argparse
    parser = argparse.ArgumentParser(description="Full daily YouTube automation")
    parser.add_argument("--storyboard", help="Override storyboard path")
    parser.add_argument("--privacy", default="public", choices=["public", "unlisted", "private"])
    parser.add_argument("--skip-analytics", action="store_true", help="Skip analytics check")
    args = parser.parse_args()
    
    start_time = datetime.now()
    
    log("🚀 Starting full daily automation pipeline")
    log("")
    
    try:
        # 1. Analytics (optional)
        if not args.skip_analytics:
            strategy = analyze_performance()
        else:
            strategy = {"content_type": "dogs_emotional", "video_count": 4, "upload_spacing_hours": 4}
        
        log("")
        
        # 2. Get storyboard
        if args.storyboard:
            storyboard_path = Path(args.storyboard)
            if not storyboard_path.is_absolute():
                root = Path(__file__).resolve().parents[1]
                storyboard_path = (root / storyboard_path).resolve()
        else:
            storyboard_path = get_todays_storyboard()
        
        if not storyboard_path or not storyboard_path.exists():
            log("❌ Storyboard not found. Exiting.")
            return 1
        
        log("")
        
        # 3. Generate and upload
        results = run_batch_generation(storyboard_path, args.privacy)
        
        if results is None:
            log("❌ Generation failed")
            return 1
        
        log("")
        
        # 4. Report
        duration = (datetime.now() - start_time).total_seconds()
        report = generate_report(strategy, results, duration)
        
        # Save report
        root = Path(__file__).resolve().parents[1]
        report_path = root / "out" / "daily_reports" / f"{datetime.now().strftime('%Y-%m-%d')}.json"
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        log(f"\n💾 Report saved: {report_path}")
        
        return 0
        
    except Exception as e:
        log(f"❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
