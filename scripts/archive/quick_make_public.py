#!/usr/bin/env python3
"""Quick script to make videos public - runs auth inline"""

from pathlib import Path
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

SCOPES = ["https://www.googleapis.com/auth/youtube.force-ssl", "https://www.googleapis.com/auth/yt-analytics.readonly"]

def get_authenticated_service():
    """Get authenticated YouTube service"""
    root = Path(__file__).resolve().parents[1]
    secrets = Path(r"C:\Users\lijin\.openclaw\secrets\youtube.oauth.json")
    token_path = root / "out" / "yt_token_full.json"
    token_path.parent.mkdir(exist_ok=True)
    
    creds = None
    
    # Try existing token
    if token_path.exists():
        print(f"Loading existing token from {token_path}")
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
    
    # Refresh or get new token
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("Refreshing expired token...")
            creds.refresh(Request())
        else:
            print("Getting new token via browser auth...")
            print(f"Using secrets: {secrets}")
            flow = InstalledAppFlow.from_client_secrets_file(str(secrets), SCOPES)
            creds = flow.run_local_server(port=8080, prompt='consent')
        
        # Save token
        token_path.write_text(creds.to_json(), encoding="utf-8")
        print(f"Saved token to {token_path}")
    
    return build("youtube", "v3", credentials=creds)

# Video IDs from today's upload
VIDEO_IDS = [
    "2Rhz9a4c1Xw",
    "ukk-q3Xsukw",
    "D5lwfOvDYBg",
    "QhwukEqiCkc",
]

try:
    print("Authenticating with YouTube...")
    youtube = get_authenticated_service()
    
    print(f"\nMaking {len(VIDEO_IDS)} videos public...")
    
    for video_id in VIDEO_IDS:
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
        
        print(f"✅ Public: https://www.youtube.com/watch?v={video_id}")
    
    print("\n🎉 All videos are now PUBLIC!")

except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
    raise
