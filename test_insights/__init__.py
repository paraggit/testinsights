"""ReportPortal AI Assistant - AI-powered assistant for ReportPortal."""

__version__ = "0.1.0"
__author__ = "Parag Kamble"
__email__ = "kamble.parag@gmail.com"
__description__ = "AI-powered assistant for ReportPortal test data analysis"

# Core imports for convenience
from test_insights.config.settings import settings

# Exception imports
from test_insights.core.exceptions import (
    APIError,
    AuthenticationError,
    ConfigurationError,
    EmbeddingError,
    RateLimitError,
    ReportPortalAIError,
    StorageError,
    SyncError,
)
from test_insights.core.logging import setup_logging
from test_insights.data_sync.storage.chromadb_client import ChromaDBClient
from test_insights.data_sync.sync.orchestrator import SyncOrchestrator
from test_insights.rag.rag_pipeline import RAGPipeline

__all__ = [
    "__version__",
    "settings",
    "setup_logging",
    "SyncOrchestrator",
    "ChromaDBClient",
    "RAGPipeline",
    "ReportPortalAIError",
    "APIError",
    "AuthenticationError",
    "RateLimitError",
    "SyncError",
    "StorageError",
    "EmbeddingError",
    "ConfigurationError",
]
