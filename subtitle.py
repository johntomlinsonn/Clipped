from faster_whisper import WhisperModel

model = WhisperModel(
    "small", 
    device="cpu", 
    compute_type="int8",  # INT8 quantization for speed
    cpu_threads=4         # Set number of threads as per your CPU cores
)
segments, info = model.transcribe("distil-large-v3", word_timestamps=True)

# Configuration
MAX_CHARS_PER_SEG = 40
MIN_DISPLAY_SEC = 1.5
MAX_DISPLAY_SEC = 6.0
OUTPUT_INTERVAL = 2.0  # create new caption block every ~2 sec

current_block = {"start": None, "end": None, "text": ""}
blocks = []

for seg in segments:
    for w in seg.words:
        if current_block["start"] is None:
            current_block["start"] = w.start
        current_block["end"] = w.end
        current_block["text"] += (w.word + " ")

        # If 2 seconds passed or text is too long, flush block
        if w.end - current_block["start"] >= OUTPUT_INTERVAL \
           or len(current_block["text"]) >= MAX_CHARS_PER_SEG:
            blocks.append(current_block.copy())
            current_block = {"start": None, "end": None, "text": ""}

# Flush final block
if current_block["text"]:
    blocks.append(current_block)

# Output subtitles with timing
for b in blocks:
    # Ensure visible time is reasonable
    display_time = max(MIN_DISPLAY_SEC, min(MAX_DISPLAY_SEC, b["end"] - b["start"]))
    start_ts = b["start"]
    print(f"{int(start_ts//60):02d}:{start_ts%60:05.2f} --> +{display_time:.2f}  {b['text'].strip()}")