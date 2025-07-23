from config import settings
import shutil

def cleanup(include_clips: bool = False):
    """
    Remove files in the storage directory.
    If include_clips is False, cleans 'audio', 'downloads', and 'transcripts' subdirectories.
    If include_clips is True, also cleans 'clips' directory.
    """
    storage_dir = settings.storage_dir
    # Define subdirectories to clean
    subdirs = ["audio", "downloads", "transcripts"]
    if include_clips:
        subdirs.append("clips")
    for subdir in subdirs:
        target_dir = storage_dir / subdir
        if target_dir.exists() and target_dir.is_dir():
            try:
                # Remove and recreate directory to clear all contents
                shutil.rmtree(target_dir)
                target_dir.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                print(f"Failed to clean {target_dir}: {e}")