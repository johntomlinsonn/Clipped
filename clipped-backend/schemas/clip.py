from pydantic import BaseModel
from typing import List

class ClipRequest(BaseModel):
    video_path: str
    json_path: str  

class ClipResponse(BaseModel):
    clip_paths: List[str]
