from fastapi import APIRouter
from schemas.cleanup import CleanupResponse, CleanupRequest
from services.cleanup_service import cleanup

router = APIRouter()

@router.post("/", response_model=CleanupResponse)
async def cleanup_endpoint(req: CleanupRequest):
    cleanup(include_clips=req.include_clips, video_paths=req.video_paths)
    return CleanupResponse(message="Cleanup complete")
