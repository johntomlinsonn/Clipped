from pydantic import BaseModel
from typing import List


class Moment(BaseModel):
    time_start: str
    time_end: str
    description: str


class AnalyzeRequest(BaseModel):
    transcript: str


class AnalyzeResponse(BaseModel):
    moments: List[Moment]
