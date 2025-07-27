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
DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)
CACHE_DIR.mkdir(parents=True, exist_ok=True)

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

def download(url):
    """Download a YouTube video with optimizations for speed."""
    # Check cache first
    cached_video = _get_cached_video(url)
    if cached_video:
        return cached_video
    
    # Optimized yt-dlp options for speed
    ydl_opts = {
        # Quality optimization: prefer 720p, mp4 format
        'format': (
            'best[height<=720][ext=mp4]/best[height<=720][ext=webm]/'
            'best[ext=mp4]/best[ext=webm]/'
            'best[height<=1080]/best'
        ),
        'outtmpl': str(DOWNLOADS_DIR / '%(title).200s.%(ext)s'),  # Limit title length and sanitize
        'writesubtitles': False,
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
            
            # Cache the video for future use
            try:
                cached_path = _cache_video(video_path, url)
                return cached_path
            except Exception as cache_error:
                logging.warning(f"Caching failed, returning original path: {cache_error}")
                return video_path
        else:
            logging.error("No video file found after download")
            return None
            
    except Exception as e:
        logging.error(f"Download failed: {str(e)}")
        return None

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