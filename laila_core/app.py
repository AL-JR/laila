from video_utils.extract_audio import extract_audio
from transcription.whisper_transcribe import transcribe_audio
from translation.translate_text import translate_text
from tts.generate_voice import generate_speech
from video_utils.download_youtube import download_youtube_video

import os
print("[debug] Current working directory:", os.getcwd())

#video file for local videos
#video_file = r"D:\python\Portfolio\laila\laila_core\test.mp4"  # Place a test video here
#video file from youtube url:

youtube_url = "https://www.youtube.com/watch?v=VtzKXsvSUts"
video_file = download_youtube_video(youtube_url)

audio_path = extract_audio(video_file)

transcript = transcribe_audio(audio_path)
print("TRANSCRIPT:", transcript)

translated_text = translate_text(transcript, src_lang="en", tgt_lang="es")
print("TRANSLATED:", translated_text)

#TS speaker list
from TTS.api import TTS

tts = TTS(model_name="tts_models/multilingual/multi-dataset/your_tts", progress_bar=False, gpu=False)

print("\n[✔] Real usable speaker IDs:")
print(list(tts.synthesizer.tts_model.speaker_manager.embeddings_by_names.keys()))

# Extract clean sample for voice cloning
from video_utils.speaker_clip import extract_speaker_sample
#speaker_wav = extract_speaker_sample(video_file, start_time="00:00:03", duration=6)

# Generate translated speech using the speaker sample
#voice_audio_path = generate_speech(translated_text, speaker_wav_path=speaker_wav)
voice_audio_path = generate_speech(translated_text, speaker_id="random", language="es")


# Next step: TTS and dubbing

#voice_audio_path = generate_speech(translated_text)
