# Laila — Automated Video Dubbing System

An end-to-end pipeline that takes an English video, translates it to Spanish, clones the original speaker's voice, and produces a fully dubbed MP4 with the original background audio preserved.

## What It Does

1. Downloads a YouTube video (or uses a local file)
2. Separates vocals from background music using Demucs
3. Transcribes speech with Whisper (timed segments)
4. Translates each segment with MarianMT
5. Extracts a voice sample from the clean vocals track
6. Synthesises each translated segment with XTTS v2 — cross-lingual voice cloning (English voice → Spanish speech)
7. Time-stretches each clip to fit its original segment duration
8. Composes a synced audio timeline at the original timestamps
9. Mixes dubbed voice back with the original background music
10. Merges the final audio into the original video

## Pipeline Architecture

```
YouTube / Local File
        │
        ▼
┌─────────────────┐
│  Extract Audio  │  ffmpeg → WAV
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Separate Vocals│  Demucs htdemucs
│  (Demucs)       │  → vocals.wav + no_vocals.wav
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Transcribe     │  Whisper medium
│  (Whisper)      │  → timed segments [{start, end, text}]
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Translate      │  MarianMT Helsinki-NLP (EN→ES)
│  (MarianMT)     │  → translated segments
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Voice Cloning  │  XTTS v2 — cross-lingual cloning
│  TTS per segment│  English reference → Spanish output
│  + Time-stretch │  ffmpeg atempo to fit original timing
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Compose Timeline│  ffmpeg adelay/amix — place clips at
│                 │  original timestamps over silence base
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Mix Background │  ffmpeg amix — blend dubbed voice
│                 │  with original no_vocals track
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Merge Video    │  Replace audio track → final MP4
└─────────────────┘
```

## Project Structure

```
laila_core/
├── app.py                          # Entry point + configuration
├── audio_utils/
│   ├── __init__.py                 # seconds_to_hms() utility
│   ├── separate_vocals.py          # Demucs vocal separation
│   ├── compose_timeline.py         # Timeline composition + background mix
│   ├── diarize.py                  # Speaker diarization (optional)
│   ├── align_speakers.py           # Assign speaker labels to segments
│   └── speaker_samples.py          # Extract best voice sample per speaker
├── transcription/
│   └── whisper_transcribe.py       # Whisper speech-to-text
├── translation/
│   └── translate_text.py           # MarianMT translation
├── tts/
│   └── generate_voice.py           # XTTS v2 cross-lingual TTS + time-stretch
├── video_utils/
│   ├── download_youtube.py         # yt-dlp YouTube downloader
│   ├── extract_audio.py            # ffmpeg audio extraction
│   ├── speaker_clip.py             # Extract speaker sample clip
│   └── merge_audio_video.py        # Merge audio into video
├── downloads/                      # Downloaded videos (auto-created)
└── output/                         # Pipeline outputs (auto-created)
    ├── audio.wav                   # Extracted raw audio
    ├── demucs/
    │   ├── vocals.wav              # Isolated vocals
    │   └── no_vocals.wav           # Background music/ambient
    ├── samples/
    │   └── original_speaker.wav    # Voice cloning reference clip
    ├── segments/
    │   └── seg_NNNN.wav            # Per-segment TTS output
    ├── composed_audio.wav          # Dubbed voice timeline
    ├── final_audio.wav             # Dubbed voice + background mix
    └── final_dubbed_video.mp4      # Final output
```

## Installation

### Prerequisites

- **Python 3.11** (system Python 3.14 is too new for some dependencies)
- **FFmpeg** in PATH — [ffmpeg.org](https://ffmpeg.org/download.html)
- **uv** for environment management (recommended)

### Setup

```bash
# Create virtual environment with Python 3.11
uv venv --python 3.11

# Activate
.venv\Scripts\activate        # Windows
source .venv/bin/activate     # Mac/Linux

# Install dependencies
uv pip install ffmpeg-python openai-whisper yt-dlp transformers sentencepiece \
    torch nltk numpy scipy f5-tts demucs melotts
```

> **Note:** On first run, the following models are downloaded and cached:
> | Model | Size |
> |---|---|
> | Demucs htdemucs | ~80MB |
> | Whisper medium | ~1.4GB |
> | MarianMT opus-mt-en-es | ~312MB |
> | XTTS v2 | ~1.8GB |

## Usage

### Configuration

Edit the top of `laila_core/app.py`:

```python
YOUTUBE_URL  = "https://youtu.be/..."   # YouTube URL to process
LOCAL_VIDEO  = None                      # Or set to a local .mp4 path
SOURCE_LANG  = "en"
TARGET_LANG  = "es"
MULTI_SPEAKER = False                    # Set True for per-speaker cloning
```

### Run

```bash
cd laila_core
PYTHONUTF8=1 python app.py
```

`PYTHONUTF8=1` is required on Windows to avoid Unicode encoding errors.

Output video: `laila_core/output/final_dubbed_video.mp4`

### Multi-Speaker Mode

To enable per-speaker voice cloning:

1. `pip install pyannote.audio`
2. Accept model terms at https://huggingface.co/pyannote/speaker-diarization-3.1
3. Set `HF_TOKEN=your_token` environment variable
4. Set `MULTI_SPEAKER = True` in `app.py`

## Key Design Decisions

**Segment-level sync** — Each translated segment is synthesised and time-stretched independently to fit its original timestamp window, keeping dubbed speech in sync with the speaker's mouth movements.

**Cross-lingual voice cloning** — XTTS v2 takes an English reference clip and generates Spanish speech in that voice. The model handles phoneme mapping across languages natively, avoiding the "English accent on Spanish words" problem.

**Demucs vocal separation** — By separating vocals before transcription, Whisper gets cleaner input (less hallucination on music). The background track is preserved separately and mixed back at the end, so the final video sounds like the original minus the English voice.

## Performance

All benchmarks on CPU (no GPU):

| Step | Time (60s video) |
|---|---|
| Demucs separation | ~2–3 min |
| Whisper transcription | ~1 min |
| Translation | ~5s |
| XTTS v2 TTS (per segment) | ~7–10s |
| Timeline compose + mix | ~5s |

**Total for a 60s video: ~10–15 minutes on CPU.**

GPU would reduce XTTS generation to under 1s per segment.

## Known Limitations

- EN→ES only by default (other MarianMT language pairs are a one-line swap)
- CPU-only (no GPU acceleration currently)
- No CLI — config is hardcoded at the top of `app.py`
- Multi-speaker mode implemented but untested

## Credits

- [Whisper](https://github.com/openai/whisper) — OpenAI
- [MarianMT](https://huggingface.co/Helsinki-NLP) — Helsinki-NLP
- [XTTS v2](https://github.com/coqui-ai/TTS) — Coqui AI
- [Demucs](https://github.com/facebookresearch/demucs) — Meta Research
- [yt-dlp](https://github.com/yt-dlp/yt-dlp)
- [FFmpeg](https://ffmpeg.org)
