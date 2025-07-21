import argparse
from pathlib import Path

from download_vid import download
from vid_scripts.analyze_script import analyze
from clip_moments import clip_moments


def main():
    parser = argparse.ArgumentParser(description="Full video clipping flow")
    parser.add_argument('url', help='YouTube video URL to process')
    args = parser.parse_args()

    # Step 1: Download video and transcript
    video_path, transcript_path = download(args.url)
    print(f"Downloaded video to {video_path}, transcript to {transcript_path}")

    # Step 2: Analyze transcript with AI to JSON
    json_path = analyze(transcript_path)
    print(f"Analysis saved to {json_path}")

    # Step 3: Clip video based on JSON
    clip_moments(video_path, json_path)
    print("Clipping completed.")


if __name__ == '__main__':
    main()