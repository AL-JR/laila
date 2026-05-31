# Laila — Handoff Notes

## What Laila Does
Automated video dubbing pipeline: downloads a video, isolates vocals, transcribes,
translates, clones the speaker's voice, and produces a dubbed MP4 with synced audio.

---

## Current Pipeline (in order)
1. Download video (YouTube or local)
2. Extract audio (ffmpeg → WAV)
3. Isolate vocals (Demucs `htdemucs` — removes background music)
4. Transcribe (Whisper `medium` → timed segments with start/end/text)
5. [Optional] Diarize speakers (pyannote.audio — multi-speaker mode)
6. Translate each segment (MarianMT Helsinki-NLP)
7. Extract voice cloning sample per speaker (from clean vocals track)
8. Synthesise TTS per segment (XTTS v2 with voice cloning + time-stretch to fit)
9. Compose audio timeline (each clip placed at original timestamp via ffmpeg adelay/amix)
10. Merge composed audio into original video → final dubbed MP4

---

## Key Files
```
laila_core/
  app.py                          # Entry point + configuration flags
  audio_utils/
    __init__.py                   # seconds_to_hms() shared utility
    separate_vocals.py            # Demucs vocal separation
    diarize.py                    # pyannote speaker diarization
    align_speakers.py             # Assigns speaker labels to Whisper segments
    speaker_samples.py            # Extracts best voice sample per speaker
    compose_timeline.py           # Places TTS clips at correct timestamps
  transcription/whisper_transcribe.py
  translation/translate_text.py   # translate_segments() + translate_text()
  tts/generate_voice.py           # generate_segment_audio() with time-stretch
  video_utils/
    download_youtube.py
    extract_audio.py
    speaker_clip.py
    merge_audio_video.py
```

---

## Configuration (top of app.py)
```python
LOCAL_VIDEO  = "test.mp4"   # or None to download from YouTube
YOUTUBE_URL  = "..."
SOURCE_LANG  = "en"
TARGET_LANG  = "es"
MULTI_SPEAKER = False       # Set True for per-speaker voice cloning
MIN_SPEAKERS = None         # Optional hint for diarization accuracy
MAX_SPEAKERS = None
```

---

## How to Run
```bash
cd laila_core
PYTHONUTF8=1 python app.py
```
`PYTHONUTF8=1` is required on Windows to avoid encoding errors with Unicode log chars.

---

## First-Run Downloads (cached after first run)
| Model | Size | Location |
|---|---|---|
| Demucs htdemucs | ~80MB | `~/.cache/torch/hub/checkpoints/` |
| Whisper medium | ~1.4GB | `~/.cache/whisper/` |
| MarianMT opus-mt-en-es | ~312MB | `~/.cache/huggingface/hub/` |
| XTTS v2 | ~1.8GB | `~/.local/share/tts/` |

Need ~4GB free on first run. ~2GB free disk on C: is sufficient once cached.

---

## Where We Left Off (updated 2026-05-30)
**Full pipeline working end-to-end with XTTS v2 cross-lingual voice cloning.**

Environment situation:
- `.venv` at project root using `uv` with Python 3.11 ✓
- XTTS v2 (Coqui TTS 0.22.0) installed via MeloTTS dependency ✓
- `xtts.py` patched: `strict=False` in `load_checkpoint` to handle checkpoint/version mismatch ✓
- All 9 pipeline steps confirmed working ✓

To run:
```
cd C:\Users\alber\Documents\Portfolio\laila
.venv\Scripts\activate
PYTHONUTF8=1 python laila_core/app.py
```

Output: `laila_core/output/final_dubbed_video.mp4`

---

## Known Issues / Next Steps
1. **Full pipeline run in progress** — verifying Steps 5–9 (translation → TTS → timeline → merge).

2. **Voice cloning quality** — XTTS v2 works best with 15–30s of clean speech.
   The sample is now auto-selected from the longest Whisper segment on the clean
   vocals track, which should help. May still need tuning for short videos.

3. **Multi-speaker mode** — implemented but untested. To enable:
   - `pip install pyannote.audio`
   - Accept model terms: https://huggingface.co/pyannote/speaker-diarization-3.1
   - Set env var: `HF_TOKEN=your_token`
   - Set `MULTI_SPEAKER = True` in app.py
   - Optionally set `MIN_SPEAKERS` / `MAX_SPEAKERS` for better accuracy

4. **CLI interface** — currently all config is hardcoded at top of app.py.
   A good next step is adding `argparse` so the user can pass `--video`, `--src`,
   `--tgt`, `--multi-speaker` etc. from the command line.

5. **Subtitle/SRT export** — the timed segments are already in memory after Step 4.
   Easy addition: write them to an `.srt` file alongside the dubbed video.

6. **YouTube download** — yt-dlp occasionally fails due to YouTube's SSAP experiment
   (server-side ads blocking certain formats). The format selector has been broadened
   but if it still fails, use `LOCAL_VIDEO` with a manually downloaded file.

---

## Dependencies
```
openai-whisper
ffmpeg-python
yt-dlp
demucs
transformers
sentencepiece
torch
f5-tts
nltk
numpy
scipy
pyannote.audio   # optional, multi-speaker only — requires HF_TOKEN
```

Install: `pip install -r laila_core/requirements.txt && pip install demucs`
