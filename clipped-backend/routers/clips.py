from fastapi import APIRouter, Response, UploadFile, File, Request
from typing import List
from pydantic import BaseModel
from config import settings
from pathlib import Path
from fastapi.responses import StreamingResponse

router = APIRouter()

class ClipsRequest(BaseModel):
    paths: List[str]

@router.post("/", response_class=StreamingResponse)
async def get_clips_files(req: ClipsRequest):
    """
    Given a list of clip paths, stream the video files as a multipart response.
    """
    import io
    import mimetypes
    from starlette.responses import StreamingResponse
    from starlette.background import BackgroundTask

    boundary = "clipsboundary"
    def file_iter():
        for rel_path in req.paths:
            # Normalize path: remove leading .., storage, clips, and handle both / and \\ separators
            norm = rel_path.replace('..', '').replace('\\', '/').replace('storage/', '').replace('clips/', '')
            clips_dir = Path(settings.storage_dir) / "clips"
            clip_path = clips_dir / Path(norm).name
            if clip_path.exists():
                mime_type, _ = mimetypes.guess_type(str(clip_path))
                yield f"--{boundary}\r\n".encode()
                yield f"Content-Type: {mime_type or 'video/mp4'}\r\n".encode()
                yield f"Content-Disposition: attachment; filename=\"{clip_path.name}\"\r\n\r\n".encode()
                with open(clip_path, "rb") as f:
                    while True:
                        chunk = f.read(8192)
                        if not chunk:
                            break
                        yield chunk
                yield b"\r\n"
        yield f"--{boundary}--\r\n".encode()

    return StreamingResponse(file_iter(), media_type=f"multipart/x-mixed-replace; boundary={boundary}")
