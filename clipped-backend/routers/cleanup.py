# (empty file)
from fastapi import APIRouter
from schemas.cleanup import CleanupResponse
from services.cleanup_service import cleanup

router = APIRouter()

@router.post("/", response_model=CleanupResponse)
async def cleanup_endpoint():
    cleanup()
    return CleanupResponse(message="Cleanup complete")
