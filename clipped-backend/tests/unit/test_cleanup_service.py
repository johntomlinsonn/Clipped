import pytest
from pathlib import Path
import services.cleanup_service as cs


def create_dirs_and_files(base: Path):
    for name in ["audio", "downloads", "transcripts", "clips"]:
        d = base / name
        d.mkdir(parents=True, exist_ok=True)
        # create a dummy file in each subdir
        (d / f"{name}_file.txt").write_text("dummy")


def test_cleanup_default(tmp_path, monkeypatch):
    # Set up a fake storage directory with files in all subfolders
    tmp_storage = tmp_path / "storage"
    tmp_storage.mkdir()
    create_dirs_and_files(tmp_storage)
    # Monkeypatch the settings.storage_dir
    monkeypatch.setattr(cs.settings, 'storage_dir', tmp_storage)

    # Cleanup without clips
    cs.cleanup()

    # audio, downloads, transcripts should be cleaned (empty)
    for name in ["audio", "downloads", "transcripts"]:
        d = tmp_storage / name
        assert d.exists() and d.is_dir()
        assert list(d.iterdir()) == []

    # clips should remain untouched (still contain the dummy file)
    clips = tmp_storage / "clips"
    assert clips.exists() and any(clips.iterdir())


def test_cleanup_include_clips(tmp_path, monkeypatch):
    # Set up a fake storage directory with files in all subfolders
    tmp_storage = tmp_path / "storage"
    tmp_storage.mkdir()
    create_dirs_and_files(tmp_storage)
    # Monkeypatch the settings.storage_dir
    monkeypatch.setattr(cs.settings, 'storage_dir', tmp_storage)

    # Cleanup including clips
    cs.cleanup(include_clips=True)

    # all subfolders should be cleaned (empty)
    for name in ["audio", "downloads", "transcripts", "clips"]:
        d = tmp_storage / name
        assert d.exists() and d.is_dir()
        assert list(d.iterdir()) == []
