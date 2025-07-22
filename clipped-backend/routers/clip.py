from fastapi import APIRouter, HTTPException
from schemas.clip import ClipRequest, ClipResponse
from services.clip_service import clip_moments
from config import settings
from pathlib import Path

router = APIRouter()

@router.post("/", response_model=ClipResponse)
async def clip_endpoint(req: ClipRequest):
    try:
        # Generate clips based on the provided JSON
        clip_moments(req.video_path, req.json_path)
        clips_dir = settings.storage_dir / 'clips'
        clip_paths = sorted(str(p) for p in clips_dir.glob('*.mp4'))
        return ClipResponse(clip_paths=clip_paths)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
