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


def resolve_overlaps(segments):
    """
    Ensure no two segments overlap in time. When two segments overlap:
    - The longer (dominant) segment wins and keeps its full duration
    - The shorter segment is trimmed to end where the longer one starts,
      or dropped entirely if it becomes too short (<0.3s)

    Args:
        segments (list[dict]): Speaker-annotated segments sorted by start time

    Returns:
        list[dict]: Non-overlapping segments sorted by start time
    """
    if not segments:
        return segments

    sorted_segs = sorted(segments, key=lambda s: s["start"])
    resolved = [sorted_segs[0]]

    for current in sorted_segs[1:]:
        prev = resolved[-1]
        if current["start"] < prev["end"]:
            # Overlap detected — determine winner by duration
            prev_dur = prev["end"] - prev["start"]
            cur_dur = current["end"] - current["start"]

            if cur_dur > prev_dur:
                # Current is longer — trim previous to end at current's start
                trimmed_dur = current["start"] - prev["start"]
                if trimmed_dur >= 0.3:
                    resolved[-1] = dict(prev, end=current["start"])
                else:
                    resolved.pop()  # prev too short after trim, drop it
                resolved.append(current)
            else:
                # Previous is longer (or equal) — trim current to start after previous
                new_start = prev["end"]
                trimmed_dur = current["end"] - new_start
                if trimmed_dur >= 0.3:
                    resolved.append(dict(current, start=new_start))
                # else drop current entirely
        else:
            resolved.append(current)

    dropped = len(sorted_segs) - len(resolved)
    if dropped:
        print(f"[*] Overlap resolution: {dropped} segment(s) trimmed/dropped")

    return resolved


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
