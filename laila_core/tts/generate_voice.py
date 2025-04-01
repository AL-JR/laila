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

nltk.download('punkt')

add_safe_globals([XttsConfig, XttsAudioConfig, BaseDatasetConfig, XttsArgs])

def generate_speech(text, output_path="output/voice.wav", speaker_id="random", speaker_wav_path=None, language="es"):
    print("[*] Generating voice audio...")

    tts = TTS(model_name="tts_models/multilingual/multi-dataset/xtts_v2", progress_bar=False, gpu=False)

    # Attempt to retrieve available speakers from the speaker manager
    if speaker_id == "random":
        if tts.synthesizer.speaker_manager is not None and tts.synthesizer.speaker_manager.speakers:
            available_speakers = [s.strip() for s in tts.synthesizer.speaker_manager.speakers.keys()]
            if available_speakers:
                speaker_id = random.choice(available_speakers)
                print(f"[✔] Randomly selected speaker: {speaker_id}")
            else:
                raise ValueError("No available speakers found for this multi-speaker model.")
        else:
            raise ValueError("Speaker manager not available. Please supply a valid speaker ID.")
    elif speaker_id:
        speaker_id = speaker_id.strip()
        if tts.synthesizer.speaker_manager is not None and tts.synthesizer.speaker_manager.speakers:
            available_speakers = [s.strip() for s in tts.synthesizer.speaker_manager.speakers.keys()]
            if speaker_id not in available_speakers:
                raise ValueError(f"[✘] Speaker ID '{speaker_id}' not in available speakers: {available_speakers}")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Split the text into smaller chunks using NLTK (for Spanish)
    chunks = sent_tokenize(text, language='spanish')
    print(f"[→] Splitting text into {len(chunks)} chunks...")

    chunk_paths = []
    for i, chunk in enumerate(chunks):
        out_path = output_path.replace(".wav", f"_{i}.wav")
        print(f"[•] Synthesizing chunk {i+1}/{len(chunks)}: {chunk[:30]}...")
        tts.tts_to_file(
            text=chunk,
            file_path=out_path,
            speaker=speaker_id,
            speaker_wav=speaker_wav_path,
            language=language
        )
        chunk_paths.append(out_path)

    # Merge the chunk files using ffmpeg
    concat_file = os.path.join(os.path.dirname(output_path), "concat_list.txt")
    with open(concat_file, "w", encoding="utf-8") as f:
        for path in chunk_paths:
            f.write(f"file '{os.path.abspath(path)}'\n")
    
    final_output = output_path.replace(".wav", "_merged.wav")
    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", concat_file,
        "-c", "copy", final_output
    ], check=True)
    
    # Cleanup temporary files
    for path in chunk_paths:
        os.remove(path)
    os.remove(concat_file)
    
    print(f"[✓] Final merged voice audio saved to {final_output}")
    return final_output

# Example usage:
if __name__ == "__main__":
    sample_text = ("qué es un problema de la diabetes, qué es un problema de la diabetes, "
                   "qué es un problema de la salud, cómo un problema de la calidad de la calidad "
                   "de la calidad de la calidad de la salud")
    final_audio = generate_speech(sample_text, speaker_id="random", language="es")
    print("Final audio file:", final_audio)
