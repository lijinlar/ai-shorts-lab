"""
Re-authenticate YouTube channels to correct tokens
Run this script for each channel to set up the token mapping
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from pathlib import Path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = [
    "https://www.googleapis.com/auth/youtube.force-ssl",
    "https://www.googleapis.com/auth/yt-analytics.readonly",
]

def authenticate_channel(token_name):
    """
    Authenticate a specific channel and save token
    
    Args:
        token_name: Name of the token file (e.g., 'aitools', 'finance', 'sleepsounds')
    """
    root = Path(__file__).resolve().parents[1]
    from config_loader import get_oauth_credentials
    secrets = get_oauth_credentials()

    if token_name == "main":
        token_path = root / "out" / "youtube_token.json"
    else:
        token_path = root / "out" / f"youtube_token_{token_name}.json"

    token_path.parent.mkdir(exist_ok=True)
    
    print(f"\n{'='*70}")
    print(f"Authenticating channel: {token_name}")
    print(f"Token will be saved to: {token_path.name}")
    print(f"{'='*70}\n")
    
    # Start OAuth flow
    flow = InstalledAppFlow.from_client_secrets_file(str(secrets), SCOPES)
    print("Opening browser for authentication...")
    print("Please select the CORRECT channel account in the browser!")
    
    creds = flow.run_local_server(port=0)
    
    # Verify which channel we authenticated
    youtube = build("youtube", "v3", credentials=creds)
    channel = youtube.channels().list(part='snippet,statistics', mine=True).execute()
    
    if channel.get('items'):
        item = channel['items'][0]
        channel_name = item['snippet']['title']
        channel_id = item['id']
        subs = item['statistics'].get('subscriberCount', '0')
        
        print(f"\n✅ Successfully authenticated!")
        print(f"   Channel: {channel_name}")
        print(f"   ID: {channel_id}")
        print(f"   Subscribers: {subs}")
        
        # Save token
        token_path.write_text(creds.to_json(), encoding='utf-8')
        print(f"\n✅ Token saved to: {token_path}")
        return True
    else:
        print("\n❌ No channel found for this account!")
        return False

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python setup_channel_auth.py <token_name>")
        print("\nAvailable token names:")
        print("  - aitools     (for AI Tools Daily)")
        print("  - finance     (for Finance Freedom)")
        print("  - sleepsounds (for Sleep Sounds Haven)")
        print("  - main        (for Gooogle Aashaan - already working)")
        sys.exit(1)
    
    token_name = sys.argv[1]
    
    if token_name not in ['main', 'aitools', 'finance', 'sleepsounds']:
        print(f"ERROR: Invalid token name '{token_name}'")
        print("Must be one of: main, aitools, finance, sleepsounds")
        sys.exit(1)
    
    success = authenticate_channel(token_name)
    
    if success:
        print(f"\n🎉 Channel '{token_name}' is ready to use!")
    else:
        print(f"\n❌ Failed to authenticate '{token_name}'")
