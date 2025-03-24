from video_utils.extract_audio import extract_audio
from transcription.whisper_transcribe import transcribe_audio
from translation.translate_text import translate_text
from tts.generate_voice import generate_speech

import os
print("[debug] Current working directory:", os.getcwd())

video_file = r"D:\python\Portfolio\laila\laila_core\test.mp4"  # Place a test video here
audio_path = extract_audio(video_file)

transcript = transcribe_audio(audio_path)
print("TRANSCRIPT:", transcript)

translated_text = translate_text(transcript, src_lang="en", tgt_lang="es")
print("TRANSLATED:", translated_text)



# Extract clean sample for voice cloning
from video_utils.speaker_clip import extract_speaker_sample
speaker_wav = extract_speaker_sample(video_file, start_time="00:00:03", duration=6)

# Generate translated speech using the speaker sample
voice_audio_path = generate_speech(translated_text, speaker_wav_path=speaker_wav)


# Next step: TTS and dubbing

voice_audio_path = generate_speech(translated_text)
