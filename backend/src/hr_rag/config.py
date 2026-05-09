from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://hr_rag:changeme@localhost:5432/hr_rag"
    google_api_key: str = ""
    backend_port: int = 8000
    debug: bool = False

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
