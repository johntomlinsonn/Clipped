import json
from pathlib import Path
import math
import subprocess
import concurrent.futures
import os
from config import settings
import logging


def create_9_16_with_blur_ffmpeg(input_path: str, output_path: str) -> None:
    """Create a 9:16 aspect ratio video with blurred background using pure FFmpeg."""
    cpu_threads = os.cpu_count() or 4
    
    cmd = [
        "ffmpeg", "-y",
        "-threads", str(cpu_threads),
        "-i", input_path,
        
        # Complex filter: create blurred background + centered main video
        "-filter_complex", 
        "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,gblur=sigma=20[bg];"
        "[0:v]scale=1080:1920:force_original_aspect_ratio=decrease[fg];"
        "[bg][fg]overlay=(W-w)/2:(H-h)/2",
        
        # Optimized encoding
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "23",
        "-c:a", "aac",
        "-b:a", "128k",
        "-movflags", "+faststart",
        
        output_path
    ]
    
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)


def clip_moments(video_path: str, moments: list[dict]) -> list[str]:
    logging.info(f"Starting optimized clip process for video {video_path} with {len(moments)} moments")
    """Create video subclips based on moments list using parallel FFmpeg processing."""
    # Return early if no moments
    if not moments:
        logging.info("No moments provided; skipping clipping")
        return []

    # Prepare output directory
    clips_dir = settings.storage_dir / 'clips'
    clips_dir.mkdir(parents=True, exist_ok=True)

    # Determine optimal number of workers (CPU cores available)
    max_workers = min(len(moments), os.cpu_count() or 4)
    logging.info(f"Using {max_workers} workers for parallel clipping")

    # Process clips in parallel
    clip_paths: list[str] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all clipping tasks
        future_to_moment = {}
        for idx, moment in enumerate(moments, start=1):
            future = executor.submit(_process_single_clip, video_path, moment, idx, clips_dir)
            future_to_moment[future] = (idx, moment)
        
        # Collect results as they complete
        for future in concurrent.futures.as_completed(future_to_moment):
            idx, moment = future_to_moment[future]
            try:
                clip_path = future.result()
                if clip_path:
                    clip_paths.append(clip_path)
                    logging.info(f"Successfully processed clip {idx}")
                else:
                    logging.warning(f"Clip {idx} was skipped or failed")
            except Exception as e:
                logging.error(f"Failed to create clip {idx}: {e}")
                continue
            
    # Sort clip paths to maintain order (since parallel processing may complete out of order)
    clip_paths.sort()
    logging.info(f"Completed all clipping tasks: {len(clip_paths)} clips generated")
    return clip_paths


def _process_single_clip(video_path: str, moment: dict, idx: int, clips_dir: Path) -> str | None:
    """Process a single clip - designed for parallel execution."""
    try:
        start = parse_time(moment['time_start'])
        end = parse_time(moment['time_end'])
        desc = moment.get('description', '')
        logging.info(f"Processing clip {idx}: start={start}, end={end}, description='{desc}'")
        
        safe_desc = "".join(c for c in desc if c.isalnum() or c in (' ', '_')).rstrip().replace(' ', '_')[:50]
        clip_name = f"clip_{idx}_{int(start)}_{int(end)}_{safe_desc}.mp4"
        clip_path = clips_dir / clip_name

        # Check if clip already exists
        if clip_path.exists():
            logging.info(f"Clip {idx} already exists at {clip_path}, skipping")
            return str(clip_path)

        # Create clip with optimized FFmpeg
        clip_with_ffmpeg_optimized(video_path, start, end, clip_path)
        logging.info(f"Saved clip {idx} to {clip_path}")
        return str(clip_path)
        
    except Exception as e:
        logging.error(f"Error processing clip {idx}: {e}")
        return None


def clip_with_ffmpeg_optimized(video_path: str, start: float, end: float, output_path: Path) -> None:
    """Optimized FFmpeg clipping with CPU-focused performance improvements."""
    # Get number of CPU threads for FFmpeg
    cpu_threads = os.cpu_count() or 4
    
    cmd = [
        "ffmpeg", "-y",
        "-threads", str(cpu_threads),  # Use all CPU cores
        "-i", str(video_path),
        "-ss", str(start), 
        "-to", str(end),
        
        # Optimized video processing
        "-vf", "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black",
        "-c:v", "libx264",
        "-preset", "veryfast",  # Much faster encoding at cost of file size
        "-crf", "23",          # Good quality-to-speed balance
        
        # Smart audio handling - copy if compatible, otherwise fast encode
        "-c:a", "aac",         # Use AAC for compatibility
        "-b:a", "128k",        # Reasonable audio bitrate
        "-ar", "44100",        # Standard sample rate
        
        # Additional CPU optimizations
        "-movflags", "+faststart",  # Enable fast start for better streaming
        "-tune", "fastdecode",      # Optimize for fast decoding
        
        str(output_path)
    ]
    
    # Run with minimal output for speed
    result = subprocess.run(
        cmd, 
        check=True, 
        stdout=subprocess.DEVNULL, 
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Only log stderr if there's an actual error
    if result.stderr and "error" in result.stderr.lower():
        logging.warning(f"FFmpeg warning for {output_path.name}: {result.stderr}")


def clip_with_ffmpeg(video_path: str, start: float, end: float, output_path: Path) -> None:
    """Legacy FFmpeg function - kept for compatibility but uses optimized version."""
    clip_with_ffmpeg_optimized(video_path, start, end, output_path)

def parse_time(ts):
    """
    Parse a timestamp string into seconds.
    Supports formats:
      - SS[.fff]
      - MM:SS[.fff]
      - HH:MM:SS[.fff]
    """
    s = ts.strip()
    parts = s.split(':')
    if len(parts) == 1:
        # seconds only
        try:
            return float(s)
        except ValueError:
            raise ValueError(f"Invalid time format: {ts}")
    elif len(parts) == 2:
        # MM:SS
        return int(parts[0]) * 60 + float(parts[1])
    elif len(parts) == 3:
        # HH:MM:SS
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
    else:
        raise ValueError(f"Invalid time format: {ts}")