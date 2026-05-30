import os
from audio_utils import seconds_to_hms
from video_utils.speaker_clip import extract_speaker_sample


def extract_samples_per_speaker(segments, vocals_path, output_dir="output/samples",
                                 target_duration=15.0, min_duration=3.0):
    """
    For each unique speaker, find their longest clean segment and extract an
    audio sample from the vocals-only track for use as a voice cloning reference.

    Args:
        segments (list[dict]): Segments with 'speaker', 'start', 'end' keys
        vocals_path (str): Path to the vocals-only audio (from Demucs)
        output_dir (str): Directory to write per-speaker WAV files
        target_duration (float): How many seconds to extract (capped at segment length)
        min_duration (float): Skip segments shorter than this

    Returns:
        dict[str, str]: Maps speaker label → path to sample WAV
    """
    os.makedirs(output_dir, exist_ok=True)

    # Find the longest segment per speaker
    best_per_speaker = {}
    for seg in segments:
        speaker = seg.get("speaker", "SPEAKER_00")
        dur = seg["end"] - seg["start"]
        if dur < min_duration:
            continue
        if speaker not in best_per_speaker or dur > (best_per_speaker[speaker]["end"] - best_per_speaker[speaker]["start"]):
            best_per_speaker[speaker] = seg

    samples = {}
    for speaker, seg in best_per_speaker.items():
        dur = min(seg["end"] - seg["start"], target_duration)
        start_hms = seconds_to_hms(seg["start"])
        out_path = os.path.join(output_dir, f"{speaker}.wav")

        print(f"[*] Extracting sample for {speaker}: {start_hms} ({dur:.1f}s) — \"{seg['text'][:50]}\"")
        try:
            extract_speaker_sample(
                vocals_path,
                start_time=start_hms,
                duration=int(dur),
                output_dir=output_dir,
            )
            # speaker_clip writes to output_dir/original_speaker.wav — rename to speaker-specific path
            default_path = os.path.join(output_dir, "original_speaker.wav")
            if os.path.exists(default_path):
                os.replace(default_path, out_path)
            samples[speaker] = out_path
            print(f"[✓] Sample saved: {out_path}")
        except Exception as e:
            print(f"[!] Could not extract sample for {speaker}: {e}")

    if not samples:
        raise RuntimeError(
            "Could not extract a voice sample for any speaker. "
            "Check that the vocals track contains audible speech."
        )

    return samples
