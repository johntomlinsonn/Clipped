import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

load_dotenv()

class Settings(BaseSettings):
    host: str = os.getenv("FASTAPI_HOST", "127.0.0.1")
    port: int = int(os.getenv("FASTAPI_PORT", 8000))
    tmp_dir: Path = Path(os.getenv("TMP_DIR", "./tmp"))

    storage_dir: Path = Path(os.getenv("STORAGE_DIR", "./storage"))

    cerebras_api_key: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


settings = Settings()
