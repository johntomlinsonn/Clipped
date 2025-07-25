import pytest
from pathlib import Path
import services.transcribe_service as ts
from tests.utils import DummyAudioClip, DummySegment, DummyModel


def test_create_transcript(monkeypatch, tmp_path):
    # Setup fake storage directory
    storage_dir = tmp_path / 'storage'
    # Monkeypatch storage_dir in settings
    monkeypatch.setattr(ts.settings, 'storage_dir', storage_dir)
    # Create dummy video file
    video_file = tmp_path / 'video.mp4'
    video_file.write_bytes(b'')
    # Patch AudioFileClip and WhisperModel
    monkeypatch.setattr(ts, 'AudioFileClip', DummyAudioClip)
    monkeypatch.setattr(ts, 'WhisperModel', DummyModel)
    url = 'http://example.com/video'
    transcript_path = ts.create_transcript(str(video_file), url)
    # Verify audio file
    audio_path = storage_dir / 'audio' / 'video.mp3'
    assert audio_path.exists()
    # Verify transcript file
    expected_tpath = storage_dir / 'transcripts' / 'video_transcript.txt'
    assert transcript_path == expected_tpath
    assert transcript_path.exists()
    content = transcript_path.read_text(encoding='utf-8')
    # Check headers and segments
    assert 'Video: video.mp4' in content
    assert f'URL: {url}' in content
    assert '"0.00": "hello"' in content
