"""
Laila - Automated Video Translation & Dubbing System
Segment-based pipeline with timestamp sync, voice cloning, and multi-speaker support.
"""

import os
import sys

import ffmpeg
from video_utils.extract_audio import extract_audio
from audio_utils.separate_vocals import separate_vocals
from audio_utils.compose_timeline import compose_audio_timeline
from transcription.whisper_transcribe import transcribe_audio
from translation.translate_text import translate_segments
from tts.generate_voice import generate_segment_audio
from video_utils.download_youtube import download_youtube_video
from video_utils.speaker_clip import extract_speaker_sample
from video_utils.merge_audio_video import merge_audio_video
from audio_utils import seconds_to_hms

# ── Configuration ────────────────────────────────────────────────────────────
YOUTUBE_URL  = "https://youtu.be/NL67yyu2N4U?si=55BchSJ5ccAOv4OY"
LOCAL_VIDEO  = "test.mp4"   # Set to a local file path to skip YouTube download

SOURCE_LANG  = "en"
TARGET_LANG  = "es"

# Set True to detect and clone each speaker separately.
# Requires: pip install pyannote.audio  +  HF_TOKEN env var
# Accept model terms at: https://huggingface.co/pyannote/speaker-diarization-3.1
MULTI_SPEAKER = False

# Optionally hint how many speakers are in the video (improves diarization accuracy)
MIN_SPEAKERS = None   # e.g. 2
MAX_SPEAKERS = None   # e.g. 4
# ─────────────────────────────────────────────────────────────────────────────


def _pick_single_speaker_sample(segments, vocals_path, min_duration=10.0):
    """Pick the longest segment as the cloning sample for single-speaker mode."""
    best = max(segments, key=lambda s: s["end"] - s["start"], default=None)
    if best and (best["end"] - best["start"]) >= min_duration:
        start_str = seconds_to_hms(best["start"])
        dur = int(best["end"] - best["start"])
        print(f"[*] Best sample: {start_str} ({dur}s) — \"{best['text'][:50]}\"")
        return extract_speaker_sample(vocals_path, start_time=start_str, duration=dur)
    else:
        print("[*] No long segment found — using fixed offset 00:00:03 (15s)")
        return extract_speaker_sample(vocals_path, start_time="00:00:03", duration=15)


def main():
    print("=" * 60)
    print("LAILA - Video Translation & Dubbing Pipeline")
    print("=" * 60)

    try:
        # ── Step 1: Get video ────────────────────────────────────────────────
        print("\n[STEP 1] Getting video file...")
        if LOCAL_VIDEO and os.path.exists(LOCAL_VIDEO):
            video_file = LOCAL_VIDEO
            print(f"[✓] Using local video: {video_file}")
        else:
            print(f"[*] Downloading from YouTube: {YOUTUBE_URL}")
            video_file = download_youtube_video(
                YOUTUBE_URL, output_path="downloads", filename="source_video.mp4"
            )
            print(f"[✓] Downloaded: {video_file}")

        probe = ffmpeg.probe(video_file)
        video_stream = next(s for s in probe["streams"] if s["codec_type"] == "video")
        total_duration = float(video_stream.get("duration") or probe["format"]["duration"])
        print(f"[✓] Duration: {total_duration:.1f}s")

        # ── Step 2: Extract + isolate vocals ────────────────────────────────
        print("\n[STEP 2] Extracting audio...")
        audio_path = extract_audio(video_file)

        print("\n[STEP 2b] Isolating vocals (Demucs)...")
        vocals_path = separate_vocals(audio_path)
        print(f"[✓] Vocals: {vocals_path}")

        # ── Step 3: Transcribe ───────────────────────────────────────────────
        print("\n[STEP 3] Transcribing...")
        segments = transcribe_audio(vocals_path)
        print(f"\nOriginal transcript ({SOURCE_LANG}):")
        print("-" * 60)
        for seg in segments:
            print(f"  [{seg['start']:.1f}s → {seg['end']:.1f}s] {seg['text']}")
        print("-" * 60)

        # ── Step 4: Diarize (multi-speaker only) ────────────────────────────
        if MULTI_SPEAKER:
            print("\n[STEP 4] Running speaker diarization...")
            from audio_utils.diarize import diarize_audio
            from audio_utils.align_speakers import assign_speakers
            from audio_utils.speaker_samples import extract_samples_per_speaker

            turns = diarize_audio(
                vocals_path,
                min_speakers=MIN_SPEAKERS,
                max_speakers=MAX_SPEAKERS,
            )
            segments = assign_speakers(segments, turns)

            unique_speakers = sorted({s["speaker"] for s in segments})
            print(f"[✓] {len(unique_speakers)} speaker(s) identified: {unique_speakers}")
            for seg in segments:
                print(f"  [{seg['start']:.1f}s → {seg['end']:.1f}s] [{seg['speaker']}] {seg['text']}")

        # ── Step 5: Translate ────────────────────────────────────────────────
        print(f"\n[STEP 5] Translating {len(segments)} segment(s) → {TARGET_LANG}...")
        segments = translate_segments(segments, src_lang=SOURCE_LANG, tgt_lang=TARGET_LANG)

        # ── Step 6: Extract voice sample(s) ─────────────────────────────────
        print("\n[STEP 6] Extracting speaker sample(s) for voice cloning...")
        if MULTI_SPEAKER:
            speaker_wavs = extract_samples_per_speaker(segments, vocals_path)
            print(f"[✓] Samples extracted for: {list(speaker_wavs.keys())}")
        else:
            single_wav = _pick_single_speaker_sample(segments, vocals_path)
            speaker_wavs = {"SPEAKER_00": single_wav}
            # Tag all segments with the single speaker so the TTS loop is uniform
            for seg in segments:
                seg.setdefault("speaker", "SPEAKER_00")
            print(f"[✓] Sample: {single_wav}")

        # ── Step 7: Synthesise each segment ─────────────────────────────────
        print(f"\n[STEP 7] Synthesising {len(segments)} segment(s)...")
        os.makedirs("output/segments", exist_ok=True)

        for i, seg in enumerate(segments):
            target_dur  = seg["end"] - seg["start"]
            out_path    = f"output/segments/seg_{i:04d}.wav"
            speaker     = seg.get("speaker", "SPEAKER_00")
            wav         = speaker_wavs.get(speaker) or next(iter(speaker_wavs.values()))
            translated  = seg.get("translated", "")

            label = f"[{speaker}]" if MULTI_SPEAKER else ""
            print(f"[•] {i+1}/{len(segments)} {label} ({target_dur:.1f}s): {translated[:60]}")

            try:
                seg["audio_path"] = generate_segment_audio(
                    text=translated,
                    target_duration=target_dur,
                    output_path=out_path,
                    speaker_wav=wav,
                    language=TARGET_LANG,
                )
            except Exception as e:
                print(f"[!] Skipping segment {i+1}: {e}")
                seg["audio_path"] = None

        # ── Step 8: Compose timeline ─────────────────────────────────────────
        print("\n[STEP 8] Composing audio timeline...")
        composed_audio = compose_audio_timeline(
            segments,
            total_duration=total_duration,
            output_path="output/composed_audio.wav",
        )
        print(f"[✓] Composed: {composed_audio}")

        # ── Step 9: Merge into final video ───────────────────────────────────
        print("\n[STEP 9] Merging audio into video...")
        final_video = merge_audio_video(
            video_file,
            composed_audio,
            output_path="output/final_dubbed_video.mp4",
        )
        print(f"[✓] Final video: {final_video}")

        print("\n" + "=" * 60)
        print("SUCCESS! Video dubbing complete!")
        print("=" * 60)
        print(f"Original video  : {video_file}")
        print(f"Dubbed video    : {final_video}")
        print(f"Language        : {SOURCE_LANG} → {TARGET_LANG}")
        print(f"Segments        : {len(segments)}")
        print(f"Multi-speaker   : {'Yes' if MULTI_SPEAKER else 'No'}")
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