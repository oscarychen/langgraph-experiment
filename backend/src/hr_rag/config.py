from pathlib import Path

from pydantic_settings import BaseSettings

# Repo root: backend/src/hr_rag/config.py -> parents[3]
ENV_FILE = Path(__file__).resolve().parents[3] / ".env"


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://hr_rag:changeme@localhost:5432/hr_rag"
    google_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"
    embedding_model: str = "models/text-embedding-004"
    embedding_dimension: int = 768
    backend_port: int = 8000
    debug: bool = False

    model_config = {
        "env_file": str(ENV_FILE),
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


settings = Settings()
