from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Server
    backend_port: int = 8000
    frontend_port: int = 5173

    # CORS
    cors_origins: list[str] = ["http://localhost:5173"]

    # LLM (for future use)
    llm_api_key: Optional[str] = None
    llm_model_name: Optional[str] = None
    llm_base_url: Optional[str] = None

    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
