import shutil
from pathlib import Path

def cleanup():
    """
    Remove all downloaded, transcript, and JSON files after clips are created.
    """
    base = Path(__file__).parent

    # Remove downloads directory
    downloads_dir = base / 'downloads'
    if downloads_dir.exists() and downloads_dir.is_dir():
        shutil.rmtree(downloads_dir)

    # Remove transcript text files
    for transcript in base.glob('*_transcript.txt'):
        try:
            transcript.unlink()
        except Exception as e:
            print(f"Failed to delete transcript {transcript}: {e}")

    # Remove audio files (.mp3)
    for audio in base.glob('*.mp3'):
        try:
            audio.unlink()
        except Exception as e:
            print(f"Failed to delete audio file {audio}: {e}")

    # Remove JSON moment files
    moments_dir = base / 'moments'
    if moments_dir.exists() and moments_dir.is_dir():
        for json_file in moments_dir.glob('*.json'):
            try:
                json_file.unlink()
            except Exception as e:
                print(f"Failed to delete JSON file {json_file}: {e}")