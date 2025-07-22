import os
from pydantic import BaseSettings


class Settings(BaseSettings):
    host: str = os.getenv("FASTAPI_HOST", "127.0.0.1")
    port: int = int(os.getenv("FASTAPI_PORT", 8000))
    tmp_dir: str = os.getenv("TMP_DIR", "./tmp")


settings = Settings()
