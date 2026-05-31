import os
import sys
import subprocess
import shutil


def separate_vocals(audio_path, output_dir="output/demucs"):
    """
    Separate vocals from background music/noise using Demucs.
    Returns the path to the vocals-only WAV file.

    Args:
        audio_path (str): Path to the input audio file
        output_dir (str): Directory to store Demucs output

    Returns:
        str: Path to the extracted vocals WAV file
    """
    print("[*] Separating vocals from background audio (Demucs)...")

    os.makedirs(output_dir, exist_ok=True)

    # Use run_demucs.py wrapper to patch torchaudio.save → soundfile,
    # avoiding the torchcodec shared-DLL requirement on Windows.
    _wrapper = os.path.join(os.path.dirname(os.path.dirname(__file__)), "run_demucs.py")
    try:
        subprocess.run(
            [
                sys.executable, _wrapper,
                "--two-stems", "vocals",   # only split into vocals + no_vocals
                "-n", "htdemucs",          # best quality model
                "-o", output_dir,
                audio_path,
            ],
            check=True,
        )
    except subprocess.CalledProcessError as e:
        print(f"[✗] Demucs failed: {e}")
        raise

    # Demucs writes to: output_dir/htdemucs/<stem_name>/<filename>/vocals.wav
    base_name = os.path.splitext(os.path.basename(audio_path))[0]
    vocals_src = os.path.join(output_dir, "htdemucs", base_name, "vocals.wav")
    no_vocals_src = os.path.join(output_dir, "htdemucs", base_name, "no_vocals.wav")

    if not os.path.exists(vocals_src):
        raise FileNotFoundError(
            f"Demucs did not produce expected output at: {vocals_src}"
        )

    # Copy both stems to flat, predictable locations
    vocals_dest = os.path.join(output_dir, "vocals.wav")
    no_vocals_dest = os.path.join(output_dir, "no_vocals.wav")
    shutil.copy2(vocals_src, vocals_dest)
    shutil.copy2(no_vocals_src, no_vocals_dest)

    print(f"[✓] Vocals isolated: {vocals_dest}")
    return vocals_dest, no_vocals_dest
