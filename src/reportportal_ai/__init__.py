# src/reportportal_ai/__init__.py
"""ReportPortal AI Assistant - AI-powered assistant for ReportPortal."""

__version__ = "0.1.0"

# src/reportportal_ai/config/__init__.py
"""Configuration module."""

from src.reportportal_ai.config.settings import settings

__all__ = ["settings"]

# src/reportportal_ai/core/__init__.py
"""Core utilities and components."""

from src.reportportal_ai.core.exceptions import (
    ReportPortalAIError,
    APIError,
    AuthenticationError,
    RateLimitError,
    SyncError,
    StorageError,
    EmbeddingError,
    ConfigurationError,
)
from src.reportportal_ai.core.logging import setup_logging

__all__ = [
    "ReportPortalAIError",
    "APIError",
    "AuthenticationError",
    "RateLimitError",
    "SyncError",
    "StorageError",
    "EmbeddingError",
    "ConfigurationError",
    "setup_logging",
]

# src/reportportal_ai/data_sync/__init__.py
"""Data synchronization module."""

from src.reportportal_ai.data_sync.sync.orchestrator import SyncOrchestrator

__all__ = ["SyncOrchestrator"]

# src/reportportal_ai/data_sync/api/__init__.py
"""ReportPortal API client module."""

from src.reportportal_ai.data_sync.api.client import ReportPortalAPIClient, PaginatedResponse

__all__ = ["ReportPortalAPIClient", "PaginatedResponse"]

# src/reportportal_ai/data_sync/storage/__init__.py
"""Storage module for vector database operations."""

from src.reportportal_ai.data_sync.storage.chromadb_client import ChromaDBClient

__all__ = ["ChromaDBClient"]

# src/reportportal_ai/data_sync/sync/__init__.py
"""Synchronization strategies and orchestration."""

from src.reportportal_ai.data_sync.sync.orchestrator import SyncOrchestrator
from src.reportportal_ai.data_sync.sync.strategies import SyncStrategy, FullSyncStrategy, IncrementalSyncStrategy

__all__ = ["SyncOrchestrator", "SyncStrategy", "FullSyncStrategy", "IncrementalSyncStrategy"]

# src/reportportal_ai/data_sync/utils/__init__.py
"""Utility functions and helpers."""

#