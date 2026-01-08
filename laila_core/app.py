"""
Laila - Automated Video Translation & Dubbing System
Translates videos from English to Spanish with voice cloning
"""

import os
import sys
from video_utils.extract_audio import extract_audio
from transcription.whisper_transcribe import transcribe_audio
from translation.translate_text import translate_text
from tts.generate_voice import generate_speech
from video_utils.download_youtube import download_youtube_video
from video_utils.speaker_clip import extract_speaker_sample
from video_utils.merge_audio_video import merge_audio_video

# Configuration
USE_VOICE_CLONING = True  # Set to True to clone the original speaker's voice
YOUTUBE_URL = "https://www.youtube.com/watch?v=VtzKXsvSUts"
LOCAL_VIDEO = None  # Set to path for local video, or None to use YouTube

# Languages
SOURCE_LANG = "en"
TARGET_LANG = "es"

def main():
    print("=" * 60)
    print("LAILA - Video Translation & Dubbing Pipeline")
    print("=" * 60)
    
    try:
        # Step 1: Get video file
        print("\n[STEP 1] Getting video file...")
        if LOCAL_VIDEO and os.path.exists(LOCAL_VIDEO):
            video_file = LOCAL_VIDEO
            print(f"[✓] Using local video: {video_file}")
        else:
            print(f"[*] Downloading from YouTube: {YOUTUBE_URL}")
            video_file = download_youtube_video(YOUTUBE_URL, output_path="downloads", filename="source_video.mp4")
            print(f"[✓] Downloaded to: {video_file}")

        # Step 2: Extract audio from video
        print("\n[STEP 2] Extracting audio from video...")
        audio_path = extract_audio(video_file)
        print(f"[✓] Audio extracted to: {audio_path}")

        # Step 3: Transcribe audio to text
        print("\n[STEP 3] Transcribing audio to text...")
        transcript = transcribe_audio(audio_path)
        print(f"[✓] Transcription complete!")
        print(f"\nOriginal transcript ({SOURCE_LANG}):")
        print("-" * 60)
        print(transcript)
        print("-" * 60)

        # Step 4: Translate text
        print(f"\n[STEP 4] Translating from {SOURCE_LANG} to {TARGET_LANG}...")
        translated_text = translate_text(transcript, src_lang=SOURCE_LANG, tgt_lang=TARGET_LANG)
        print(f"[✓] Translation complete!")
        print(f"\nTranslated text ({TARGET_LANG}):")
        print("-" * 60)
        print(translated_text)
        print("-" * 60)

        # Step 5: Extract speaker sample for voice cloning (optional)
        speaker_wav = None
        if USE_VOICE_CLONING:
            print("\n[STEP 5] Extracting speaker sample for voice cloning...")
            try:
                # Extract a 6-second sample starting at 3 seconds
                # Adjust start_time to find a clear speaking segment
                speaker_wav = extract_speaker_sample(
                    video_file, 
                    start_time="00:00:03", 
                    duration=6
                )
                print(f"[✓] Speaker sample extracted: {speaker_wav}")
            except Exception as e:
                print(f"[!] Warning: Could not extract speaker sample: {e}")
                print("[!] Continuing without voice cloning...")
                USE_VOICE_CLONING = False

        # Step 6: Generate speech from translated text
        print(f"\n[STEP 6] Generating {TARGET_LANG} speech...")
        if USE_VOICE_CLONING and speaker_wav:
            print("[*] Using voice cloning with original speaker...")
            voice_audio_path = generate_speech(
                translated_text, 
                output_path="output/translated_voice.wav",
                speaker_wav_path=speaker_wav,
                language=TARGET_LANG
            )
        else:
            print("[*] Using default TTS voice...")
            voice_audio_path = generate_speech(
                translated_text,
                output_path="output/translated_voice.wav",
                language=TARGET_LANG
            )
        print(f"[✓] Speech generated: {voice_audio_path}")

        # Step 7: Merge new audio with original video
        print("\n[STEP 7] Creating final dubbed video...")
        final_video = merge_audio_video(
            video_file,
            voice_audio_path,
            output_path="output/final_dubbed_video.mp4"
        )
        print(f"[✓] Final video created: {final_video}")

        # Success summary
        print("\n" + "=" * 60)
        print("SUCCESS! Video dubbing complete!")
        print("=" * 60)
        print(f"Original video: {video_file}")
        print(f"Final dubbed video: {final_video}")
        print(f"Language: {SOURCE_LANG} → {TARGET_LANG}")
        print(f"Voice cloning: {'Enabled' if USE_VOICE_CLONING else 'Disabled'}")
        print("=" * 60)

    except KeyboardInterrupt:
        print("\n\n[!] Process interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n[✗] ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    print("[DEBUG] Current working directory:", os.getcwd())
    main()