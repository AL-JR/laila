import ffmpeg
import os

def merge_audio_video(video_path, audio_path, output_path="output/final_video.mp4"):
    """
    Replace the audio track of a video with new audio.
    
    Args:
        video_path (str): Path to the original video file
        audio_path (str): Path to the new audio file
        output_path (str): Path for the output video file
        
    Returns:
        str: Path to the final video with replaced audio
    """
    print("[*] Merging new audio with video...")
    
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else "output", exist_ok=True)
    
    try:
        # Get video input without audio
        video = ffmpeg.input(video_path).video
        
        # Get new audio input
        audio = ffmpeg.input(audio_path).audio
        
        # Merge video and audio
        ffmpeg.output(
            video, 
            audio, 
            output_path,
            vcodec='copy',  # Copy video without re-encoding
            acodec='aac',   # Encode audio as AAC
            audio_bitrate='192k',
            strict='experimental'
        ).overwrite_output().run(capture_output=True)
        
        print(f"[✓] Final dubbed video saved to: {output_path}")
        return output_path
        
    except ffmpeg.Error as e:
        print(f"[✗] Error merging audio and video: {e}")
        print(f"[✗] stderr: {e.stderr.decode() if e.stderr else 'No error details'}")
        raise

def adjust_audio_speed(audio_path, target_duration, output_path="output/adjusted_audio.wav"):
    """
    Adjust audio speed to match target duration (useful if translation is different length).
    
    Args:
        audio_path (str): Path to the audio file
        target_duration (float): Target duration in seconds
        output_path (str): Path for the adjusted audio file
        
    Returns:
        str: Path to the adjusted audio file
    """
    print(f"[*] Adjusting audio speed to match target duration of {target_duration}s...")
    
    try:
        # Get current duration
        probe = ffmpeg.probe(audio_path)
        current_duration = float(probe['streams'][0]['duration'])
        
        # Calculate speed factor
        speed_factor = current_duration / target_duration
        
        # Adjust speed using atempo filter
        # atempo has limits: 0.5 to 2.0, so chain if needed
        if 0.5 <= speed_factor <= 2.0:
            ffmpeg.input(audio_path).filter('atempo', speed_factor).output(
                output_path
            ).overwrite_output().run(capture_output=True)
        else:
            # Chain multiple atempo filters for extreme speed changes
            print(f"[!] Large speed adjustment needed: {speed_factor}x")
            if speed_factor > 2.0:
                # Speed up: chain multiple atempo=2.0
                chain = ffmpeg.input(audio_path)
                remaining = speed_factor
                while remaining > 2.0:
                    chain = chain.filter('atempo', 2.0)
                    remaining /= 2.0
                chain = chain.filter('atempo', remaining)
                chain.output(output_path).overwrite_output().run(capture_output=True)
            else:
                # Slow down: chain multiple atempo=0.5
                chain = ffmpeg.input(audio_path)
                remaining = speed_factor
                while remaining < 0.5:
                    chain = chain.filter('atempo', 0.5)
                    remaining /= 0.5
                chain = chain.filter('atempo', remaining)
                chain.output(output_path).overwrite_output().run(capture_output=True)
        
        print(f"[✓] Audio speed adjusted (factor: {speed_factor:.2f}x)")
        return output_path
        
    except Exception as e:
        print(f"[✗] Error adjusting audio speed: {e}")
        raise