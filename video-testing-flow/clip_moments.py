import json
from pathlib import Path
import math
import subprocess

# Video clip dependency
try:
    from moviepy.video.io.VideoFileClip import VideoFileClip
except ImportError:
    print("Missing dependency: moviepy. Install with 'pip install moviepy'.")
    exit(1)


def parse_time(ts):
    parts = ts.strip().split(':')
    if len(parts) == 2:
        return int(parts[0]) * 60 + float(parts[1])
    elif len(parts) == 3:
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
    else:
        raise ValueError(f"Invalid time format: {ts}")


def clip_moments(video_path, json_path):
    """Create video subclips based on moments JSON, with subtitles."""
    base = Path(__file__).parent
    # Load moments
    data = json.loads(Path(json_path).read_text(encoding='utf-8'))
    moments = data.get('viral_moments', [])
    if not moments:
        print(f"No moments found in {json_path}")
        return

    # Prepare output directory
    clips_dir = base / 'clip-moments'
    clips_dir.mkdir(exist_ok=True)

    # Load full video
    video = VideoFileClip(str(video_path))

    # Process each moment
    for idx, moment in enumerate(moments, start=1):
        start = parse_time(moment['time_start'])
        end = parse_time(moment['time_end'])
        desc = moment.get('description', '')
        safe_desc = "".join(c for c in desc if c.isalnum() or c in (' ', '_')).rstrip().replace(' ', '_')[:50]
        clip_name = f"clip_{idx}_{int(start)}_{int(end)}_{safe_desc}.mp4"
        clip_path = clips_dir / clip_name
        print(f"Creating clip {idx}: {start}s to {end}s -> {clip_path}")

        # Extract subclip and write without subtitles
        try:
            subclip = video.subclip(start, end)
        except AttributeError:
            subclip = video.subclipped(start, end)
        subclip.write_videofile(str(clip_path), codec='libx264', audio_codec='aac', fps=video.fps)

    print("All clips created in:", clips_dir)
