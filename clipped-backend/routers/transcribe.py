from fastapi import APIRouter, HTTPException
from schemas.transcribe import TranscribeRequest, TranscribeResponse
from services.transcribe_service import create_transcript

router = APIRouter()

@router.post("/", response_model=TranscribeResponse)
async def transcribe_endpoint(req: TranscribeRequest):
    transcript_path = create_transcript(req.video_path, req.url)
    if not transcript_path:
        raise HTTPException(status_code=500, detail="Transcription failed")
    return TranscribeResponse(transcript_path=str(transcript_path))
