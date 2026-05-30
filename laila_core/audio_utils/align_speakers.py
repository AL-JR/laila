from collections import defaultdict


def assign_speakers(whisper_segments, diarization_turns):
    """
    Assign a speaker label to each Whisper segment by finding the diarization
    turn with the most time overlap with that segment.

    Args:
        whisper_segments (list[dict]): Whisper output — each has start, end, text, translated
        diarization_turns (list[dict]): Pyannote output — each has start, end, speaker

    Returns:
        list[dict]: whisper_segments with a 'speaker' key added to each entry.
                    Segments with no overlapping turn get speaker="SPEAKER_00".
    """
    for seg in whisper_segments:
        seg_start = seg["start"]
        seg_end   = seg["end"]

        # Accumulate overlap duration per speaker
        overlap_by_speaker = defaultdict(float)
        for turn in diarization_turns:
            overlap_start = max(seg_start, turn["start"])
            overlap_end   = min(seg_end,   turn["end"])
            overlap = overlap_end - overlap_start
            if overlap > 0:
                overlap_by_speaker[turn["speaker"]] += overlap

        if overlap_by_speaker:
            seg["speaker"] = max(overlap_by_speaker, key=overlap_by_speaker.get)
        else:
            seg["speaker"] = "SPEAKER_00"

    return whisper_segments


def group_by_speaker(segments):
    """
    Return a dict mapping speaker label → list of segments for that speaker.

    Args:
        segments (list[dict]): Segments already annotated with 'speaker'

    Returns:
        dict[str, list[dict]]
    """
    grouped = defaultdict(list)
    for seg in segments:
        grouped[seg.get("speaker", "SPEAKER_00")].append(seg)
    return dict(grouped)
