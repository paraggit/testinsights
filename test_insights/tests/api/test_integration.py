"""Integration tests for API workflows."""

from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from test_insights.tests.fixtures.mock_data import (
    SLACK_BOT_QUERIES,
    get_mock_rag_response,
    get_mock_search_results,
    get_mock_sync_stats,
)


class TestSlackBotWorkflow:
    """Test typical Slack bot integration workflows."""

    def test_slack_bot_query_workflow(self, client_with_mocks: TestClient):
        """Test complete Slack bot query workflow."""
        # Simulate a Slack bot asking questions
        for query_data in SLACK_BOT_QUERIES:
            mock_response = get_mock_rag_response()
            mock_response["analysis"]["intent"] = query_data["expected_intent"]

            with patch("test_insights.rag.rag_pipeline.RAGPipeline") as mock_rag_class:
                mock_rag = AsyncMock()
                mock_rag.query.return_value = mock_response
                mock_rag_class.return_value = mock_rag

                # Make request (as Slack bot would)
                request_data = {
                    "query": query_data["query"],
                    "show_sources": False,  # Slack responses should be clean
                    "n_results": 15,
                }

                response = client_with_mocks.post("/query", json=request_data)

                assert response.status_code == 200
                data = response.json()

                # Verify response structure for Slack
                assert "response" in data
                assert "analysis" in data
                assert data["analysis"]["intent"] == query_data["expected_intent"]

                # Verify no sources in response (clean for Slack)
                if not request_data["show_sources"]:
                    assert data.get("search_results") is None

    def test_slack_bot_error_handling(self, client_with_mocks: TestClient):
        """Test Slack bot error handling scenarios."""
        error_scenarios = [
            {
                "request": {"query": ""},  # Empty query
                "expected_status": 422,
            },
            {
                "request": {"query": "x" * 1000},  # Too long query
                "expected_status": 422,
            },
            {
                "request": {"query": "test", "n_results": -1},  # Invalid n_results
                "expected_status": 422,
            },
        ]

        for scenario in error_scenarios:
            response = client_with_mocks.post("/query", json=scenario["request"])
            assert response.status_code == scenario["expected_status"]

            # Verify error response format is suitable for Slack
            if response.status_code != 200:
                data = response.json()
                assert "detail" in data or "error" in data


class TestDataSyncWorkflow:
    """Test data synchronization workflows."""

    def test_initial_setup_workflow(self, client_with_mocks: TestClient):
        """Test initial setup workflow for new installations."""
        # 1. Check system status (should show no data)
        with patch("test_insights.api.app.sync_orchestrator") as mock_orchestrator:
            mock_orchestrator.get_sync_status.return_value = {
                "storage_stats": {"total_documents": 0},
                "last_sync": None,
                "sync_type": None,
            }

            response = client_with_mocks.get("/status")
            assert response.status_code == 200
            data = response.json()
            assert data["storage_stats"]["total_documents"] == 0

        # 2. Perform initial full sync
        mock_stats = get_mock_sync_stats()
        mock_stats["sync_type"] = "full"

        with patch("test_insights.api.app.sync_orchestrator") as mock_orchestrator:
            mock_orchestrator.sync.return_value = mock_stats

            response = client_with_mocks.post("/sync", json={"full": True})
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "full" in data["message"]

        # 3. Check status after sync
        with patch("test_insights.api.app.sync_orchestrator") as mock_orchestrator:
            mock_orchestrator.get_sync_status.return_value = {
                "storage_stats": {"total_documents": 1250},
                "last_sync": "2024-01-15T10:30:00Z",
                "sync_type": "full",
            }

            response = client_with_mocks.get("/status")
            assert response.status_code == 200
            data = response.json()
            assert data["storage_stats"]["total_documents"] > 0

    def test_incremental_sync_workflow(self, client_with_mocks: TestClient):
        """Test incremental sync workflow for regular updates."""
        # Simulate regular incremental sync
        mock_stats = get_mock_sync_stats()
        mock_stats["sync_type"] = "incremental"
        mock_stats["entity_stats"] = {"test_item": 25, "log": 15}  # Smaller numbers

        with patch("test_insights.api.app.sync_orchestrator") as mock_orchestrator:
            mock_orchestrator.sync.return_value = mock_stats

            response = client_with_mocks.post("/sync", json={"full": False})
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "incremental" in data["message"]
            assert data["stats"]["sync_type"] == "incremental"

    def test_project_specific_sync_workflow(self, client_with_mocks: TestClient):
        """Test project-specific sync workflow."""
        # Sync specific projects only
        mock_stats = get_mock_sync_stats()
        mock_stats["projects_synced"] = ["web-app", "api-service"]

        with patch("test_insights.api.app.sync_orchestrator") as mock_orchestrator:
            mock_orchestrator.sync.return_value = mock_stats

            request_data = {
                "projects": ["web-app", "api-service"],
                "entity_types": ["launch", "test_item"],
                "full": False,
            }

            response = client_with_mocks.post("/sync", json=request_data)
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True


class TestQueryAnalysisWorkflow:
    """Test query analysis and processing workflows."""

    def test_different_query_intents(self, client_with_mocks: TestClient):
        """Test handling of different query intents."""
        intent_test_cases = [
            {
                "query": "How many tests failed yesterday?",
                "expected_intent": "count",
                "should_have_metrics": True,
            },
            {
                "query": "Why did the login test fail?",
                "expected_intent": "analysis",
                "should_have_metrics": False,
            },
            {
                "query": "Show me test trends over the last month",
                "expected_intent": "trend",
                "should_have_metrics": True,
            },
            {
                "query": "Compare this week vs last week",
                "expected_intent": "comparison",
                "should_have_metrics": True,
            },
        ]

        for case in intent_test_cases:
            mock_response = get_mock_rag_response()
            mock_response["analysis"]["intent"] = case["expected_intent"]

            if not case["should_have_metrics"]:
                mock_response["metrics"] = None

            with patch("test_insights.rag.rag_pipeline.RAGPipeline") as mock_rag_class:
                mock_rag = AsyncMock()
                mock_rag.query.return_value = mock_response
                mock_rag_class.return_value = mock_rag

                request_data = {
                    "query": case["query"],
                    "show_sources": True,
                    "n_results": 20,
                }

                response = client_with_mocks.post("/query", json=request_data)
                assert response.status_code == 200
                data = response.json()

                assert data["analysis"]["intent"] == case["expected_intent"]

                if case["should_have_metrics"]:
                    assert data["metrics"] is not None
                else:
                    assert data["metrics"] is None

    def test_provider_switching_workflow(self, client_with_mocks: TestClient):
        """Test switching between different LLM providers."""
        providers = ["openai", "anthropic", "ollama"]

        for provider in providers:
            mock_response = get_mock_rag_response()
            mock_response["model"] = f"test-{provider}-model"

            with patch("test_insights.rag.rag_pipeline.RAGPipeline") as mock_rag_class:
                mock_rag = AsyncMock()
                mock_rag.query.return_value = mock_response
                mock_rag_class.return_value = mock_rag

                request_data = {
                    "query": "Test query for different providers",
                    "provider": provider,
                    "show_sources": False,
                    "n_results": 15,
                }

                response = client_with_mocks.post("/query", json=request_data)
                assert response.status_code == 200
                data = response.json()

                assert data["model"] == f"test-{provider}-model"


class TestSearchAndQueryWorkflow:
    """Test combined search and query workflows."""

    def test_explore_then_query_workflow(self, client_with_mocks: TestClient):
        """Test workflow where user explores data then asks specific questions."""
        # 1. First, explore data with search
        mock_search_results = get_mock_search_results()

        with patch("test_insights.api.app.storage_client") as mock_client:
            mock_client.query.return_value = mock_search_results

            search_request = {
                "query": "timeout error",
                "entity_types": ["test_item", "log"],
                "limit": 10,
            }

            response = client_with_mocks.post("/search", json=search_request)
            assert response.status_code == 200
            search_data = response.json()

            assert len(search_data["results"]) > 0
            assert search_data["total_found"] > 0

        # 2. Based on search results, ask specific question
        mock_rag_response = get_mock_rag_response()
        mock_rag_response["search_results"] = mock_search_results

        with patch("test_insights.rag.rag_pipeline.RAGPipeline") as mock_rag_class:
            mock_rag = AsyncMock()
            mock_rag.query.return_value = mock_rag_response
            mock_rag_class.return_value = mock_rag

            query_request = {
                "query": "Why are there so many timeout errors in the API tests?",
                "show_sources": True,
                "n_results": 20,
            }

            response = client_with_mocks.post("/query", json=query_request)
            assert response.status_code == 200
            query_data = response.json()

            assert "response" in query_data
            assert query_data["search_results"] is not None
            assert len(query_data["search_results"]) > 0

    def test_iterative_query_refinement(self, client_with_mocks: TestClient):
        """Test iterative query refinement workflow."""
        # Simulate a user refining their queries based on results
        queries = [
            "Show me test failures",  # Broad initial query
            "Show me API test failures from yesterday",  # More specific
            "Why did the API authentication tests fail yesterday?",  # Very specific
        ]

        for i, query in enumerate(queries):
            mock_response = get_mock_rag_response()
            mock_response["analysis"]["keywords"] = query.lower().split()

            # Make responses more specific as queries get more specific
            if i == 0:
                mock_response["metrics"]["total_items"] = 100
            elif i == 1:
                mock_response["metrics"]["total_items"] = 25
            else:
                mock_response["metrics"]["total_items"] = 5

            with patch("test_insights.rag.rag_pipeline.RAGPipeline") as mock_rag_class:
                mock_rag = AsyncMock()
                mock_rag.query.return_value = mock_response
                mock_rag_class.return_value = mock_rag

                request_data = {
                    "query": query,
                    "show_sources": i == len(queries) - 1,  # Show sources for final query
                    "n_results": 20,
                }

                response = client_with_mocks.post("/query", json=request_data)
                assert response.status_code == 200
                data = response.json()

                # Verify results become more focused
                assert data["metrics"]["total_items"] <= 100


class TestErrorRecoveryWorkflow:
    """Test error recovery workflows."""

    def test_sync_failure_recovery(self, client_with_mocks: TestClient):
        """Test recovery from sync failures."""
        # 1. Attempt sync that fails
        with patch("test_insights.api.app.sync_orchestrator") as mock_orchestrator:
            mock_orchestrator.sync.side_effect = Exception("Connection timeout")

            response = client_with_mocks.post("/sync", json={"full": False})
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is False
            assert "Connection timeout" in data["message"]

        # 2. Check status to verify no data was corrupted
        with patch("test_insights.api.app.sync_orchestrator") as mock_orchestrator:
            mock_orchestrator.get_sync_status.return_value = {
                "storage_stats": {"total_documents": 1000},  # Previous data intact
                "last_sync": "2024-01-14T10:30:00Z",  # Old sync time
                "sync_type": "incremental",
            }

            response = client_with_mocks.get("/status")
            assert response.status_code == 200
            data = response.json()
            assert data["storage_stats"]["total_documents"] > 0

        # 3. Retry sync successfully
        mock_stats = get_mock_sync_stats()

        with patch("test_insights.api.app.sync_orchestrator") as mock_orchestrator:
            mock_orchestrator.sync.return_value = mock_stats

            response = client_with_mocks.post("/sync", json={"full": False})
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True

    def test_query_fallback_workflow(self, client_with_mocks: TestClient):
        """Test fallback when primary query method fails."""
        # 1. Try query with primary provider (fails)
        with patch("test_insights.api.app.get_llm_provider") as mock_get_provider:
            mock_get_provider.side_effect = Exception("API key invalid")

            request_data = {
                "query": "Show me test results",
                "provider": "openai",
                "show_sources": False,
                "n_results": 10,
            }

            response = client_with_mocks.post("/query", json=request_data)
            assert response.status_code == 500
            data = response.json()
            assert "error" in data

        # 2. Fallback to search for basic data exploration
        mock_search_results = get_mock_search_results()

        with patch("test_insights.api.app.storage_client") as mock_client:
            mock_client.query.return_value = mock_search_results

            search_request = {
                "query": "test results",
                "limit": 10,
            }

            response = client_with_mocks.post("/search", json=search_request)
            assert response.status_code == 200
            search_data = response.json()
            assert len(search_data["results"]) > 0

    def test_maintenance_mode_workflow(self, client_with_mocks: TestClient):
        """Test behavior during maintenance operations."""
        # 1. Clear storage (maintenance operation)
        with patch("test_insights.api.app.storage_client") as mock_client:
            mock_client.delete_by_entity_type.return_value = 1000

            response = client_with_mocks.delete("/storage")
            assert response.status_code == 200
            data = response.json()
            assert "Successfully deleted" in data["message"]

        # 2. Verify system status shows empty storage
        with patch("test_insights.api.app.sync_orchestrator") as mock_orchestrator:
            mock_orchestrator.get_sync_status.return_value = {
                "storage_stats": {"total_documents": 0},
                "last_sync": None,
                "sync_type": None,
            }

            response = client_with_mocks.get("/status")
            assert response.status_code == 200
            data = response.json()
            assert data["storage_stats"]["total_documents"] == 0

        # 3. Perform full resync
        mock_stats = get_mock_sync_stats()
        mock_stats["sync_type"] = "full"

        with patch("test_insights.api.app.sync_orchestrator") as mock_orchestrator:
            mock_orchestrator.sync.return_value = mock_stats

            response = client_with_mocks.post("/sync", json={"full": True})
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
