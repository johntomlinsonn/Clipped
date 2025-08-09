from fastapi import APIRouter, HTTPException, Query
from schemas.full_flow import FullFlowRequest, FullFlowResponse
from services.download_service import download as download_video, get_transcript_path
from services.transcribe_service import create_transcript
from services.caption_service import generate_captions, generate_captions_parallel, generate_captioned_clips_from_moments
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
    captions: bool = Query(False, description="Generate captioned videos for all clips in parallel")
):
    """
    Optimized async pipeline that runs processes concurrently when dependencies are ready.
    
    Pipeline stages:
    1. Download video + transcript (parallel when possible)
    2. Transcription (if needed) 
    3. Analysis (starts immediately when transcript ready)
    4. Clipping (starts immediately when analysis complete)
    5. Captioning all clips in parallel (if requested)
    6. Cleanup (optional, runs concurrently)
    """
    logging.info(f"Full flow job started for URL: {req.url}")

    # Prepare containers accessible after threadpool closes
    clip_paths: list[str] = []
    captioned_video_paths: list[str] = []

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

            moments_list = moments_data.get('viral_moments', [])

            if captions:
                # Directly produce captioned clips from original video & transcript without interim clips
                logging.info("Captions requested: generating captioned clips directly without intermediate video clips")
                # Ensure transcript exists (already created earlier); pass moments to caption service
                captioned_video_paths = await loop.run_in_executor(
                    executor,
                    partial(generate_captioned_clips_from_moments, str(video_path), moments_list, transcript_path, str(req.url))
                )
                # For cleanup logic later, treat original clips list as empty since we didn't create them
                clip_paths = []
            else:
                # Standard clipping flow when not captioning
                clipping_task = loop.run_in_executor(
                    executor,
                    partial(clip_moments, str(video_path), moments_list)
                )
                clip_paths = await clipping_task
                logging.info(f"Clipping completed, generated {len(clip_paths)} clips")

            # Step 5: (Only if captions requested and we produced direct captioned clips) or caption existing clips
            if captions and not captioned_video_paths and clip_paths:
                logging.info(f"Step 5: Generating captions for {len(clip_paths)} clips in parallel using generate_captions_parallel")
                captioning_task = loop.run_in_executor(
                    executor,
                    partial(
                        generate_captions_parallel,
                        clip_paths,
                        str(req.url)
                    )
                )
                captioned_video_paths = await captioning_task
                logging.info(f"Captioning completed: {len(captioned_video_paths)}/{len(clip_paths)} clips successfully captioned")
            
        except Exception as e:
            logging.error(f"Full flow pipeline failed: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Pipeline failed: {str(e)}")
    
    # Determine which originals to delete (only originals that have captioned versions)
    originals_to_delete: list[str] = []
    if captions:
        # If we generated direct captioned clips, no originals to delete; else delete original temp clips
        originals_to_delete = clip_paths.copy() if clip_paths else []

    # Step 6: Start cleanup in background after executor is closed
    if clean:
        logging.info("Step 6: Starting cleanup of temporary files in background")
        async def cleanup_background():
            try:
                with ThreadPoolExecutor(max_workers=1) as cleanup_executor:
                    loop = asyncio.get_event_loop()
                    cleanup_future = loop.run_in_executor(
                        cleanup_executor,
                        partial(cleanup, include_clips=False, video_paths=originals_to_delete)
                    )
                    await cleanup_future
                    logging.info("Background cleanup completed")
            except Exception as e:
                logging.error(f"Background cleanup failed: {e}")
        asyncio.create_task(cleanup_background())
        logging.info("Cleanup started in background")
    else:
        logging.info("Skipping cleanup of temporary files")

    # Return response with both clip paths and captioned video paths
    response = FullFlowResponse(clip_paths=clip_paths)
    if captioned_video_paths:
        if hasattr(response, 'captioned_video_paths'):
            response.captioned_video_paths = captioned_video_paths
        else:
            logging.info(f"Captioned video paths: {captioned_video_paths}")
    return response