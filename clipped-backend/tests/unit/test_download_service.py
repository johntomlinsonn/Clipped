import pytest
from pathlib import Path
import services.download_service as ds

class DummyYDL:
    def __init__(self, opts):
        self.opts = opts
    def __enter__(self):
        return self
    def __exit__(self, *args):
        return False
    def extract_info(self, url, download=False):
        return {'title': 'testvideo', 'ext': 'mp4'}
    def download(self, urls):
        # simulate creation of downloaded file
        outtmpl = self.opts['outtmpl']
        filename = outtmpl.replace('%(title)s', 'testvideo').replace('%(ext)s', 'mp4')
        Path(filename).write_bytes(b'fake content')

def test_download_success(tmp_path, monkeypatch):
    # Prepare a temporary downloads directory
    tmp_downloads = tmp_path / 'downloads'
    tmp_downloads.mkdir()
    monkeypatch.setattr(ds, 'DOWNLOADS_DIR', tmp_downloads)
    # Patch YoutubeDL to our dummy implementation
    monkeypatch.setattr(ds.yt_dlp, 'YoutubeDL', DummyYDL)
    url = 'http://example.com/video'
    video_path = ds.download(url)
    assert video_path == tmp_downloads / 'testvideo.mp4'
    assert (tmp_downloads / 'testvideo.mp4').exists()

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
