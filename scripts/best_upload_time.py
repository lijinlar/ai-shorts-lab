"""
Analyze best upload time for a channel based on when viewers are most active.
Usage: python best_upload_time.py <token_name>
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from pathlib import Path
from datetime import datetime, timedelta, timezone
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

SCOPES = [
    "https://www.googleapis.com/auth/youtube.force-ssl",
    "https://www.googleapis.com/auth/yt-analytics.readonly",
]

def load_creds(token_name: str) -> Credentials:
    root = Path(__file__).resolve().parents[1]
    token_path = root / "out" / f"youtube_token_{token_name}.json"
    if not token_path.exists():
        raise SystemExit(f"Token not found: {token_path}. Run auth_and_analyze_channel.py first.")
    creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
    return creds

def main(token_name: str):
    creds = load_creds(token_name)
    yt  = build("youtube", "v3", credentials=creds)
    yta = build("youtubeAnalytics", "v2", credentials=creds)

    ch = yt.channels().list(part="snippet,statistics", mine=True).execute()
    item = ch["items"][0]
    ch_id = item["id"]
    ch_name = item["snippet"]["title"]

    end = datetime.now(timezone.utc).date()
    start = end - timedelta(days=90)  # 90-day window for more reliable patterns

    print(f"\nAnalyzing: {ch_name} (last 90 days)\n")

    # --- Day of week breakdown ---
    day_resp = yta.reports().query(
        ids=f"channel=={ch_id}",
        startDate=str(start),
        endDate=str(end),
        metrics="views,estimatedMinutesWatched",
        dimensions="day",
        sort="day",
    ).execute()

    day_views = {0:0, 1:0, 2:0, 3:0, 4:0, 5:0, 6:0}
    day_counts = {0:0, 1:0, 2:0, 3:0, 4:0, 5:0, 6:0}
    for row in day_resp.get("rows", []):
        date_str, views, watch = row[0], row[1], row[2]
        d = datetime.strptime(date_str, "%Y-%m-%d").weekday()  # 0=Mon, 6=Sun
        day_views[d] += views
        day_counts[d] += 1

    day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    avg_by_day = {d: (day_views[d] / day_counts[d] if day_counts[d] else 0) for d in range(7)}
    best_day = max(avg_by_day, key=avg_by_day.get)

    print("=== Views by Day of Week (avg/day) ===")
    for d in range(7):
        bar = "█" * int(avg_by_day[d] / max(avg_by_day.values()) * 20)
        marker = " <-- BEST" if d == best_day else ""
        print(f"  {day_names[d]:<12} {avg_by_day[d]:>6.0f} views  {bar}{marker}")

    # --- Hour of day breakdown ---
    try:
        hour_resp = yta.reports().query(
            ids=f"channel=={ch_id}",
            startDate=str(start),
            endDate=str(end),
            metrics="views",
            dimensions="insightPlaybackLocationType",
            sort="-views",
        ).execute()
    except Exception:
        pass

    # Try hour dimension
    try:
        hour_resp = yta.reports().query(
            ids=f"channel=={ch_id}",
            startDate=str(start),
            endDate=str(end),
            metrics="views",
            dimensions="hour",
            sort="hour",
        ).execute()

        hour_views = {h: 0 for h in range(24)}
        for row in hour_resp.get("rows", []):
            h, v = int(row[0]), row[1]
            hour_views[h] = v

        max_h_views = max(hour_views.values()) if hour_views else 1
        best_hour = max(hour_views, key=hour_views.get)

        print("\n=== Views by Hour (UTC) ===")
        for h in range(24):
            bar = "█" * int(hour_views[h] / max_h_views * 20)
            marker = " <-- PEAK" if h == best_hour else ""
            print(f"  {h:02d}:00  {hour_views[h]:>6.0f}  {bar}{marker}")

        # Convert peak UTC hour to Dubai time (UTC+4)
        dubai_hour = (best_hour + 4) % 24
        print(f"\n  Peak UTC hour: {best_hour:02d}:00")
        print(f"  Peak Dubai time: {dubai_hour:02d}:00")

    except Exception as e:
        print(f"\n(Hour breakdown not available: {e})")
        dubai_hour = None
        best_hour = None

    # --- Top performing days from individual video data ---
    print("\n=== Recent Upload Performance by Day ===")
    try:
        videos_resp = yt.search().list(
            part="snippet",
            channelId=ch_id,
            type="video",
            order="date",
            maxResults=20,
        ).execute()

        video_ids = [v["id"]["videoId"] for v in videos_resp.get("items", [])]
        if video_ids:
            vid_details = yt.videos().list(
                part="snippet,statistics",
                id=",".join(video_ids)
            ).execute()

            for v in vid_details.get("items", []):
                pub = v["snippet"]["publishedAt"]
                pub_dt = datetime.fromisoformat(pub.replace("Z", "+00:00"))
                day_name = day_names[pub_dt.weekday()]
                pub_hour_dubai = (pub_dt.hour + 4) % 24
                views = v["statistics"].get("viewCount", "?")
                title = v["snippet"]["title"][:45]
                print(f"  {day_name:<10} {pub_hour_dubai:02d}:xx Dubai  {int(views) if views != '?' else views:>6} views  {title}")
    except Exception as e:
        print(f"  (Could not load video history: {e})")

    # --- Summary recommendation ---
    print(f"\n{'='*60}")
    print(f"  RECOMMENDATION")
    print(f"{'='*60}")
    print(f"  Best day:  {day_names[best_day]}")
    if best_hour is not None:
        dubai_peak = (best_hour + 4) % 24
        # Suggest uploading 1-2 hours before peak so YouTube indexes it in time
        upload_hour = (dubai_peak - 2) % 24
        print(f"  Peak viewing (Dubai): {dubai_peak:02d}:00")
        print(f"  Suggested upload time: {upload_hour:02d}:00 Dubai (2h before peak)")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    token_name = sys.argv[1] if len(sys.argv) > 1 else "eatdrinkwander"
    main(token_name)
