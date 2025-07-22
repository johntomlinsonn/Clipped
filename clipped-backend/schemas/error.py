from pydantic import BaseModel
from typing import Optional


class ErrorResponse(BaseModel):
    """
    Standard error response schema for all endpoints.
    """
    status_code: int
    error: str
    details: Optional[str] = None
