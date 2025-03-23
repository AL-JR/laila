import ffmpeg
import os
def extract_audio(video_path, output_audio_path="output/audio.wav"):
    os.environ["PATH"] += os.pathsep + r"D:\ffmpeg-7.1.1-essentials_build\bin"

    base_dir = os.path.dirname(__file__)  # path to /laila_core/video_utils
    output_audio_path = os.path.join(base_dir, "..", "output", "audio.wav")
    output_audio_path = os.path.abspath(output_audio_path)

    os.makedirs(os.path.dirname(output_audio_path), exist_ok=True)

    ffmpeg.input(video_path).output(output_audio_path, ac=1, ar='16k').run(overwrite_output=True)
    print(f"[✓] Audio extracted to {output_audio_path}")
    return output_audio_path