from config import settings
import shutil

def cleanup():
    """
    Remove all files in the storage directory.
    """
    storage_dir = settings.storage_dir
    # Delete all contents in storage directory
    if storage_dir.exists() and storage_dir.is_dir():
        for item in storage_dir.iterdir():
            try:
                if item.is_dir():
                    shutil.rmtree(item)
                else:
                    item.unlink()
            except Exception as e:
                print(f"Failed to delete {item}: {e}")