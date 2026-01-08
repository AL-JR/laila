"""
Configuration file for Laila Video Translation Pipeline
Edit these settings to customize your dubbing experience
"""

# ============================================================================
# VIDEO SOURCE SETTINGS
# ============================================================================

# YouTube URL (set to None if using local video)
YOUTUBE_URL = "https://www.youtube.com/watch?v=VtzKXsvSUts"

# Local video file path (set to None if using YouTube)
LOCAL_VIDEO = None
# Example: LOCAL_VIDEO = r"C:\Videos\my_video.mp4"

# ============================================================================
# LANGUAGE SETTINGS
# ============================================================================

SOURCE_LANG = "en"  # Source language code
TARGET_LANG = "es"  # Target language code

# Supported language pairs (for MarianMT):
# en -> es (English to Spanish)
# en -> fr (English to French)
# en -> de (English to German)
# en -> it (English to Italian)
# en -> pt (English to Portuguese)
# Add more as needed: https://huggingface.co/Helsinki-NLP

# ============================================================================
# VOICE SETTINGS
# ============================================================================

# Enable voice cloning to match original speaker's voice
USE_VOICE_CLONING = True

# Speaker sample extraction settings (for voice cloning)
SPEAKER_SAMPLE_START = "00:00:03"  # Start time (HH:MM:SS or MM:SS)
SPEAKER_SAMPLE_DURATION = 6        # Duration in seconds

# Tips for choosing speaker sample:
# - Find a segment with clear, steady speech
# - Avoid segments with background music or noise
# - 5-6 seconds is usually sufficient
# - Try different start times if quality is poor

# ============================================================================
# MODEL SETTINGS
# ============================================================================

# Whisper transcription model size
# Options: "tiny", "base", "small", "medium", "large"
# Larger = more accurate but slower
WHISPER_MODEL = "medium"

# Use GPU acceleration (requires CUDA-compatible GPU)
USE_GPU = False

# ============================================================================
# OUTPUT SETTINGS
# ============================================================================

# Output directories
DOWNLOADS_DIR = "downloads"
OUTPUT_DIR = "output"
SAMPLES_DIR = "output/samples"

# Output filenames
EXTRACTED_AUDIO = "audio.wav"
TRANSLATED_VOICE = "translated_voice.wav"
FINAL_VIDEO = "final_dubbed_video.mp4"

# ============================================================================
# ADVANCED SETTINGS
# ============================================================================

# Audio extraction settings
AUDIO_SAMPLE_RATE = "16k"  # Sample rate for transcription
AUDIO_CHANNELS = 1          # Mono audio

# Speaker sample settings for voice cloning
SPEAKER_SAMPLE_RATE = "22050"  # Higher quality for TTS

# Translation settings
MAX_TRANSLATION_LENGTH = 512  # Maximum tokens per translation batch

# TTS chunk processing
# (Text is split into sentences for better TTS quality)
ENABLE_TEXT_CHUNKING = True

# Video output settings
VIDEO_CODEC = "copy"        # Copy video without re-encoding (fast)
AUDIO_CODEC = "aac"         # Audio codec for final video
AUDIO_BITRATE = "192k"      # Audio quality

# ============================================================================
# DEBUG SETTINGS
# ============================================================================

# Print debug information
VERBOSE = True

# Keep intermediate files (for debugging)
KEEP_TEMP_FILES = False