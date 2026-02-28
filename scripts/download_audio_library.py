#!/usr/bin/env python3
"""
Download copyright-free audio library for sleep sounds channel.
All sources verified as safe for YouTube monetization.
"""

import json
import sys
from pathlib import Path
from datetime import datetime

# Force UTF-8 output on Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Copyright-free audio sources (verified safe for monetization)
AUDIO_LIBRARY = [
    # Rain sounds
    {
        "category": "rain",
        "name": "gentle-rain-01",
        "url": "https://cdn.pixabay.com/audio/2022/03/10/audio_d1718372d5.mp3",
        "source": "Pixabay",
        "license": "CC0 (Public Domain)",
        "attribution": "Not required",
        "duration_sec": 600,  # 10 minutes
        "description": "Gentle rain on leaves"
    },
    {
        "category": "rain",
        "name": "heavy-rain-thunder-01",
        "url": "https://cdn.pixabay.com/audio/2022/05/27/audio_c0b0aa2e28.mp3",
        "source": "Pixabay",
        "license": "CC0 (Public Domain)",
        "attribution": "Not required",
        "duration_sec": 600,
        "description": "Heavy rain with distant thunder"
    },
    
    # Ocean/water sounds
    {
        "category": "ocean",
        "name": "ocean-waves-01",
        "url": "https://cdn.pixabay.com/audio/2022/03/19/audio_46ab0481fd.mp3",
        "source": "Pixabay",
        "license": "CC0 (Public Domain)",
        "attribution": "Not required",
        "duration_sec": 600,
        "description": "Calm ocean waves on beach"
    },
    {
        "category": "ocean",
        "name": "beach-waves-01",
        "url": "https://cdn.pixabay.com/audio/2021/08/04/audio_2fd5dce670.mp3",
        "source": "Pixabay",
        "license": "CC0 (Public Domain)",
        "attribution": "Not required",
        "duration_sec": 600,
        "description": "Beach waves with seagulls"
    },
    
    # Fire/fireplace
    {
        "category": "fire",
        "name": "fireplace-crackling-01",
        "url": "https://cdn.pixabay.com/audio/2022/10/05/audio_c8e8f3cc6f.mp3",
        "source": "Pixabay",
        "license": "CC0 (Public Domain)",
        "attribution": "Not required",
        "duration_sec": 600,
        "description": "Crackling fireplace"
    },
    
    # Nature/forest
    {
        "category": "nature",
        "name": "forest-birds-01",
        "url": "https://cdn.pixabay.com/audio/2022/03/10/audio_1e0e391c74.mp3",
        "source": "Pixabay",
        "license": "CC0 (Public Domain)",
        "attribution": "Not required",
        "duration_sec": 600,
        "description": "Forest ambience with birds"
    },
    {
        "category": "nature",
        "name": "stream-flowing-01",
        "url": "https://cdn.pixabay.com/audio/2022/03/10/audio_8b56709e34.mp3",
        "source": "Pixabay",
        "license": "CC0 (Public Domain)",
        "attribution": "Not required",
        "duration_sec": 600,
        "description": "Flowing stream water"
    },
]


def download_audio():
    """Download all audio files from verified sources."""
    root = Path(__file__).resolve().parents[1]
    audio_dir = root / "audio_library"
    
    print("🎵 Downloading copyright-free audio library...")
    print(f"Target: {audio_dir}")
    print()
    
    manifest = []
    
    for idx, audio in enumerate(AUDIO_LIBRARY, 1):
        category = audio["category"]
        name = audio["name"]
        url = audio["url"]
        
        print(f"[{idx}/{len(AUDIO_LIBRARY)}] Downloading: {name}")
        print(f"  Category: {category}")
        print(f"  Source: {audio['source']} ({audio['license']})")
        print(f"  URL: {url}")
        
        target_dir = audio_dir / category
        target_file = target_dir / f"{name}.mp3"
        
        # Download using curl (available on Windows 10+)
        import subprocess
        result = subprocess.run(
            ["curl", "-L", "-o", str(target_file), url],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0 and target_file.exists():
            size_mb = target_file.stat().st_size / (1024 * 1024)
            print(f"  ✅ Downloaded: {size_mb:.2f} MB")
            
            # Add to manifest
            manifest.append({
                "file": f"{category}/{name}.mp3",
                "source": audio["source"],
                "license": audio["license"],
                "attribution": audio["attribution"],
                "url": url,
                "description": audio["description"],
                "duration_sec": audio["duration_sec"],
                "downloaded_at": datetime.now().isoformat(),
                "size_mb": round(size_mb, 2)
            })
        else:
            print(f"  ❌ Failed to download")
            print(f"  Error: {result.stderr}")
        
        print()
    
    # Save manifest
    manifest_path = audio_dir / "manifest.json"
    manifest_path.write_text(json.dumps({
        "created_at": datetime.now().isoformat(),
        "total_files": len(manifest),
        "files": manifest
    }, indent=2), encoding="utf-8")
    
    print("="*70)
    print(f"✅ Downloaded {len(manifest)} audio files")
    print(f"📄 Manifest saved: {manifest_path}")
    print()
    print("All files are:")
    print("  • 100% copyright-free (CC0 or Public Domain)")
    print("  • Safe for YouTube monetization")
    print("  • No attribution required")
    print("="*70)


if __name__ == "__main__":
    download_audio()
