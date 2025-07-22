import os
import urllib.request
from pathlib import Path
import yt_dlp

# Downloads directory (unified)
DOWNLOADS_DIR = Path(__file__).parent / 'downloads'
DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)

def download(url):
    """Download a YouTube video and its transcript."""
    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',
        'outtmpl': str(DOWNLOADS_DIR / '%(title)s.%(ext)s'),
        'writesubtitles': False,
        'writeautomaticsub': False,
        'merge_output_format': 'mp4',
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        ydl.download([url])
    # Find downloaded video file
    video_files = list(DOWNLOADS_DIR.glob('*.mp4'))
    video_path = video_files[0] if video_files else None
    
    return video_path