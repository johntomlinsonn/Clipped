import os
import json
import hashlib
import io
from pathlib import Path
import threading
import concurrent.futures
import subprocess
from queue import Queue
from faster_whisper import WhisperModel
from config import settings

_model = None
_model_loaded_event = threading.Event()
_cache_dir = None

def _init_cache():
    global _cache_dir
    _cache_dir = settings.storage_dir / ".transcript_cache"
    _cache_dir.mkdir(parents=True, exist_ok=True)

def _load_model():
    global _model
    try:
        _model = WhisperModel(
            "small.en",
            device="cpu",    
            compute_type="int8",        
            cpu_threads=4,
        )
        _model_loaded_event.set()
    except Exception:
        _model_loaded_event.set()

threading.Thread(target=_load_model, daemon=True).start()
threading.Thread(target=_init_cache, daemon=True).start()

def _get_audio_duration(audio_path: Path) -> float:
    cmd = [
        "ffprobe", "-v", "quiet", "-show_entries", "format=duration",
        "-of", "csv=p=0", str(audio_path)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return float(result.stdout.strip())

def _chunk_hash(video_path: str, start: float, duration: float) -> str:
    content = f"{video_path}-{start}-{duration}-small.en"
    return hashlib.sha256(content.encode()).hexdigest()

def _get_cached_transcript(hash_key: str) -> list:
    cache_file = _cache_dir / f"{hash_key}.json"
    if cache_file.exists():
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return None

def _save_cached_transcript(hash_key: str, segments: list) -> None:
    cache_file = _cache_dir / f"{hash_key}.json"
    try:
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(segments, f)
    except Exception:
        pass

def _extract_chunk_to_memory(audio_path: Path, start: float, duration: float) -> io.BytesIO:
    cmd = [
        "ffmpeg", "-ss", str(start), "-t", str(duration),
        "-i", str(audio_path), "-f", "wav", "-ac", "1", "-ar", "16000", 
        "-loglevel", "quiet", "pipe:1"
    ]
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    return io.BytesIO(proc.stdout)

def _group_chunks(chunks: list, target_duration: float = 120.0) -> list:
    grouped = []
    current_group = []
    current_duration = 0.0
    
    for chunk in chunks:
        chunk_duration = chunk['duration']
        if current_duration + chunk_duration <= target_duration:
            current_group.append(chunk)
            current_duration += chunk_duration
        else:
            if current_group:
                grouped.append(current_group)
            current_group = [chunk]
            current_duration = chunk_duration
    
    if current_group:
        grouped.append(current_group)
    
    return grouped

def _prefetch_audio_chunks(audio_path: Path, chunk_groups: list, chunk_queue: Queue, model: WhisperModel) -> None:
    for group_idx, chunk_group in enumerate(chunk_groups):
        hash_key = _chunk_hash(str(audio_path), chunk_group[0]['start'], sum(c['duration'] for c in chunk_group))
        
        cached_segments = _get_cached_transcript(hash_key)
        if cached_segments:
            chunk_queue.put((cached_segments, True))
            continue
        
        start_time = chunk_group[0]['start']
        total_duration = sum(chunk['duration'] for chunk in chunk_group)
        
        try:
            audio_buffer = _extract_chunk_to_memory(audio_path, start_time, total_duration)
            chunk_queue.put((audio_buffer, start_time, total_duration, hash_key, False))
        except Exception:
            chunk_queue.put(([], True))
    
    chunk_queue.put(None)

def _transcribe_consumer(chunk_queue: Queue, result_queue: Queue, model: WhisperModel) -> None:
    while True:
        item = chunk_queue.get()
        if item is None:
            break
        
        if len(item) == 2:
            segments, is_cached = item
            result_queue.put(segments)
        else:
            audio_buffer, start_offset, duration, hash_key, is_cached = item
            try:
                raw_segments, _ = model.transcribe(audio_buffer)
                segments = []
                for seg in raw_segments:
                    segment_info = {
                        "start": getattr(seg, "start", 0.0) + start_offset,
                        "end": getattr(seg, "end", 0.0) + start_offset,
                        "text": getattr(seg, "text", "").strip()
                    }
                    segments.append(segment_info)
                
                _save_cached_transcript(hash_key, segments)
                result_queue.put(segments)
            except Exception:
                result_queue.put([])

def _pipeline_transcribe(audio_path: Path, model: WhisperModel, chunk_duration: float = 120.0, max_workers: int = 4) -> list:
    total_duration = _get_audio_duration(audio_path)
    
    chunks = []
    start = 0.0
    while start < total_duration:
        end = min(start + 60.0, total_duration)
        chunks.append({
            'start': start,
            'duration': end - start
        })
        start = end
    
    chunk_groups = _group_chunks(chunks, chunk_duration)
    chunk_queue = Queue(maxsize=max_workers * 2)
    result_queue = Queue()
    
    producer_thread = threading.Thread(
        target=_prefetch_audio_chunks,
        args=(audio_path, chunk_groups, chunk_queue, model)
    )
    
    consumer_threads = []
    for _ in range(min(max_workers, len(chunk_groups))):
        t = threading.Thread(
            target=_transcribe_consumer,
            args=(chunk_queue, result_queue, model)
        )
        consumer_threads.append(t)
        t.start()
    
    producer_thread.start()
    producer_thread.join()
    
    for _ in consumer_threads:
        chunk_queue.put(None)
    
    for t in consumer_threads:
        t.join()
    
    all_segments = []
    while not result_queue.empty():
        segments = result_queue.get()
        all_segments.extend(segments)
    
    all_segments.sort(key=lambda s: s["start"])
    return all_segments

def _write_transcript(transcript_path: Path, video_name: str, url: str, segments: list) -> None:
    lines = [
        f"Video: {video_name}\n",
        f"URL: {url}\n\n",
        "{\n"
    ]
    
    for segment in segments:
        start = segment.get('start', 0.0)
        text = segment.get('text', '').strip().replace('"', "'")
        lines.append(f'  "{start:.2f}": "{text}",\n')
    
    lines.append("}\n")
    
    with open(transcript_path, "w", encoding="utf-8") as f:
        f.writelines(lines)

def create_transcript(video_path: str, url: str, chunk_duration: float = 120.0, max_workers: int = 4, force_serial: bool = False) -> Path:
    video_path = Path(video_path)
    
    audio_dir = settings.storage_dir / "audio"
    transcript_dir = settings.storage_dir / "transcripts"
    audio_dir.mkdir(parents=True, exist_ok=True)
    transcript_dir.mkdir(parents=True, exist_ok=True)

    transcript_path = transcript_dir / f"{video_path.stem}_transcript.txt"
    if transcript_path.exists():
        return transcript_path

    audio_path = audio_dir / f"{video_path.stem}.mp3"
    cmd = [
        "ffmpeg", "-y", "-i", str(video_path),
        "-vn", "-acodec", "mp3", "-ab", "128k", "-loglevel", "quiet", str(audio_path)
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    _model_loaded_event.wait()
    
    if _model is None:
        raise RuntimeError("Whisper model failed to load")
        
    if force_serial:
        raw_segments, _ = _model.transcribe(str(audio_path))
        segments = [{"start": getattr(seg, "start", 0.0), 
                    "end": getattr(seg, "end", 0.0),
                    "text": getattr(seg, "text", "")} for seg in raw_segments]
    else:
        try:
            segments = _pipeline_transcribe(audio_path, _model, chunk_duration, max_workers)
        except Exception:
            raw_segments, _ = _model.transcribe(str(audio_path))
            segments = [{"start": getattr(seg, "start", 0.0), 
                        "end": getattr(seg, "end", 0.0),
                        "text": getattr(seg, "text", "")} for seg in raw_segments]

    _write_transcript(transcript_path, video_path.name, url, segments)
    return transcript_path
