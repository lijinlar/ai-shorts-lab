"""
Authorize and fetch analytics for any YouTube channel.
Usage: python auth_and_analyze_channel.py <token_name>
Example: python auth_and_analyze_channel.py eatdrinkwander
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from pathlib import Path
from datetime import datetime, timedelta
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = [
    "https://www.googleapis.com/auth/youtube.force-ssl",
    "https://www.googleapis.com/auth/yt-analytics.readonly",
]

def get_or_create_creds(token_name: str) -> Credentials:
    root = Path(__file__).resolve().parents[1]
    from config_loader import get_oauth_credentials
    secrets = get_oauth_credentials()
    token_path = root / "out" / f"youtube_token_{token_name}.json"
    token_path.parent.mkdir(exist_ok=True)

    creds = None
    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)

    if creds and creds.expired and creds.refresh_token:
        print("Refreshing existing token...")
        creds.refresh(Request())
    elif not creds or not creds.valid:
        print(f"\n{'='*60}")
        print(f"  Opening browser — log in as the '{token_name}' account")
        print(f"{'='*60}\n")
        flow = InstalledAppFlow.from_client_secrets_file(str(secrets), SCOPES)
        creds = flow.run_local_server(port=0)

    token_path.write_text(creds.to_json(), encoding="utf-8")
    return creds


def fetch_analytics(creds: Credentials):
    yt = build("youtube", "v3", credentials=creds)
    yta = build("youtubeAnalytics", "v2", credentials=creds)

    # Channel info
    ch = yt.channels().list(part="snippet,statistics,contentDetails", mine=True).execute()
    if not ch.get("items"):
        print("No channel found.")
        return
    item = ch["items"][0]
    name = item["snippet"]["title"]
    ch_id = item["id"]
    stats = item["statistics"]
    subs = int(stats.get("subscriberCount", 0))
    total_views = int(stats.get("viewCount", 0))
    total_videos = int(stats.get("videoCount", 0))

    print(f"\n{'='*60}")
    print(f"  Channel: {name}")
    print(f"  ID: {ch_id}")
    print(f"  Subscribers: {subs:,}")
    print(f"  Total Views: {total_views:,}")
    print(f"  Total Videos: {total_videos:,}")
    print(f"{'='*60}\n")

    # Analytics - last 28 days
    end = datetime.utcnow().date()
    start = end - timedelta(days=28)

    # Overview metrics
    resp = yta.reports().query(
        ids=f"channel=={ch_id}",
        startDate=str(start),
        endDate=str(end),
        metrics="views,estimatedMinutesWatched,averageViewDuration,likes,comments,subscribersGained,subscribersLost",
        dimensions="day",
        sort="day",
    ).execute()

    rows = resp.get("rows", [])
    total_v = sum(r[1] for r in rows)
    total_watch = sum(r[2] for r in rows)
    avg_dur = sum(r[3] for r in rows) / len(rows) if rows else 0
    total_likes = sum(r[4] for r in rows)
    total_comments = sum(r[5] for r in rows)
    net_subs = sum(r[6] - r[7] for r in rows)

    print(f"  === Last 28 Days ===")
    print(f"  Views: {int(total_v):,}")
    print(f"  Watch time: {int(total_watch):,} minutes ({total_watch/60:.0f} hours)")
    print(f"  Avg view duration: {avg_dur:.0f} seconds")
    print(f"  Likes: {int(total_likes):,}")
    print(f"  Comments: {int(total_comments):,}")
    print(f"  Net subscribers: {int(net_subs):+,}")

    # Top 10 videos last 28 days
    print(f"\n  === Top Videos (Last 28 Days) ===")
    top = yta.reports().query(
        ids=f"channel=={ch_id}",
        startDate=str(start),
        endDate=str(end),
        metrics="views,estimatedMinutesWatched,averageViewDuration,likes",
        dimensions="video",
        sort="-views",
        maxResults=10,
    ).execute()

    video_ids = [r[0] for r in top.get("rows", [])]
    if video_ids:
        details = yt.videos().list(
            part="snippet",
            id=",".join(video_ids)
        ).execute()
        id_to_title = {v["id"]: v["snippet"]["title"] for v in details.get("items", [])}

        for i, r in enumerate(top.get("rows", []), 1):
            vid_id, views, watch, dur, likes = r
            title = id_to_title.get(vid_id, vid_id)[:55]
            print(f"  {i:2}. {views:>6,} views | {dur:.0f}s avg | {title}")

    # Traffic sources
    print(f"\n  === Traffic Sources ===")
    src = yta.reports().query(
        ids=f"channel=={ch_id}",
        startDate=str(start),
        endDate=str(end),
        metrics="views",
        dimensions="insightTrafficSourceType",
        sort="-views",
    ).execute()
    for r in src.get("rows", [])[:6]:
        print(f"  {r[0]:<30} {int(r[1]):>8,} views")

    print(f"\n  Token saved. Run again anytime without re-auth.")


if __name__ == "__main__":
    token_name = sys.argv[1] if len(sys.argv) > 1 else "eatdrinkwander"
    creds = get_or_create_creds(token_name)
    fetch_analytics(creds)
