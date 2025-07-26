import json
from pathlib import Path
import math
import subprocess
from moviepy.video.io.VideoFileClip import VideoFileClip
from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip
from config import settings
import logging


def create_9_16_with_blur(clip):
    """Create a 9:16 aspect ratio video with the original in center and blurred background"""
    # Get original dimensions
    w, h = clip.size
    
    # Calculate 9:16 dimensions based on original width
    target_width = w
    target_height = int(w * 16 / 9)
    
    # If the calculated height is smaller than original, use original height and adjust width
    if target_height < h:
        target_height = h
        target_width = int(h * 9 / 16)
    
    # Create background - just a scaled version for now (blur can be added later)
    background = clip.resized((target_width, target_height))
    
    # Calculate scaling for the main clip to fit nicely in the center
    # We want to maintain aspect ratio and fit within reasonable bounds
    scale_factor = min(target_width * 0.8 / w, target_height * 0.6 / h)
    main_clip = clip.resized(scale_factor)
    
    # Center the main clip
    main_clip = main_clip.with_position('center')
    
    # Composite the clips
    final_clip = CompositeVideoClip([background, main_clip], size=(target_width, target_height))
    
    return final_clip


def clip_moments(video_path: str, moments: list[dict]) -> list[str]:
    logging.info(f"Starting clip process for video {video_path} with {len(moments)} moments")
    """Create video subclips based on moments list using FFmpeg for speed."""
    # Return early if no moments
    if not moments:
        logging.info("No moments provided; skipping clipping")
        return []

    # Prepare output directory
    clips_dir = settings.storage_dir / 'clips'
    clips_dir.mkdir(parents=True, exist_ok=True)

    # Process each moment, collect clip paths
    clip_paths: list[str] = []
    for idx, moment in enumerate(moments, start=1):
        start = parse_time(moment['time_start'])
        end = parse_time(moment['time_end'])
        desc = moment.get('description', '')
        logging.info(f"Clipping moment {idx}: start={start}, end={end}, description='{desc}'")
        safe_desc = "".join(c for c in desc if c.isalnum() or c in (' ', '_')).rstrip().replace(' ', '_')[:50]
        clip_name = f"clip_{idx}_{int(start)}_{int(end)}_{safe_desc}.mp4"
        clip_path = clips_dir / clip_name

        # Check if clip already exists
        if clip_path.exists():
            logging.info(f"Clip {idx} already exists at {clip_path}, skipping")
            clip_paths.append(str(clip_path))
            continue

        # Use FFmpeg for fast clipping
        try:
            clip_with_ffmpeg(video_path, start, end, clip_path)
            logging.info(f"Saved clip {idx} to {clip_path}")
            clip_paths.append(str(clip_path))
        except Exception as e:
            logging.error(f"Failed to create clip {idx}: {e}")
            continue
            
    logging.info("Completed all clipping tasks")
    return clip_paths


def clip_with_ffmpeg(video_path: str, start: float, end: float, output_path: Path) -> None:
    """Use FFmpeg to extract a clip from video and convert to 9:16 aspect ratio with black bars"""
    cmd = [
        "ffmpeg", "-y", "-i", str(video_path),
        "-ss", str(start), "-to", str(end),
        "-vf", "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black",
        "-c:v", "libx264",  # Re-encode video with x264
        "-c:a", "aac",      # Re-encode audio with AAC for compatibility
        "-b:a", "128k",     # Set audio bitrate
        "-ar", "44100",     # Set audio sample rate
        str(output_path)
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

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