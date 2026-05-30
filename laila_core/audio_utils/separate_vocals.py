import os
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

    try:
        subprocess.run(
            [
                "python", "-m", "demucs",
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
    vocals_path = os.path.join(output_dir, "htdemucs", base_name, "vocals.wav")

    if not os.path.exists(vocals_path):
        raise FileNotFoundError(
            f"Demucs did not produce expected output at: {vocals_path}"
        )

    # Copy to a flat, predictable location
    dest = os.path.join(output_dir, "vocals.wav")
    shutil.copy2(vocals_path, dest)

    print(f"[✓] Vocals isolated: {dest}")
    return dest
