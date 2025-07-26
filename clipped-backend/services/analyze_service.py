import os
import json
from pathlib import Path
from dotenv import load_dotenv
from cerebras.cloud.sdk import Cerebras

from config import settings
# Environment loaded via config; discard manual load

# Load system prompt from external file
def load_system_prompt() -> str:
    """Load system prompt from external file"""
    prompt_path = Path(__file__).parent.parent / "system-prompt.txt"
    return prompt_path.read_text(encoding='utf-8')

SYSTEM_PROMPT = load_system_prompt()

def parse_time(ts: str) -> float:
    ts_str = ts.strip()
    # If format is plain seconds (e.g., '333.00'), parse directly
    if ':' not in ts_str:
        try:
            return float(ts_str)
        except ValueError:
            raise ValueError(f"Invalid time format: {ts}")
    parts = ts_str.split(':')
    if len(parts) == 2:
        return int(parts[0]) * 60 + float(parts[1])
    elif len(parts) == 3:
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
    else:
        raise ValueError(f"Invalid time format: {ts}")

def parse_transcript_lines(path: Path) -> list[tuple[float, str]]:
    """Read transcript txt and return list of (time_seconds, text)"""
    lines = path.read_text(encoding='utf-8').splitlines()
    entries = []
    for line in lines:
        if line.startswith('[') and ']' in line:
            time_str, text = line[1:].split(']', 1)
            try:
                t = parse_time(time_str)
                entries.append((t, text.strip()))
            except ValueError:
                continue
    return entries


def chunk_script(text, max_chars=8000):
    return [text[i:i+max_chars] for i in range(0, len(text), max_chars)]


def filter_moments_within_bounds(moments: list[dict], video_duration: float) -> list[dict]:
    """
    Ensure all viral moments are within the bounds of the video duration.
    Delete any moment not within bounds in place.
    """
    # Iterate backwards to remove invalid moments
    for i in range(len(moments) - 1, -1, -1):
        moment = moments[i]
        try:
            start = parse_time(moment.get('time_start', '0:00'))
            end = parse_time(moment.get('time_end', '0:00'))
        except ValueError:
            del moments[i]
            continue
        if not (0 <= start < end <= video_duration):
            del moments[i]
    return moments


def analyze_transcript(transcript_path):
    """Analyze a transcript file and output a JSON of viral moments."""
    transcript_path = Path(transcript_path)
    text = transcript_path.read_text(encoding='utf-8')
    
    client = Cerebras(api_key=settings.cerebras_api_key)
    # parse full transcript for subtitles lookup
    raw_transcript = Path(transcript_path)
    transcript_lines = parse_transcript_lines(raw_transcript)
    all_moments = []
    chunks = chunk_script(text)
    for idx, chunk in enumerate(chunks, start=1):
        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": "script: " + chunk}
            ],
            model="qwen-3-32b",
        )
        content = response.choices[0].message.content
        json_str = content.strip()
        if json_str.startswith("```json"):
            parts = json_str.split('```')
            if len(parts) >= 2:
                json_str = parts[1]
        start_idx = json_str.find('{')
        end_idx = json_str.rfind('}')
        if start_idx != -1 and end_idx != -1:
            json_str = json_str[start_idx:end_idx+1]
        try:
            result = json.loads(json_str)
            all_moments.extend(result.get('viral_moments', []))
        except Exception:
            # Skip invalid chunks
            continue

    # Enrich moments with subtitles
    for moment in all_moments:
        start = parse_time(moment.get('time_start', '0:00'))
        end = parse_time(moment.get('time_end',   '0:00'))
        subs = []
        for t, text in transcript_lines:
            if start <= t <= end:
                subs.append({'time': t, 'text': text})
        moment['subtitles'] = subs
    # Filter moments within the actual video duration
    video_duration = sum([parse_time(t[1]) - parse_time(t[0]) for t in zip(transcript_lines[:-1], transcript_lines[1:])])
    #all_moments = filter_moments_within_bounds(all_moments, video_duration)
    # Return moments data as dict
    return {'viral_moments': all_moments}
