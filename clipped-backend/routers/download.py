from fastapi import APIRouter, HTTPException
from schemas.download import DownloadRequest, DownloadResponse
from services.download_service import download as download_video

router = APIRouter()

@router.post("/", response_model=DownloadResponse)
async def download_endpoint(req: DownloadRequest):
    try:
        # Convert HttpUrl to string for the download service
        video_path = download_video(str(req.url))
        if not video_path:
            raise HTTPException(status_code=500, detail="Video download failed")
        return DownloadResponse(video_path=str(video_path))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
