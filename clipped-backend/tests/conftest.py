import pytest
from fastapi.testclient import TestClient
from config import settings
from pathlib import Path
import shutil

@pytest.fixture
def tmp_storage(tmp_path, monkeypatch):
    """
    Override the storage directory to use a temporary path for tests.
    """
    # Monkey-patch settings.storage_dir to temporary path
    monkeypatch.setattr(settings, "storage_dir", tmp_path)
    # Create expected subdirectories
    (tmp_path / "audio").mkdir()
    (tmp_path / "clips").mkdir()
    (tmp_path / "transcripts").mkdir()
    return tmp_path

@pytest.fixture
def client(tmp_storage):
    """
    TestClient fixture for FastAPI app, using temporary storage directory.
    """
    from app import app
    return TestClient(app)

@pytest.fixture
def sample_video(tmp_path):
    """
    Provide a sample video file for testing by copying the real test file from test-files/sample.mp4.
    """
    # Determine repository root (two levels above tests dir)
    repo_root = Path(__file__).resolve().parents[2]
    test_file = repo_root / "test-files" / "sample.mp4"
    if test_file.exists():
        dest = tmp_path / test_file.name
        shutil.copy(test_file, dest)
        return dest
    # Fallback: create a minimal dummy file
    video_file = tmp_path / "sample.mp4"
    video_file.write_bytes(b"dummy video content")
    return video_file
