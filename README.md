# Laila - Automated Video Translation & Dubbing System

An automated pipeline that translates English videos to Spanish with optional voice cloning to preserve the original speaker's voice characteristics.

## Features

- ✅ Download videos from YouTube or use local files
- ✅ Extract and transcribe audio using OpenAI Whisper
- ✅ Translate text using MarianMT models
- ✅ Generate natural-sounding speech with XTTS v2
- ✅ **Optional voice cloning** to match original speaker
- ✅ Automatic audio-video synchronization
- ✅ Export final dubbed video

## Project Structure

```
laila/
├── app.py                          # Main pipeline orchestrator
├── requirements.txt                # Python dependencies
├── video_utils/
│   ├── download_youtube.py         # YouTube video downloader
│   ├── extract_audio.py            # Audio extraction from video
│   ├── speaker_clip.py             # Extract speaker sample for cloning
│   └── merge_audio_video.py        # Merge new audio with video
├── transcription/
│   └── whisper_transcribe.py       # Speech-to-text transcription
├── translation/
│   └── translate_text.py           # Text translation
├── tts/
│   └── generate_voice.py           # Text-to-speech synthesis
├── downloads/                      # Downloaded videos (auto-created)
└── output/                         # Generated files (auto-created)
    ├── audio.wav                   # Extracted audio
    ├── translated_voice_final.wav  # Generated speech
    ├── final_dubbed_video.mp4      # Final output
    └── samples/                    # Speaker samples
```

## Installation

### Prerequisites

1. **Python 3.8+**
2. **FFmpeg** - Must be installed and in PATH
   - Windows: Download from [ffmpeg.org](https://ffmpeg.org/download.html)
   - Mac: `brew install ffmpeg`
   - Linux: `sudo apt install ffmpeg`

### Setup

1. Clone or download the project

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Download NLTK data (first run only):
```python
python -c "import nltk; nltk.download('punkt')"
```

## Usage

### Basic Usage

1. Edit `app.py` configuration:
```python
YOUTUBE_URL = "https://www.youtube.com/watch?v=YOUR_VIDEO_ID"
USE_VOICE_CLONING = True  # Enable/disable voice cloning
```

2. Run the pipeline:
```bash
python app.py
```

3. Find your dubbed video in `output/final_dubbed_video.mp4`

### Using Local Videos

To process a local video file:

```python
LOCAL_VIDEO = r"C:\path\to\your\video.mp4"
YOUTUBE_URL = None
```

### Voice Cloning

Voice cloning captures the original speaker's voice characteristics:

1. **Enable it**: Set `USE_VOICE_CLONING = True` in `app.py`
2. **Adjust timing**: Modify `start_time` in the speaker sample extraction to find a clear speaking segment:
```python
speaker_wav = extract_speaker_sample(
    video_file, 
    start_time="00:00:05",  # Start at 5 seconds
    duration=6               # 6-second sample
)
```

**Tips for best results:**
- Choose a segment with clear, steady speech
- Avoid background music or noise
- 5-6 seconds is usually sufficient

### Language Configuration

Currently supports English → Spanish. To add other languages:

```python
SOURCE_LANG = "en"  # Source language
TARGET_LANG = "es"  # Target language (es, fr, de, etc.)
```

## How It Works

1. **Video Acquisition**: Downloads from YouTube or loads local file
2. **Audio Extraction**: Extracts audio track as WAV (16kHz mono)
3. **Transcription**: Uses Whisper AI to convert speech to text
4. **Translation**: Translates text using MarianMT neural translation
5. **Speaker Sampling** (optional): Extracts clean audio sample for voice cloning
6. **Speech Synthesis**: Generates translated speech with XTTS v2
   - With voice cloning: Mimics original speaker
   - Without: Uses default TTS voice
7. **Video Merging**: Replaces original audio with translated audio

## Troubleshooting

### FFmpeg not found
- Ensure FFmpeg is installed and in your system PATH
- Windows: Add FFmpeg bin directory to Environment Variables

### CUDA/GPU errors
- The pipeline is configured to use CPU by default
- For GPU acceleration, modify `gpu=False` to `gpu=True` in generate_voice.py

### Translation model not found
- The first run downloads the translation model (~300MB)
- Ensure you have a stable internet connection

### Voice quality issues
- Try different speaker sample segments (adjust `start_time`)
- Ensure sample has clear speech without background noise
- Increase `duration` from 6 to 10 seconds

### Audio/video sync issues
- Use the `adjust_audio_speed()` function in merge_audio_video.py
- This stretches/compresses audio to match original duration

## Performance Notes

- **First run**: Slower due to model downloads
- **Whisper model**: "medium" balances speed/accuracy. Options:
  - `tiny`: Fastest, less accurate
  - `base`: Fast, decent accuracy
  - `small`: Good balance
  - `medium`: Better accuracy (default)
  - `large`: Best accuracy, slowest
- **Processing time**: ~5-10 minutes for a 5-minute video

## Known Limitations

- Currently supports EN→ES translation only (extendable)
- Long videos (>30 min) may require chunking
- Very fast speech may not dub perfectly
- Background music/sound effects are removed

## Future Improvements

- [ ] Support more language pairs
- [ ] Preserve background audio/music
- [ ] Batch processing multiple videos
- [ ] Web interface (Gradio/Streamlit)
- [ ] Real-time progress tracking
- [ ] GPU acceleration option

## Credits

- **Whisper**: OpenAI
- **MarianMT**: Helsinki-NLP
- **XTTS v2**: Coqui TTS
- **FFmpeg**: FFmpeg team

## License

This project is for educational purposes. Ensure you have rights to process any videos you use.