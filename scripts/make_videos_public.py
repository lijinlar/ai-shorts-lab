#!/usr/bin/env python3
"""
Make today's videos public using YouTube Data API
"""

from pathlib import Path
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Full access scope
SCOPES = ["https://www.googleapis.com/auth/youtube.force-ssl", "https://www.googleapis.com/auth/yt-analytics.readonly"]

def main():
    root = Path(__file__).resolve().parents[1]
    secrets = Path(r"C:\Users\lijin\.openclaw\secrets\youtube.oauth.json")
    
    # Fresh auth with full scope
    flow = InstalledAppFlow.from_client_secrets_file(str(secrets), SCOPES)
    creds = flow.run_local_server(port=8080)
    
    youtube = build("youtube", "v3", credentials=creds)
    
    # Today's video IDs
    video_ids = [
        "2Rhz9a4c1Xw",  # Military dog reunion
        "ukk-q3Xsukw",  # Abandoned dog rescue
        "D5lwfOvDYBg",  # Elderly dog reunion
        "QhwukEqiCkc",  # Deaf dog sign language
    ]
    
    for video_id in video_ids:
        youtube.videos().update(
            part="status",
            body={
                "id": video_id,
                "status": {
                    "privacyStatus": "public",
                    "selfDeclaredMadeForKids": False,
                }
            }
        ).execute()
        
        print(f"✅ Made public: https://www.youtube.com/watch?v={video_id}")
    
    # Save token for future use
    token_path = root / "out" / "youtube_token.json"
    token_path.parent.mkdir(exist_ok=True)
    token_path.write_text(creds.to_json(), encoding="utf-8")
    print(f"\n💾 Saved token to: {token_path}")


if __name__ == "__main__":
    main()
