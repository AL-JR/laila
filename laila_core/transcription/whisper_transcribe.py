import whisper

def transcribe_audio(audio_path):
    print("[*] Transcribing...")
    model = whisper.load_model("base")  # or "small", "medium", "large"
    result = model.transcribe(audio_path)
    print("[✓] Transcription complete.")
    return result["text"]