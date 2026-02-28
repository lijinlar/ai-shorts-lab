import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

tokens = [
    ('aitools', 'youtube_token_aitools.json'),
    ('finance', 'youtube_token_finance.json'),
    ('sleepsounds', 'youtube_token_sleepsounds.json')
]

for name, token in tokens:
    creds = Credentials.from_authorized_user_file(f'out/{token}', ['https://www.googleapis.com/auth/youtube.force-ssl'])
    yt = build('youtube', 'v3', credentials=creds)
    channel = yt.channels().list(part='snippet', mine=True).execute()['items'][0]
    print(f'{name} token -> {channel["snippet"]["title"]} (ID: {channel["id"]})')
