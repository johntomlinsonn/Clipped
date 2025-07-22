from pydantic import BaseModel

class TranscribeRequest(BaseModel):
    video_path: str

class TranscribeResponse(BaseModel):
    transcript_path: str
