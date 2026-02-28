from __future__ import annotations

import argparse
import sys
from pathlib import Path

from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
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


def get_creds(channel: str = "main") -> Credentials:
    root = Path(__file__).resolve().parents[1]
    if channel == "main":
        token_path = root / "out" / "youtube_token.json"
    else:
        token_path = root / "out" / f"youtube_token_{channel}.json"
    
    if not token_path.exists():
        raise SystemExit(
            f"Missing token at {token_path}. Run: .\\.venv\\Scripts\\python scripts\\youtube_auth.py"
        )
    return Credentials.from_authorized_user_file(str(token_path), SCOPES)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", required=True)
    ap.add_argument("--title", required=True)
    ap.add_argument("--description", default="")
    ap.add_argument("--tags", default="")
    ap.add_argument("--privacy", choices=["public", "unlisted", "private"], default="public")
    ap.add_argument("--category", default="22")
    ap.add_argument("--channel", choices=["main", "aitools", "dogs", "finance", "sleepsounds"], default="main", 
                    help="Which channel to upload to (uses corresponding token)")
    args = ap.parse_args()

    video_path = Path(args.file)
    if not video_path.exists():
        raise SystemExit(f"File not found: {video_path}")

    creds = get_creds(args.channel)
    youtube = build("youtube", "v3", credentials=creds)

    body = {
        "snippet": {
            "title": args.title,
            "description": args.description,
            "tags": [t.strip() for t in args.tags.split(",") if t.strip()],
            "categoryId": args.category,
        },
        "status": {
            "privacyStatus": args.privacy,
            "selfDeclaredMadeForKids": False,
        },
    }

    media = MediaFileUpload(str(video_path), mimetype="video/mp4", chunksize=-1, resumable=True)

    req = youtube.videos().insert(part=",".join(body.keys()), body=body, media_body=media)
    resp = None
    while resp is None:
        status, resp = req.next_chunk()
        if status:
            print(f"Upload progress: {int(status.progress() * 100)}%")

    video_id = resp.get("id")
    print("Uploaded video id:", video_id)
    print("URL: https://www.youtube.com/watch?v=" + video_id)


if __name__ == "__main__":
    main()
