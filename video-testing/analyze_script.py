#script to read entire video transcript from subtitles
import os
from pathlib import Path
from dotenv import load_dotenv
from cerebras.cloud.sdk import Cerebras
import json

# Load environment variables from .env
load_dotenv(Path(__file__).parent / '.env')
 
# Path to the transcript file
transcript_path = r"C:\Users\PC\Documents\CS\opus\downloads\Impractical Jokers Funniest Moments Mashup  Part 51_transcript.txt"
try:
    with open(transcript_path, 'r', encoding='utf-8') as f:
        script = f.read()
    print(f"Loaded transcript from: {transcript_path}")
except FileNotFoundError:
    print(f"Transcript file not found: {transcript_path}")
    script = ""
except Exception as e:
    print(f"Error reading transcript: {e}")
    script = ""



client = Cerebras(
    api_key=os.getenv("CEREBRAS_API_KEY"),
)
 
# Define system prompt
system = """
{
  "role": "Expert Script Analyzer with 8+ years of experience identifying viral-worthy moments from YouTube transcripts for TikTok, Instagram Reels, and short-form video platforms.",
  "goal": "Extract self-contained, emotionally resonant, or comedically powerful moments from YouTube video transcripts. Each moment must be a fully-formed scene with a natural arc (beginning → build-up → payoff). Moments must be between 10 and 80 seconds long — longer moments should only be included if they clearly form one unified, engaging scene.",
  "context_dump": "The input is a YouTube video transcript with timestamps and speaker dialogue. The tone varies — often comedic, chaotic, spontaneous, or heartfelt. Your task is to find moments that naturally lend themselves to viral short-form video content. Focus especially on moments with absurd humor, irony, suspense, surprise, or wholesome/inspiring emotional impact.",
  "expected_output_format": {
    "viral_moments": [
      {
        "time_start": "m:ss",
        "time_end": "m:ss",
        "description": "A clear and concise explanation of the moment and why it would go viral — including what makes it funny, shocking, relatable, or emotional."
      }
    ]
  },
  "rules": [
    "✅ Each moment must be between **10 and 80 seconds long**.",
    "✅ The moment must be a **full, self-contained scene**, with a clear beginning, middle, and end. No cutoffs.",
    "✅ Longer moments (>40s) should only be selected if the entire section flows as a cohesive unit and remains engaging throughout.",
    "✅ Always prefer scenes with strong **emotional or visual payoff**, especially those with a narrative, twist, or punchline.",
    "✅ Apply **~2 seconds of padding** before and after the moment when transcript context allows, to improve pacing.",
    "✅ Use **only actual content from the transcript** — no hallucination or inferred events.",
    "✅ Prioritize high-viral potential moments that fit TikTok trends: comedy, awkwardness, chaos, irony, inspiration, emotional appeal, danger, surprise, or sarcasm.",
    "❌ Do NOT extract isolated one-liners. Extract multi-line, scene-based segments.",
    "❌ Do NOT include moments under 10 seconds or over 80 seconds unless 100% justifiable as a tight, continuous viral scene.",
    "❌ Do NOT hallucinate, assume visual content, or include anything not clearly supported by the transcript."
  ],
  "best_practices_notes": [
    "🎯 Think like a TikTok editor. Would this clip stop the scroll, keep attention, and deliver a clear payoff?",
    "🧠 Use Chain-of-Thought (CoT): (1) Read transcript; (2) Identify potential scene with natural arc; (3) Check length (10–80s); (4) Add ~2s context buffer; (5) Describe clearly; (6) Format as JSON.",
    "🎬 Clip-worthy traits include: prank escalation, argument/confusion with payoff, danger/rescue scenes, sincere monologues, absurd plans, unexpected turns, or high-stakes chaos.",
    "✂️ Don't trim off beginnings or endings early just to fit a time limit — completeness is more important than brevity."
  ],
  "few_shot_examples": [
    {
      "input_prompt": "Find full viral moments in a YouTube prank video with sarcasm, alligators, and awkwardness.",
      "expected_output": {
        "viral_moments": [
          {
            "time_start": "0:35",
            "time_end": "1:30",
            "description": "A guy steals a bike and insists it's his while the real owner hilariously argues in disbelief. The whole scene is structured like a slow-burning prank with deadpan humor and escalation."
          },
          {
            "time_start": "2:42",
            "time_end": "3:19",
            "description": "One friend lays down covered in fish to bait gators while others watch nervously. The absurdity and danger build up until gators actually start approaching."
          },
          {
            "time_start": "10:11",
            "time_end": "10:24",
            "description": "A sarcastic rant about how hard it is to ignore girls — a self-deprecating monologue with ironic confidence that fits TikTok humor perfectly."
          },
          {
            "time_start": "4:01",
            "time_end": "5:10",
            "description": "Kole drags the team through gator-infested waters while visibly panicking, delivering funny dialogue and commentary. It’s a chaotic, extended scene full of suspense and absurdity that earns its longer duration."
          }
        ]
      }
    }
  ],
  "optimized_prompt": "System: You are a top-tier script analyst and viral content editor. <thought>Step 1: Parse transcript. Step 2: Identify segments with a clear arc. Step 3: Ensure 10–80 second duration. Step 4: Add 2 seconds of padding before/after when context allows. Step 5: Describe the moment and return it in clean JSON.</thought> Your task is to extract only moments with real viral potential — no hallucination, no fragments. Prioritize clarity, pacing, emotional engagement, and clean output."
}
"""

# Function to split transcript into manageable chunks
def chunk_script(text, max_chars=8000):
    return [text[i:i+max_chars] for i in range(0, len(text), max_chars)]

# Prepare to collect viral moments
all_moments = []
chunks = chunk_script(script)
print(f"Processing {len(chunks)} transcript chunk(s)...")
for idx, chunk in enumerate(chunks, start=1):
    print(f"--- Chunk {idx}/{len(chunks)} ---")
    response = client.chat.completions.create(
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": "script: " + chunk}
        ],
        model="qwen-3-32b",
    )
    # Extract and parse JSON from response
    try:
        # Access first choice message content
        content = response.choices[0].message.content
    except Exception as e:
        print(f"Error reading response content for chunk {idx}: {e}")
        continue
    # Clean up response content to extract JSON object
    json_str = content.strip()
    # Remove markdown fences if present
    if json_str.startswith("```json"):
        # Strip leading ```json and trailing ```
        parts = json_str.split('```')
        if len(parts) >= 2:
            json_str = parts[1]
    # Extract substring between first { and last }
    start_idx = json_str.find('{')
    end_idx = json_str.rfind('}')
    if start_idx != -1 and end_idx != -1:
        json_str = json_str[start_idx:end_idx+1]
    try:
        result = json.loads(json_str)
        all_moments.extend(result.get("viral_moments", []))
    except Exception as e:
        print(f"Warning: failed to parse JSON for chunk {idx}: {e}")
        print("Response content was:")
        print(content)

# Pretty-print aggregated viral moments


for moment in all_moments:
    start = moment.get("time_start")
    end = moment.get("time_end")
    desc = moment.get("description")
    print(f"[{start} - {end}] {desc}")