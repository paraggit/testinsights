"""Configuration settings for the ReportPortal AI Assistant."""

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

    # LLM settings
    llm_provider: str = "ollama"  # openai, anthropic, or ollama
    llm_model: Optional[str] = None  # Auto-detected based on provider
    llm_temperature: float = 0.7
    llm_max_tokens: int = 2000

    # Provider-specific settings
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4-turbo-preview"

    anthropic_api_key: Optional[str] = None
    anthropic_model: str = "claude-3-opus-20240229"

    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama2"

    # RAG settings
    rag_n_results: int = 20  # Number of documents to retrieve
    rag_include_raw_results: bool = False

    @property
    def reportportal_base_url(self) -> str:
        """Get the base URL for ReportPortal API."""
        return f"{self.reportportal_url}/api"


# Global settings instance
settings = Settings()
