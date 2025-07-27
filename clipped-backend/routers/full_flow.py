from fastapi import APIRouter, HTTPException, Query
from schemas.full_flow import FullFlowRequest, FullFlowResponse
from services.download_service import download as download_video, get_transcript_path
from services.transcribe_service import create_transcript
from services.analyze_service import analyze_transcript
from services.clip_service import clip_moments
from services.cleanup_service import cleanup
from config import settings

import logging
router = APIRouter()

@router.post("/", response_model=FullFlowResponse)
async def full_flow_endpoint(req: FullFlowRequest, clean: bool = Query(True, description="Remove temporary files after processing")):
    logging.info(f"Full flow job started for URL: {req.url}")
    
    # Step 1: Download video and attempt transcript download
    logging.info("Step 1: Downloading video and checking for transcript")
    video_path, transcript_available = download_video(str(req.url))
    if not video_path:
        raise HTTPException(status_code=500, detail="Video download failed")
    logging.info(f"Video downloaded to {video_path}")

    # Step 2: Handle transcript (use existing or create new)
    if transcript_available:
        logging.info("Step 2: Using downloaded YouTube transcript")
        transcript_path = get_transcript_path(str(req.url))
        if not transcript_path:
            # Fallback to transcription if cached transcript is missing
            logging.warning("Cached transcript missing, falling back to transcription")
            transcript_path = create_transcript(str(video_path), str(req.url))
    else:
        logging.info("Step 2: No YouTube transcript available, transcribing video")
        transcript_path = create_transcript(str(video_path), str(req.url))
    
    logging.info(f"Transcript ready at {transcript_path}")

    # Step 3: Analyze transcript
    logging.info("Step 3: Analyzing transcript")
    moments_data = analyze_transcript(transcript_path)

    # Step 4: Clip based on analysis
    logging.info("Step 4: Clipping moments")
    # Pass moments list directly to clip_service
    clip_paths = clip_moments(str(video_path), moments_data.get('viral_moments', []))
    logging.info(f"Clipping completed, generated {len(clip_paths)} clips")

    if clean:
        logging.info("Step 5: Cleaning up temporary files")
        cleanup(include_clips=False)
    else:
        logging.info("Skipping cleanup of temporary files")

    return FullFlowResponse(clip_paths=clip_paths)
