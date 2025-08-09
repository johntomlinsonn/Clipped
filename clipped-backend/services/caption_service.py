from pathlib import Path
from services.transcribe_service import create_transcript
import subprocess
import platform
import os
from datetime import timedelta
from config import settings

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
                    segments.append((start_time, text))
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
    Burns TikTok-style captions into a 9:16 video (converts to 9:16 first with blurred background).
    
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
    
    # Normalize path for cross-platform compatibility
    normalized_srt_path = srt_path.replace('\\', '/').replace(':', '\\:')
    font_size = 11
    y_position = int(video_height * 0.1)
    subtitle_style = (
        f"FontName=Arial Bold,FontSize={font_size},PrimaryColour=&H00FFFF&,OutlineColour=&H000000&,BackColour=&H80000000&," \
        f"Outline=2,Shadow=1,Alignment=2,MarginV={y_position},Bold=1"
    )
    # Build filter_complex: create blurred 9:16 background, overlay foreground, then add subtitles
    filter_complex = (
        f"[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,gblur=sigma=80[bg];"  # increased blur
        f"[0:v]scale=1080:1920:force_original_aspect_ratio=decrease[fg];"
        f"[bg][fg]overlay=(W-w)/2:(H-h)/2,subtitles='{normalized_srt_path}':force_style='{subtitle_style}'"
    )
    cmd = [
        'ffmpeg','-y',
        '-i', video_path,
        '-filter_complex', filter_complex,
        '-c:v','libx264','-preset','medium','-crf','23',
        '-c:a','aac','-b:a','128k',
        output_path
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ FFmpeg error occurred while burning captions: {e.stderr}")
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
    return output_path

def generate_captions_parallel(video_paths: list[str], url: str) -> list[str]:
    """
    Process multiple videos in parallel, generating captioned videos for each.
    Returns a list of output paths for captioned videos.
    """
    import concurrent.futures
    from pathlib import Path
    import os
    import logging

    logging.info(f"Starting optimized parallel captioning for {len(video_paths)} videos")
    if not video_paths:
        logging.info("No videos provided; skipping captioning")
        return []

    max_workers = min(len(video_paths), os.cpu_count() or 4)
    logging.info(f"Using {max_workers} workers for parallel captioning")

    output_paths: list[str] = []
    future_to_video = {}

    def _process_single_caption(video_path: str, idx: int) -> str | None:
        output_path = str(Path(video_path).with_name(f"captioned_{Path(video_path).name}"))
        logging.info(f"Processing caption {idx}: video={video_path}")
        try:
            generate_captions(video_path, url, output_path)
            logging.info(f"Saved captioned video {idx} to {output_path}")
            return output_path
        except Exception as e:
            logging.error(f"Error processing caption {idx}: {e}")
            return None

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        for idx, video_path in enumerate(video_paths, start=1):
            future = executor.submit(_process_single_caption, video_path, idx)
            future_to_video[future] = (idx, video_path)

        for future in concurrent.futures.as_completed(future_to_video):
            idx, video_path = future_to_video[future]
            try:
                result = future.result()
                if result:
                    output_paths.append(result)
                    logging.info(f"Successfully processed caption {idx}")
                else:
                    logging.warning(f"Caption {idx} was skipped or failed")
            except Exception as e:
                logging.error(f"Failed to create caption {idx}: {e}")
                continue

    output_paths.sort()
    logging.info(f"Completed all captioning tasks: {len(output_paths)} captioned videos generated")
    return output_paths

def generate_captioned_clips_from_moments(video_path: str, moments: list[dict], transcript_path: str, url: str) -> list[str]:
    """Generate captioned clips directly from the source video using existing transcript.
    Avoids creating intermediate non-captioned video clips. Creates per-moment SRT files
    with shifted timestamps and burns them while cutting the segment in a single ffmpeg pass.
    """
    import logging
    import concurrent.futures
    from tempfile import TemporaryDirectory

    # Parse full transcript once
    transcript_entries = []
    try:
        with open(transcript_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        start_idx = next((i for i, l in enumerate(lines) if l.strip() == '{'), None)
        if start_idx is not None:
            for line in lines[start_idx+1:]:
                if line.strip() == '}':
                    break
                if ':' in line:
                    try:
                        time_part, text_part = line.split(':', 1)
                        ts = float(time_part.strip().strip('"'))
                        text = text_part.strip().strip('",')
                        transcript_entries.append((ts, text))
                    except Exception:
                        continue
    except Exception as e:
        logging.error(f"Failed to parse transcript {transcript_path}: {e}")
        return []

    def parse_time(ts: str) -> float:
        s = ts.strip()
        parts = s.split(':')
        if len(parts) == 1:
            return float(s)
        if len(parts) == 2:
            return int(parts[0]) * 60 + float(parts[1])
        if len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
        raise ValueError(f"Invalid time format: {ts}")

    clips_dir = settings.storage_dir / 'clips'
    clips_dir.mkdir(parents=True, exist_ok=True)
    outputs: list[str] = []

    def build_and_run(moment: dict, idx: int) -> str | None:
        try:
            start = parse_time(moment['time_start'])
            end = parse_time(moment['time_end'])
            if end <= start:
                return None
            duration = end - start
            # Collect transcript lines within range
            segment_lines = [(ts, txt) for (ts, txt) in transcript_entries if start <= ts < end]
            if not segment_lines:
                # Fallback: include closest previous line
                prev = [t for t in transcript_entries if t[0] < start]
                if prev:
                    segment_lines = [prev[-1]]
            # Build SRT with shifted times
            srt_parts = []
            for i, (ts, txt) in enumerate(segment_lines, start=1):
                local_start = ts - start
                local_end = local_start + 1.5
                srt_parts.append(f"{i}\n{seconds_to_srt_time(local_start)} --> {seconds_to_srt_time(local_end)}\n{txt}\n\n")
            # Create output file name
            desc = moment.get('description', '')
            safe_desc = ''.join(c for c in desc if c.isalnum() or c in (' ', '_')).rstrip().replace(' ', '_')[:50]
            output_path = clips_dir / f"captioned_clip_{idx}_{int(start)}_{int(end)}_{safe_desc}.mp4"
            with TemporaryDirectory() as td:
                srt_file = Path(td) / 'segment.srt'
                with open(srt_file, 'w', encoding='utf-8') as sf:
                    sf.writelines(srt_parts)
                normalized_srt = str(srt_file).replace('\\', '/').replace(':', '\\:')
                font_size = 11
                y_position = int(1920 * 0.1)
                subtitle_style = (
                    f"FontName=Arial Bold,FontSize={font_size},PrimaryColour=&H00FFFF&,OutlineColour=&H000000&,BackColour=&H80000000&," \
                    f"Outline=2,Shadow=1,Alignment=2,MarginV={y_position},Bold=1"
                )
                filter_complex = (
                    f"[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,gblur=sigma=80[bg];"  # increased blur
                    f"[0:v]scale=1080:1920:force_original_aspect_ratio=decrease[fg];"
                    f"[bg][fg]overlay=(W-w)/2:(H-h)/2,subtitles='{normalized_srt}':force_style='{subtitle_style}'"
                )
                cmd = [
                    'ffmpeg','-y',
                    '-ss', str(start), '-t', str(duration),
                    '-i', video_path,
                    '-filter_complex', filter_complex,
                    '-c:v','libx264','-preset','medium','-crf','23',
                    '-c:a','aac','-b:a','128k',
                    str(output_path)
                ]
                subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
            return str(output_path)
        except Exception as e:
            logging.error(f"Failed to build captioned clip {idx}: {e}")
            return None

    import logging
    max_workers = min(len(moments), os.cpu_count() or 4)
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(build_and_run, m, i): i for i, m in enumerate(moments, start=1)}
        for fut in concurrent.futures.as_completed(futures):
            res = fut.result()
            if res:
                outputs.append(res)
    outputs.sort()
    return outputs