import os
import ffmpeg

def extract_speaker_sample(video_path, start_time="00:00:03", duration=5, output_dir="laila_core/samples"):
    """
    Extract a short clean audio sample from the video for voice cloning.

    Parameters:
        video_path (str): Path to the video file.
        start_time (str): Time to start the clip (format: HH:MM:SS).
        duration (int): Duration of the audio clip in seconds.
        output_dir (str): Where to save the sample.

    Returns:
        str: Path to the extracted speaker sample.
    """
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "original_speaker.wav")

    (
        ffmpeg
        .input(video_path, ss=start_time, t=duration)
        .output(output_path, format='wav', acodec='pcm_s16le', ar='16000', ac=1)
        .overwrite_output()
        .run(quiet=False)
    )

    print(f"[✓] Speaker sample saved to: {output_path}")
    return output_path
