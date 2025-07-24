import os
import json
from pathlib import Path
from dotenv import load_dotenv
from cerebras.cloud.sdk import Cerebras

# Load environment variables
ROOT_DIR = Path(__file__).parent.parent
load_dotenv(ROOT_DIR / '.env')

# System prompt for viral moment extraction
SYSTEM_PROMPT = r"""
{
  "role": "Expert Comedic Video Analyst specializing in reality TV and improv-based humor. Over a decade of experience dissecting viral-worthy clips from Impractical Jokers-style content.",
  "goal": "Analyze mashup-style YouTube videos containing segments from Impractical Jokers. Your task is to extract full, standalone comedic segments that are strong enough to go viral on platforms like TikTok or YouTube Shorts. Only make cuts at natural segment boundaries where a full moment exists. Never cut mid-segment. Include cuts only when absolutely necessary and only if the resulting moment is clearly viral-worthy.",
  "context_dump": "Input is a transcript from a YouTube mashup video made up of several Impractical Jokers moments. Each segment has already been trimmed by an editor, but may still include multiple moments. Your job is to refine this into stronger short-form moments by further cutting only at clear scene transitions — **never mid-joke, prank, or narrative**.",
  "expected_output_format": {
    "viral_moments": [
      {
        "time_start": "m:ss",
        "time_end": "m:ss",
        "description": "Why this segment is funny and would work well on TikTok or Reels. Include details like payoff, escalation, awkwardness, character reactions, or ironic setup."
      }
    ]
  },
  "rules": [
    "✅ Each clip must be **at least 15 seconds long**, ideally 15–80 seconds.",
    "✅ Only create a new cut if there is a **natural break** — such as the end of a prank, the conclusion of a joke, or a hard transition in tone or setting.",
    "✅ Each extracted moment must feel **complete** — with a setup, escalation, and payoff (or full awkward beat).",
    "✅ Prioritize clips where one or more Jokers are clearly the focus of the joke, being punished, embarrassed, or reacting hilariously.",
    "✅ Use ~2 seconds of padding before and after when possible to allow context or enhance pacing.",
    "✅ Do NOT hallucinate or guess — only use what’s directly visible in the transcript.",
    "✅ ensure all moments are within the clear start and end times of the original video.",
    "❌ Do NOT cut mid-scene, mid-joke, or in a way that removes the payoff.",
    "❌ Do NOT extract scenes that are purely filler, setup-only, or dialogue without visual payoff unless it builds to an emotional or comedic hit.",
    "❌ Do NOT output moments under 15 seconds."
  ],
  "best_practices_notes": [
    "🎯 Treat each mashup video like a buffet — select only the most viral-worthy **full bites**. If a moment feels like a half-bite (cutoff or no payoff), discard or extend it.",
    "🎬 Strong segments often include: Joker getting caught, being awkward in public, being forced to say embarrassing lines, failing a challenge, or getting punished.",
    "🧠 Use Chain-of-Thought (CoT): (1) Parse full transcript; (2) Look for clear start & end of a scene; (3) Check if clip is funny on its own; (4) Add buffer if needed; (5) Format as JSON.",
    "📱 Ask yourself: Would this moment stop someone’s scroll on TikTok or Reels and get them to laugh or watch to the end?",
    "✂️ Fewer cuts are better — only trim when the viral value of the clip justifies it."
  ],
  "few_shot_examples": [
    {
      "input_prompt": "Mashup video of 6 Impractical Jokers pranks involving punishments, mall dares, and weird interviews. Identify viral clips.",
      "expected_output": {
        "viral_moments": [
          {
            "time_start": "1:14",
            "time_end": "1:42",
            "description": "Sal is forced to tell a stranger they smell like soup. The awkwardness, the stranger’s confused reaction, and Sal breaking into laughter make it a perfect self-contained joke with setup and payoff."
          },
          {
            "time_start": "3:05",
            "time_end": "3:50",
            "description": "Joe pretends to be a mall security guard and yells at an old man for 'too much swagger.' The absurd premise and the old man's deadpan reaction make this a viral moment."
          },
          {
            "time_start": "5:20",
            "time_end": "5:58",
            "description": "Q fails at a grocery store dare and runs away mid-sentence. His retreat and the Joker commentary make this moment chaotic and viral-worthy."
          }
        ]
      }
    }
  ],
  "optimized_prompt": "System: You are a comedic segment extractor working with mashup Impractical Jokers videos. Your task is to find only full segments (15–80 seconds) that stand on their own as short-form content. Only cut between full segments, and only if it makes for a better viral moment. Never interrupt a setup or payoff. Use chain-of-thought: (1) read transcript, (2) identify start of funny moment, (3) verify arc is complete, (4) format clean JSON output."
}
"""

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


def analyze_transcript(transcript_path):
    """Analyze a transcript file and output a JSON of viral moments."""
    transcript_path = Path(transcript_path)
    text = transcript_path.read_text(encoding='utf-8')
    
    client = Cerebras(api_key=os.getenv('CEREBRAS_API_KEY'))
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
    # Return moments data as dict
    return {'viral_moments': all_moments}
