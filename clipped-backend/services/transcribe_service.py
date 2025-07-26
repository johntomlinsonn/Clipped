import os
from pathlib import Path
import logging
from moviepy.audio.io.AudioFileClip import AudioFileClip
from faster_whisper import WhisperModel
from config import settings

import threading
import concurrent.futures
import subprocess
from moviepy.audio.io.AudioFileClip import AudioFileClip
from pathlib import Path

# Preload Whisper model in background to overlap with video download
_model = None
_model_loaded_event = threading.Event()


def _load_model():
    global _model
    try:
        logging.info("Loading Whisper model medium.en in background")
        _model = WhisperModel(
            "medium.en",
            device="cpu",    
            compute_type="int8",        
            cpu_threads=4,
        )
        logging.info("Whisper model loaded successfully")
        _model_loaded_event.set()
    except Exception as e:
        logging.error(f"Failed to load Whisper model: {e}")
        _model_loaded_event.set()  # Set event even on failure to prevent infinite waiting


# Kick off background loading of the model
logging.info("Starting Whisper model loading thread")
threading.Thread(target=_load_model, daemon=True).start()
logging.info("Whisper model loading initiated in background thread")
 
def _parallel_transcribe(audio_path: Path, model: WhisperModel, audio_dir: Path, chunk_duration: float = 60.0, max_workers: int = 4):
    """
    Split audio into chunks and transcribe each chunk in parallel.
    Returns a list of segments with adjusted start times.
    """
    # Determine total duration
    clip = AudioFileClip(str(audio_path))
    total_duration = clip.duration
    clip.close()

    # Prepare chunk parameters
    chunks = []
    start = 0.0
    idx = 1
    while start < total_duration:
        end = min(start + chunk_duration, total_duration)
        chunk_path = audio_dir / f"{audio_path.stem}_chunk_{idx}.mp3"
        chunks.append((idx, start, end, chunk_path))
        start = end
        idx += 1

    # Worker to transcribe a single chunk
    def _transcribe_chunk(idx, start_offset, end, chunk_path):
        # Extract chunk using ffmpeg
        cmd = [
            "ffmpeg", "-y", "-i", str(audio_path),
            "-ss", str(start_offset), "-to", str(end),
            str(chunk_path)
        ]
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        # Transcribe chunk
        segs, _ = model.transcribe(str(chunk_path))
        # Adjust segment start times
        for seg in segs:
            setattr(seg, "start", getattr(seg, "start", 0.0) + start_offset)
        # Clean up chunk file
        try:
            chunk_path.unlink()
        except Exception:
            pass
        return segs

    # Execute in parallel
    segments = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [
            executor.submit(_transcribe_chunk, idx, start, end, path)
            for idx, start, end, path in chunks
        ]
        for future in concurrent.futures.as_completed(futures):
            try:
                segments.extend(future.result())
            except Exception as e:
                logging.warning(f"Chunk transcription failed: {e}")
    # Sort segments by start time
    segments.sort(key=lambda s: getattr(s, "start", 0.0))
    return segments
   
def _write_transcript(transcript_path: Path, video_name: str, url: str, segments: list) -> None:
    """
    Write segments and metadata to a transcript file.
    This version builds the output in memory before writing, for faster I/O.
    """
    lines = [
        f"Video: {video_name}\n",
        f"URL: {url}\n\n",
        "{\n"
    ]
    # Append segments lines
    for segment in segments:
        start = getattr(segment, 'start', 0.0)
        # replace any double-quotes in text with single-quotes
        text = getattr(segment, 'text', '').strip().replace('"', "'")
        lines.append(f'  "{start:.2f}": "{text}",\n')
    lines.append("}\n")
    # Write all at once
    with open(transcript_path, "w", encoding="utf-8") as f:
        f.writelines(lines)


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
    logging.info(f"Starting transcription for video {video_path.name} from URL {url}")
    # Prepare directories
    audio_dir = settings.storage_dir / "audio"
    transcript_dir = settings.storage_dir / "transcripts"
    audio_dir.mkdir(parents=True, exist_ok=True)
    transcript_dir.mkdir(parents=True, exist_ok=True)

    # Check if transcript already exists
    transcript_path = transcript_dir / f"{video_path.stem}_transcript.txt"
    if transcript_path.exists():
        logging.info(f"Transcript already exists at {transcript_path}, skipping transcription")
        return transcript_path

    # Extract audio to mp3
    audio_path = audio_dir / f"{video_path.stem}.mp3"
    logging.info(f"Extracting audio to {audio_path} via ffmpeg")
    cmd = [
        "ffmpeg", "-y", "-i", str(video_path),
        "-vn", "-acodec", "mp3", str(audio_path)
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    logging.info("Audio extraction completed")

    # Transcribe using Whisper (faster-whisper)
    logging.info("Waiting for Whisper model to load")
    _model_loaded_event.wait()
    
    if _model is None:
        raise RuntimeError("Whisper model failed to load")
        
    model = _model
    # Transcribe audio serially
    logging.info("Transcribing audio using serial transcription")
    raw_segments, _ = model.transcribe(str(audio_path))
    segments = list(raw_segments)
    logging.info(f"Serial transcription produced {len(segments)} segments")

    # Prepare transcript output
    transcript_path = transcript_dir / f"{video_path.stem}_transcript.txt"
    logging.info(f"Writing transcript to {transcript_path}")
    # Write transcript file
    _write_transcript(transcript_path, video_path.name, url, segments)
    logging.info("Transcript creation completed")

    return transcript_path
