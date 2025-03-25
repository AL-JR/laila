# from TTS.api import TTS
# import os

# def generate_speech(text, output_path="output/voice.wav", language="es"):
#     print("[*] Generating voice audio...")

#     # Load a multilingual model
#     tts = TTS(model_name="tts_models/multilingual/multi-dataset/your_tts", progress_bar=False, gpu=False)

#     # Ensure output dir exists
#     os.makedirs(os.path.dirname(output_path), exist_ok=True)

#     # Generate audio
#     tts.tts_to_file(text=text, file_path=output_path)
    
#     print(f"[✓] Voice audio saved to {output_path}")
#     return output_path
# import os
# from TTS.api import TTS

# def generate_speech(text, output_path="output/voice.wav", language="es", speaker_wav_path=None):
#     print("[*] Generating voice audio...")

#     # Load multilingual voice cloning model
#     tts = TTS(model_name="tts_models/multilingual/multi-dataset/your_tts", progress_bar=False, gpu=False)

#     # Ensure output directory exists
#     os.makedirs(os.path.dirname(output_path), exist_ok=True)

#     # Generate audio with voice cloning
#     tts.tts_to_file(
#         text=text,
#         file_path=output_path,
#         speaker_wav=speaker_wav_path,
#         language=language
#     )

#     print(f"[✓] Voice audio saved to {output_path}")
#     return output_path
from torch.serialization import add_safe_globals
from TTS.tts.configs.xtts_config import XttsConfig
from TTS.tts.models.xtts import XttsAudioConfig, XttsArgs
from TTS.config.shared_configs import BaseDatasetConfig
from TTS.api import TTS
import os
import torch
import random

add_safe_globals([XttsConfig, XttsAudioConfig, BaseDatasetConfig, XttsArgs])
import re

def split_into_sentences(text, max_chars=250):
    sentences = re.split(r'(?<=[.?!])\s+', text)
    chunks = []
    current_chunk = ""

    for sentence in sentences:
        if len(current_chunk) + len(sentence) <= max_chars:
            current_chunk += " " + sentence
        else:
            chunks.append(current_chunk.strip())
            current_chunk = sentence
    if current_chunk:
        chunks.append(current_chunk.strip())
    return chunks

def generate_speech(text, output_path="output/voice.wav", speaker_id=None, speaker_wav_path=None, language="es"):
    print("[*] Generating voice audio...")

    from torch.serialization import add_safe_globals
    from TTS.tts.configs.xtts_config import XttsConfig
    from TTS.tts.models.xtts import XttsAudioConfig, XttsArgs
    from TTS.config.shared_configs import BaseDatasetConfig
    import torch
    add_safe_globals([XttsConfig, XttsAudioConfig, BaseDatasetConfig, XttsArgs])

    from TTS.api import TTS
    import os
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    tts = TTS(model_name="tts_models/multilingual/multi-dataset/xtts_v2", progress_bar=False, gpu=False)

    if speaker_id == "random":
        import random
        speaker_id = random.choice(list(tts.tts_model.speaker_manager.speakers.keys()))
        print(f"[✔] Using random speaker: {speaker_id}")
    else:
        speaker_id = speaker_id.strip()

    # Split text into smaller chunks
    chunks = split_into_sentences(text, max_chars=250)

    combined_paths = []
    for i, chunk in enumerate(chunks):
        print(f"[•] Generating part {i + 1}/{len(chunks)}...")
        part_path = output_path.replace(".wav", f"_part{i}.wav")
        tts.tts_to_file(
            text=chunk,
            file_path=part_path,
            speaker=speaker_id,
            speaker_wav=speaker_wav_path,
            language=language
        )
        combined_paths.append(part_path)

    print(f"[✓] Generated {len(combined_paths)} audio chunks.")
    return combined_paths

