from fastapi import APIRouter, HTTPException
from schemas.analyze import AnalyzeRequest, AnalyzeResponse
from services.analyze_service import analyze_transcript

router = APIRouter()

@router.post("/", response_model=AnalyzeResponse)
async def analyze_endpoint(req: AnalyzeRequest):
    moments = analyze_transcript(req.transcript)
    return AnalyzeResponse(moments=moments)
