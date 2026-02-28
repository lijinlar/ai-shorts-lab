# WanGP Integration Status - Feb 16, 2026 (10:45 PM)

## What's Working ✅

### 1. Video Format Conversion Scripts
- **Location**: `scripts/`
- **Scripts created**:
  - `add_captions.py` - Adds text captions to videos (FFmpeg drawtext)
  - `convert_to_shorts_format.py` - Converts to 1080x1920 Shorts format with blurred background
  
### 2. Individual Scene Generation (Manual Process)
**Proven working method from Feb 16 testing:**
1. Start WanGP server: 
   ```
   cd C:\Users\lijin\.openclaw\workspace\Wan2GP
   .\venv\Scripts\python.exe wgp.py
   ```
2. Generate scenes through UI at http://localhost:7860
3. Use ultra-detailed prompts (emphasize main subject repeatedly)
4. Clean outputs directory before each generation
5. Pick up generated video from `outputs/`

**Test results:**
- Successfully generated 40-second Short (8 scenes)
- Successfully uploaded to YouTube: https://youtube.com/watch?v=-V1VrtJUt-Y
- Shorts format conversion working correctly

### 3. Upload Scripts
- `scripts/youtube_upload.py` - Working (OAuth tokens refreshed Feb 16)
- Uploaded test videos successfully

### 4. Daily Pipeline Structure
- `scripts/full_daily_pipeline.py` - Updated to use WanGP
- `scripts/batch_generate_upload_series_wangp.py` - Created for batch processing

## What's NOT Working ❌

### WanGP Batch/CLI Mode (`--process`)
**Issue**: WanGP `--process` mode hangs indefinitely with no output

**What we tried:**
1. `--process queue.zip` with JSON manifest → hangs
2. Direct API calls via gradio_client → server crashes
3. subprocess calls with queue files → hangs

**Root cause**: Unknown - possibly:
- Queue JSON format incorrect
- WanGP batch mode bug
- Windows-specific issue
- Profile/model loading issue

**Status**: Blocked until we debug WanGP internals or find alternative

## For Tomorrow's 8 AM Task

### Option 1: Manual Generation (Recommended for now)
**Time required**: ~2 hours for 4 videos

1. **Get storyboard**:
   ```bash
   cd C:\Users\lijin\Projects\t2v-shorts-lab
   # Check for today's storyboard in storyboards/
   ```

2. **Start WanGP**:
   ```bash
   cd C:\Users\lijin\.openclaw\workspace\Wan2GP
   .\venv\Scripts\python.exe wgp.py
   ```

3. **For each video** (4 total):
   - Open http://localhost:7860
   - For each scene in the video:
     - Copy prompt from storyboard JSON
     - Generate in WanGP (5-7 min per scene)
     - Wait for completion
     - Download from outputs/
   
4. **Post-process each video**:
   ```bash
   # Concatenate scenes (if multiple)
   ffmpeg -f concat -safe 0 -i concat.txt -c copy video_concat.mp4
   
   # Add captions
   python scripts/add_captions.py video_concat.mp4 video_captioned.mp4 <caption_json>
   
   # Convert to Shorts format
   python scripts/convert_to_shorts_format.py video_captioned.mp4 video_final.mp4
   ```

5. **Upload**:
   ```bash
   python scripts/youtube_upload.py --file video_final.mp4 --title "..." --description "..." --keywords "shorts" --privacyStatus public
   ```

### Option 2: Semi-Automated (If batch mode gets fixed tonight)
Run the full pipeline:
```bash
python scripts/full_daily_pipeline.py
```

This will attempt to use WanGP batch mode. **Currently blocked.**

## Next Steps to Fix Automation

1. **Debug WanGP `--process` mode**:
   - Check WanGP logs for errors
   - Try different queue.json formats
   - Test with WanGP developer examples
   - Contact WanGP maintainers if needed

2. **Alternative: Gradio API approach**:
   - Get WanGP server running stable
   - Use gradio_client to call generation function
   - Stream results back
   - (Attempted, server crashed - needs investigation)

3. **Alternative: Interactive automation**:
   - Use pyautogui to automate the WanGP UI
   - Less reliable but might work

## Summary

**For tomorrow (8 AM)**: Use **Manual Generation (Option 1)**
- All the pieces work individually
- Just needs manual coordination
- Proven successful (we uploaded test video today)

**Longer term**: Fix WanGP batch processing for full automation
- Current blocker: `--process` mode hanging
- Needs deeper WanGP debugging

---
Last updated: Feb 16, 2026 - 10:45 PM
