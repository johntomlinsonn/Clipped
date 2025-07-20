import os
import json
import shutil
from pathlib import Path

try:
    # Prefer the editor interface, which includes subclip()
    from moviepy.editor import VideoFileClip
except ImportError:
    try:
        from moviepy.video.io.VideoFileClip import VideoFileClip
    except ImportError:
        print("Missing dependency: moviepy. Install with 'pip install moviepy'.")
        exit(1)

# Paths
BASE_DIR = Path(__file__).parent
DOWNLOADS_DIR = BASE_DIR / '..' / 'downloads'
MOMENTS_DIR = BASE_DIR / 'moments'
CLIPS_DIR = BASE_DIR / 'clips'

# Ensure clips directory exists
CLIPS_DIR.mkdir(exist_ok=True)

# Find the original video file
# You can change this to a specific filename if needed
video_files = list(DOWNLOADS_DIR.glob('*.mp4'))
if not video_files:
    print(f"No video files found in {DOWNLOADS_DIR}")
    exit(1)
original_video = video_files[0]
print(f"Original video: {original_video}")

# Copy original into clips dir
working_video = CLIPS_DIR / original_video.name
shutil.copy(original_video, working_video)
print(f"Copied video to: {working_video}")

# Load moments JSON
json_files = list(MOMENTS_DIR.glob('*_moments.json'))
if not json_files:
    print(f"No moments JSON found in {MOMENTS_DIR}")
    exit(1)
moments_file = json_files[0]
print(f"Loading moments from: {moments_file}")
with open(moments_file, 'r', encoding='utf-8') as f:
    data = json.load(f)
    moments = data.get('viral_moments', [])

# Load video clip once
video = VideoFileClip(str(working_video))

# Helper to parse m:ss into seconds

def parse_time(ts):
    parts = ts.strip().split(':')
    if len(parts) == 2:
        return int(parts[0]) * 60 + float(parts[1])
    elif len(parts) == 3:
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
    else:
        raise ValueError(f"Invalid time format: {ts}")

# Create each subclip
for idx, moment in enumerate(moments, start=1):
    start = parse_time(moment['time_start'])
    end = parse_time(moment['time_end'])
    desc = moment.get('description', '')
    # Output filename
    safe_desc = "".join(c for c in desc if c.isalnum() or c in (' ', '_')).rstrip().replace(' ', '_')[:50]
    clip_name = f"clip_{idx}_{start:.0f}_{end:.0f}_{safe_desc}.mp4"
    clip_path = CLIPS_DIR / clip_name
    print(f"Creating clip {idx}: {start}s to {end}s -> {clip_path}")
    # Create a subclip; some VideoFileClip objects use `subclipped` method
    try:
        subclip = video.subclip(start, end)
    except AttributeError:
        subclip = video.subclipped(start, end)
    subclip.write_videofile(str(clip_path), codec='libx264', audio_codec='aac')

print("All clips created in:", CLIPS_DIR)
