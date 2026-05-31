import os
import subprocess
import ffmpeg


def compose_audio_timeline(segments, total_duration, output_path="output/composed_audio.wav"):
    """
    Place per-segment audio clips at their original timestamps over a silent base track,
    producing a single audio file that is sync'd to the original video.

    Args:
        segments (list[dict]): Each dict must have keys:
            start (float): segment start time in seconds
            end   (float): segment end time in seconds
            audio_path (str): path to the TTS audio for this segment
        total_duration (float): total video duration in seconds
        output_path (str): path for the composed output WAV

    Returns:
        str: path to the composed audio file
    """
    print(f"[*] Composing audio timeline ({len(segments)} segments, {total_duration:.1f}s)...")

    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else "output", exist_ok=True)

    # Filter out segments with no audio file
    valid = [s for s in segments if s.get("audio_path") and os.path.exists(s["audio_path"])]
    if not valid:
        raise ValueError("No valid segment audio files to compose.")

    # Build ffmpeg command
    # Input 0: silence base of total_duration
    # Inputs 1..N: segment audio files
    cmd = ["ffmpeg", "-y"]

    # Silence base — -t must come BEFORE -i to limit the lavfi source duration
    cmd += ["-f", "lavfi", "-t", str(total_duration), "-i", "anullsrc=r=24000:cl=mono"]

    # Segment inputs
    for seg in valid:
        cmd += ["-i", seg["audio_path"]]

    # Build filter_complex
    # Each segment input gets an adelay, then everything is amixed with the silence base
    filter_parts = []
    labels = ["[0]"]  # base silence

    for i, seg in enumerate(valid):
        input_idx = i + 1
        delay_ms = int(seg["start"] * 1000)
        label = f"[a{i}]"
        filter_parts.append(f"[{input_idx}]adelay={delay_ms}|{delay_ms}{label}")
        labels.append(label)

    n_inputs = len(labels)
    mix = "".join(labels) + f"amix=inputs={n_inputs}:duration=first:normalize=0[out]"
    filter_parts.append(mix)

    filter_complex = ";".join(filter_parts)

    cmd += ["-filter_complex", filter_complex, "-map", "[out]", output_path]

    try:
        subprocess.run(cmd, check=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        print(f"[✗] Timeline composition failed: {e}")
        raise

    print(f"[✓] Audio timeline composed: {output_path}")
    return output_path


def mix_with_background(dubbed_audio, background_audio, output_path="output/final_audio.wav"):
    """
    Mix the dubbed voice timeline with the original background (no_vocals) track.

    Args:
        dubbed_audio (str): Path to the composed TTS audio
        background_audio (str): Path to the no_vocals background track from Demucs
        output_path (str): Path for the mixed output WAV

    Returns:
        str: Path to the mixed audio file
    """
    print("[*] Mixing dubbed voice with background audio...")
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else "output", exist_ok=True)

    cmd = [
        "ffmpeg", "-y",
        "-i", dubbed_audio,
        "-i", background_audio,
        "-filter_complex", "amix=inputs=2:duration=first:normalize=0",
        output_path,
    ]

    try:
        subprocess.run(cmd, check=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        print(f"[✗] Background mix failed: {e}")
        raise

    print(f"[✓] Mixed audio: {output_path}")
    return output_path
