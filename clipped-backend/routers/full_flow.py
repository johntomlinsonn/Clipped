from fastapi import APIRouter, HTTPException, Query
from schemas.full_flow import FullFlowRequest, FullFlowResponse
from services.download_service import download as download_video, get_transcript_path
from services.transcribe_service import create_transcript
from services.caption_service import generate_captions
from services.analyze_service import analyze_transcript
from services.clip_service import clip_moments
from services.cleanup_service import cleanup
from config import settings

import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from pathlib import Path

router = APIRouter()

@router.post("/", response_model=FullFlowResponse)
async def full_flow_endpoint(
    req: FullFlowRequest,
    clean: bool = Query(True, description="Remove temporary files after processing"),
    captions: bool = Query(False, description="Generate a captioned video after clipping")
):
    """
    Optimized async pipeline that runs processes concurrently when dependencies are ready.
    
    Pipeline stages:
    1. Download video + transcript (parallel when possible)
    2. Transcription (if needed) 
    3. Analysis (starts immediately when transcript ready)
    4. Clipping (starts immediately when analysis complete)
    5. Cleanup (optional, runs concurrently)
    """
    logging.info(f"Full flow job started for URL: {req.url}")
    
    # Create thread pool for CPU-bound tasks
    with ThreadPoolExecutor(max_workers=4) as executor:
        try:
            # Step 1: Download video (blocking but necessary first step)
            logging.info("Step 1: Downloading video and checking for transcript")
            loop = asyncio.get_event_loop()
            
            # Run download in thread pool to avoid blocking
            download_task = loop.run_in_executor(
                executor, 
                partial(download_video, str(req.url))
            )
            
            video_path, transcript_available = await download_task
            if not video_path:
                raise HTTPException(status_code=500, detail="Video download failed")
            
            # Ensure video_path is absolute string path for FFmpeg compatibility
            video_path = str(Path(video_path).resolve())
            logging.info(f"Video downloaded to {video_path}")

            # Step 2: Handle transcript - this can start immediately after download
            transcript_task = None
            
            if transcript_available:
                logging.info("Step 2: Using downloaded YouTube transcript")
                # Try to get existing transcript first (fast operation)
                transcript_path = get_transcript_path(str(req.url))
                if transcript_path:
                    logging.info(f"Found cached transcript at {transcript_path}")
                    # Create a completed future for consistency
                    transcript_future = asyncio.Future()
                    transcript_future.set_result(transcript_path)
                    transcript_task = transcript_future
                else:
                    # Fallback to transcription
                    logging.warning("Cached transcript missing, falling back to transcription")
                    transcript_task = loop.run_in_executor(
                        executor,
                        partial(create_transcript, str(video_path), str(req.url))
                    )
            else:
                logging.info("Step 2: No YouTube transcript available, transcribing video")
                transcript_task = loop.run_in_executor(
                    executor,
                    partial(create_transcript, str(video_path), str(req.url))
                )
            
            # Wait for transcript to be ready
            transcript_path = await transcript_task
            logging.info(f"Transcript ready at {transcript_path}")

            # Step 3: Analysis can start immediately when transcript is ready
            logging.info("Step 3: Analyzing transcript")
            analysis_task = loop.run_in_executor(
                executor,
                partial(analyze_transcript, transcript_path)
            )
            
            # Step 4: Wait for analysis, then start clipping
            moments_data = await analysis_task
            logging.info("Step 4: Clipping moments")
            
            # Clipping can run in parallel with cleanup preparation
            clipping_task = loop.run_in_executor(
                executor,
                partial(clip_moments, str(video_path), moments_data.get('viral_moments', []))
            )
            
            # Wait for clipping to complete
            clip_paths = await clipping_task
            logging.info(f"Clipping completed, generated {len(clip_paths)} clips")

            # Optionally generate a captioned video using the first clip (or the full video if no clips)
            captioned_video_path = None
            if captions:
                try:
                    # Use the first clip if available, else the original video
                    input_video = clip_paths[0] if clip_paths else video_path
                    output_captioned = str(Path(input_video).with_name(f"captioned_{Path(input_video).name}"))
                    # Use the transcript path already obtained
                    generate_captions(input_video, str(req.url), output_captioned)
                    captioned_video_path = output_captioned
                    logging.info(f"Captioned video generated at {output_captioned}")
                except Exception as e:
                    logging.error(f"Captioned video generation failed: {e}")
            
        except Exception as e:
            logging.error(f"Full flow pipeline failed: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Pipeline failed: {str(e)}")
    
    # Step 5: Start cleanup in background after executor is closed
    if clean:
        logging.info("Step 5: Starting cleanup of temporary files in background")
        # Start cleanup in background with a new executor - don't wait for it
        async def cleanup_background():
            try:
                with ThreadPoolExecutor(max_workers=1) as cleanup_executor:
                    loop = asyncio.get_event_loop()
                    cleanup_future = loop.run_in_executor(
                        cleanup_executor,
                        partial(cleanup, include_clips=False)
                    )
                    await cleanup_future
                    logging.info("Background cleanup completed")
            except Exception as e:
                logging.error(f"Background cleanup failed: {e}")
        
        # Start cleanup task in background
        asyncio.create_task(cleanup_background())
        logging.info("Cleanup started in background")
    else:
        logging.info("Skipping cleanup of temporary files")

    # Optionally include captioned video path in response if generated
    response = FullFlowResponse(clip_paths=clip_paths)
    if 'captioned_video_path' in locals() and captioned_video_path:
        # If your FullFlowResponse supports extra fields, add it; otherwise, log it
        if hasattr(response, 'captioned_video_path'):
            response.captioned_video_path = captioned_video_path
        else:
            logging.info(f"Captioned video path: {captioned_video_path}")
    return response
