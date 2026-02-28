from __future__ import annotations

import json
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    "https://www.googleapis.com/auth/youtube.force-ssl",
    "https://www.googleapis.com/auth/yt-analytics.readonly",
]


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    from config_loader import get_oauth_credentials
    secrets = get_oauth_credentials()
    token_path = root / "out" / "youtube_token.json"
    token_path.parent.mkdir(exist_ok=True)

    if not secrets.exists():
        raise SystemExit(f"Missing credentials JSON at: {secrets}")

    creds: Credentials | None = None
    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)

    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    elif not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file(str(secrets), SCOPES)
        # Opens browser; local redirect server
        creds = flow.run_local_server(port=0)

    token_path.write_text(creds.to_json(), encoding="utf-8")
    print(f"Saved token to: {token_path}")


if __name__ == "__main__":
    main()
