from pydantic import BaseModel
from typing import List
from schemas.analyze import Moment

class ClipRequest(BaseModel):
    video_path: str
    moments: List[Moment]

class ClipResponse(BaseModel):
    clip_paths: List[str]
