import os
import json
from pathlib import Path
import logging
import threading
import concurrent.futures
import subprocess
from faster_whisper import WhisperModel
from config import settings

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
 
def _get_audio_duration(audio_path: Path) -> float:
    """
    Get audio duration using ffprobe (faster than loading with MoviePy).
    Returns duration in seconds.
    """
    cmd = [
        "ffprobe", "-v", "quiet", "-show_entries", "format=duration",
        "-of", "csv=p=0", str(audio_path)
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return float(result.stdout.strip())
    except Exception as e:
        logging.error(f"Failed to get audio duration with ffprobe: {e}")
        # Fallback to a basic approach - this should rarely happen
        raise RuntimeError(f"Could not determine audio duration: {e}")


def _parallel_transcribe(audio_path: Path, model: WhisperModel, audio_dir: Path, chunk_duration: float = 60.0, max_workers: int = 4):
    """
    Split audio into chunks and transcribe each chunk in parallel.
    Returns a list of segments with adjusted start times.
    """
    # Determine total duration using ffprobe (faster than MoviePy)
    total_duration = _get_audio_duration(audio_path)
    logging.info(f"Audio duration: {total_duration:.2f} seconds, chunk_duration: {chunk_duration}s, max_workers: {max_workers}")

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

    logging.info(f"Split audio into {len(chunks)} chunks for parallel processing")

    # Worker to transcribe a single chunk
    def _transcribe_chunk(idx, start_offset, end, chunk_path):
        try:
            logging.debug(f"Processing chunk {idx}: {start_offset:.2f}s - {end:.2f}s")
            # Extract chunk using ffmpeg
            cmd = [
                "ffmpeg", "-y", "-i", str(audio_path),
                "-ss", str(start_offset), "-to", str(end),
                "-acodec", "mp3", str(chunk_path)
            ]
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            # Transcribe chunk
            segs, _ = model.transcribe(str(chunk_path))
            # Convert to list and adjust segment start times
            segment_list = []
            for seg in segs:
                # Create a new segment with adjusted timestamp
                adjusted_start = getattr(seg, "start", 0.0) + start_offset
                adjusted_end = getattr(seg, "end", 0.0) + start_offset
                text = getattr(seg, "text", "").strip()
                
                # Create a simple dict to store segment info
                segment_info = {
                    "start": adjusted_start,
                    "end": adjusted_end, 
                    "text": text
                }
                segment_list.append(segment_info)
            
            logging.debug(f"Chunk {idx} transcribed: {len(segment_list)} segments")
            return segment_list
            
        except Exception as e:
            logging.error(f"Failed to transcribe chunk {idx}: {e}")
            return []
        finally:
            # Clean up chunk file
            try:
                if chunk_path.exists():
                    chunk_path.unlink()
            except Exception as cleanup_error:
                logging.warning(f"Failed to cleanup chunk file {chunk_path}: {cleanup_error}")

    # Execute in parallel
    segments = []
    logging.info(f"Starting parallel transcription with {max_workers} workers")
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [
            executor.submit(_transcribe_chunk, idx, start, end, path)
            for idx, start, end, path in chunks
        ]
        
        completed_chunks = 0
        for future in concurrent.futures.as_completed(futures):
            try:
                chunk_segments = future.result()
                segments.extend(chunk_segments)
                completed_chunks += 1
                logging.info(f"Completed chunk {completed_chunks}/{len(chunks)}")
            except Exception as e:
                logging.warning(f"Chunk transcription failed: {e}")
    
    # Sort segments by start time
    segments.sort(key=lambda s: s["start"])
    logging.info(f"Parallel transcription completed: {len(segments)} total segments")
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
        # Handle both dict format (from parallel) and object format (from serial)
        if isinstance(segment, dict):
            start = segment.get('start', 0.0)
            text = segment.get('text', '').strip().replace('"', "'")
        else:
            start = getattr(segment, 'start', 0.0)
            text = getattr(segment, 'text', '').strip().replace('"', "'")
        
        lines.append(f'  "{start:.2f}": "{text}",\n')
    lines.append("}\n")
    # Write all at once
    with open(transcript_path, "w", encoding="utf-8") as f:
        f.writelines(lines)


def create_transcript(video_path: str, url: str, chunk_duration: float = 60.0, max_workers: int = 4, force_serial: bool = False) -> Path:
    """
    Extract audio from video, transcribe using Whisper, and write transcript file.

    Args:
        video_path (str): Path to the video file.
        url (str): Original video URL.
        chunk_duration (float): Duration of each chunk in seconds for parallel processing.
        max_workers (int): Maximum number of parallel workers.
        force_serial (bool): Force serial transcription (for debugging or fallback).

    Returns:
        Path: Path to the generated transcript text file.
    """
    video_path = Path(video_path)
    logging.info(f"Starting transcription for video {video_path.name} from URL {url}")
    logging.info(f"Using chunk_duration={chunk_duration}s, max_workers={max_workers}, force_serial={force_serial}")
    
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
        "-vn", "-acodec", "mp3", "-ab", "128k", str(audio_path)
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    logging.info("Audio extraction completed")

    # Transcribe using Whisper (faster-whisper)
    logging.info("Waiting for Whisper model to load")
    _model_loaded_event.wait()
    
    if _model is None:
        raise RuntimeError("Whisper model failed to load")
        
    model = _model
    
    # Choose transcription method based on parameters and audio length
    try:
        if force_serial:
            logging.info("Using serial transcription (forced)")
            raw_segments, _ = model.transcribe(str(audio_path))
            segments = [{"start": getattr(seg, "start", 0.0), 
                        "end": getattr(seg, "end", 0.0),
                        "text": getattr(seg, "text", "")} for seg in raw_segments]
        else:
            # Get audio duration to decide on parallel processing
            duration = _get_audio_duration(audio_path)
            
            # Use parallel processing for longer audio or always if chunk_duration allows
            if duration > chunk_duration:
                logging.info(f"Using parallel transcription for {duration:.2f}s audio")
                segments = _parallel_transcribe(audio_path, model, audio_dir, chunk_duration, max_workers)
            else:
                logging.info(f"Using serial transcription for short audio ({duration:.2f}s)")
                raw_segments, _ = model.transcribe(str(audio_path))
                segments = [{"start": getattr(seg, "start", 0.0), 
                            "end": getattr(seg, "end", 0.0),
                            "text": getattr(seg, "text", "")} for seg in raw_segments]
        
        logging.info(f"Transcription completed: {len(segments)} segments")
        
    except Exception as e:
        logging.error(f"Parallel transcription failed: {e}")
        logging.info("Falling back to serial transcription")
        # Fallback to serial transcription
        raw_segments, _ = model.transcribe(str(audio_path))
        segments = [{"start": getattr(seg, "start", 0.0), 
                    "end": getattr(seg, "end", 0.0),
                    "text": getattr(seg, "text", "")} for seg in raw_segments]
        logging.info(f"Fallback transcription completed: {len(segments)} segments")

    # Write transcript file
    logging.info(f"Writing transcript to {transcript_path}")
    _write_transcript(transcript_path, video_path.name, url, segments)
    logging.info("Transcript creation completed")

    return transcript_path
