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

def generate_speech(text, output_path="output/voice.wav", speaker_id=None, speaker_wav_path=None, language="es"):
    print("[*] Generating voice audio...")

    # Allow safe deserialization
    add_safe_globals([XttsConfig, XttsAudioConfig, BaseDatasetConfig, XttsArgs])

    # Load model
    tts = TTS(model_name="tts_models/multilingual/multi-dataset/xtts_v2", progress_bar=False, gpu=False)

    # Get usable speakers
    available_speakers = list(tts.synthesizer.tts_model.speaker_manager.speakers.keys())
    print("[✔] Real usable speaker IDs:")
    print(available_speakers)

    # Handle random speaker
    if speaker_id == "random":
        speaker_id = random.choice(available_speakers)
        print(f"[✔] Randomly selected speaker: {speaker_id}")
    elif speaker_id:
        speaker_id = speaker_id.strip()
        if speaker_id not in available_speakers:
            raise ValueError(f"[✘] Speaker ID '{speaker_id}' not in available speakers: {available_speakers}")

    # Ensure output path exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Generate audio
    tts.tts_to_file(
        text=text,
        file_path=output_path,
        speaker_wav=speaker_wav_path,
        speaker=speaker_id,
        language=language
    )

    print(f"[✓] Voice audio saved to {output_path}")
    return output_path
