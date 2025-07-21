import os
import urllib.request
from pathlib import Path
import yt_dlp

# Downloads directory (unified)
DOWNLOADS_DIR = Path(__file__).parent / 'downloads'
DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)

# Extract transcript functions

def extract_transcript_with_timestamps(info, output_path):
    title = info.get('title', 'video')
    clean_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
    transcript_filename = f"{clean_title}_transcript.txt"
    transcript_path = output_path / transcript_filename
    # Subtitles
    subtitles = info.get('subtitles', {})
    automatic_captions = info.get('automatic_captions', {})
    subtitle_data = None
    if 'en' in subtitles:
        subtitle_data = subtitles['en']
    elif 'en' in automatic_captions:
        subtitle_data = automatic_captions['en']
    if subtitle_data:
        vtt = next((s for s in subtitle_data if s.get('ext') == 'vtt'), None)
        if vtt and vtt.get('url'):
            try:
                with urllib.request.urlopen(vtt['url']) as resp:
                    vtt_content = resp.read().decode('utf-8')
                transcript_text = parse_vtt_to_transcript(vtt_content)
                with open(transcript_path, 'w', encoding='utf-8') as f:
                    f.write(transcript_text)
                return transcript_path
            except Exception:
                pass
    # fallback
    with open(transcript_path, 'w', encoding='utf-8') as f:
        f.write('No transcript available.')
    return transcript_path


def parse_vtt_to_transcript(vtt_content):
    lines = vtt_content.split('\n')
    transcript = []
    current_time = ''
    current_text = ''
    for line in lines:
        line = line.strip()
        if not line or line.startswith('WEBVTT') or line.startswith('NOTE'):
            continue
        if '-->' in line:
            if current_time and current_text:
                transcript.append(f"[{current_time}] {current_text}")
            current_time = line.split(' --> ')[0]
            current_text = ''
        else:
            current_text = current_text + (' ' if current_text else '') + line
    if current_time and current_text:
        transcript.append(f"[{current_time}] {current_text}")
    return '\n'.join(transcript)


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
    # Extract transcript
    transcript_path = extract_transcript_with_timestamps(info, DOWNLOADS_DIR)
    return video_path, transcript_path
