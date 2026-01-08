import ffmpeg
import os

def extract_audio(video_path, output_audio_path=None):
    """
    Extract audio from video file and save as WAV.
    
    Args:
        video_path (str): Path to the video file
        output_audio_path (str): Path for output audio file (optional)
        
    Returns:
        str: Path to the extracted audio file
    """
    # If no output path specified, create one in the output directory
    if output_audio_path is None:
        base_dir = os.path.dirname(__file__)
        output_audio_path = os.path.join(base_dir, "..", "output", "audio.wav")
        output_audio_path = os.path.abspath(output_audio_path)

    os.makedirs(os.path.dirname(output_audio_path), exist_ok=True)

    try:
        ffmpeg.input(video_path).output(
            output_audio_path, 
            ac=1,  # Mono audio
            ar='16k'  # 16kHz sample rate
        ).run(overwrite_output=True)
        print(f"[✓] Audio extracted to {output_audio_path}")
        return output_audio_path
    except ffmpeg.Error as e:
        print(f"[✗] Error extracting audio: {e}")
        raise