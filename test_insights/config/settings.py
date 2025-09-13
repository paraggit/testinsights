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

    # API Server settings
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_debug: bool = False
    api_log_level: str = "INFO"
    api_log_format: str = "json"
    api_cors_origins: str = "*"
    api_max_request_size: int = 10485760  # 10MB
    api_request_timeout: int = 300  # 5 minutes

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

    # Logging settings (keeping for backward compatibility)
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
    openai_base_url: str = "https://api.openai.com/v1"

    anthropic_api_key: Optional[str] = None
    anthropic_model: str = "claude-3-opus-20240229"
    anthropic_base_url: str = "https://api.anthropic.com"

    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama2"

    # RAG settings
    rag_n_results: int = 20  # Number of documents to retrieve
    rag_include_raw_results: bool = False

    # Monitoring & Observability
    enable_metrics: bool = False
    metrics_endpoint: str = "/metrics"
    enable_health_check: bool = True
    health_check_endpoint: str = "/health"
    enable_request_logging: bool = True

    # Slack Integration (optional)
    slack_bot_token: Optional[str] = None
    slack_signing_secret: Optional[str] = None
    slack_default_channel: Optional[str] = None

    # Development & Testing
    dev_mode: bool = False
    enable_docs: bool = True
    swagger_title: str = "TestInsight API"
    enable_redoc: bool = True
    enable_openapi_json: bool = True

    # Performance Tuning
    workers: int = 1
    worker_connections: int = 1000
    keep_alive_timeout: int = 65
    max_concurrent_requests: int = 100
    connection_pool_size: int = 20

    # Authentication & Security (for future use)
    api_key: Optional[str] = None
    jwt_secret: Optional[str] = None
    jwt_expiration: int = 3600
    enable_rate_limiting: bool = False
    rate_limit_per_minute: int = 100

    # Caching (for future use)
    enable_caching: bool = False
    cache_ttl: int = 300
    cache_backend: str = "memory"
    redis_url: Optional[str] = None

    # Database Backup & Maintenance
    enable_auto_backup: bool = False
    backup_interval_hours: int = 24
    backup_retention_days: int = 7
    backup_directory: Path = Path("./backups")

    # External Integrations (for future use)
    webhook_url: Optional[str] = None
    smtp_host: Optional[str] = None
    smtp_port: int = 587
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    email_from: Optional[str] = None

    # Custom Configuration
    custom_api_title: str = "TestInsight API"
    custom_api_description: str = "AI-powered ReportPortal test analytics"
    custom_api_version: str = "0.1.0"
    contact_name: str = "TestInsight Support"
    contact_email: str = "support@testinsight.example.com"
    contact_url: str = "https://github.com/your-org/testinsight"
    license_name: str = "MIT"
    license_url: str = "https://opensource.org/licenses/MIT"

    @property
    def reportportal_base_url(self) -> str:
        """Get the base URL for ReportPortal API."""
        return f"{self.reportportal_url}/api"

    @property
    def cors_origins_list(self) -> list[str]:
        """Get CORS origins as a list."""
        if self.api_cors_origins == "*":
            return ["*"]
        return [origin.strip() for origin in self.api_cors_origins.split(",")]

    @property
    def effective_log_level(self) -> str:
        """Get the effective log level (API-specific or general)."""
        return self.api_log_level if hasattr(self, "api_log_level") else self.log_level

    @property
    def effective_log_format(self) -> str:
        """Get the effective log format (API-specific or general)."""
        return self.api_log_format if hasattr(self, "api_log_format") else self.log_format

    def get_openai_config(self) -> dict:
        """Get OpenAI configuration as a dictionary."""
        return {
            "api_key": self.openai_api_key,
            "model": self.openai_model,
            "base_url": self.openai_base_url,
            "temperature": self.llm_temperature,
            "max_tokens": self.llm_max_tokens,
        }

    def get_anthropic_config(self) -> dict:
        """Get Anthropic configuration as a dictionary."""
        return {
            "api_key": self.anthropic_api_key,
            "model": self.anthropic_model,
            "base_url": self.anthropic_base_url,
            "temperature": self.llm_temperature,
            "max_tokens": self.llm_max_tokens,
        }

    def get_ollama_config(self) -> dict:
        """Get Ollama configuration as a dictionary."""
        return {
            "base_url": self.ollama_base_url,
            "model": self.ollama_model,
            "temperature": self.llm_temperature,
            "max_tokens": self.llm_max_tokens,
        }

    def get_slack_config(self) -> dict:
        """Get Slack configuration as a dictionary."""
        return {
            "bot_token": self.slack_bot_token,
            "signing_secret": self.slack_signing_secret,
            "default_channel": self.slack_default_channel,
        }

    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.dev_mode or self.api_debug

    def is_production(self) -> bool:
        """Check if running in production mode."""
        return not self.is_development()


# Global settings instance
settings = Settings()
