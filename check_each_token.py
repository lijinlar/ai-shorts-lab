import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from pathlib import Path

tokens = [
    'youtube_token.json',
    'youtube_token_aitools.json',
    'youtube_token_dogs.json',
    'youtube_token_finance.json',
    'youtube_token_sleepsounds.json'
]

print("="*80)
print("COMPLETE TOKEN MAPPING")
print("="*80)

for token_file in tokens:
    token_path = Path(f'out/{token_file}')
    token_name = token_file.replace('youtube_token_', '').replace('youtube_token.json', 'MAIN').replace('.json', '')
    
    try:
        creds = Credentials.from_authorized_user_file(
            str(token_path), 
            ['https://www.googleapis.com/auth/youtube.force-ssl']
        )
        yt = build('youtube', 'v3', credentials=creds)
        channel = yt.channels().list(part='snippet,statistics', mine=True).execute()
        
        if channel.get('items'):
            item = channel['items'][0]
            print(f"\n{token_name}:")
            print(f"  File: {token_file}")
            print(f"  Channel: {item['snippet']['title']}")
            print(f"  ID: {item['id']}")
            print(f"  Stats: {item['statistics'].get('subscriberCount', '0')} subs, {item['statistics'].get('videoCount', '0')} videos")
            
    except Exception as e:
        print(f"\n{token_name}: ERROR - {e}")

print("\n" + "="*80)
