from pydantic import BaseModel
from typing import List, Optional

class Moment(BaseModel):
    time_start: str
    time_end: str
    description: Optional[str] = None

class ClipRequest(BaseModel):
    video_path: str
    moments: List[Moment]

class ClipResponse(BaseModel):
    clip_paths: List[str]
