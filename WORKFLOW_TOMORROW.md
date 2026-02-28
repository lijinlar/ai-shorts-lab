# YouTube Shorts Workflow for Tomorrow (Feb 17, 8 AM)

## Semi-Automated Method (Working!)

### Prerequisites
1. WanGP server running at http://localhost:7860
   - If not running: `cd C:\Users\lijin\.openclaw\workspace\Wan2GP && .\venv\Scripts\python.exe wgp.py`

### Workflow

**Terminal 1: Auto-Processor**
```bash
cd C:\Users\lijin\Projects\t2v-shorts-lab
python scripts/auto_process_wangp.py
```
Leave this running - it monitors WanGP outputs

**Browser: Generate Scenes**
1. Open http://localhost:7860
2. For each scene in your storyboard:
   - Copy prompt from storyboard JSON
   - Paste into WanGP prompt box
   - Click "Generate"
   - Wait 3-5 minutes
   - Script in Terminal 1 auto-processes it
3. Repeat for all scenes (typically 8 scenes per video)

**Terminal 1: After All Scenes**
- Press Ctrl+C to stop auto-processor
- It will show summary of processed scenes

**Terminal 2: Combine & Prepare for Upload**
```bash
python scripts/combine_and_upload.py
```
This creates the final Shorts-ready video in `out/`

**Upload to YouTube**
```bash
python scripts/youtube_upload.py \
  --file "out/video_TIMESTAMP_FINAL.mp4" \
  --title "Your Video Title #Shorts" \
  --description "Description here" \
  --keywords "shorts" "dogs" "pets" \
  --privacyStatus public
```

### Time Estimate
- 4 videos × 8 scenes each = 32 scenes
- 5 minutes per scene = 160 minutes (~2.5 hours)
- Post-processing: 10 minutes
- **Total: ~3 hours**

### For Multiple Videos
Repeat the process for each video:
1. Generate 8 scenes
2. Ctrl+C the auto-processor
3. Run combine_and_upload.py
4. Upload
5. Clean out/processed_scenes/ folder
6. Start again for next video

### Automation Status
- ✅ Scene organization: Automated
- ✅ Caption addition: Automated
- ✅ Shorts format conversion: Automated
- ⚠️ Scene generation: Manual (WanGP UI)
- ✅ Upload: Script available

**The only manual part is clicking "Generate" in the UI for each scene.**

---

## Full Automation (Not Working Yet)
WanGP `--process` CLI mode has issues. Working on debugging this for future full automation.

Once fixed, will be able to run:
```bash
python scripts/full_daily_pipeline.py
```
And everything happens automatically.

---
Last updated: Feb 16, 2026 - 11:10 PM
