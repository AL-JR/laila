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
import os
from TTS.api import TTS

def generate_speech(text, output_path="output/voice.wav", language="es", speaker_wav_path=None):
    print("[*] Generating voice audio...")

    # Load multilingual voice cloning model
    tts = TTS(model_name="tts_models/multilingual/multi-dataset/your_tts", progress_bar=False, gpu=False)

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Generate audio with voice cloning
    tts.tts_to_file(
        text=text,
        file_path=output_path,
        speaker_wav=speaker_wav_path,
        language=language
    )

    print(f"[✓] Voice audio saved to {output_path}")
    return output_path
