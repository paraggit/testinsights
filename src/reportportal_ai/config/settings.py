"""Configuration settings for the ReportPortal AI Assistant."""

import os
from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )
    
    # ReportPortal API settings
    reportportal_url: str
    reportportal_api_token: str
    reportportal_project: Optional[str] = None
    
    # ChromaDB settings
    chroma_persist_directory: Path = Path("./chroma_db")
    chroma_collection_name: str = "reportportal_data"
    
    # Sync settings
    sync_batch_size: int = 100
    sync_rate_limit: int = 10  # requests per second
    sync_timeout: int = 30  # seconds
    sync_max_retries: int = 3
    
    # Embedding settings
    embedding_model: str = "all-MiniLM-L6-v2"
    embedding_batch_size: int = 32
    
    # Logging settings
    log_level: str = "INFO"
    log_format: str = "json"  # json or console
    
    # Feature flags
    enable_incremental_sync: bool = True
    enable_full_sync: bool = True
    
    @property
    def reportportal_base_url(self) -> str:
        """Get the base URL for ReportPortal API."""
        return f"{self.reportportal_url}/api"


# Global settings instance
settings = Settings()