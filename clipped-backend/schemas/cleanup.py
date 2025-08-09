from pydantic import BaseModel, Field
from typing import List, Optional


class CleanupRequest(BaseModel):
    include_clips: bool = Field(False, description="If True, also wipe entire 'clips' directory after selective deletions")
    video_paths: Optional[List[str]] = Field(None, description="Specific video file paths (within storage dir) to delete")


class CleanupResponse(BaseModel):
    message: str