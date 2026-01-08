import os
import random
import subprocess
import nltk
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
    Generate speech from text using XTTS v2 model with optional voice cloning.
    
    Args:
        text (str): Text to convert to speech
        output_path (str): Path for output audio file
        speaker_id (str): Speaker ID for multi-speaker model (optional)
        speaker_wav_path (str): Path to speaker sample for voice cloning (optional)
        language (str): Language code (default: "es" for Spanish)
        
    Returns:
        str: Path to the generated audio file
    """
    print("[*] Generating voice audio...")

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
            if speaker_wav_path:
                # Voice cloning mode
                tts.tts_to_file(
                    text=chunk,
                    file_path=out_path,
                    speaker_wav=speaker_wav_path,
                    language=language
                )
            else:
                # Default speaker mode (XTTS v2 doesn't use speaker_id, it uses speaker_wav)
                tts.tts_to_file(
                    text=chunk,
                    file_path=out_path,
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