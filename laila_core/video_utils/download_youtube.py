
import os
import yt_dlp

def download_youtube_video(url, output_path="downloads", filename="video.mp4"):
    os.makedirs(output_path, exist_ok=True)
    full_path = os.path.join(output_path, filename)

    ydl_opts = {
        'outtmpl': full_path,
        'format': 'bestvideo+bestaudio/best',
        'merge_output_format': 'mp4'
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    
    return full_path

