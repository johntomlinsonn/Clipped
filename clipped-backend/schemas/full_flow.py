from pydantic import BaseModel, HttpUrl
from typing import List

class FullFlowRequest(BaseModel):
    url: HttpUrl

class FullFlowResponse(BaseModel):
    clip_paths: List[str]
