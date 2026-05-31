import os
import subprocess
from audio_utils import seconds_to_hms
from video_utils.speaker_clip import extract_speaker_sample


def extract_samples_per_speaker(segments, vocals_path, output_dir="output/samples",
                                 target_duration=20.0, min_seg_duration=0.5):
    """
    For each unique speaker, build a voice cloning reference by concatenating
    their longest segments up to target_duration seconds total.

    Args:
        segments (list[dict]): Segments with 'speaker', 'start', 'end' keys
        vocals_path (str): Path to the vocals-only audio (from Demucs)
        output_dir (str): Directory to write per-speaker WAV files
        target_duration (float): Target total seconds to collect per speaker
        min_seg_duration (float): Skip segments shorter than this

    Returns:
        dict[str, str]: Maps speaker label -> path to sample WAV
    """
    os.makedirs(output_dir, exist_ok=True)

    # Group segments by speaker, sorted by duration descending
    from collections import defaultdict
    speaker_segs = defaultdict(list)
    for seg in segments:
        speaker = seg.get("speaker", "SPEAKER_00")
        dur = seg["end"] - seg["start"]
        if dur >= min_seg_duration:
            speaker_segs[speaker].append(seg)

    for speaker in speaker_segs:
        speaker_segs[speaker].sort(key=lambda s: s["end"] - s["start"], reverse=True)

    samples = {}
    for speaker, segs in speaker_segs.items():
        clips, total = [], 0.0

        for seg in segs:
            dur = min(seg["end"] - seg["start"], target_duration - total)
            if dur <= 0:
                break
            clip_path = os.path.join(output_dir, f"_{speaker}_clip{len(clips)}.wav")
            try:
                extract_speaker_sample(
                    vocals_path,
                    start_time=seconds_to_hms(seg["start"]),
                    duration=max(1, int(dur)),
                    output_path=clip_path,
                )
                clips.append(clip_path)
                total += dur
            except Exception as e:
                print(f"[!] Could not extract clip for {speaker}: {e}")
            if total >= target_duration:
                break

        if not clips:
            print(f"[!] No usable clips found for {speaker}, skipping.")
            continue

        out_path = os.path.join(output_dir, f"{speaker}.wav")

        if len(clips) == 1:
            os.replace(clips[0], out_path)
        else:
            # Concatenate all clips into one reference file
            inputs = []
            for c in clips:
                inputs += ["-i", c]
            subprocess.run(
                ["ffmpeg", "-y"] + inputs +
                ["-filter_complex", f"concat=n={len(clips)}:v=0:a=1[out]",
                 "-map", "[out]", out_path],
                check=True, capture_output=True,
            )
            for c in clips:
                if os.path.exists(c):
                    os.remove(c)

        print(f"[✓] Voice reference for {speaker}: {len(clips)} clip(s), {total:.1f}s → {out_path}")
        samples[speaker] = out_path

    if not samples:
        raise RuntimeError(
            "Could not extract a voice sample for any speaker. "
            "Check that the vocals track contains audible speech."
        )

    return samples
