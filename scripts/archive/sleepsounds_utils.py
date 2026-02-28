#!/usr/bin/env python3
"""
Sleep Sounds Channel Utilities
Handles audio selection, video generation, and proper attribution.
"""

import json
import random
from pathlib import Path
from typing import Dict, List


def get_audio_library() -> Dict:
    """Load audio library manifest."""
    root = Path(__file__).resolve().parents[1]
    manifest_path = root / "audio_library" / "manifest.json"
    
    if not manifest_path.exists():
        raise FileNotFoundError(f"Audio manifest not found: {manifest_path}")
    
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def select_audio_for_today(category: str = None) -> Dict:
    """
    Select an audio file for today's upload.
    Uses rotation to avoid repeating same audio too frequently.
    
    Args:
        category: Optional category filter (rain, ocean, fire, nature)
    
    Returns:
        Dict with audio file info and attribution
    """
    library = get_audio_library()
    files = library["files"]
    
    # Filter by category if specified
    if category:
        files = [f for f in files if f["category"] == category]
    
    if not files:
        raise ValueError(f"No audio files found for category: {category}")
    
    # For now, random selection. TODO: Add rotation tracking to avoid repeats
    selected = random.choice(files)
    
    return {
        "file_path": Path("audio_library") / selected["category"] / selected["file"],
        "category": selected["category"],
        "description": selected["description"],
        "artist": selected["artist"],
        "attribution": library["attribution_text"],
        "size_mb": selected["size_mb"]
    }


def generate_video_description(audio_info: Dict, video_title: str) -> str:
    """
    Generate YouTube video description with proper attribution.
    
    Args:
        audio_info: Audio file info from select_audio_for_today()
        video_title: Title of the video
    
    Returns:
        Complete video description with attribution
    """
    
    category_descriptions = {
        "rain": "Perfect for sleep, relaxation, meditation, or focus. Let the soothing sound of rain help you unwind.",
        "ocean": "Relax to the calming sounds of ocean waves. Perfect for sleep, meditation, stress relief, or studying.",
        "fire": "Cozy fireplace sounds for relaxation, sleep, or creating a warm ambience. Perfect for cold nights.",
        "nature": "Natural sounds to help you relax, focus, or sleep. Immerse yourself in the peaceful sounds of nature."
    }
    
    description = f"""{video_title}

{category_descriptions.get(audio_info['category'], 'Relax and unwind with these soothing sounds.')}

🎧 Use headphones for the best experience
⏰ Perfect for:
• Sleep & Insomnia Relief
• Meditation & Mindfulness
• Study & Focus
• Stress Relief & Relaxation
• Background Ambience

---

📢 Audio Credit:
{audio_info['attribution']}
Artist: {audio_info['artist']}

---

#sleepsounds #relaxation #meditation #study #ambience #{audio_info['category']}sounds
"""
    
    return description.strip()


def get_visual_prompt_for_audio(audio_info: Dict) -> str:
    """
    Generate AI visual prompt matching the audio theme.
    
    Args:
        audio_info: Audio file info from select_audio_for_today()
    
    Returns:
        Prompt for SDXL/SVD video generation
    """
    
    prompts = {
        "rain": [
            "Rain falling gently on window glass, water droplets, peaceful grey clouds, soft natural lighting",
            "Raindrops on green leaves, forest canopy, misty atmosphere, calming nature scene",
            "Rain falling on calm lake surface, ripples forming, peaceful grey sky background",
        ],
        "ocean": [
            "Calm ocean waves washing onto sandy beach, sunset colors, peaceful seascape",
            "Ocean water surface view, gentle waves, blue sky, serene horizon",
            "Beach waves rolling in slow motion, foam on sand, tropical paradise",
        ],
        "fire": [
            "Crackling fireplace with glowing embers, warm orange flames, cozy ambience",
            "Campfire burning steadily, wood logs, dancing flames, dark background",
            "Close-up of burning fire, orange and red flames, peaceful warmth",
        ],
        "nature": [
            "Peaceful forest stream flowing over rocks, green moss, dappled sunlight",
            "Birds in lush green forest, sunlight through tree canopy, serene nature",
            "Flowing river through forest, smooth water, natural landscape, tranquil scene",
        ]
    }
    
    category_prompts = prompts.get(audio_info["category"], prompts["nature"])
    return random.choice(category_prompts)


def get_video_title_for_audio(audio_info: Dict, duration_min: int = 60) -> str:
    """
    Generate catchy video title for sleep sounds video.
    
    Args:
        audio_info: Audio file info from select_audio_for_today()
        duration_min: Video duration in minutes
    
    Returns:
        YouTube video title (optimized for SEO)
    """
    
    title_templates = {
        "rain": [
            f"Rain Sounds for Sleeping {duration_min} Minutes - Relaxing Rain Ambience for Sleep & Stress Relief",
            f"Gentle Rain Sounds {duration_min} Min - Sleep, Study, Relax - Peaceful Rain Ambience",
            f"Rain on Window {duration_min} Minutes - Sleep Sounds, Rain for Studying, Relaxation",
        ],
        "ocean": [
            f"Ocean Waves Sounds for Sleeping {duration_min} Minutes - Relaxing Sea Waves for Sleep & Meditation",
            f"Calming Ocean Sounds {duration_min} Min - Beach Waves for Sleep, Study, Relaxation",
            f"Beach Waves {duration_min} Minutes - Ocean Sounds for Sleep, Focus, Stress Relief",
        ],
        "fire": [
            f"Fireplace Sounds {duration_min} Minutes - Crackling Fire for Sleep, Study, Relaxation",
            f"Cozy Fireplace Ambience {duration_min} Min - Fire Sounds for Sleeping, Reading, Relaxing",
            f"Crackling Fire {duration_min} Minutes - Fireplace Sounds for Sleep & Winter Ambience",
        ],
        "nature": [
            f"Nature Sounds for Sleeping {duration_min} Minutes - Forest Ambience for Sleep & Relaxation",
            f"Peaceful Nature Sounds {duration_min} Min - Birds, Stream, Forest - Sleep, Study, Meditate",
            f"Forest Sounds {duration_min} Minutes - Relaxing Nature Ambience for Sleep & Focus",
        ]
    }
    
    templates = title_templates.get(audio_info["category"], title_templates["nature"])
    return random.choice(templates)


if __name__ == "__main__":
    # Test the functions
    print("Testing Sleep Sounds Utilities\n")
    
    audio = select_audio_for_today()
    print(f"Selected Audio: {audio['file_path']}")
    print(f"Category: {audio['category']}")
    print(f"Artist: {audio['artist']}")
    print()
    
    title = get_video_title_for_audio(audio)
    print(f"Video Title:\n{title}\n")
    
    description = generate_video_description(audio, title)
    print(f"Video Description:\n{description}\n")
    
    prompt = get_visual_prompt_for_audio(audio)
    print(f"Visual Prompt:\n{prompt}\n")
