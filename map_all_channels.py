import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from pathlib import Path

# Check all token files
token_dir = Path('out')
all_tokens = list(token_dir.glob('youtube_token*.json'))

print("="*70)
print("CHANNEL MAPPING - ALL TOKENS")
print("="*70)

channels = {}
for token_file in all_tokens:
    token_name = token_file.stem.replace('youtube_token', '').replace('_', '') or 'main'
    
    try:
        creds = Credentials.from_authorized_user_file(
            str(token_file), 
            ['https://www.googleapis.com/auth/youtube.force-ssl']
        )
        yt = build('youtube', 'v3', credentials=creds)
        channel_info = yt.channels().list(part='snippet,statistics', mine=True).execute()
        
        if channel_info.get('items'):
            item = channel_info['items'][0]
            channel_id = item['id']
            channel_name = item['snippet']['title']
            subs = item['statistics'].get('subscriberCount', '0')
            videos = item['statistics'].get('videoCount', '0')
            
            if channel_id not in channels:
                channels[channel_id] = {
                    'name': channel_name,
                    'id': channel_id,
                    'subs': subs,
                    'videos': videos,
                    'tokens': []
                }
            
            channels[channel_id]['tokens'].append(token_name)
            
    except Exception as e:
        print(f"ERROR with {token_name}: {e}")

print(f"\nFound {len(channels)} unique channels:\n")

for idx, (channel_id, info) in enumerate(channels.items(), 1):
    print(f"{idx}. {info['name']}")
    print(f"   ID: {channel_id}")
    print(f"   Stats: {info['subs']} subs, {info['videos']} videos")
    print(f"   Tokens: {', '.join(info['tokens'])}")
    print()

print("="*70)
