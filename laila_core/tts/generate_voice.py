import os
import subprocess
import ffmpeg
from torch.serialization import add_safe_globals
from TTS.tts.configs.xtts_config import XttsConfig
from TTS.tts.models.xtts import XttsAudioConfig, XttsArgs
from TTS.config.shared_configs import BaseDatasetConfig

add_safe_globals([XttsConfig, XttsAudioConfig, BaseDatasetConfig, XttsArgs])

_tts_instance = None


def _get_tts():
    """Lazy-load and cache the XTTS v2 instance."""
    global _tts_instance
    if _tts_instance is None:
        print("[*] Loading XTTS v2 model...")
        os.environ["COQUI_TOS_AGREED"] = "1"
        from TTS.api import TTS
        _tts_instance = TTS(
            model_name="tts_models/multilingual/multi-dataset/xtts_v2",
            progress_bar=False,
            gpu=False,
        )
        print("[✓] XTTS v2 loaded.")
    return _tts_instance


def generate_segment_audio(text, target_duration, output_path, speaker_wav, language="es"):
    """
    Generate TTS for a single segment using XTTS v2 cross-lingual voice cloning,
    then time-stretch to fit target_duration.

    Args:
        text (str): Text to synthesize
        target_duration (float): Original segment duration in seconds
        output_path (str): Path for the final (stretched) audio file
        speaker_wav (str): Path to speaker reference audio for voice cloning
        language (str): Target language code (e.g. "es", "en", "fr")

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
    tts.tts_to_file(
        text=text,
        file_path=raw_path,
        speaker_wav=speaker_wav,
        language=language,
    )

    # Probe the generated duration
    probe = ffmpeg.probe(raw_path)
    generated_duration = float(probe["streams"][0]["duration"])

    # Time-stretch to match target_duration
    speed_factor = generated_duration / target_duration

    MAX_FACTOR = 1.8
    MIN_FACTOR = 0.5

    if speed_factor > MAX_FACTOR:
        # Too extreme to stretch cleanly — use natural duration to preserve quality
        print(f"[!] Stretch factor {speed_factor:.2f}x exceeds {MAX_FACTOR}x — using natural duration.")
        import shutil
        shutil.move(raw_path, output_path)
        return output_path
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
