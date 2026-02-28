from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

# Force UTF-8 output on Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

SCOPES = [
    "https://www.googleapis.com/auth/youtube.force-ssl",
    "https://www.googleapis.com/auth/yt-analytics.readonly",
]


def load_creds() -> Credentials:
    root = Path(__file__).resolve().parents[1]
    token_path = root / "out" / "youtube_token.json"
    if not token_path.exists():
        raise SystemExit(
            f"Missing token at {token_path}. Run: .\\.venv\\Scripts\\python scripts\\youtube_auth.py"
        )
    return Credentials.from_authorized_user_file(str(token_path), SCOPES)


def get_channel_id(youtube) -> str:
    resp = youtube.channels().list(part="id,snippet,statistics", mine=True).execute()
    items = resp.get("items", [])
    if not items:
        raise SystemExit("No channels found for this account.")
    return items[0]["id"]


def query_report(analytics, channel_id: str, start: str, end: str, metrics: str, dimensions: str | None = None, filters: str | None = None, sort: str | None = None, max_results: int = 25):
    params = {
        "ids": f"channel=={channel_id}",
        "startDate": start,
        "endDate": end,
        "metrics": metrics,
        "maxResults": max_results,
    }
    if dimensions:
        params["dimensions"] = dimensions
    if filters:
        params["filters"] = filters
    if sort:
        params["sort"] = sort
    return analytics.reports().query(**params).execute()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=7, help="Lookback window")
    args = ap.parse_args()

    creds = load_creds()
    youtube = build("youtube", "v3", credentials=creds)
    analytics = build("youtubeAnalytics", "v2", credentials=creds)

    channel_id = get_channel_id(youtube)

    # YouTube Analytics often has same-day lag; default to reporting up to yesterday.
    end = dt.date.today() - dt.timedelta(days=1)
    start = end - dt.timedelta(days=max(1, args.days))

    start_s = start.isoformat()
    end_s = end.isoformat()

    out_dir = Path(__file__).resolve().parents[1] / "out" / "analytics"
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1) High-level channel overview
    overview = query_report(
        analytics,
        channel_id,
        start_s,
        end_s,
        metrics="views,estimatedMinutesWatched,averageViewDuration,averageViewPercentage,likes,comments,shares,subscribersGained,subscribersLost",
    )

    # 2) Daily trend
    daily = query_report(
        analytics,
        channel_id,
        start_s,
        end_s,
        metrics="views,estimatedMinutesWatched,likes,comments,subscribersGained",
        dimensions="day",
        sort="day",
        max_results=400,
    )

    # 3) Top videos by views (within window)
    top_videos = query_report(
        analytics,
        channel_id,
        start_s,
        end_s,
        metrics="views,estimatedMinutesWatched,averageViewDuration,averageViewPercentage,likes,comments,shares",
        dimensions="video",
        sort="-views",
        max_results=25,
    )

    # 4) Traffic sources
    traffic = query_report(
        analytics,
        channel_id,
        start_s,
        end_s,
        metrics="views,estimatedMinutesWatched",
        dimensions="insightTrafficSourceType",
        sort="-views",
        max_results=25,
    )

    payload = {
        "channelId": channel_id,
        "startDate": start_s,
        "endDate": end_s,
        "overview": overview,
        "daily": daily,
        "topVideos": top_videos,
        "trafficSources": traffic,
    }

    out_path = out_dir / f"report_{start_s}_to_{end_s}.json"
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Wrote: {out_path}")


if __name__ == "__main__":
    main()
