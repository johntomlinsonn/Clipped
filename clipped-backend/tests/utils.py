from pathlib import Path

class DummyYDL:
    def __init__(self, opts):
        self.opts = opts
    def __enter__(self):
        return self
    def __exit__(self, *args):
        return False
    def extract_info(self, url, download=False):
        return {'title': 'video', 'ext': 'mp4'}
    def download(self, urls):
        outtmpl = self.opts['outtmpl']
        filename = outtmpl.replace('%(title)s','video').replace('%(ext)s','mp4')
        Path(filename).write_bytes(b'data')

class DummyAudioClip:
    def __init__(self, path):
        pass
    def write_audiofile(self, path):
        Path(path).write_text('audio')
    def close(self):
        pass

class DummySegment:
    def __init__(self, start, text):
        self.start = start
        self.text = text

class DummyModel:
    def __init__(self, *args, **kwargs):
        pass
    def transcribe(self, audio_path):
        return [DummySegment(0.0, 'hello')], None

class DummySubclip:
    def __init__(self, fps):
        self.fps = fps
    def write_videofile(self, path, **kwargs):
        Path(path).write_bytes(b'v')
    def close(self):
        pass

class DummyVideo:
    def __init__(self, path):
        self.fps = 24
    def subclip(self, s, e):
        return DummySubclip(self.fps)
    def close(self):
        pass
