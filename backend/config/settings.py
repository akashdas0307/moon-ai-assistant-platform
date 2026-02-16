from pydantic_settings import BaseSettings
from typing import Optional
from pathlib import Path


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

    # File workspace settings
    WORKSPACE_DIR: Path = Path(__file__).parent.parent / "workspace"
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10 MB
    ALLOWED_EXTENSIONS: set = {
        ".py", ".js", ".ts", ".tsx", ".jsx",
        ".md", ".txt", ".json", ".yaml", ".yml",
        ".html", ".css", ".sh", ".env"
    }

    class Config:
        env_file = ".env"
        case_sensitive = False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Create workspace directory if it doesn't exist
        self.WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)


# Global settings instance
settings = Settings()
