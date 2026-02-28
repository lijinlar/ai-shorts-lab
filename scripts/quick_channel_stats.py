#!/usr/bin/env python3
"""Quick channel stats using full-scope token"""

from pathlib import Path
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/youtube.force-ssl", "https://www.googleapis.com/auth/yt-analytics.readonly"]

root = Path(__file__).resolve().parents[1]
token_path = root / "out" / "yt_token_full.json"

creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
youtube = build("youtube", "v3", credentials=creds)

# Get channel stats
channels = youtube.channels().list(
    part="statistics,snippet",
    mine=True
).execute()

if channels["items"]:
    stats = channels["items"][0]["statistics"]
    snippet = channels["items"][0]["snippet"]
    
    print(f"Channel: {snippet['title']}")
    print(f"Subscribers: {stats.get('subscriberCount', 'Hidden')}")
    print(f"Total Views: {stats.get('viewCount', 0)}")
    print(f"Videos: {stats.get('videoCount', 0)}")

# Get latest videos
videos = youtube.search().list(
    part="snippet",
    forMine=True,
    type="video",
    order="date",
    maxResults=10
).execute()

print(f"\nLatest {len(videos['items'])} videos:")
for item in videos["items"]:
    video_id = item["id"]["videoId"]
    title = item["snippet"]["title"]
    
    # Get video stats
    video_stats = youtube.videos().list(
        part="statistics",
        id=video_id
    ).execute()
    
    if video_stats["items"]:
        vstats = video_stats["items"][0]["statistics"]
        views = vstats.get("viewCount", 0)
        likes = vstats.get("likeCount", 0)
        print(f"  {title[:50]}: {views} views, {likes} likes")
