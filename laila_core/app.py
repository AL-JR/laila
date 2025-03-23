from video_utils.extract_audio import extract_audio
from transcription.whisper_transcribe import transcribe_audio
from translation.translate_text import translate_text

import os
print("[debug] Current working directory:", os.getcwd())

video_file = r"D:\python\Portfolio\laila\laila_core\test.mp4"  # Place a test video here
audio_path = extract_audio(video_file)

transcript = transcribe_audio(audio_path)
print("TRANSCRIPT:", transcript)

translated_text = translate_text(transcript, src_lang="en", tgt_lang="es")
print("TRANSLATED:", translated_text)

# Next step: TTS and dubbing