import whisper

def transcribe_audio(audio_path):
    """
    Transcribe audio file to text using OpenAI Whisper.
    
    Args:
        audio_path (str): Path to the audio file
        
    Returns:
        str: Transcribed text
    """
    print("[*] Transcribing...")
    model = whisper.load_model("medium")  # Options: "tiny", "base", "small", "medium", "large"
    result = model.transcribe(audio_path, word_timestamps=True)
    print("[✓] Transcription complete.")
    return result["text"]