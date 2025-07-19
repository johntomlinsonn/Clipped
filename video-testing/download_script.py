import yt_dlp
import os

def extract_transcript_with_timestamps(info, output_path):
    """
    Extract transcript with timestamps from video info and save as .txt
    """
    try:
        title = info.get('title', 'Unknown_Video')
        # Clean title for filename
        clean_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
        transcript_filename = f"{clean_title}_transcript.txt"
        transcript_path = os.path.join(output_path, transcript_filename)
        
        # Try to get subtitles from the info

        automatic_captions = info.get('automatic_captions', {})
        
        # Look for English subtitles first, then auto-generated
        subtitle_data = None
        if 'en' in automatic_captions:
            subtitle_data = automatic_captions['en']
       
        if subtitle_data:
            # Find VTT format subtitles
            vtt_subtitle = None
            for sub in subtitle_data:
                if sub.get('ext') == 'vtt':
                    vtt_subtitle = sub
                    break
            
            if vtt_subtitle and 'url' in vtt_subtitle:
                # Download and parse VTT file
                import urllib.request
                
                try:
                    with urllib.request.urlopen(vtt_subtitle['url']) as response:
                        vtt_content = response.read().decode('utf-8')
                    
                    # Parse VTT and convert to readable transcript
                    transcript_text = parse_vtt_to_transcript(vtt_content)
                    
                    # Save to file
                    with open(transcript_path, 'w', encoding='utf-8') as f:
                        f.write(f"Video Title: {title}\n")
                        f.write(transcript_text)
                    
                    return transcript_path
                    
                except Exception as e:
                    print(f"Error downloading transcript: {str(e)}")
        
        # If no subtitles available, create a placeholder
        with open(transcript_path, 'w', encoding='utf-8') as f:
            f.write(f"Video Title: {title}\n")
            f.write(f"URL: {info.get('webpage_url', 'Unknown')}\n")
            f.write(f"Duration: {info.get('duration', 'Unknown')} seconds\n")
            f.write("=" * 50 + "\n\n")
            f.write("No transcript available for this video.\n")
            f.write("Either subtitles are disabled or not generated for this content.")
        
        return transcript_path
        
    except Exception as e:
        print(f"Error creating transcript file: {str(e)}")
        return None

def parse_vtt_to_transcript(vtt_content):
    """
    Parse VTT subtitle content and convert to readable transcript with timestamps
    """
    lines = vtt_content.split('\n')
    transcript = []
    current_time = ""
    current_text = ""
    
    for line in lines:
        line = line.strip()
        
        # Skip VTT headers and empty lines
        if line.startswith('WEBVTT') or line.startswith('NOTE') or not line:
            continue
        
        # Check if line contains timestamp (format: 00:00:00.000 --> 00:00:00.000)
        if '-->' in line:
            # Save previous entry if exists
            if current_time and current_text:
                transcript.append(f"[{current_time}] {current_text}")
            
            # Extract start time
            current_time = line.split(' --> ')[0]
            current_text = ""
        else:
            # This is subtitle text
            if current_text:
                current_text += " " + line
            else:
                current_text = line
    
    # Add the last entry
    if current_time and current_text:
        transcript.append(f"[{current_time}] {current_text}")
    
    return '\n'.join(transcript)

def download_highest_quality(url, output_path='downloads'):
    """
    Download video in the absolute highest quality available
    """
    
    ydl_opts = {
        # This format string prioritizes:
        # 1. Best video quality available
        # 2. Best audio quality available  
        # 3. Combines them if they're separate streams
        'format': 'bestvideo+bestaudio/best',
        
        # Alternative high-quality formats to try
        'format_selector': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best[ext=mp4]/best',
        
        'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
        'writeinfojson': True,
        # Don't write subtitle files directly - we'll process them programmatically
        'writesubtitles': False,
        'writeautomaticsub': False,
        
        # Merge video and audio into single file if needed
        'merge_output_format': 'mp4',
        
        # Post-processing options
        'postprocessors': [{
            'key': 'FFmpegVideoConvertor',
            'preferedformat': 'mp4',
        }],
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            print(f"Title: {info.get('title', 'Unknown')}")
            print(f"Duration: {info.get('duration', 'Unknown')} seconds")
            
            # Show available formats
            formats = info.get('formats', [])
            if formats:
                best_video = max((f for f in formats if f.get('vcodec') != 'none'), 
                               key=lambda x: (x.get('height', 0), x.get('width', 0)), default=None)
                best_audio = max((f for f in formats if f.get('acodec') != 'none'), 
                               key=lambda x: x.get('abr', 0), default=None)
                
                if best_video:
                    print(f"Best video: {best_video.get('height', 'Unknown')}p @ {best_video.get('fps', 'Unknown')}fps")
                if best_audio:
                    print(f"Best audio: {best_audio.get('abr', 'Unknown')} kbps")
            
            print("\nDownloading in highest quality...")
            ydl.download([url])
            
            # Extract and save transcript with timestamps
            transcript_path = extract_transcript_with_timestamps(info, output_path)
            if transcript_path:
                print(f"Transcript saved to: {transcript_path}")
                
            print("High-quality download completed!")
            
            return info
            
    except Exception as e:
        print(f"Error downloading: {str(e)}")
        return None

# SPECIFIC QUALITY DOWNLOAD - Choose exact resolution
def download_specific_quality(url, height=1080, output_path='downloads'):
    """
    Download video in specific quality (height in pixels) with transcript
    
    Args:
        url: YouTube URL
        height: Video height (e.g., 720, 1080, 1440, 2160 for 4K)
        output_path: Download directory
    """
    
    # Create downloads directory
    os.makedirs(output_path, exist_ok=True)
    
    # Format selection prioritizes the requested height
    format_string = f'bestvideo[height<={height}]+bestaudio/best[height<={height}]'
    
    ydl_opts = {
        'format': format_string,
        'outtmpl': os.path.join(output_path, '%(title)s_%(height)sp.%(ext)s'),
        'writeinfojson': True,
        # Don't write subtitle files directly - we'll process them programmatically
        'writesubtitles': False,
        'writeautomaticsub': False,
        'merge_output_format': 'mp4',
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            print(f"Title: {info.get('title', 'Unknown')}")
            print(f"Requesting: {height}p quality")
            
            ydl.download([url])
            
            # Extract and save transcript with timestamps
            transcript_path = extract_transcript_with_timestamps(info, output_path)
            if transcript_path:
                print(f"Transcript saved to: {transcript_path}")
            
            print(f"Download completed in {height}p!")
            
            return info
            
    except Exception as e:
        print(f"Error downloading: {str(e)}")
        return None

# Test with your URL - try highest quality first
test_url = input("Enter YouTube URL: ").strip()

download_specific_quality(test_url, 1080)