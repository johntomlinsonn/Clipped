import argparse
from pathlib import Path

from download_vid import download
from create_transcript import create_transcript
from vid_scripts.analyze_script import analyze
from clip_moments import clip_moments
from cleanup import cleanup


def main():
    parser = argparse.ArgumentParser(description="Full video clipping flow")
    parser.add_argument('url', help='YouTube video URL to process')
    args = parser.parse_args()

    # Step 1: Download video
    video_path, _ = download(args.url)
    print(f"Downloaded video to {video_path}")

    # Step 2: Create transcript using Whisper
    transcript_path = create_transcript(video_path, args.url)
    print(f"Generated transcript at {transcript_path}")

    # Step 3: Analyze transcript with AI to JSON
    json_path = analyze(transcript_path)
    print(f"Analysis saved to {json_path}")

    # Step 4: Clip video based on JSON
    clip_moments(video_path, json_path)
    print("Clipping completed.")
    cleanup()


if __name__ == '__main__':
    main()