"""Mock data and fixtures for testing."""

from datetime import datetime, timedelta
from typing import Any, Dict, List


def get_mock_search_results() -> List[Dict[str, Any]]:
    """Get mock search results for testing."""
    return [
        {
            "document": "Test case: login_with_invalid_credentials failed with assertion error",
            "metadata": {
                "entity_type": "test_item",
                "status": "FAILED",
                "launch_name": "Nightly Tests",
                "item_name": "login_with_invalid_credentials",
                "project_name": "web-app",
                "start_time": "2024-01-15T10:30:00Z",
            },
            "distance": 0.1234,
        },
        {
            "document": "API timeout occurred during user authentication request",
            "metadata": {
                "entity_type": "log",
                "status": "FAILED",
                "launch_name": "API Tests",
                "item_name": "test_user_auth",
                "project_name": "api-service",
                "start_time": "2024-01-15T11:15:00Z",
            },
            "distance": 0.2567,
        },
        {
            "document": "Database connection successful, user profile loaded",
            "metadata": {
                "entity_type": "test_item",
                "status": "PASSED",
                "launch_name": "Database Tests",
                "item_name": "test_db_connection",
                "project_name": "backend",
                "start_time": "2024-01-15T09:45:00Z",
            },
            "distance": 0.3456,
        },
    ]


def get_mock_rag_response() -> Dict[str, Any]:
    """Get mock RAG pipeline response."""
    return {
        "response": "Based on the test data from the last 7 days, I found 23 failed "
        "tests across 3 different test suites. The main causes of failures were "
        "timeout errors (12 tests) and assertion failures (11 tests). The API "
        "test suite had the highest failure rate at 15%.",
        "analysis": {
            "intent": "search",
            "entity_types": ["test_item"],
            "time_filter": {"description": "last 7 days"},
            "status_filter": ["FAILED"],
            "keywords": ["failed", "tests", "last", "days"],
            "metrics_requested": True,
        },
        "metrics": {
            "total_items": 150,
            "failure_rate": 15.3,
            "success_rate": 84.7,
            "by_status": {"FAILED": 23, "PASSED": 127},
            "by_entity_type": {"test_item": 150},
        },
        "search_results": get_mock_search_results(),
        "model": "gpt-4-turbo-preview",
        "usage": {"total_tokens": 1250, "prompt_tokens": 800, "completion_tokens": 450},
    }


def get_mock_sync_stats() -> Dict[str, Any]:
    """Get mock synchronization statistics."""
    return {
        "entity_stats": {"launch": 5, "test_item": 150, "log": 75, "project": 3},
        "total_processed": 233,
        "errors": [],
        "duration_seconds": 45.67,
        "sync_type": "incremental",
        "timestamp": datetime.utcnow().isoformat(),
    }


def get_mock_storage_stats() -> Dict[str, Any]:
    """Get mock storage statistics."""
    return {
        "total_documents": 1250,
        "by_entity_type": {
            "test_item": 800,
            "launch": 150,
            "log": 300,
            "project": 5,
            "user": 10,
            "filter": 8,
            "dashboard": 2,
        },
        "last_updated": datetime.utcnow().isoformat(),
        "collection_name": "reportportal_data",
    }


def get_mock_status_response() -> Dict[str, Any]:
    """Get mock system status response."""
    return {
        "status": "operational",
        "storage_stats": get_mock_storage_stats(),
        "last_sync": (datetime.utcnow() - timedelta(hours=2)).isoformat(),
        "sync_type": "incremental",
        "version": "0.1.0",
        "uptime_seconds": 3600,
    }


def get_mock_config_response() -> Dict[str, Any]:
    """Get mock configuration response."""
    return {
        "reportportal_url": "https://reportportal.example.com",
        "reportportal_project": "web-app",
        "api_token": "***abc123",
        "llm_provider": "openai",
        "embedding_model": "all-MiniLM-L6-v2",
        "chroma_collection_name": "reportportal_data",
        "sync_batch_size": 100,
        "sync_rate_limit": 10,
        "api_host": "0.0.0.0",
        "api_port": 8000,
        "custom_api_title": "TestInsight API",
    }


# Sample request payloads for testing
SAMPLE_QUERY_REQUEST = {
    "query": "Show me failed tests from the last 7 days",
    "provider": "openai",
    "model": "gpt-4-turbo-preview",
    "stream": False,
    "show_sources": True,
    "n_results": 20,
}

SAMPLE_SEARCH_REQUEST = {
    "query": "timeout error",
    "entity_types": ["test_item", "log"],
    "limit": 10,
}

SAMPLE_SYNC_REQUEST = {
    "projects": ["web-app", "api-service"],
    "entity_types": ["launch", "test_item"],
    "full": False,
}

# Sample Slack bot queries
SLACK_BOT_QUERIES = [
    {
        "query": "What tests failed yesterday?",
        "context": "Daily standup question",
        "expected_intent": "search",
    },
    {
        "query": "Show me the success rate for API tests this week",
        "context": "Weekly metrics request",
        "expected_intent": "count",
    },
    {
        "query": "Why did the login tests fail?",
        "context": "Root cause analysis",
        "expected_intent": "analysis",
    },
    {
        "query": "Compare test results between this week and last week",
        "context": "Trend analysis",
        "expected_intent": "comparison",
    },
]

# Error scenarios for testing
ERROR_SCENARIOS = [
    {
        "name": "invalid_provider",
        "request": {"query": "test query", "provider": "invalid_provider"},
        "expected_error": "LLMProviderError",
    },
    {
        "name": "missing_query",
        "request": {"provider": "openai"},
        "expected_error": "ValidationError",
    },
    {
        "name": "invalid_n_results",
        "request": {"query": "test query", "n_results": -1},
        "expected_error": "ValidationError",
    },
    {
        "name": "query_too_long",
        "request": {"query": "x" * 1000},
        "expected_error": "ValidationError",
    },
]
