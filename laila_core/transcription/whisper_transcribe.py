import whisper

def transcribe_audio(audio_path):
    print("[*] Transcribing...")
    model = whisper.load_model("medium")  # or "small", "medium", "large"
    result = model.transcribe(audio_path, word_timestamps= True)
    print("[✓] Transcription complete.")
    return result["text"]