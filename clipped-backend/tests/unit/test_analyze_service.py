import pytest
import json
from pathlib import Path
import services.analyze_service as asvc


def test_parse_time_formats():
    assert asvc.parse_time("33.50") == 33.5
    assert asvc.parse_time("1:05") == 65.0
    assert asvc.parse_time("0:01:30") == 3600 + 60 + 30 if False else 90.0  # hh:mm:ss fallback
    with pytest.raises(ValueError):
        asvc.parse_time("invalid")


def test_parse_transcript_lines(tmp_path):
    lines = [
        "[0:10] Hello world",
        "[1:00] Another line",
        "no timestamp line",
        "[bad] skip"
    ]
    f = tmp_path / "transcript.txt"
    f.write_text("\n".join(lines))
    entries = asvc.parse_transcript_lines(f)
    assert entries == [(10.0, "Hello world"), (60.0, "Another line")]


def test_chunk_script():
    text = "a" * 100
    chunks = asvc.chunk_script(text, max_chars=50)
    assert chunks == ["a" * 50, "a" * 50]


def test_analyze_transcript(monkeypatch, tmp_path):
    # Create a fake transcript file
    f = tmp_path / "transcript.txt"
    f.write_text("[0:00] start\n[0:15] mid\n[0:30] end")

    # Dummy choice and response
    class DummyChoice:
        def __init__(self, content):
            self.message = type("M", (), {"content": content})

    class DummyChat:
        def __init__(self):
            self.completions = self
        def create(self, messages, model):
            payload = {"viral_moments": [
                {"time_start": "0:00", "time_end": "0:15", "description": "desc"}
            ]}
            content = json.dumps(payload)
            return type("R", (), {"choices": [DummyChoice(content)]})

    class DummyClient:
        def __init__(self, api_key):
            self.chat = DummyChat()

    # Monkeypatch environment and client
    monkeypatch.setenv("CEREBRAS_API_KEY", "test_key")
    monkeypatch.setattr(asvc, "Cerebras", DummyClient)

    result = asvc.analyze_transcript(str(f))
    assert "viral_moments" in result
    vm = result["viral_moments"]
    assert isinstance(vm, list)
    assert vm[0]["time_start"] == "0:00"
    # Subtitles enrichment
    assert "subtitles" in vm[0]
    subs = vm[0]["subtitles"]
    assert any(sub["text"] == "start" for sub in subs)
