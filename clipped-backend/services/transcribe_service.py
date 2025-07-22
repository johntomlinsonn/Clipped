import os
from pathlib import Path

from moviepy.audio.io.AudioFileClip import AudioFileClip
from faster_whisper import WhisperModel
from config import settings


def create_transcript(video_path: str, url: str) -> Path:
    """
    Extract audio from video, transcribe using Whisper, and write transcript file.

    Args:
        video_path (str): Path to the video file.
        url (str): Original video URL.

    Returns:
        Path: Path to the generated transcript text file.
    """
    video_path = Path(video_path)
    # Prepare directories
    audio_dir = settings.storage_dir / 'audio'
    transcript_dir = settings.storage_dir / 'transcripts'
    audio_dir.mkdir(parents=True, exist_ok=True)
    transcript_dir.mkdir(parents=True, exist_ok=True)

    # Extract audio to mp3
    audio_path = audio_dir / f"{video_path.stem}.mp3"
    clip = AudioFileClip(str(video_path))
    clip.write_audiofile(str(audio_path))

    # Transcribe using Whisper (faster-whisper)
    model = WhisperModel(
        "distil-large-v3",
        device="cpu",
        compute_type="int8",  # INT8 quantization for speed
        cpu_threads=4           # Set number of threads as per your CPU cores
    )
    # returns (segments, info)
    segments, _ = model.transcribe(str(audio_path))

    # Prepare transcript output
    transcript_path = transcript_dir / f"{video_path.stem}_transcript.txt"
    with open(transcript_path, 'w', encoding='utf-8') as f:
        f.write(f"Video: {video_path.name}\n")
        f.write(f"URL: {url}\n\n")
        f.write("{\n")
        # Write each segment's start time and text
        for segment in segments:
            start = getattr(segment, 'start', 0.0)
            text = getattr(segment, 'text', '').strip().replace('"', "'")
            f.write(f'  "{start:.2f}": "{text}",\n')
        f.write("}\n")

    return transcript_path
