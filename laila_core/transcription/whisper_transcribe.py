import whisper


def transcribe_audio(audio_path):
    """
    Transcribe audio file using OpenAI Whisper.

    Args:
        audio_path (str): Path to the audio file

    Returns:
        list[dict]: Segments with keys: start (float), end (float), text (str)
    """
    print("[*] Transcribing...")
    model = whisper.load_model("medium")
    result = model.transcribe(audio_path, word_timestamps=True)

    segments = [
        {"start": s["start"], "end": s["end"], "text": s["text"].strip()}
        for s in result["segments"]
        if s["text"].strip()
    ]

    print(f"[✓] Transcription complete — {len(segments)} segment(s).")
    return segments