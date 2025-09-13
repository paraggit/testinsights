"""Test client and fixtures for API testing."""

import os
import tempfile
from pathlib import Path
from typing import Any, Dict, Generator
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi.testclient import TestClient

from test_insights.api.app import app
from test_insights.config.settings import Settings


@pytest.fixture
def temp_chroma_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for ChromaDB during tests."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def test_settings(temp_chroma_dir: Path) -> Settings:
    """Create test settings with temporary directories."""
    # Override settings for testing
    test_env = {
        "REPORTPORTAL_URL": "https://test.reportportal.com",
        "REPORTPORTAL_API_TOKEN": "test_token_123",
        "REPORTPORTAL_PROJECT": "test_project",
        "CHROMA_PERSIST_DIRECTORY": str(temp_chroma_dir),
        "LLM_PROVIDER": "openai",
        "OPENAI_API_KEY": "test_openai_key",
        "API_HOST": "127.0.0.1",
        "API_PORT": "8001",
        "DEV_MODE": "true",
        "ENABLE_DOCS": "true",
    }

    with patch.dict(os.environ, test_env):
        # Create new settings instance with test environment
        settings = Settings()
        yield settings


@pytest.fixture
def mock_storage_client():
    """Mock ChromaDB storage client."""
    mock_client = AsyncMock()

    # Mock common methods
    mock_client.get_collection_info.return_value = {"name": "test_collection"}
    mock_client.query.return_value = []
    mock_client.delete_by_entity_type.return_value = 0

    return mock_client


@pytest.fixture
def mock_sync_orchestrator():
    """Mock sync orchestrator."""
    mock_orchestrator = AsyncMock()

    # Mock common methods
    mock_orchestrator.sync.return_value = {
        "entity_stats": {"test_item": 10},
        "total_processed": 10,
        "errors": [],
    }
    mock_orchestrator.get_sync_status.return_value = {
        "storage_stats": {"total_documents": 100},
        "last_sync": "2024-01-15T10:30:00Z",
        "sync_type": "incremental",
    }

    return mock_orchestrator


@pytest.fixture
def mock_llm_provider():
    """Mock LLM provider."""
    mock_provider = AsyncMock()

    # Mock response
    mock_response = Mock()
    mock_response.content = "Test AI response"
    mock_response.model = "gpt-4-turbo-preview"
    mock_response.usage = {"total_tokens": 100, "prompt_tokens": 50, "completion_tokens": 50}

    mock_provider.generate.return_value = mock_response
    mock_provider.format_context.return_value = "Formatted context"

    return mock_provider


@pytest.fixture
def mock_rag_pipeline():
    """Mock RAG pipeline."""
    mock_rag = AsyncMock()

    mock_rag.query.return_value = {
        "response": "Test RAG response",
        "analysis": {"intent": "search", "entity_types": ["test_item"]},
        "metrics": {"total_items": 10},
        "search_results": [],
        "model": "gpt-4-turbo-preview",
        "usage": {"total_tokens": 100},
    }

    return mock_rag


@pytest.fixture
def client_with_mocks(
    test_settings: Settings,
    mock_storage_client,
    mock_sync_orchestrator,
    mock_llm_provider,
    mock_rag_pipeline,
) -> TestClient:
    """Create test client with all dependencies mocked."""

    with (
        patch("test_insights.api.app.storage_client", mock_storage_client),
        patch("test_insights.api.app.sync_orchestrator", mock_sync_orchestrator),
        patch("test_insights.api.app.settings", test_settings),
        patch("test_insights.api.app.get_llm_provider", return_value=mock_llm_provider),
        patch("test_insights.rag.rag_pipeline.RAGPipeline", return_value=mock_rag_pipeline),
    ):
        client = TestClient(app)
        yield client


@pytest.fixture
def client() -> TestClient:
    """Create basic test client without mocks."""
    return TestClient(app)


@pytest.fixture
def sample_query_requests() -> Dict[str, Dict[str, Any]]:
    """Sample query requests for testing."""
    return {
        "basic": {
            "query": "Show me failed tests",
            "show_sources": False,
            "n_results": 10,
        },
        "with_provider": {
            "query": "What tests failed yesterday?",
            "provider": "openai",
            "model": "gpt-4-turbo-preview",
            "show_sources": True,
            "n_results": 20,
        },
        "slack_style": {
            "query": "What's the success rate this week?",
            "show_sources": False,
            "n_results": 15,
        },
    }


@pytest.fixture
def sample_search_requests() -> Dict[str, Dict[str, Any]]:
    """Sample search requests for testing."""
    return {
        "basic": {
            "query": "timeout error",
            "limit": 10,
        },
        "with_filters": {
            "query": "login failed",
            "entity_types": ["test_item"],
            "limit": 5,
        },
        "multiple_entities": {
            "query": "database connection",
            "entity_types": ["test_item", "log"],
            "limit": 20,
        },
    }


@pytest.fixture
def sample_sync_requests() -> Dict[str, Dict[str, Any]]:
    """Sample sync requests for testing."""
    return {
        "incremental": {
            "full": False,
        },
        "full": {
            "full": True,
        },
        "specific_projects": {
            "projects": ["web-app", "api-service"],
            "entity_types": ["launch", "test_item"],
            "full": False,
        },
    }


class MockAsyncContextManager:
    """Mock async context manager for testing."""

    def __init__(self, mock_obj):
        self.mock_obj = mock_obj

    async def __aenter__(self):
        return self.mock_obj

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


@pytest.fixture
def mock_ollama_provider():
    """Mock Ollama provider with async context manager."""
    mock_provider = AsyncMock()

    # Mock the context manager behavior
    mock_provider.__aenter__ = AsyncMock(return_value=mock_provider)
    mock_provider.__aexit__ = AsyncMock(return_value=None)

    # Mock response
    mock_response = Mock()
    mock_response.content = "Test Ollama response"
    mock_response.model = "llama2"
    mock_response.usage = {"total_tokens": 80}

    mock_provider.generate.return_value = mock_response
    mock_provider.format_context.return_value = "Formatted context"

    return mock_provider
