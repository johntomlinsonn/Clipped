import pytest
from pathlib import Path
import services.clip_service as cs

class DummySubclip:
    def __init__(self, fps):
        self.fps = fps
    def write_videofile(self, path, codec, audio_codec, fps):
        Path(path).write_bytes(b'video')
    def close(self):
        pass

class DummyVideo:
    def __init__(self, path):
        self.fps = 24
    def subclip(self, start, end):
        return DummySubclip(self.fps)
    def close(self):
        pass


def test_clip_moments_empty():
    assert cs.clip_moments("any.mp4", []) == []


def test_clip_moments(monkeypatch, tmp_path):
    # Prepare a fake storage dir
    tmp_storage = tmp_path / "storage"
    tmp_storage.mkdir()
    monkeypatch.setattr(cs.settings, 'storage_dir', tmp_storage)
    # Create a dummy video file
    fake_video = tmp_path / "video.mp4"
    fake_video.write_bytes(b'')
    # Mock VideoFileClip
    monkeypatch.setattr(cs, 'VideoFileClip', DummyVideo)
    moments = [{"time_start": "0:00", "time_end": "0:02", "description": "Test desc"}]
    paths = cs.clip_moments(str(fake_video), moments)
    assert len(paths) == 1
    clip_path = Path(paths[0])
    assert clip_path.parent == tmp_storage / 'clips'
    assert clip_path.exists()
    assert 'clip_1_0_2_Test_desc' in clip_path.name
