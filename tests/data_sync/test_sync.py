"""Tests for data synchronization functionality."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta

from src.reportportal_ai.data_sync.sync.orchestrator import SyncOrchestrator
from src.reportportal_ai.data_sync.sync.strategies import FullSyncStrategy, IncrementalSyncStrategy
from src.reportportal_ai.data_sync.api.client import PaginatedResponse
from src.reportportal_ai.data_sync.storage.chromadb_client import ChromaDBClient


@pytest.fixture
def mock_api_client():
    """Create a mock API client."""
    client = Mock()
    client.__aenter__ = AsyncMock(return_value=client)
    client.__aexit__ = AsyncMock(return_value=None)
    
    # Mock API methods
    client.get_projects = AsyncMock(return_value=[
        {"id": 1, "projectName": "test-project", "organization": "test-org"}
    ])
    
    client.get_users = AsyncMock(return_value=PaginatedResponse(
        items=[
            {"id": 1, "userId": "user1", "fullName": "Test User", "email": "test@example.com"}
        ],
        total=1,
        page=0,
        size=100
    ))
    
    client.get_launches = AsyncMock(return_value=PaginatedResponse(
        items=[
            {
                "id": 1,
                "name": "Test Launch",
                "number": 1,
                "status": "PASSED",
                "startTime": datetime.utcnow().isoformat()
            }
        ],
        total=1,
        page=0,
        size=100
    ))
    
    client.get_test_items = AsyncMock(return_value=PaginatedResponse(
        items=[],
        total=0,
        page=0,
        size=100
    ))
    
    client.get_logs = AsyncMock(return_value=PaginatedResponse(
        items=[],
        total=0,
        page=0,
        size=100
    ))
    
    client.get_filters = AsyncMock(return_value=PaginatedResponse(
        items=[],
        total=0,
        page=0,
        size=100
    ))
    
    client.get_dashboards = AsyncMock(return_value=PaginatedResponse(
        items=[],
        total=0,
        page=0,
        size=100
    ))
    
    return client


@pytest.fixture
def mock_storage_client():
    """Create a mock storage client."""
    client = Mock(spec=ChromaDBClient)
    client.upsert_documents = AsyncMock(return_value=1)
    client.delete_by_entity_type = AsyncMock(return_value=0)
    client.get_existing_ids = AsyncMock(return_value=set())
    client.get_statistics = AsyncMock(return_value={
        "total_documents": 0,
        "by_entity_type": {}
    })
    return client


@pytest.mark.asyncio
async def test_sync_orchestrator_full_sync(mock_api_client, mock_storage_client):
    """Test full sync functionality."""
    orchestrator = SyncOrchestrator(
        api_client=mock_api_client,
        storage_client=mock_storage_client
    )
    
    stats = await orchestrator.sync(
        sync_type="full",
        project_names=["test-project"],
        entity_types=["project", "launch"]
    )
    
    assert stats["sync_type"] == "full"
    assert "start_time" in stats
    assert "end_time" in stats
    assert "duration_seconds" in stats
    assert isinstance(stats["entity_stats"], dict)
    
    # Verify API calls
    mock_api_client.get_projects.assert_called_once()
    mock_api_client.get_launches.assert_called()
    
    # Verify storage calls
    assert mock_storage_client.upsert_documents.called


@pytest.mark.asyncio
async def test_sync_orchestrator_incremental_sync(mock_api_client, mock_storage_client):
    """Test incremental sync functionality."""
    orchestrator = SyncOrchestrator(
        api_client=mock_api_client,
        storage_client=mock_storage_client
    )
    
    stats = await orchestrator.sync(
        sync_type="incremental",
        project_names=["test-project"]
    )
    
    assert stats["sync_type"] == "incremental"
    assert "cutoff_time" in stats
    assert stats["lookback_hours"] == 24


@pytest.mark.asyncio
async def test_full_sync_strategy(mock_api_client, mock_storage_client):
    """Test full sync strategy."""
    strategy = FullSyncStrategy(mock_api_client, mock_storage_client)
    
    stats = await strategy.sync(
        project_names=["test-project"],
        entity_types=["project", "user"]
    )
    
    assert stats["sync_type"] == "full"
    assert "entity_stats" in stats
    assert isinstance(stats["errors"], list)


@pytest.mark.asyncio
async def test_incremental_sync_strategy(mock_api_client, mock_storage_client):
    """Test incremental sync strategy."""
    strategy = IncrementalSyncStrategy(
        mock_api_client,
        mock_storage_client,
        lookback_hours=12
    )
    
    stats = await strategy.sync(project_names=["test-project"])
    
    assert stats["sync_type"] == "incremental"
    assert stats["lookback_hours"] == 12


def test_paginated_response():
    """Test PaginatedResponse class."""
    response = PaginatedResponse(
        items=[1, 2, 3],
        total=10,
        page=0,
        size=3
    )
    
    assert len(response.items) == 3
    assert response.total == 10
    assert response.has_next is True
    
    # Test last page
    last_page = PaginatedResponse(
        items=[10],
        total=10,
        page=3,
        size=3
    )
    assert last_page.has_next is False


@pytest.mark.asyncio
async def test_sync_error_handling(mock_api_client, mock_storage_client):
    """Test error handling during sync."""
    # Make API call fail
    mock_api_client.get_projects.side_effect = Exception("API Error")
    
    orchestrator = SyncOrchestrator(
        api_client=mock_api_client,
        storage_client=mock_storage_client
    )
    
    stats = await orchestrator.sync(
        sync_type="full",
        entity_types=["project"]
    )
    
    assert len(stats["errors"]) > 0
    assert stats["errors"][0]["entity"] == "project"


@pytest.mark.asyncio
async def test_storage_client_id_generation():
    """Test ChromaDB client ID generation."""
    client = ChromaDBClient()
    
    # Test different entity types
    launch_id = client._generate_id("launch", {"id": 123})
    assert launch_id == "launch:123"
    
    user_id = client._generate_id("user", {"userId": "testuser"})
    assert user_id == "user:testuser"
    
    project_id = client._generate_id("project", {"projectName": "test-proj"})
    assert project_id == "project:test-proj"


@pytest.mark.asyncio
async def test_storage_client_text_extraction():
    """Test text extraction for embeddings."""
    client = ChromaDBClient()
    
    # Test launch text extraction
    launch_text = client._extract_text_content("launch", {
        "name": "Test Launch",
        "description": "Launch description",
        "status": "PASSED",
        "attributes": [
            {"key": "build", "value": "123"},
            {"key": "branch", "value": "main"}
        ]
    })
    
    assert "Launch: Test Launch" in launch_text
    assert "Description: Launch description" in launch_text
    assert "Status: PASSED" in launch_text
    assert "build: 123" in launch_text
    assert "branch: main" in launch_text


if __name__ == "__main__":
    pytest.main([__file__, "-v"])