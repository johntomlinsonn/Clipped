import os
from pydantic import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    host: str = os.getenv("FASTAPI_HOST", "127.0.0.1")
    port: int = int(os.getenv("FASTAPI_PORT", 8000))
    tmp_dir: Path = Path(os.getenv("TMP_DIR", "./tmp"))

    storage_dir: Path = Path(os.getenv("STORAGE_DIR", "./storage"))


settings = Settings()
