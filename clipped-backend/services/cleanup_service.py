from config import settings
import shutil
from pathlib import Path
from typing import Iterable, Optional

def cleanup(include_clips: bool = False, video_paths: Optional[Iterable[str]] = None):
    """
    Remove files in the storage directory.

    Args:
        include_clips: If False, cleans 'audio', 'downloads', and 'transcripts' only.
                       If True, also cleans the entire 'clips' directory (after any selective deletions).
        video_paths: Optional iterable of specific clip video file paths to delete (e.g. original clips
                     after captioned versions are generated). Only files that exist and are within the
                     storage directory will be deleted. Does not remove captioned videos unless explicitly listed.
                     If provided (and include_clips is False) ONLY these files will be deleted and no
                     directory-wide cleanup will occur.
    """
    storage_dir = settings.storage_dir

    # 1. Selective deletion of provided video paths (non-destructive to other files)
    if video_paths:
        for vp in video_paths:
            try:
                p = Path(vp)
                # Ensure path is inside the storage directory for safety
                try:
                    p.relative_to(storage_dir)
                except ValueError:
                    # Skip files outside storage directory
                    continue
                if p.exists() and p.is_file():
                    try:
                        p.unlink()
                    except Exception:
                        pass
            except Exception:
                continue
        # If only targeted deletions requested and not a full clips cleanup, stop here
        if not include_clips:
            return

    # 2. Directory cleaning (only when not returning early above)
    subdirs = ["audio", "downloads", "transcripts"]
    if include_clips:
        subdirs.append("clips")

    for subdir in subdirs:
        target_dir = storage_dir / subdir
        if target_dir.exists() and target_dir.is_dir():
            try:
                shutil.rmtree(target_dir)
                target_dir.mkdir(parents=True, exist_ok=True)
            except Exception:
                # Non-fatal; continue cleaning others
                continue