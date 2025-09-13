"""Test API endpoints."""

from unittest.mock import AsyncMock, patch

from fastapi import status
from fastapi.testclient import TestClient

from test_insights.tests.fixtures.mock_data import (
    SAMPLE_QUERY_REQUEST,
    SAMPLE_SEARCH_REQUEST,
    SAMPLE_SYNC_REQUEST,
    get_mock_rag_response,
    get_mock_search_results,
    get_mock_status_response,
    get_mock_sync_stats,
)


class TestRootEndpoint:
    """Test root endpoint."""

    def test_root_endpoint(self, client_with_mocks: TestClient):
        """Test root endpoint returns basic info."""
        response = client_with_mocks.get("/")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "docs" in data
        assert data["message"] == "TestInsight API"


class TestHealthEndpoint:
    """Test health check endpoint."""

    def test_health_check_success(self, client_with_mocks: TestClient):
        """Test successful health check."""
        response = client_with_mocks.get("/health")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "healthy"

    def test_health_check_failure(self, client_with_mocks: TestClient):
        """Test health check failure when storage is unavailable."""
        with patch("test_insights.api.app.storage_client") as mock_client:
            mock_client.get_collection_info.side_effect = Exception("Storage unavailable")

            response = client_with_mocks.get("/health")

            assert response.status_code == status.HTTP_500_OK  # Our custom error handler
            data = response.json()
            assert "error" in data
            assert "StorageError" in data.get("error_type", "")


class TestQueryEndpoint:
    """Test query endpoint."""

    def test_query_basic(self, client_with_mocks: TestClient):
        """Test basic query functionality."""
        mock_response = get_mock_rag_response()

        with patch("test_insights.rag.rag_pipeline.RAGPipeline") as mock_rag_class:
            mock_rag = AsyncMock()
            mock_rag.query.return_value = mock_response
            mock_rag_class.return_value = mock_rag

            response = client_with_mocks.post("/query", json=SAMPLE_QUERY_REQUEST)

            assert response.status_code == status.HTTP_200_OK
            data = response.json()

            assert "response" in data
            assert "analysis" in data
            assert "metrics" in data
            assert data["response"] == mock_response["response"]

    def test_query_with_different_providers(self, client_with_mocks: TestClient):
        """Test query with different LLM providers."""
        providers = ["openai", "anthropic", "ollama"]

        for provider in providers:
            request_data = {**SAMPLE_QUERY_REQUEST, "provider": provider}
            mock_response = get_mock_rag_response()

            with patch("test_insights.rag.rag_pipeline.RAGPipeline") as mock_rag_class:
                mock_rag = AsyncMock()
                mock_rag.query.return_value = mock_response
                mock_rag_class.return_value = mock_rag

                response = client_with_mocks.post("/query", json=request_data)

                assert response.status_code == status.HTTP_200_OK
                data = response.json()
                assert "response" in data

    def test_query_validation_errors(self, client_with_mocks: TestClient):
        """Test query validation errors."""
        # Missing required field
        response = client_with_mocks.post("/query", json={})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

        # Invalid n_results
        invalid_request = {**SAMPLE_QUERY_REQUEST, "n_results": -1}
        response = client_with_mocks.post("/query", json=invalid_request)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

        # Query too long
        long_query_request = {**SAMPLE_QUERY_REQUEST, "query": "x" * 1000}
        response = client_with_mocks.post("/query", json=long_query_request)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_query_with_sources(self, client_with_mocks: TestClient):
        """Test query with show_sources enabled."""
        request_data = {**SAMPLE_QUERY_REQUEST, "show_sources": True}
        mock_response = get_mock_rag_response()

        with patch("test_insights.rag.rag_pipeline.RAGPipeline") as mock_rag_class:
            mock_rag = AsyncMock()
            mock_rag.query.return_value = mock_response
            mock_rag_class.return_value = mock_rag

            response = client_with_mocks.post("/query", json=request_data)

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert "search_results" in data
            assert data["search_results"] is not None

    def test_query_ollama_provider(self, client_with_mocks: TestClient):
        """Test query with Ollama provider (async context manager)."""
        request_data = {**SAMPLE_QUERY_REQUEST, "provider": "ollama"}
        mock_response = get_mock_rag_response()

        with patch("test_insights.api.app.get_llm_provider") as mock_get_provider:
            mock_provider = AsyncMock()
            mock_provider.__aenter__ = AsyncMock(return_value=mock_provider)
            mock_provider.__aexit__ = AsyncMock(return_value=None)
            mock_get_provider.return_value = mock_provider

            with patch("test_insights.rag.rag_pipeline.RAGPipeline") as mock_rag_class:
                mock_rag = AsyncMock()
                mock_rag.query.return_value = mock_response
                mock_rag_class.return_value = mock_rag

                response = client_with_mocks.post("/query", json=request_data)

                assert response.status_code == status.HTTP_200_OK
                data = response.json()
                assert "response" in data


class TestSearchEndpoint:
    """Test search endpoint."""

    def test_search_basic(self, client_with_mocks: TestClient):
        """Test basic search functionality."""
        mock_results = get_mock_search_results()

        with patch("test_insights.api.app.storage_client") as mock_client:
            mock_client.query.return_value = mock_results

            response = client_with_mocks.post("/search", json=SAMPLE_SEARCH_REQUEST)

            assert response.status_code == status.HTTP_200_OK
            data = response.json()

            assert "results" in data
            assert "total_found" in data
            assert data["total_found"] == len(mock_results)

    def test_search_with_entity_types(self, client_with_mocks: TestClient):
        """Test search with entity type filtering."""
        request_data = {**SAMPLE_SEARCH_REQUEST, "entity_types": ["test_item", "log"]}
        mock_results = get_mock_search_results()

        with patch("test_insights.api.app.storage_client") as mock_client:
            mock_client.query.return_value = mock_results

            response = client_with_mocks.post("/search", json=request_data)

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert "results" in data

    def test_search_validation_errors(self, client_with_mocks: TestClient):
        """Test search validation errors."""
        # Missing required field
        response = client_with_mocks.post("/search", json={})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

        # Invalid limit
        invalid_request = {**SAMPLE_SEARCH_REQUEST, "limit": -1}
        response = client_with_mocks.post("/search", json=invalid_request)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_search_empty_results(self, client_with_mocks: TestClient):
        """Test search with no results."""
        with patch("test_insights.api.app.storage_client") as mock_client:
            mock_client.query.return_value = []

            response = client_with_mocks.post("/search", json=SAMPLE_SEARCH_REQUEST)

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["results"] == []
            assert data["total_found"] == 0


class TestSyncEndpoint:
    """Test sync endpoint."""

    def test_sync_incremental(self, client_with_mocks: TestClient):
        """Test incremental sync."""
        mock_stats = get_mock_sync_stats()

        with patch("test_insights.api.app.sync_orchestrator") as mock_orchestrator:
            mock_orchestrator.sync.return_value = mock_stats

            response = client_with_mocks.post("/sync", json={"full": False})

            assert response.status_code == status.HTTP_200_OK
            data = response.json()

            assert data["success"] is True
            assert "incremental" in data["message"]
            assert "stats" in data

    def test_sync_full(self, client_with_mocks: TestClient):
        """Test full sync."""
        mock_stats = get_mock_sync_stats()

        with patch("test_insights.api.app.sync_orchestrator") as mock_orchestrator:
            mock_orchestrator.sync.return_value = mock_stats

            response = client_with_mocks.post("/sync", json={"full": True})

            assert response.status_code == status.HTTP_200_OK
            data = response.json()

            assert data["success"] is True
            assert "full" in data["message"]

    def test_sync_with_projects(self, client_with_mocks: TestClient):
        """Test sync with specific projects."""
        mock_stats = get_mock_sync_stats()

        with patch("test_insights.api.app.sync_orchestrator") as mock_orchestrator:
            mock_orchestrator.sync.return_value = mock_stats

            response = client_with_mocks.post("/sync", json=SAMPLE_SYNC_REQUEST)

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["success"] is True

    def test_sync_failure(self, client_with_mocks: TestClient):
        """Test sync failure handling."""
        with patch("test_insights.api.app.sync_orchestrator") as mock_orchestrator:
            mock_orchestrator.sync.side_effect = Exception("Sync failed")

            response = client_with_mocks.post("/sync", json={"full": False})

            assert response.status_code == status.HTTP_200_OK
            data = response.json()

            assert data["success"] is False
            assert "Sync failed" in data["message"]


class TestStatusEndpoint:
    """Test status endpoint."""

    def test_status_success(self, client_with_mocks: TestClient):
        """Test successful status check."""
        mock_status = get_mock_status_response()

        with patch("test_insights.api.app.sync_orchestrator") as mock_orchestrator:
            mock_orchestrator.get_sync_status.return_value = mock_status

            response = client_with_mocks.get("/status")

            assert response.status_code == status.HTTP_200_OK
            data = response.json()

            assert data["status"] == "operational"
            assert "storage_stats" in data
            assert "last_sync" in data

    def test_status_failure(self, client_with_mocks: TestClient):
        """Test status check failure."""
        with patch("test_insights.api.app.sync_orchestrator") as mock_orchestrator:
            mock_orchestrator.get_sync_status.side_effect = Exception("Status check failed")

            response = client_with_mocks.get("/status")

            assert response.status_code == status.HTTP_500_OK  # Our custom error handler
            data = response.json()
            assert "error" in data


class TestStorageEndpoint:
    """Test storage management endpoint."""

    def test_clear_storage_success(self, client_with_mocks: TestClient):
        """Test successful storage clearing."""
        with patch("test_insights.api.app.storage_client") as mock_client:
            mock_client.delete_by_entity_type.return_value = 100

            response = client_with_mocks.delete("/storage")

            assert response.status_code == status.HTTP_200_OK
            data = response.json()

            assert "Successfully deleted" in data["message"]
            assert data["status"] == "completed"

    def test_clear_storage_failure(self, client_with_mocks: TestClient):
        """Test storage clearing failure."""
        with patch("test_insights.api.app.storage_client") as mock_client:
            mock_client.delete_by_entity_type.side_effect = Exception("Delete failed")

            response = client_with_mocks.delete("/storage")

            assert response.status_code == status.HTTP_500_OK  # Our custom error handler
            data = response.json()
            assert "error" in data


class TestConfigEndpoint:
    """Test configuration endpoint."""

    def test_get_config(self, client_with_mocks: TestClient):
        """Test get configuration."""
        response = client_with_mocks.get("/config")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Check that sensitive values are masked
        assert "reportportal_url" in data
        assert "api_token" in data
        assert data["api_token"].startswith("***")

        # Check that non-sensitive values are present
        assert "llm_provider" in data
        assert "embedding_model" in data


class TestDocumentationEndpoints:
    """Test documentation endpoints."""

    def test_openapi_json(self, client_with_mocks: TestClient):
        """Test OpenAPI JSON endpoint."""
        response = client_with_mocks.get("/openapi.json")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "info" in data
        assert "paths" in data
        assert data["info"]["title"] == "TestInsight API"

    def test_swagger_docs(self, client_with_mocks: TestClient):
        """Test Swagger documentation endpoint."""
        response = client_with_mocks.get("/docs")

        assert response.status_code == status.HTTP_200_OK
        assert "text/html" in response.headers["content-type"]

    def test_redoc_docs(self, client_with_mocks: TestClient):
        """Test ReDoc documentation endpoint."""
        response = client_with_mocks.get("/redoc")

        assert response.status_code == status.HTTP_200_OK
        assert "text/html" in response.headers["content-type"]


class TestErrorHandling:
    """Test error handling scenarios."""

    def test_404_not_found(self, client_with_mocks: TestClient):
        """Test 404 error handling."""
        response = client_with_mocks.get("/nonexistent")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_method_not_allowed(self, client_with_mocks: TestClient):
        """Test 405 method not allowed."""
        response = client_with_mocks.post("/health")
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_large_request_body(self, client_with_mocks: TestClient):
        """Test handling of large request bodies."""
        large_query = "x" * 10000  # Very large query
        request_data = {**SAMPLE_QUERY_REQUEST, "query": large_query}

        response = client_with_mocks.post("/query", json=request_data)
        # Should be rejected by validation
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
