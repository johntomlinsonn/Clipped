from pydantic import BaseModel, HttpUrl

class DownloadRequest(BaseModel):
    url: HttpUrl

class DownloadResponse(BaseModel):
    video_path: str
