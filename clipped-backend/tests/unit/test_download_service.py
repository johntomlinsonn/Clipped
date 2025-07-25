import pytest
from pathlib import Path
import services.download_service as ds
from tests.utils import DummyYDL

def test_download_success(tmp_path, monkeypatch):
    # Prepare a temporary downloads directory
    tmp_downloads = tmp_path / 'downloads'
    tmp_downloads.mkdir()
    monkeypatch.setattr(ds, 'DOWNLOADS_DIR', tmp_downloads)
    # Patch YoutubeDL to our dummy implementation
    monkeypatch.setattr(ds.yt_dlp, 'YoutubeDL', DummyYDL)
    url = 'http://example.com/video'
    video_path = ds.download(url)
    assert video_path == tmp_downloads / 'video.mp4'
    assert (tmp_downloads / 'video.mp4').exists()

def test_download_no_file(tmp_path, monkeypatch):
    # Prepare a temporary downloads directory
    tmp_downloads = tmp_path / 'downloads'
    tmp_downloads.mkdir()
    monkeypatch.setattr(ds, 'DOWNLOADS_DIR', tmp_downloads)
    # Use a dummy YDL that creates no file
    class DummyYDLNoFile(DummyYDL):
        def download(self, urls):
            pass
    monkeypatch.setattr(ds.yt_dlp, 'YoutubeDL', DummyYDLNoFile)
    video_path = ds.download('http://example.com/video')
    assert video_path is None
