from pathlib import Path
from services.transcribe_service import create_transcript
import subprocess
import platform
import os
from datetime import timedelta

def transcribe(video_path: str, url: str) -> Path:
    """
    Calls the transcribe method from transcribe_service.py.
    Returns the path to the transcript file.
    """
    return create_transcript(video_path, url)

def transcription_to_srt(transcript_path: Path, srt_path: Path) -> None:
    """
    Parses the transcript and writes it in SRT format.
    """
    

    segments = []
    with open(transcript_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    # Find the start of the JSON-like segment dictionary
    start_idx = next((i for i, l in enumerate(lines) if l.strip() == "{"), None)
    if start_idx is not None:
        for line in lines[start_idx+1:]:
            if line.strip() == "}":
                break
            # Parse: "  "5.00": "This is the first subtitle"," 
            if ":" in line:
                try:
                    time_part, text_part = line.split(":", 1)
                    start_time = float(time_part.strip().strip('"'))
                    text = text_part.strip().strip('",')
                    # Split long text into smaller chunks (max 6 words per caption)
                    words = text.split()
                    chunk_size = 6
                    for i in range(0, len(words), chunk_size):
                        chunk = ' '.join(words[i:i+chunk_size])
                        # Offset start time for each chunk
                        chunk_start = start_time + (i // chunk_size) * 1.5  # 1.5s per chunk
                        segments.append((chunk_start, chunk))
                except Exception:
                    continue

    # Estimate end times (next start or +1.5s)
    srt_entries = []
    for idx, (start, text) in enumerate(segments):
        end = segments[idx+1][0] if idx+1 < len(segments) else start + 1.5
        srt_entries.append((idx+1, start, end, text))

    with open(srt_path, "w", encoding="utf-8") as f:
        for idx, start, end, text in srt_entries:
            f.write(f"{idx}\n")
            f.write(f"{seconds_to_srt_time(start)} --> {seconds_to_srt_time(end)}\n")
            f.write(f"{text}\n\n")

def burn_captions(video_path: str, srt_path: str,
                  output_path: str, video_width: int,
                  video_height: int) -> None:
    """
    Burns TikTok-style captions into a 9:16 video.
    
    Args:
        video_path: Path to input video file
        srt_path: Path to SRT subtitle file
        output_path: Path for output video file
        video_width: Width of the video in pixels
        video_height: Height of the video in pixels
    
    The captions will be:
    - White text with black outline
    - Arial Bold font
    - Positioned at the top of the screen
    - Sized appropriately for mobile viewing
    """
    
    # Validate input files exist
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")
    
    if not os.path.exists(srt_path):
        raise FileNotFoundError(f"SRT file not found: {srt_path}")
    
    # Calculate font size based on video dimensions (roughly 4% of video height)
    font_size = 11
    
    # Position captions at top (about 10% from top)
    y_position = int(video_height * 0.1)
    
    # Normalize path for cross-platform compatibility
    # Convert backslashes to forward slashes and escape any remaining special characters
    normalized_srt_path = srt_path.replace('\\', '/').replace(':', '\\:')
    
    # Create the subtitle filter for TikTok-style appearance
    subtitle_filter = (
        f"subtitles='{normalized_srt_path}'"
        f":force_style='"
        f"FontName=Arial Bold,"
        f"FontSize={font_size},"
        f"PrimaryColour=&H00FFFF&,"  # Yellow text
        f"OutlineColour=&H000000&,"  # Black outline
        f"BackColour=&H80000000&,"   # Semi-transparent background
        f"Outline=2,"                # Outline thickness
        f"Shadow=1,"                 # Drop shadow
        f"Alignment=2,"              # Top center alignment
        f"MarginV={y_position},"     # Vertical margin from top
        f"Bold=1"                    # Bold font
        f"'"
    )
    
    # Build FFmpeg command
    cmd = [
        'ffmpeg',
        '-i', video_path,
        '-vf', subtitle_filter,
        '-c:a', 'copy',              # Copy audio without re-encoding
        '-c:v', 'libx264',           # Use H.264 for video encoding
        '-preset', 'medium',         # Balance between speed and quality
        '-crf', '23',                # Good quality setting
        '-y',                        # Overwrite output file if it exists
        output_path
    ]
    
    try:
        print(f"Processing video: {video_path}")
        print(f"Adding captions from: {srt_path}")
        print(f"Output will be saved to: {output_path}")
        print(f"Caption settings: {font_size}px Arial Bold, white with black outline")
        
        # Run FFmpeg command
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True
        )
        
        print("✅ Video processing completed successfully!")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ FFmpeg error occurred:")
        print(f"Return code: {e.returncode}")
        print(f"Error output: {e.stderr}")
        raise
    
    except FileNotFoundError:
        print("❌ FFmpeg not found. Please install FFmpeg and ensure it's in your PATH.")
        print("Installation instructions:")
        print("- Windows: Download from https://ffmpeg.org/download.html")
        print("- macOS: brew install ffmpeg")
        print("- Linux: sudo apt install ffmpeg (Ubuntu/Debian)")
        raise

def seconds_to_srt_time(seconds: float) -> str:
    """
    Convert seconds (may include fractions) into 'HH:MM:SS,mmm' format for SRT.
    """
    total = timedelta(seconds=seconds)
    # Format as 'H:MM:SS.sss', then split to get milliseconds
    time_str = str(total)  # e.g. '0:01:23.456789'
    if '.' in time_str:
        hms, frac = time_str.split('.')
        ms = frac[:3].ljust(3, '0')
    else:
        hms, ms = time_str, '000'
    hh, mm, ss = hms.split(':')
    return f"{int(hh):02d}:{int(mm):02d}:{int(ss):02d},{ms}"


def generate_captions(video_path: str, url: str, output_path: str) -> str:
    """
    Full pipeline: transcribe -> parse to SRT -> burn captions.
    Returns the path to the captioned video.
    """
    transcript_path = transcribe(video_path, url)
    srt_path = Path(transcript_path).with_suffix('.srt')
    transcription_to_srt(transcript_path, srt_path)
    burn_captions(video_path, str(srt_path), output_path, video_height=1920, video_width=1080)