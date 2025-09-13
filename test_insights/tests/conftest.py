"""Pytest configuration and shared fixtures."""

import os
import tempfile
from pathlib import Path
from typing import Generator
from unittest.mock import AsyncMock, Mock

import pytest
from fastapi.testclient import TestClient

from test_insights.api.app import app

# Configure pytest
pytest_plugins = ["test_insights.tests.fixtures.test_client"]


@pytest.fixture(scope="session")
def test_env_vars():
    """Set up test environment variables for the session."""
    test_env = {
        "REPORTPORTAL_URL": "https://test.reportportal.com",
        "REPORTPORTAL_API_TOKEN": "test_token_12345",
        "REPORTPORTAL_PROJECT": "test_project",
        "LLM_PROVIDER": "openai",
        "OPENAI_API_KEY": "test_openai_key",
        "API_HOST": "127.0.0.1",
        "API_PORT": "8001",
        "DEV_MODE": "true",
        "ENABLE_DOCS": "true",
        "ENABLE_REDOC": "true",
        "ENABLE_OPENAPI_JSON": "true",
        "LOG_LEVEL": "DEBUG",
        "API_LOG_LEVEL": "DEBUG",
    }

    # Store original values
    original_env = {}
    for key, value in test_env.items():
        original_env[key] = os.environ.get(key)
        os.environ[key] = value

    yield test_env

    # Restore original values
    for key, original_value in original_env.items():
        if original_value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = original_value


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def mock_chroma_client():
    """Mock ChromaDB client for testing."""
    mock_client = AsyncMock()

    # Mock common methods
    mock_client.get_collection_info.return_value = {
        "name": "test_collection",
        "metadata": {"test": True},
    }
    mock_client.query.return_value = []
    mock_client.delete_by_entity_type.return_value = 0
    mock_client.add_documents.return_value = True

    return mock_client


@pytest.fixture
def mock_sync_orchestrator():
    """Mock sync orchestrator for testing."""
    mock_orchestrator = AsyncMock()

    # Mock common methods
    mock_orchestrator.sync.return_value = {
        "entity_stats": {"test_item": 10, "launch": 5},
        "total_processed": 15,
        "errors": [],
        "duration_seconds": 30.5,
    }

    mock_orchestrator.get_sync_status.return_value = {
        "storage_stats": {
            "total_documents": 100,
            "by_entity_type": {"test_item": 80, "launch": 20},
        },
        "last_sync": "2024-01-15T10:30:00Z",
        "sync_type": "incremental",
    }

    return mock_orchestrator


@pytest.fixture
def mock_openai_provider():
    """Mock OpenAI provider for testing."""
    mock_provider = AsyncMock()

    # Mock response object
    mock_response = Mock()
    mock_response.content = "Test OpenAI response"
    mock_response.model = "gpt-4-turbo-preview"
    mock_response.usage = {
        "total_tokens": 100,
        "prompt_tokens": 60,
        "completion_tokens": 40,
    }

    mock_provider.generate.return_value = mock_response
    mock_provider.format_context.return_value = "Formatted context"

    return mock_provider


@pytest.fixture
def mock_anthropic_provider():
    """Mock Anthropic provider for testing."""
    mock_provider = AsyncMock()

    # Mock response object
    mock_response = Mock()
    mock_response.content = "Test Anthropic response"
    mock_response.model = "claude-3-opus-20240229"
    mock_response.usage = {
        "total_tokens": 120,
        "prompt_tokens": 70,
        "completion_tokens": 50,
    }

    mock_provider.generate.return_value = mock_response
    mock_provider.format_context.return_value = "Formatted context"

    return mock_provider


@pytest.fixture
def mock_ollama_provider():
    """Mock Ollama provider for testing."""
    mock_provider = AsyncMock()

    # Mock async context manager
    mock_provider.__aenter__ = AsyncMock(return_value=mock_provider)
    mock_provider.__aexit__ = AsyncMock(return_value=None)

    # Mock response object
    mock_response = Mock()
    mock_response.content = "Test Ollama response"
    mock_response.model = "llama2"
    mock_response.usage = {
        "total_tokens": 80,
        "prompt_tokens": 50,
        "completion_tokens": 30,
    }

    mock_provider.generate.return_value = mock_response
    mock_provider.format_context.return_value = "Formatted context"

    return mock_provider


@pytest.fixture
def mock_rag_pipeline():
    """Mock RAG pipeline for testing."""
    mock_rag = AsyncMock()

    mock_rag.query.return_value = {
        "response": "Test RAG response",
        "analysis": {
            "intent": "search",
            "entity_types": ["test_item"],
            "keywords": ["test", "query"],
            "metrics_requested": True,
        },
        "metrics": {
            "total_items": 50,
            "failure_rate": 20.0,
            "success_rate": 80.0,
        },
        "search_results": [],
        "model": "test-model",
        "usage": {"total_tokens": 100},
    }

    return mock_rag


@pytest.fixture
def api_client():
    """Create a test client for the API."""
    return TestClient(app)


@pytest.fixture
def authenticated_client(api_client):
    """Create an authenticated test client (for future auth implementation)."""
    # For now, just return the regular client
    # In the future, this could add authentication headers
    return api_client


# Test data fixtures
@pytest.fixture
def sample_test_data():
    """Sample test data for testing."""
    return {
        "launches": [
            {
                "id": 1,
                "name": "Nightly Tests",
                "status": "FAILED",
                "start_time": "2024-01-15T10:00:00Z",
                "end_time": "2024-01-15T11:30:00Z",
            },
            {
                "id": 2,
                "name": "API Tests",
                "status": "PASSED",
                "start_time": "2024-01-15T12:00:00Z",
                "end_time": "2024-01-15T12:45:00Z",
            },
        ],
        "test_items": [
            {
                "id": 1,
                "name": "test_login_success",
                "status": "PASSED",
                "launch_id": 2,
                "start_time": "2024-01-15T12:10:00Z",
            },
            {
                "id": 2,
                "name": "test_login_invalid_credentials",
                "status": "FAILED",
                "launch_id": 1,
                "start_time": "2024-01-15T10:15:00Z",
            },
        ],
        "logs": [
            {
                "id": 1,
                "message": "Login test completed successfully",
                "level": "INFO",
                "test_item_id": 1,
                "time": "2024-01-15T12:10:30Z",
            },
            {
                "id": 2,
                "message": "AssertionError: Expected status 200, got 401",
                "level": "ERROR",
                "test_item_id": 2,
                "time": "2024-01-15T10:15:45Z",
            },
        ],
    }


# Pytest markers
def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "api: API endpoint tests")
    config.addinivalue_line("markers", "config: Configuration tests")
    config.addinivalue_line("markers", "slow: Slow-running tests")
    config.addinivalue_line("markers", "requires_llm: Tests that require LLM provider")
    config.addinivalue_line("markers", "requires_storage: Tests that require storage")


# Custom test classes for organization
class APITestCase:
    """Base class for API test cases."""

    pass


class IntegrationTestCase:
    """Base class for integration test cases."""

    pass


class UnitTestCase:
    """Base class for unit test cases."""

    pass
