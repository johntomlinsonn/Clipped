import pytest
from pathlib import Path
from fastapi.testclient import TestClient
import services.download_service as ds
import services.transcribe_service as ts
import services.clip_service as cs
import routers.clip as clip_router
import services.cleanup_service as cul
from app import app
from tests.utils import DummyYDL, DummyAudioClip, DummySegment, DummyModel, DummySubclip, DummyVideo
import config
import importlib

client = TestClient(app)



@pytest.fixture(autouse=True)
def setup(monkeypatch, tmp_path):
    storage = tmp_path / 'storage'
    storage.mkdir()
    # ensure download dir exists for DummyYDL
    (storage / 'downloads').mkdir(parents=True, exist_ok=True)
    # patch storage dirs

    monkeypatch.setattr(config.settings, 'storage_dir', storage)
    monkeypatch.setattr(cul.settings, 'storage_dir', storage)
    monkeypatch.setattr(cs.settings, 'storage_dir', storage)

    monkeypatch.setattr('services.transcribe_service.WhisperModel', DummyModel)
    importlib.reload(ts)
    monkeypatch.setattr(ds, 'DOWNLOADS_DIR', storage / 'downloads')
    # patch external dependencies
    monkeypatch.setattr(ds.yt_dlp, 'YoutubeDL', DummyYDL)
    monkeypatch.setattr(ts, 'AudioFileClip', DummyAudioClip)
    # ensure preload event is set and model is DummyModel
    ts._model = DummyModel()
    ts._model_loaded_event.set()
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
