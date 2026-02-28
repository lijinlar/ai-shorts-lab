"""
TikTok Daily Upload - Integrated with YouTube Pipeline
Uploads the same 4 daily videos to TikTok automatically
"""

import sys
import io
import json
from pathlib import Path
from datetime import datetime

# Fix Windows console encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')


def get_latest_youtube_videos():
    """Get today's uploaded YouTube videos from daily report"""
    workspace = Path(__file__).parent.parent
    reports_dir = workspace / "out" / "daily_reports"
    
    today = datetime.now().strftime("%Y-%m-%d")
    report_file = reports_dir / f"{today}.json"
    
    if not report_file.exists():
        print(f"❌ No YouTube report found for {today}")
        return []
    
    with open(report_file) as f:
        report = json.load(f)
    
    videos = []
    for result in report.get("results", []):
        slug = result.get("slug", "")
        title = result.get("title", "")
        video_file = workspace / "out" / "series" / f"{slug}.mp4"
        
        if video_file.exists():
            videos.append({
                "path": str(video_file),
                "slug": slug,
                "youtube_title": title,
                "youtube_url": result.get("url", "")
            })
    
    return videos


def tiktok_optimize_caption(youtube_title):
    """Convert YouTube title to TikTok caption"""
    # Remove YouTube-specific formatting
    caption = youtube_title
    
    # Remove #shorts tag
    caption = caption.replace("#shorts", "").strip()
    
    # Clean up emojis at start (keep them but not excessive)
    # Make more casual and engaging for TikTok
    
    # Add TikTok hashtags
    tiktok_hashtags = [
        "#dogsoftiktok",
        "#fyp",
        "#viral",
        "#rescuedog",
        "#dogrescue",
        "#heartwarming",
        "#wholesome"
    ]
    
    caption += "\n\n" + " ".join(tiktok_hashtags)
    
    return caption[:2200]  # TikTok caption limit


def upload_to_tiktok(videos):
    """Upload videos to TikTok (uses manual browser for now)"""
    print("\nTikTok Upload Instructions:")
    print("=" * 60)
    print("Since TikTok API is restricted, here are the videos to upload:")
    print("=" * 60)
    
    for i, video in enumerate(videos, 1):
        caption = tiktok_optimize_caption(video["youtube_title"])
        print(f"\nVideo {i}: {Path(video['path']).name}")
        print(f"Path: {video['path']}")
        print(f"Caption:")
        print(caption)
        print(f"YouTube: {video['youtube_url']}")
        print("-" * 60)
    
    # TODO: Implement automated upload when TikTok API becomes available
    # For now, this generates upload instructions
    
    return {
        "date": datetime.now().isoformat(),
        "total": len(videos),
        "method": "manual",
        "videos": videos
    }


def main():
    """Main TikTok upload workflow"""
    print("TikTok Daily Upload")
    
    # Get today's YouTube videos
    videos = get_latest_youtube_videos()
    
    if not videos:
        print("No videos to upload")
        return
    
    print(f"Found {len(videos)} videos from today's YouTube upload")
    
    # Upload to TikTok
    result = upload_to_tiktok(videos)
    
    # Save report
    workspace = Path(__file__).parent.parent
    report_path = workspace / "out" / "tiktok_reports" / f"{datetime.now().strftime('%Y-%m-%d')}.json"
    report_path.parent.mkdir(exist_ok=True, parents=True)
    
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    print(f"\nReport saved: {report_path}")


if __name__ == "__main__":
    main()
