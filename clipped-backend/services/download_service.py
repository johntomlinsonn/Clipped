import os
import urllib.request
from pathlib import Path
import yt_dlp
import hashlib
import logging
from config import settings

# Downloads directory (unified)
DOWNLOADS_DIR = settings.storage_dir / 'downloads'
CACHE_DIR = DOWNLOADS_DIR / 'cache'
TRANSCRIPTS_DIR = settings.storage_dir / 'transcripts'
DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)
CACHE_DIR.mkdir(parents=True, exist_ok=True)
TRANSCRIPTS_DIR.mkdir(parents=True, exist_ok=True)

def _get_url_hash(url: str) -> str:
    """Generate a hash for the URL to use as cache key."""
    return hashlib.md5(url.encode()).hexdigest()

def _get_cached_video(url: str) -> Path | None:
    """Check if video is already cached."""
    url_hash = _get_url_hash(url)
    cached_files = list(CACHE_DIR.glob(f"{url_hash}.*"))
    if cached_files:
        cached_file = cached_files[0]
        if cached_file.exists() and cached_file.stat().st_size > 0:
            logging.info(f"Found cached video: {cached_file}")
            return cached_file
    return None

def _cache_video(video_path: Path, url: str) -> Path:
    """Cache the downloaded video with URL hash."""
    url_hash = _get_url_hash(url)
    cached_path = CACHE_DIR / f"{url_hash}{video_path.suffix}"
    
    # Move video to cache directory
    if video_path.exists():
        try:
            # Use shutil.move for better cross-platform compatibility
            import shutil
            shutil.move(str(video_path), str(cached_path))
            logging.info(f"Cached video: {cached_path}")
            return cached_path
        except Exception as e:
            logging.warning(f"Failed to cache video, using original path: {str(e)}")
            # If caching fails, return the original path
            return video_path
    return video_path

def _get_transcript_path(url: str) -> Path:
    """Get the expected transcript file path for a URL."""
    url_hash = _get_url_hash(url)
    return TRANSCRIPTS_DIR / f"{url_hash}_transcript.txt"

def _check_cached_transcript(url: str) -> bool:
    """Check if transcript is already cached."""
    transcript_path = _get_transcript_path(url)
    if transcript_path.exists() and transcript_path.stat().st_size > 0:
        logging.info(f"Found cached transcript: {transcript_path}")
        return True
    return False

def download_transcript(url: str, video_info: dict) -> bool:
    """Attempt to download YouTube transcript/subtitles."""
    transcript_path = _get_transcript_path(url)
    
    # Check if already exists
    if transcript_path.exists():
        logging.info("Transcript already exists, skipping download")
        return True
    
    # Configure yt-dlp for transcript only
    ydl_opts = {
        'writesubtitles': True,
        'writeautomaticsub': True,
        'subtitleslangs': ['en', 'en-US', 'en-GB'],
        'subtitlesformat': 'best',
        'skip_download': True,  # Only download subtitles
        'outtmpl': str(TRANSCRIPTS_DIR / f"{_get_url_hash(url)}_%(title)s.%(ext)s"),
        'restrictfilenames': True,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            logging.info("Attempting to download transcript...")
            ydl.download([url])
            
        # Find downloaded subtitle files
        url_hash = _get_url_hash(url)
        subtitle_files = (
            list(TRANSCRIPTS_DIR.glob(f"{url_hash}_*.vtt")) +
            list(TRANSCRIPTS_DIR.glob(f"{url_hash}_*.srt")) +
            list(TRANSCRIPTS_DIR.glob(f"{url_hash}_*.ttml"))
        )
        
        if subtitle_files:
            # Convert the first found subtitle to plain text
            subtitle_file = subtitle_files[0]
            _convert_subtitle_to_text(subtitle_file, transcript_path)
            
            # Clean up subtitle file
            subtitle_file.unlink()
            
            logging.info(f"Transcript downloaded and converted: {transcript_path}")
            return True
        else:
            logging.info("No transcript/subtitles available for this video")
            return False
            
    except Exception as e:
        logging.warning(f"Failed to download transcript: {str(e)}")
        return False

def _convert_subtitle_to_text(subtitle_file: Path, output_path: Path) -> None:
    """Convert subtitle file (VTT/SRT) to JSON format matching transcribe_service."""
    try:
        with open(subtitle_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse subtitle file and extract timed segments
        segments = []
        lines = content.split('\n')
        current_segment = {}
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Skip format headers
            if line.startswith('WEBVTT') or line.startswith('NOTE'):
                continue
                
            # Check for timestamp line
            if '-->' in line:
                # Parse timestamps (format: 00:00:00.000 --> 00:00:00.000)
                try:
                    start_str, end_str = line.split(' --> ')
                    start_time = _parse_timestamp_to_seconds(start_str)
                    end_time = _parse_timestamp_to_seconds(end_str)
                    current_segment = {
                        'start': start_time,
                        'end': end_time,
                        'text': ''
                    }
                except Exception:
                    continue
                    
            # Skip numeric sequence identifiers
            elif line.isdigit():
                continue
                
            # Skip HTML/formatting tags
            elif line.startswith('<') and line.endswith('>'):
                continue
                
            # This should be subtitle text
            else:
                if current_segment and 'start' in current_segment:
                    # Append text to current segment
                    if current_segment['text']:
                        current_segment['text'] += ' ' + line
                    else:
                        current_segment['text'] = line
                    
                    # If we have a complete segment, add it
                    if current_segment['text'] and 'end' in current_segment:
                        # Clean up the text
                        current_segment['text'] = current_segment['text'].strip()
                        if current_segment['text']:  # Only add non-empty segments
                            segments.append(current_segment.copy())
                        current_segment = {}
        
        # Write in the same format as transcribe_service
        _write_transcript_json(output_path, segments)
            
    except Exception as e:
        logging.error(f"Failed to convert subtitle to JSON: {str(e)}")
        raise

def _parse_timestamp_to_seconds(timestamp_str: str) -> float:
    """Convert timestamp string (HH:MM:SS.mmm or MM:SS.mmm) to seconds."""
    try:
        # Remove any extra formatting
        timestamp_str = timestamp_str.strip()
        
        # Handle different timestamp formats
        if timestamp_str.count(':') == 2:
            # HH:MM:SS.mmm format
            hours, minutes, seconds = timestamp_str.split(':')
            total_seconds = float(hours) * 3600 + float(minutes) * 60 + float(seconds)
        elif timestamp_str.count(':') == 1:
            # MM:SS.mmm format
            minutes, seconds = timestamp_str.split(':')
            total_seconds = float(minutes) * 60 + float(seconds)
        else:
            # Just seconds
            total_seconds = float(timestamp_str)
            
        return total_seconds
    except Exception:
        return 0.0

def _write_transcript_json(transcript_path: Path, segments: list) -> None:
    """Write transcript in the same JSON format as transcribe_service."""
    # Get video name from path for header
    video_name = transcript_path.stem.replace('_transcript', '')
    
    lines = [
        f"Video: {video_name}\n",
        f"URL: [Downloaded Transcript]\n",
        f"NOTE: This transcript was downloaded from YouTube. Each line typically represents ~5 seconds of content. Be aware that moments may end abruptly between transcript segments.\n\n",
        "{\n"
    ]
    
    # Write segments in the same format as transcribe_service
    for segment in segments:
        start = segment.get('start', 0.0)
        text = segment.get('text', '').strip().replace('"', "'")
        if text:  # Only write non-empty text
            lines.append(f'  "{start:.2f}": "{text}",\n')
    
    lines.append("}\n")
    
    with open(transcript_path, "w", encoding="utf-8") as f:
        f.writelines(lines)

def get_transcript_path(url: str) -> str | None:
    """Get the path to the transcript file if it exists."""
    transcript_path = _get_transcript_path(url)
    if transcript_path.exists():
        return str(transcript_path)
    return None

def download(url):
    """Download a YouTube video with optimizations for speed."""
    # Check cache first
    cached_video = _get_cached_video(url)
    if cached_video:
        # Check if we also have a cached transcript
        transcript_available = _check_cached_transcript(url)
        return cached_video, transcript_available
    
    # Optimized yt-dlp options for speed
    ydl_opts = {
        # Quality optimization: prefer 720p, mp4 format
        'format': (
            'best[height<=720][ext=mp4]/best[height<=720][ext=webm]/'
            'best[ext=mp4]/best[ext=webm]/'
            'best[height<=1080]/best'
        ),
        'outtmpl': str(DOWNLOADS_DIR / '%(title).200s.%(ext)s'),  # Limit title length and sanitize
        'writesubtitles': False,  # We'll handle transcripts separately
        'writeautomaticsub': False,
        'merge_output_format': 'mp4',
        'restrictfilenames': True,  # Remove special characters from filenames
        
        # Performance optimizations
        'concurrent_fragment_downloads': 4,  # Parallel chunk downloads
        'fragment_retries': 3,
        'retries': 3,
        'geo_bypass': True,  # CDN optimization
        'prefer_ffmpeg': True,
        
        # Network optimizations
        'socket_timeout': 30,
        'http_chunk_size': 10485760,  # 10MB chunks
        
        # Skip unnecessary processing
        'skip_download': False,
        'ignoreerrors': False,
        'no_warnings': False,
        
        # Speed up extraction
        'extract_flat': False,
        'lazy_playlist': True,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Extract info first (fast operation)
            info = ydl.extract_info(url, download=False)
            logging.info(f"Video info extracted: {info.get('title', 'Unknown')} - {info.get('duration', 'Unknown')}s")
            
            # Download the video
            logging.info("Starting optimized download...")
            ydl.download([url])
            
        # Find downloaded video file
        video_files = list(DOWNLOADS_DIR.glob('*.mp4'))
        if not video_files:
            # Try other formats if mp4 not found
            video_files = list(DOWNLOADS_DIR.glob('*.webm')) + list(DOWNLOADS_DIR.glob('*.mkv'))
        
        if video_files:
            # Get the most recently created file (in case multiple exist)
            video_path = max(video_files, key=lambda f: f.stat().st_mtime)
            logging.info(f"Download completed: {video_path}")
            
            # Try to download transcript
            transcript_available = download_transcript(url, info)
            
            # Cache the video for future use
            try:
                cached_path = _cache_video(video_path, url)
                return cached_path, transcript_available
            except Exception as cache_error:
                logging.warning(f"Caching failed, returning original path: {cache_error}")
                return video_path, transcript_available
        else:
            logging.error("No video file found after download")
            return None, False
            
    except Exception as e:
        logging.error(f"Download failed: {str(e)}")
        return None, False

def clear_video_cache() -> bool:
    """Clear all cached videos."""
    try:
        import shutil
        if CACHE_DIR.exists():
            shutil.rmtree(CACHE_DIR)
            CACHE_DIR.mkdir(parents=True, exist_ok=True)
            logging.info("Video cache cleared successfully")
            return True
        return True
    except Exception as e:
        logging.error(f"Failed to clear video cache: {str(e)}")
        return False

def get_cache_size() -> dict:
    """Get information about the video cache."""
    try:
        cache_files = list(CACHE_DIR.glob("*"))
        total_size = sum(f.stat().st_size for f in cache_files if f.is_file())
        
        return {
            "total_files": len(cache_files),
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "cache_directory": str(CACHE_DIR)
        }
    except Exception as e:
        logging.error(f"Failed to get cache size: {str(e)}")
        return {
            "total_files": 0,
            "total_size_bytes": 0,
            "total_size_mb": 0,
            "cache_directory": str(CACHE_DIR),
            "error": str(e)
        }