import json
from pathlib import Path
import math
import subprocess
from moviepy.video.io.VideoFileClip import VideoFileClip
from config import settings
import logging


def clip_moments(video_path: str, moments: list[dict]) -> list[str]:
    logging.info(f"Starting clip process for video {video_path} with {len(moments)} moments")
    """Create video subclips based on moments list."""
    # Return early if no moments
    if not moments:
        logging.info("No moments provided; skipping clipping")
        return []

    # Prepare output directory
    clips_dir = settings.storage_dir / 'clips'
    clips_dir.mkdir(parents=True, exist_ok=True)

    # We'll load the full video inside the loop per clip to avoid audio reader exhaustion

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

        # Load the video fresh for each clip
        fullvid = VideoFileClip(str(video_path))
        try:
            subclip = fullvid.subclip(start, end)
        except AttributeError:
            subclip = fullvid.subclipped(start, end)
        # Write clip including audio
        subclip.write_videofile(str(clip_path), codec='libx264', audio_codec='aac', fps=fullvid.fps)
        # Close resources
        try:
            subclip.close()
            fullvid.close()
        except Exception as e:
            logging.warning(f"Error closing clip resources: {e}")
        logging.info(f"Saved clip {idx} to {clip_path}")
        clip_paths.append(str(clip_path))
    logging.info("Completed all clipping tasks")
    return clip_paths

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