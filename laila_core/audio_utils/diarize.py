import os


def diarize_audio(audio_path, hf_token=None, min_speakers=None, max_speakers=None):
    """
    Run speaker diarization using pyannote.audio 3.x.

    Requires:
      - pip install pyannote.audio
      - A HuggingFace token with access to pyannote/speaker-diarization-3.1
        (accept terms at https://huggingface.co/pyannote/speaker-diarization-3.1)
      - Set env var HF_TOKEN or pass hf_token directly

    Args:
        audio_path (str): Path to the audio file (WAV recommended)
        hf_token (str): HuggingFace token. Falls back to HF_TOKEN env var.
        min_speakers (int): Optional minimum number of speakers
        max_speakers (int): Optional maximum number of speakers

    Returns:
        list[dict]: Sorted list of diarization turns, each with:
            start   (float): turn start in seconds
            end     (float): turn end in seconds
            speaker (str):   speaker label e.g. "SPEAKER_00"
    """
    try:
        from pyannote.audio import Pipeline
    except ImportError:
        raise ImportError(
            "pyannote.audio is required for multi-speaker diarization.\n"
            "Install it with: pip install pyannote.audio"
        )

    token = hf_token or os.environ.get("HF_TOKEN")
    if not token:
        raise ValueError(
            "A HuggingFace token is required for pyannote diarization.\n"
            "Set the HF_TOKEN environment variable or pass hf_token= directly.\n"
            "Accept the model terms at: https://huggingface.co/pyannote/speaker-diarization-3.1"
        )

    # Log in so huggingface_hub caches the token for all downstream downloads
    from huggingface_hub import login
    login(token=token, add_to_git_credential=False)

    print("[*] Loading pyannote speaker diarization pipeline...")
    pipeline = Pipeline.from_pretrained(
        "pyannote/speaker-diarization-3.1",
        token=token,
    )

    kwargs = {}
    if min_speakers is not None:
        kwargs["min_speakers"] = min_speakers
    if max_speakers is not None:
        kwargs["max_speakers"] = max_speakers

    print(f"[*] Running diarization on: {audio_path}")
    result = pipeline(audio_path, **kwargs)

    # Newer pyannote wraps the annotation in a DiarizeOutput object
    diarization = getattr(result, "speaker_diarization", result)

    turns = []
    for turn, _, speaker in diarization.itertracks(yield_label=True):
        turns.append({
            "start":   round(turn.start, 3),
            "end":     round(turn.end, 3),
            "speaker": speaker,
        })

    turns.sort(key=lambda t: t["start"])

    speakers = sorted({t["speaker"] for t in turns})
    print(f"[✓] Diarization complete — {len(turns)} turns, {len(speakers)} speaker(s): {speakers}")
    return turns
