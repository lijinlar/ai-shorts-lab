#!/usr/bin/env python3
"""
Update privacy status of YouTube videos
"""

import argparse
from pathlib import Path
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

SCOPES = [
    "https://www.googleapis.com/auth/youtube.force-ssl",
]


def get_creds():
    root = Path(__file__).resolve().parents[1]
    token_path = root / "out" / "youtube_token.json"
    if not token_path.exists():
        raise SystemExit(
            f"Missing token at {token_path}. Run: .venv\\Scripts\\python scripts\\youtube_auth.py"
        )
    return Credentials.from_authorized_user_file(str(token_path), SCOPES)


def update_privacy(video_id, privacy_status):
    """Update privacy status of a video"""
    creds = get_creds()
    youtube = build("youtube", "v3", credentials=creds)
    
    # Get current video details
    video = youtube.videos().list(
        part="status",
        id=video_id
    ).execute()
    
    if not video.get("items"):
        print(f"❌ Video {video_id} not found")
        return False
    
    # Update privacy status
    video["items"][0]["status"]["privacyStatus"] = privacy_status
    
    youtube.videos().update(
        part="status",
        body={
            "id": video_id,
            "status": {
                "privacyStatus": privacy_status,
                "selfDeclaredMadeForKids": False,
            }
        }
    ).execute()
    
    print(f"✅ Updated {video_id} to {privacy_status}")
    return True


def main():
    ap = argparse.ArgumentParser(description="Update YouTube video privacy status")
    ap.add_argument("--video-id", action="append", help="Video ID to update (can specify multiple)")
    ap.add_argument("--privacy", choices=["public", "unlisted", "private"], required=True)
    args = ap.parse_args()
    
    if not args.video_id:
        print("❌ No video IDs provided. Use --video-id <ID>")
        return 1
    
    for video_id in args.video_id:
        update_privacy(video_id, args.privacy)
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
