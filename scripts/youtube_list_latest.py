from __future__ import annotations

import json
from pathlib import Path

from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

SCOPES = ["https://www.googleapis.com/auth/youtube.force-ssl", "https://www.googleapis.com/auth/yt-analytics.readonly"]


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    creds = Credentials.from_authorized_user_file(str(root / "out" / "youtube_token.json"), SCOPES)
    yt = build("youtube", "v3", credentials=creds)

    resp = yt.search().list(part="snippet", forMine=True, type="video", order="date", maxResults=25).execute()
    ids = [it["id"]["videoId"] for it in resp.get("items", [])]

    if not ids:
        print("No videos found")
        return

    v = yt.videos().list(part="snippet,statistics,contentDetails,status", id=",".join(ids)).execute()
    out = root / "out" / "analytics" / "latest_videos.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(v, indent=2), encoding="utf-8")
    print(f"Wrote: {out}")


if __name__ == "__main__":
    main()
