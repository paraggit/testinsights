# src/test_insights/__init__.py
"""ReportPortal AI Assistant - AI-powered assistant for ReportPortal."""

__version__ = "0.1.0"

# src/test_insights/config/__init__.py
"""Configuration module."""

from test_insights.config.settings import settings

__all__ = ["settings"]

# src/test_insights/core/__init__.py
"""Core utilities and components."""

from test_insights.core.exceptions import (
    ReportPortalAIError,
    APIError,
    AuthenticationError,
    RateLimitError,
    SyncError,
    StorageError,
    EmbeddingError,
    ConfigurationError,
)
from test_insights.core.logging import setup_logging

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

# src/test_insights/data_sync/__init__.py
"""Data synchronization module."""

from test_insights.data_sync.sync.orchestrator import SyncOrchestrator

__all__ = ["SyncOrchestrator"]

# src/test_insights/data_sync/api/__init__.py
"""ReportPortal API client module."""

from test_insights.data_sync.api.client import ReportPortalAPIClient, PaginatedResponse

__all__ = ["ReportPortalAPIClient", "PaginatedResponse"]

# src/test_insights/data_sync/storage/__init__.py
"""Storage module for vector database operations."""

from test_insights.data_sync.storage.chromadb_client import ChromaDBClient

__all__ = ["ChromaDBClient"]

# src/test_insights/data_sync/sync/__init__.py
"""Synchronization strategies and orchestration."""

from test_insights.data_sync.sync.orchestrator import SyncOrchestrator
from test_insights.data_sync.sync.strategies import SyncStrategy, FullSyncStrategy, IncrementalSyncStrategy

__all__ = ["SyncOrchestrator", "SyncStrategy", "FullSyncStrategy", "IncrementalSyncStrategy"]

# src/test_insights/data_sync/utils/__init__.py
"""Utility functions and helpers."""

#