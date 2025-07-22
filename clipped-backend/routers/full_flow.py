from fastapi import APIRouter, HTTPException
from schemas.full_flow import FullFlowRequest, FullFlowResponse
from services.download_service import download as download_video
from services.transcribe_service import create_transcript
from services.analyze_service import analyze_transcript
from services.clip_service import clip_moments
from config import settings

router = APIRouter()

@router.post("/", response_model=FullFlowResponse)
async def full_flow_endpoint(req: FullFlowRequest):
    # Step 1: Download video
    video_path = download_video(str(req.url))
    if not video_path:
        raise HTTPException(status_code=500, detail="Video download failed")

    # Step 2: Transcribe video
    transcript_path = create_transcript(str(video_path), str(req.url))

    # Step 3: Analyze transcript
    json_path = analyze_transcript(transcript_path)

    # Step 4: Clip based on analysis
    clip_moments(str(video_path), str(json_path))
    clips_dir = settings.storage_dir / 'clips'
    clip_paths = sorted(str(p) for p in clips_dir.glob('*.mp4'))

    return FullFlowResponse(clip_paths=clip_paths)
