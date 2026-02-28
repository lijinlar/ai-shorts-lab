"""
Convert horizontal video to vertical Shorts format with blurred background (TikTok style)
"""
import subprocess
import sys
from pathlib import Path

def convert_to_shorts(input_video: str, output_video: str):
    """
    Convert video to 9:16 vertical format with blurred background
    
    Args:
        input_video: Path to input video (any aspect ratio)
        output_video: Path to output video (1080x1920)
    """
    
    # FFmpeg filter complex (TikTok style for HORIZONTAL videos):
    # 1. [bg] - Scale to 1080 width, blur heavily, then scale/crop to 1080x1920
    # 2. [fg] - Scale original to 1080 width (keeps it horizontal)
    # 3. Overlay fg on bg, centered vertically
    # Result: Original video fills WIDTH, blurred background fills TOP and BOTTOM gaps
    # This is the correct approach for landscape videos -> portrait Shorts
    
    cmd = [
        "ffmpeg",
        "-i", input_video,
        "-filter_complex",
        (
            "[0:v]scale=1080:-1,boxblur=30:5,"
            "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920[bg];"
            "[0:v]scale=1080:-1[fg];"
            "[bg][fg]overlay=0:(H-h)/2"
        ),
        "-c:a", "copy",
        "-y",
        output_video
    ]
    
    print(f"Converting to Shorts format...")
    print(f"Input:  {input_video}")
    print(f"Output: {output_video}")
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        output_path = Path(output_video)
        print(f"\nSuccess!")
        print(f"Size: {output_path.stat().st_size / 1_000_000:.1f} MB")
        print(f"Format: 1080x1920 (9:16) with blurred background")
        return True
    else:
        print(f"\nFailed:")
        print(result.stderr)
        return False

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python convert_to_shorts_format.py <input_video> <output_video>")
        sys.exit(1)
    
    input_video = sys.argv[1]
    output_video = sys.argv[2]
    
    success = convert_to_shorts(input_video, output_video)
    sys.exit(0 if success else 1)
