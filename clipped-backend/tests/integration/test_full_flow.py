import pytest
from pathlib import Path
from fastapi.testclient import TestClient
import services.download_service as ds
import services.transcribe_service as ts
import services.clip_service as cs
import routers.clip as clip_router
import services.cleanup_service as cul
from app import app

client = TestClient(app)

class DummyYDL:
    def __init__(self, opts): self.opts = opts
    def __enter__(self): return self
    def __exit__(self, *args): return False
    def extract_info(self, url, download=False): return {'title': 'video', 'ext': 'mp4'}
    def download(self, urls):
        outtmpl = self.opts['outtmpl']
        filename = outtmpl.replace('%(title)s','video').replace('%(ext)s','mp4')
        Path(filename).write_bytes(b'data')

class DummyAudioClip:
    def __init__(self,path): pass
    def write_audiofile(self,path): Path(path).write_text('audio')
    def close(self): pass

class DummySegment:
    def __init__(self,start,text): self.start=start; self.text=text

class DummyModel:
    def __init__(self,*args,**kwargs): pass
    def transcribe(self,audio_path): return [DummySegment(0.0,'hello')], None

class DummySubclip:
    def __init__(self,fps): self.fps=fps
    def write_videofile(self,path,**kwargs): Path(path).write_bytes(b'v')
    def close(self): pass

class DummyVideo:
    def __init__(self,path): self.fps=24
    def subclip(self,s,e): return DummySubclip(self.fps)
    def close(self): pass


@pytest.fixture(autouse=True)
def setup(monkeypatch, tmp_path):
    storage = tmp_path / 'storage'
    storage.mkdir()
    # ensure download dir exists for DummyYDL
    (storage / 'downloads').mkdir(parents=True, exist_ok=True)
    # patch storage dirs
    monkeypatch.setattr(cul.settings, 'storage_dir', storage)
    monkeypatch.setattr(cs.settings, 'storage_dir', storage)
    monkeypatch.setattr(ts.settings, 'storage_dir', storage)
    monkeypatch.setattr(ds, 'DOWNLOADS_DIR', storage / 'downloads')
    # patch external dependencies
    monkeypatch.setattr(ds.yt_dlp, 'YoutubeDL', DummyYDL)
    monkeypatch.setattr(ts, 'AudioFileClip', DummyAudioClip)
    monkeypatch.setattr(ts, 'WhisperModel', DummyModel)
    monkeypatch.setattr(cs, 'VideoFileClip', DummyVideo)
    monkeypatch.setattr(clip_router, 'clip_moments', lambda video_path, moments: [])
    yield


def test_full_flow(tmp_path):
    # 1. Download
    r1 = client.post('/download', json={'url': 'https://youtu.be/qfXkwvJ2uZI?si=X9cWYUdjYra1y3_N'})
    assert r1.status_code == 200
    video_path = Path(r1.json()['video_path'])
    assert video_path.exists()

    # 2. Transcribe
    r2 = client.post('/transcribe', json={'video_path': str(video_path), 'url': 'https://youtu.be/qfXkwvJ2uZI?si=X9cWYUdjYra1y3_N'})
    assert r2.status_code == 200
    transcript_path = Path(r2.json()['transcript_path'])
    assert transcript_path.exists()

    # 3. Clip
    moments = [{"time_start": "0:00", "time_end": "0:02", "description": "Test desc"}]
    r3 = client.post('/clip', json={'video_path': str(video_path), 'moments': moments})
    assert r3.status_code == 200
    clips = r3.json().get('clip_paths', [])
    assert isinstance(clips, list)

    # 4. Cleanup
    r4 = client.post('/cleanup?include_clips=true')
    assert r4.status_code == 200
    # verify all subdirs are empty
    for sub in ['audio','downloads','transcripts','clips']:
        dir_path = tmp_path/'storage'/sub
        if dir_path.exists():
            assert list(dir_path.iterdir()) == []
