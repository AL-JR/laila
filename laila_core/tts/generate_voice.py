import os
import subprocess
import ffmpeg
from f5_tts.api import F5TTS

_tts_instance = None


def _get_tts():
    """Lazy-load and cache the F5-TTS instance."""
    global _tts_instance
    if _tts_instance is None:
        print("[*] Loading F5-TTS model (first run may download ~1GB)...")
        _tts_instance = F5TTS()
        print("[✓] F5-TTS model loaded.")
    return _tts_instance


def generate_segment_audio(text, target_duration, output_path, speaker_wav, language="es"):
    """
    Generate TTS for a single segment and time-stretch it to fit target_duration.

    Args:
        text (str): Text to synthesize
        target_duration (float): Original segment duration in seconds
        output_path (str): Path for the final (stretched) audio file
        speaker_wav (str): Path to speaker reference audio for voice cloning
        language (str): Language code (unused by F5-TTS, kept for interface compatibility)

    Returns:
        str: Path to the time-stretched audio file
    """
    if not text.strip():
        silence_path = output_path.replace(".wav", "_silence.wav")
        subprocess.run([
            "ffmpeg", "-y",
            "-f", "lavfi",
            "-i", "anullsrc=r=24000:cl=mono",
            "-t", str(target_duration),
            silence_path
        ], check=True, capture_output=True)
        return silence_path

    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)
    raw_path = output_path.replace(".wav", "_raw.wav")

    tts = _get_tts()

    # Auto-transcribe the reference clip so F5-TTS can condition on it
    ref_text = tts.transcribe(speaker_wav)

    wav, sr, _ = tts.infer(
        ref_file=speaker_wav,
        ref_text=ref_text,
        gen_text=text,
        file_wave=raw_path,
    )

    # Probe the generated duration
    probe = ffmpeg.probe(raw_path)
    generated_duration = float(probe["streams"][0]["duration"])

    # Time-stretch to match target_duration
    speed_factor = generated_duration / target_duration

    MAX_FACTOR = 2.5
    MIN_FACTOR = 0.5
    if speed_factor > MAX_FACTOR:
        print(f"[!] Stretch factor {speed_factor:.2f}x exceeds {MAX_FACTOR}x — clamping.")
        speed_factor = MAX_FACTOR
    elif speed_factor < MIN_FACTOR:
        print(f"[!] Stretch factor {speed_factor:.2f}x below {MIN_FACTOR}x — clamping.")
        speed_factor = MIN_FACTOR

    atempo_filters = _build_atempo_chain(speed_factor)
    filter_str = ",".join(atempo_filters)

    subprocess.run([
        "ffmpeg", "-y", "-i", raw_path,
        "-filter:a", filter_str,
        output_path
    ], check=True, capture_output=True)

    if os.path.exists(raw_path):
        os.remove(raw_path)

    return output_path


def _build_atempo_chain(factor):
    """Build a list of atempo filter strings to achieve the given speed factor."""
    filters = []
    remaining = factor
    if factor > 1.0:
        while remaining > 2.0:
            filters.append("atempo=2.0")
            remaining /= 2.0
        filters.append(f"atempo={remaining:.6f}")
    else:
        while remaining < 0.5:
            filters.append("atempo=0.5")
            remaining /= 0.5
        filters.append(f"atempo={remaining:.6f}")
    return filters
