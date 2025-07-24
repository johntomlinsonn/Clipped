from fastapi import APIRouter, HTTPException, Query
from schemas.full_flow import FullFlowRequest, FullFlowResponse
from services.download_service import download as download_video
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
    # Step 1: Download video
    logging.info("Step 1: Downloading video")
    video_path = download_video(str(req.url))
    if not video_path:
        raise HTTPException(status_code=500, detail="Video download failed")
    logging.info(f"Video downloaded to {video_path}")

    # Step 2: Transcribe video
    logging.info("Step 2: Transcribing video")
    transcript_path = create_transcript(str(video_path), str(req.url))
    logging.info(f"Transcript created at {transcript_path}")

    # Step 3: Analyze transcript
    logging.info("Step 3: Analyzing transcript")
    moments_data = analyze_transcript(transcript_path)

    # Step 4: Clip based on analysis
    logging.info("Step 4: Clipping moments")
    # Pass moments list directly to clip_service
    clip_paths = clip_moments(str(video_path), moments_data.get('viral_moments', []))
    logging.info(f"Clipping completed, generated {len(clip_paths)} clips")

    # Step 5: Cleanup downloaded files
    if clean:
        logging.info("Step 5: Cleaning up temporary files")
        cleanup(include_clips=False)
    else:
        logging.info("Skipping cleanup of temporary files")

    return FullFlowResponse(clip_paths=clip_paths)
