# wan2shorts 🐕📱

> Turn text prompts into viral YouTube Shorts — fully automated, runs daily.

![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Platform](https://img.shields.io/badge/platform-Windows%20%28CUDA%29-lightgrey)

**wan2shorts** is an end-to-end pipeline that takes a JSON storyboard of scene prompts and automatically generates, captions, formats, and uploads YouTube Shorts — no manual video editing required.

Powered by [WanGP](https://github.com/deepbeepmeep/Wan2GP) (Wan2.1 14B), FFmpeg, and the YouTube Data API.

---

## 🎬 Live Example

All videos on **[@GoooogleAashaan](https://youtube.com/@GoooogleAashaan)** are generated entirely by this pipeline — no stock footage, no manual editing.

---

## How It Works

```
Storyboard JSON
      │
      ▼
WanGP (Wan2.1 14B)          ← generates each scene as a video clip
      │
      ▼
FFmpeg concat                ← joins scene clips into one video
      │
      ▼
Caption overlay              ← adds text captions with FFmpeg drawtext
      │
      ▼
Portrait conversion          ← converts 832×480 landscape → 1080×1920 (9:16)
(blurred background)           with blurred background fill
      │
      ▼
YouTube upload               ← uploads as public Short via YouTube API
```

---

## ✨ Features

- **Text-to-video**: Write scene prompts → get a complete Short
- **Auto-captions**: Scene text overlaid on video
- **Portrait conversion**: Automatic landscape → 1080×1920 Shorts format
- **YouTube API integration**: Uploads directly, sets title/description/tags/privacy
- **Daily automation**: Run on a schedule, report results
- **Low-VRAM mode**: Works on 6GB GPUs with env overrides
- **Batch generation**: Generate and upload multiple videos in one run

---

## Requirements

- **OS**: Windows 10/11 (WanGP requires Windows + CUDA)
- **GPU**: NVIDIA with 8GB+ VRAM (6GB works — see [Low-VRAM Mode](#low-vram-mode))
- **Python**: 3.10+
- **FFmpeg**: Installed and in `PATH`
- **WanGP**: Installed separately — see [WanGP setup](https://github.com/deepbeepmeep/Wan2GP)
- **YouTube Data API v3** credentials (OAuth2)

---

## Installation

```bash
git clone https://github.com/lijinlar/ai-shorts-lab
cd ai-shorts-lab
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

---

## Setup

### 1. Install WanGP

Follow the [WanGP installation guide](https://github.com/deepbeepmeep/Wan2GP). By default, wan2shorts expects WanGP at:

```
C:\Users\<you>\.openclaw\workspace\Wan2GP\
```

To change this, edit `WAN2GP_DIR` in `scripts/generate_shorts_wangp.py`.

### 2. YouTube Authentication

```bash
python scripts/youtube_auth.py --channel main
```

This opens a browser to authorize via OAuth2. The token is saved to `out/youtube_token.json`.

For multiple channels, use `--channel dogs`, `--channel aitools`, etc. — each gets its own token file.

---

## Storyboard Format

Storyboards are JSON files that define what to generate. See `storyboards/example.json` for a full example.

```json
{
  "default": {
    "sceneSeconds": 3,
    "fps": 24,
    "width": 480,
    "height": 832,
    "backend": "wangp",
    "upscale4k": false
  },
  "videos": [
    {
      "title": "Dog Reunites With Owner After 18 Months 😭 #shorts",
      "description": "Emotional dog reunion. #shorts #dog",
      "scenes": [
        {
          "prompt": "Extreme close-up: a golden retriever's nose twitches near a front door, amber light, static camera. Ultra-realistic, photorealistic, cinematic 4K, shallow depth of field, smooth motion, sharp focus"
        },
        {
          "prompt": "Medium wide: soldier drops duffel bag at door, retriever freezes with ears perked, tail wagging, warm hallway light, slow push-in. Ultra-realistic, photorealistic, cinematic 4K, shallow depth of field, smooth motion, sharp focus"
        }
      ]
    }
  ]
}
```

### Prompt tips for best results

Each scene prompt should include:
1. **Shot type** — `Extreme close-up`, `Medium wide`, `Low angle`, etc.
2. **Subject detail** — breed, color, expression, body language
3. **Action** — precise movement with speed/direction
4. **Environment** — lighting, surfaces, time of day
5. **Camera motion** — `static`, `slow push-in`, `tracking shot`, etc.
6. **Quality suffix** — always end with: `Ultra-realistic, photorealistic, cinematic 4K, shallow depth of field, smooth motion, sharp focus`

---

## Running

### Generate and upload from a storyboard

```bash
python scripts/full_daily_pipeline.py --storyboard storyboards/example.json
```

### Upload as unlisted (for testing)

```bash
python scripts/full_daily_pipeline.py --storyboard storyboards/example.json --privacy unlisted
```

### Generate a single video directly

```bash
python scripts/generate_shorts_wangp.py storyboards/example.json out/my_video.mp4
```

### Daily automation

Set up a scheduled task (Windows Task Scheduler) or cron to run:

```bash
python scripts/full_daily_pipeline.py --storyboard storyboards/todays_storyboard.json
```

---

## Low-VRAM Mode

If you have a 6GB GPU or hit CUDA out-of-memory errors, set these environment variables before running:

```bash
set WANGP_MODEL_TYPE=t2v_1.3B
set WANGP_STEPS=10
set WANGP_CFG=4.0
```

Or in PowerShell:

```powershell
$env:WANGP_MODEL_TYPE = "t2v_1.3B"
$env:WANGP_STEPS = "10"
```

This switches to the 1.3B parameter model and reduces inference steps — much lower VRAM usage, slightly lower quality.

---

## Project Structure

```
ai-shorts-lab/
├── scripts/
│   ├── full_daily_pipeline.py          # Main entry point — runs the full pipeline
│   ├── generate_shorts_wangp.py        # Core: storyboard → video via WanGP
│   ├── batch_generate_upload_series_wangp.py  # Batch multi-video generation
│   ├── add_captions.py                 # FFmpeg caption overlay
│   ├── concat_scenes.py                # FFmpeg scene concatenation
│   ├── convert_to_shorts_format.py     # Landscape → 1080×1920 portrait
│   ├── youtube_upload.py               # YouTube API upload
│   ├── youtube_auth.py                 # OAuth2 token setup
│   ├── youtube_analytics_report.py     # Performance analytics
│   ├── combine_and_upload.py           # Combine scenes + upload in one step
│   ├── wangp_generate_scene.py         # Low-level WanGP scene generator
│   ├── auto_process_wangp.py           # WanGP queue auto-processor
│   ├── daily_youtube_automation.py     # Alternate daily automation entry
│   └── archive/                        # Experimental/superseded scripts
├── storyboards/
│   └── example.json                    # Example storyboard — start here
├── out/                                # Generated videos and tokens (gitignored)
├── requirements.txt
└── README.md
```

---

## Known Quirks

- **WanGP always outputs 832×480** — the model generates landscape video regardless of the `width`/`height` params in the storyboard. The pipeline automatically converts to 1080×1920 portrait using a blurred background fill. This is expected behavior.

- **No audio by default** — WanGP generates silent video. Background music support is not yet built in. Add audio via FFmpeg separately if needed.

- **GPU memory spikes** — each scene is generated independently to avoid OOM. Large frame counts (>81 frames) can still crash on 8GB GPUs.

- **YouTube Shorts classification** — YouTube automatically classifies videos as Shorts if they are ≤60 seconds and in portrait (9:16) format. The `#shorts` tag in the title/description helps but is not strictly required.

---

## License

MIT — free to use, modify, and build on.

---

## Credits

- Video generation: [WanGP / Wan2.1](https://github.com/deepbeepmeep/Wan2GP) by deepbeepmeep
- YouTube API: Google YouTube Data API v3
- Video processing: FFmpeg
