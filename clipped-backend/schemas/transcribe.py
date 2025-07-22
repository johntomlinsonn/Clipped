from pydantic import BaseModel, HttpUrl

class TranscribeRequest(BaseModel):
    video_path: str
    url: HttpUrl 

class TranscribeResponse(BaseModel):
    transcript_path: str
