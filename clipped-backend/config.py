import os
from pathlib import Path
from dotenv import load_dotenv
from pydantic import BaseSettings, Field, SettingsConfigDict

load_dotenv()

class Settings(BaseSettings):
    host: str = Field("127.0.0.1", env="FASTAPI_HOST")
    port: int = Field(8000, env="FASTAPI_PORT")
    tmp_dir: Path = Field(Path("./tmp"), env="TMP_DIR")
    storage_dir: Path = Field(Path("./storage"), env="STORAGE_DIR")

    cerebras_api_key: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


settings = Settings()
