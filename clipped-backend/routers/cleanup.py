from fastapi import APIRouter, Query
from schemas.cleanup import CleanupResponse
from services.cleanup_service import cleanup

router = APIRouter()

@router.post("/", response_model=CleanupResponse)
async def cleanup_endpoint(remove_clips: bool = Query(True, description="Remove all clips after processing")):
    cleanup(include_clips=remove_clips)
    return CleanupResponse(message="Cleanup complete")
