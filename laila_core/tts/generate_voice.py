import os
import subprocess
import nltk
import ffmpeg
from nltk.tokenize import sent_tokenize
from torch.serialization import add_safe_globals
from TTS.tts.configs.xtts_config import XttsConfig
from TTS.tts.models.xtts import XttsAudioConfig, XttsArgs
from TTS.config.shared_configs import BaseDatasetConfig
from TTS.api import TTS

# Download NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

add_safe_globals([XttsConfig, XttsAudioConfig, BaseDatasetConfig, XttsArgs])

def generate_speech(text, output_path="output/voice.wav", speaker_id=None, speaker_wav_path=None, language="es"):
    """
    Generate speech from text using XTTS v2 model with voice cloning.
    Note: XTTS v2 requires a speaker_wav for voice cloning.
    
    Args:
        text (str): Text to convert to speech
        output_path (str): Path for output audio file
        speaker_id (str): Deprecated - not used by XTTS v2
        speaker_wav_path (str): Path to speaker sample for voice cloning (REQUIRED)
        language (str): Language code (default: "es" for Spanish)
        
    Returns:
        str: Path to the generated audio file
    """
    print("[*] Generating voice audio...")
    
    if not speaker_wav_path:
        raise ValueError(
            "XTTS v2 requires a speaker sample for voice cloning. "
            "Please provide speaker_wav_path or enable USE_VOICE_CLONING in app.py"
        )

    tts = TTS(model_name="tts_models/multilingual/multi-dataset/xtts_v2", progress_bar=False, gpu=False)

    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else "output", exist_ok=True)

    # Split the text into smaller chunks using NLTK
    lang_map = {'es': 'spanish', 'en': 'english', 'fr': 'french', 'de': 'german'}
    nltk_lang = lang_map.get(language, 'spanish')
    
    try:
        chunks = sent_tokenize(text, language=nltk_lang)
    except:
        # Fallback to simple splitting if language not available
        chunks = [s.strip() + '.' for s in text.split('.') if s.strip()]
    
    print(f"[→] Splitting text into {len(chunks)} chunks...")

    chunk_paths = []
    for i, chunk in enumerate(chunks):
        if not chunk.strip():
            continue
            
        out_path = output_path.replace(".wav", f"_chunk_{i}.wav")
        print(f"[•] Synthesizing chunk {i+1}/{len(chunks)}: {chunk[:50]}...")
        
        try:
            # Voice cloning with XTTS v2
            tts.tts_to_file(
                text=chunk,
                file_path=out_path,
                speaker_wav=speaker_wav_path,
                language=language
            )
            chunk_paths.append(out_path)
        except Exception as e:
            print(f"[✗] Error synthesizing chunk {i+1}: {e}")
            continue

    if not chunk_paths:
        raise ValueError("No audio chunks were successfully generated!")

    # If only one chunk, just rename it
    if len(chunk_paths) == 1:
        final_output = output_path.replace(".wav", "_final.wav")
        os.rename(chunk_paths[0], final_output)
        print(f"[✓] Final voice audio saved to {final_output}")
        return final_output

    # Merge the chunk files using ffmpeg
    concat_file = os.path.join(os.path.dirname(output_path) or "output", "concat_list.txt")
    with open(concat_file, "w", encoding="utf-8") as f:
        for path in chunk_paths:
            f.write(f"file '{os.path.abspath(path)}'\n")
    
    final_output = output_path.replace(".wav", "_final.wav")
    
    try:
        subprocess.run([
            "ffmpeg", "-y", "-f", "concat", "-safe", "0",
            "-i", concat_file,
            "-c", "copy", final_output
        ], check=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        print(f"[✗] FFmpeg error: {e}")
        # Fallback: use the first chunk if merging fails
        print("[!] Falling back to first chunk only...")
        final_output = output_path.replace(".wav", "_final.wav")
        os.rename(chunk_paths[0], final_output)
        chunk_paths = chunk_paths[1:]  # Keep rest for cleanup
    
    # Cleanup temporary files
    for path in chunk_paths:
        if os.path.exists(path):
            os.remove(path)
    if os.path.exists(concat_file):
        os.remove(concat_file)
    
    print(f"[✓] Final voice audio saved to {final_output}")
    return final_output


def generate_segment_audio(text, target_duration, output_path, speaker_wav, language="es"):
    """
    Generate TTS for a single segment and time-stretch it to fit target_duration.

    Args:
        text (str): Text to synthesize
        target_duration (float): Original segment duration in seconds
        output_path (str): Path for the final (stretched) audio file
        speaker_wav (str): Path to speaker sample for voice cloning
        language (str): Language code

    Returns:
        str: Path to the time-stretched audio file
    """
    if not text.strip():
        # Return silence of target_duration
        silence_path = output_path.replace(".wav", "_silence.wav")
        subprocess.run([
            "ffmpeg", "-y",
            "-f", "lavfi",
            "-i", f"anullsrc=r=22050:cl=mono",
            "-t", str(target_duration),
            silence_path
        ], check=True, capture_output=True)
        return silence_path

    raw_path = output_path.replace(".wav", "_raw.wav")

    tts = TTS(model_name="tts_models/multilingual/multi-dataset/xtts_v2", progress_bar=False, gpu=False)
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)

    tts.tts_to_file(
        text=text,
        file_path=raw_path,
        speaker_wav=speaker_wav,
        language=language
    )

    # Probe the generated duration
    probe = ffmpeg.probe(raw_path)
    generated_duration = float(probe["streams"][0]["duration"])

    # Time-stretch to match target_duration
    speed_factor = generated_duration / target_duration

    # Clamp to a perceptually reasonable range — warn if extreme
    MAX_FACTOR = 2.5
    MIN_FACTOR = 0.5
    if speed_factor > MAX_FACTOR:
        print(f"[!] Segment stretch factor {speed_factor:.2f}x exceeds {MAX_FACTOR}x — clamping.")
        speed_factor = MAX_FACTOR
    elif speed_factor < MIN_FACTOR:
        print(f"[!] Segment stretch factor {speed_factor:.2f}x below {MIN_FACTOR}x — clamping.")
        speed_factor = MIN_FACTOR

    # Build atempo filter chain (each filter limited to 0.5–2.0)
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