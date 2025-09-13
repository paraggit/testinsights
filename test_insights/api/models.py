"""Pydantic models for FastAPI endpoints."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class QueryRequest(BaseModel):
    """Request model for natural language queries.

    This model defines the structure for querying ReportPortal test data using natural language.
    The AI will process your query and return insights based on your test execution data.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "query": "Show me failed tests from the last 7 days",
                    "provider": "openai",
                    "model": "gpt-4-turbo-preview",
                    "stream": False,
                    "show_sources": True,
                    "n_results": 20,
                },
                {
                    "query": "What's the success rate for API tests this week?",
                    "show_sources": False,
                    "n_results": 15,
                },
                {
                    "query": "Why did the login tests fail yesterday?",
                    "provider": "anthropic",
                    "show_sources": True,
                    "n_results": 25,
                },
            ]
        }
    )

    query: str = Field(
        ...,
        description="Natural language query about your test data",
        examples=[
            "What tests failed yesterday?",
            "Show me the success rate for API tests this week",
            "Why did the login tests fail?",
            "Find tests with timeout errors",
            "Compare test results between this week and last week",
            "What's the trend of test failures over the past month?",
        ],
        min_length=3,
        max_length=500,
    )
    provider: Optional[str] = Field(
        None,
        description="LLM provider to use for processing the query",
        examples=["openai", "anthropic", "ollama"],
    )
    model: Optional[str] = Field(
        None,
        description="Specific model to use (provider-dependent)",
        examples=["gpt-4-turbo-preview", "claude-3-opus-20240229", "llama2"],
    )
    stream: bool = Field(
        False, description="Enable streaming response for real-time chat interfaces"
    )
    show_sources: bool = Field(
        False, description="Include source documents and metadata in the response"
    )
    n_results: int = Field(
        20, description="Number of relevant documents to retrieve for context", ge=1, le=50
    )


class SearchRequest(BaseModel):
    """Request model for vector storage search.

    Perform semantic search across stored ReportPortal data without AI processing.
    This is useful for finding specific documents or data points.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"query": "timeout error", "entity_types": ["test_item", "log"], "limit": 10},
                {"query": "login authentication", "entity_types": ["test_item"], "limit": 5},
            ]
        }
    )

    query: str = Field(
        ...,
        description="Search query for semantic matching",
        examples=["timeout error", "login failed", "API response", "database connection"],
        min_length=2,
        max_length=200,
    )
    entity_types: Optional[List[str]] = Field(
        None,
        description="Filter results by ReportPortal entity types",
        examples=[["test_item"], ["launch", "test_item"], ["log"]],
    )
    limit: int = Field(10, description="Maximum number of results to return", ge=1, le=100)


class SyncRequest(BaseModel):
    """Request model for data synchronization.

    Trigger synchronization of data from ReportPortal to the local vector database.
    This is required before querying if you have new test data.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "projects": ["web-app", "api-service"],
                    "entity_types": ["launch", "test_item"],
                    "full": False,
                },
                {"full": True},
                {"projects": ["mobile-app"], "full": False},
            ]
        }
    )

    projects: Optional[List[str]] = Field(
        None,
        description="Specific project names to sync (if not specified, syncs all projects)",
        examples=[["web-app", "api-service"], ["mobile-app"]],
    )
    entity_types: Optional[List[str]] = Field(
        None,
        description="Specific entity types to sync (if not specified, syncs all types)",
        examples=[["launch", "test_item"], ["test_item", "log"]],
    )
    full: bool = Field(False, description="Perform full sync (true) or incremental sync (false)")


class QueryResponse(BaseModel):
    """Response model for natural language queries.

    Contains the AI-generated response along with metadata about the query processing.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "response": "Based on the test data from the last 7 days, I found 23 "
                "failed tests across 3 different test suites. The main causes of "
                "failures were timeout errors (12 tests) and assertion failures "
                "(11 tests). The API test suite had the highest failure rate at 15%.",
                "analysis": {
                    "intent": "search",
                    "entity_types": ["test_item"],
                    "time_filter": {"description": "last 7 days"},
                    "status_filter": ["FAILED"],
                },
                "metrics": {
                    "total_items": 150,
                    "failure_rate": 15.3,
                    "success_rate": 84.7,
                    "by_status": {"FAILED": 23, "PASSED": 127},
                },
                "model": "gpt-4-turbo-preview",
                "usage": {"total_tokens": 1250, "prompt_tokens": 800, "completion_tokens": 450},
            }
        }
    )

    response: str = Field(..., description="AI-generated response to your query")
    analysis: Optional[Dict[str, Any]] = Field(
        None, description="Metadata about how the query was analyzed and processed"
    )
    metrics: Optional[Dict[str, Any]] = Field(
        None, description="Calculated metrics and statistics from the retrieved data"
    )
    search_results: Optional[List[Dict[str, Any]]] = Field(
        None,
        description="Source documents used to generate the response (only if show_sources=true)",
    )
    model: Optional[str] = Field(
        None, description="The specific AI model that generated the response"
    )
    usage: Optional[Dict[str, Any]] = Field(
        None, description="Token usage statistics for the API call"
    )


class SearchResponse(BaseModel):
    """Response model for vector storage search.

    Contains the raw search results from the vector database.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "results": [
                    {
                        "document": "Test case: login_with_invalid_credentials failed with "
                        "assertion error",
                        "metadata": {
                            "entity_type": "test_item",
                            "status": "FAILED",
                            "launch_name": "Nightly Tests",
                            "item_name": "login_with_invalid_credentials",
                        },
                        "distance": 0.1234,
                    }
                ],
                "total_found": 15,
            }
        }
    )

    results: List[Dict[str, Any]] = Field(
        ..., description="List of matching documents with metadata and similarity scores"
    )
    total_found: int = Field(
        ..., description="Total number of results found (may be limited by the limit parameter)"
    )


class SyncResponse(BaseModel):
    """Response model for data synchronization.

    Contains the result of the synchronization operation.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "message": "Sync completed successfully (incremental)",
                "stats": {
                    "entity_stats": {"launch": 5, "test_item": 150, "log": 75},
                    "total_processed": 230,
                    "errors": [],
                },
                "duration_seconds": 45.67,
            }
        }
    )

    success: bool = Field(..., description="Whether the synchronization completed successfully")
    message: str = Field(..., description="Human-readable status message")
    stats: Optional[Dict[str, Any]] = Field(
        None, description="Detailed statistics about what was synchronized"
    )
    duration_seconds: Optional[float] = Field(
        None, description="How long the synchronization took to complete"
    )


class StatusResponse(BaseModel):
    """Response model for system status.

    Provides information about the current state of the system and data.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "operational",
                "storage_stats": {
                    "total_documents": 1250,
                    "by_entity_type": {"test_item": 800, "launch": 150, "log": 300},
                },
                "last_sync": "2024-01-15T10:30:00Z",
                "sync_type": "incremental",
            }
        }
    )

    status: str = Field(
        ...,
        description="Overall system status",
        examples=["operational", "degraded", "maintenance"],
    )
    storage_stats: Optional[Dict[str, Any]] = Field(
        None, description="Statistics about the stored data"
    )
    last_sync: Optional[str] = Field(
        None, description="Timestamp of the last successful synchronization"
    )
    sync_type: Optional[str] = Field(
        None, description="Type of the last sync operation", examples=["incremental", "full"]
    )


class ErrorResponse(BaseModel):
    """Error response model.

    Standard error response format for all API endpoints.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "error": "Failed to process query",
                "detail": "The specified LLM provider is not configured",
                "error_type": "LLMProviderError",
            }
        }
    )

    error: str = Field(..., description="Human-readable error message")
    detail: Optional[str] = Field(None, description="Additional technical details about the error")
    error_type: Optional[str] = Field(
        None,
        description="Specific error category",
        examples=["LLMProviderError", "StorageError", "SyncError", "ConfigurationError"],
    )
