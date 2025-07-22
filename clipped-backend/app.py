from fastapi import FastAPI
from config import settings
from routers.download import router as download_router
from routers.transcribe import router as transcribe_router
from routers.clip import router as clip_router
from routers.cleanup import router as cleanup_router
from routers.analyze import router as analyze_router

app = FastAPI(title="Clipped API")

app.include_router(download_router, prefix="/download", tags=["download"])
app.include_router(transcribe_router, prefix="/transcribe", tags=["transcribe"])
app.include_router(clip_router, prefix="/clip", tags=["clip"])
app.include_router(cleanup_router, prefix="/cleanup", tags=["cleanup"])
app.include_router(analyze_router, prefix="/analyze", tags=["analyze"])
 
# Mount central storage for media files (downloads, clips, transcripts, etc.)
from fastapi.staticfiles import StaticFiles
app.mount(
    "/media",
    StaticFiles(directory=str(settings.storage_dir)),
    name="media"
)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app:app",
        host=settings.host,
        port=settings.port,
        reload=True,
    )
