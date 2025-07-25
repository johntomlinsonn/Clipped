import pytest
from pathlib import Path
import services.transcribe_service as ts

class DummyAudioClip:
    def __init__(self, path):
        pass
    def write_audiofile(self, path):
        Path(path).write_text('audio data')
    def close(self):
        pass

class DummySegment:
    def __init__(self, start, text):
        self.start = start
        self.text = text

class DummyModel:
    def __init__(self, model_name, device, compute_type, cpu_threads):
        pass
    def transcribe(self, audio_path):
        segments = [DummySegment(0.0, 'hello world'), DummySegment(1.23, 'test segment')]
        return segments, None


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
    assert '"0.00": "hello world"' in content
    assert '"1.23": "test segment"' in content
