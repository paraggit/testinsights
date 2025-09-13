"""Test API models and validation."""

import pytest
from pydantic import ValidationError

from test_insights.api.models import (
    ErrorResponse,
    QueryRequest,
    QueryResponse,
    SearchRequest,
    SearchResponse,
    StatusResponse,
    SyncRequest,
    SyncResponse,
)


class TestQueryRequest:
    """Test QueryRequest model."""

    def test_valid_query_request(self):
        """Test valid query request creation."""
        request = QueryRequest(
            query="Show me failed tests",
            provider="openai",
            model="gpt-4-turbo-preview",
            stream=False,
            show_sources=True,
            n_results=20,
        )

        assert request.query == "Show me failed tests"
        assert request.provider == "openai"
        assert request.model == "gpt-4-turbo-preview"
        assert request.stream is False
        assert request.show_sources is True
        assert request.n_results == 20

    def test_query_request_defaults(self):
        """Test query request with default values."""
        request = QueryRequest(query="Test query")

        assert request.query == "Test query"
        assert request.provider is None
        assert request.model is None
        assert request.stream is False
        assert request.show_sources is False
        assert request.n_results == 20

    def test_query_request_validation(self):
        """Test query request validation."""
        # Missing required field
        with pytest.raises(ValidationError):
            QueryRequest()

        # Query too short
        with pytest.raises(ValidationError):
            QueryRequest(query="ab")  # min_length=3

        # Query too long
        with pytest.raises(ValidationError):
            QueryRequest(query="x" * 501)  # max_length=500

        # Invalid n_results
        with pytest.raises(ValidationError):
            QueryRequest(query="test", n_results=0)  # ge=1

        with pytest.raises(ValidationError):
            QueryRequest(query="test", n_results=51)  # le=50

    def test_query_request_examples(self):
        """Test that model has examples configured."""
        assert hasattr(QueryRequest, "model_config")
        config = QueryRequest.model_config
        assert "json_schema_extra" in config
        assert "examples" in config["json_schema_extra"]

        examples = config["json_schema_extra"]["examples"]
        assert len(examples) > 0

        # Test that examples are valid
        for example in examples:
            request = QueryRequest(**example)
            assert request.query is not None


class TestSearchRequest:
    """Test SearchRequest model."""

    def test_valid_search_request(self):
        """Test valid search request creation."""
        request = SearchRequest(
            query="timeout error",
            entity_types=["test_item", "log"],
            limit=10,
        )

        assert request.query == "timeout error"
        assert request.entity_types == ["test_item", "log"]
        assert request.limit == 10

    def test_search_request_defaults(self):
        """Test search request with default values."""
        request = SearchRequest(query="test")

        assert request.query == "test"
        assert request.entity_types is None
        assert request.limit == 10

    def test_search_request_validation(self):
        """Test search request validation."""
        # Missing required field
        with pytest.raises(ValidationError):
            SearchRequest()

        # Query too short
        with pytest.raises(ValidationError):
            SearchRequest(query="a")  # min_length=2

        # Query too long
        with pytest.raises(ValidationError):
            SearchRequest(query="x" * 201)  # max_length=200

        # Invalid limit
        with pytest.raises(ValidationError):
            SearchRequest(query="test", limit=0)  # ge=1

        with pytest.raises(ValidationError):
            SearchRequest(query="test", limit=101)  # le=100


class TestSyncRequest:
    """Test SyncRequest model."""

    def test_valid_sync_request(self):
        """Test valid sync request creation."""
        request = SyncRequest(
            projects=["web-app", "api-service"],
            entity_types=["launch", "test_item"],
            full=True,
        )

        assert request.projects == ["web-app", "api-service"]
        assert request.entity_types == ["launch", "test_item"]
        assert request.full is True

    def test_sync_request_defaults(self):
        """Test sync request with default values."""
        request = SyncRequest()

        assert request.projects is None
        assert request.entity_types is None
        assert request.full is False

    def test_sync_request_all_optional(self):
        """Test that all fields are optional."""
        # Should not raise validation error
        request = SyncRequest()
        assert request.full is False


class TestQueryResponse:
    """Test QueryResponse model."""

    def test_valid_query_response(self):
        """Test valid query response creation."""
        response = QueryResponse(
            response="Test AI response",
            analysis={"intent": "search", "entity_types": ["test_item"]},
            metrics={"total_items": 100, "failure_rate": 15.0},
            search_results=[{"document": "test", "metadata": {}, "distance": 0.1}],
            model="gpt-4-turbo-preview",
            usage={"total_tokens": 150, "prompt_tokens": 100, "completion_tokens": 50},
        )

        assert response.response == "Test AI response"
        assert response.analysis["intent"] == "search"
        assert response.metrics["total_items"] == 100
        assert len(response.search_results) == 1
        assert response.model == "gpt-4-turbo-preview"
        assert response.usage["total_tokens"] == 150

    def test_query_response_minimal(self):
        """Test query response with only required fields."""
        response = QueryResponse(response="Minimal response")

        assert response.response == "Minimal response"
        assert response.analysis is None
        assert response.metrics is None
        assert response.search_results is None
        assert response.model is None
        assert response.usage is None

    def test_query_response_validation(self):
        """Test query response validation."""
        # Missing required field
        with pytest.raises(ValidationError):
            QueryResponse()


class TestSearchResponse:
    """Test SearchResponse model."""

    def test_valid_search_response(self):
        """Test valid search response creation."""
        results = [
            {"document": "test1", "metadata": {"type": "test"}, "distance": 0.1},
            {"document": "test2", "metadata": {"type": "log"}, "distance": 0.2},
        ]

        response = SearchResponse(results=results, total_found=2)

        assert len(response.results) == 2
        assert response.total_found == 2
        assert response.results[0]["document"] == "test1"

    def test_search_response_empty(self):
        """Test search response with no results."""
        response = SearchResponse(results=[], total_found=0)

        assert response.results == []
        assert response.total_found == 0

    def test_search_response_validation(self):
        """Test search response validation."""
        # Missing required fields
        with pytest.raises(ValidationError):
            SearchResponse()

        with pytest.raises(ValidationError):
            SearchResponse(results=[])  # Missing total_found


class TestSyncResponse:
    """Test SyncResponse model."""

    def test_valid_sync_response_success(self):
        """Test valid successful sync response."""
        response = SyncResponse(
            success=True,
            message="Sync completed successfully",
            stats={"entity_stats": {"test_item": 100}, "total_processed": 100},
            duration_seconds=45.67,
        )

        assert response.success is True
        assert response.message == "Sync completed successfully"
        assert response.stats["total_processed"] == 100
        assert response.duration_seconds == 45.67

    def test_valid_sync_response_failure(self):
        """Test valid failed sync response."""
        response = SyncResponse(
            success=False,
            message="Sync failed: Connection timeout",
            stats=None,
            duration_seconds=None,
        )

        assert response.success is False
        assert "Connection timeout" in response.message
        assert response.stats is None
        assert response.duration_seconds is None

    def test_sync_response_validation(self):
        """Test sync response validation."""
        # Missing required fields
        with pytest.raises(ValidationError):
            SyncResponse()

        with pytest.raises(ValidationError):
            SyncResponse(success=True)  # Missing message


class TestStatusResponse:
    """Test StatusResponse model."""

    def test_valid_status_response(self):
        """Test valid status response creation."""
        response = StatusResponse(
            status="operational",
            storage_stats={"total_documents": 1250, "by_entity_type": {"test_item": 800}},
            last_sync="2024-01-15T10:30:00Z",
            sync_type="incremental",
        )

        assert response.status == "operational"
        assert response.storage_stats["total_documents"] == 1250
        assert response.last_sync == "2024-01-15T10:30:00Z"
        assert response.sync_type == "incremental"

    def test_status_response_minimal(self):
        """Test status response with only required fields."""
        response = StatusResponse(status="operational")

        assert response.status == "operational"
        assert response.storage_stats is None
        assert response.last_sync is None
        assert response.sync_type is None

    def test_status_response_validation(self):
        """Test status response validation."""
        # Missing required field
        with pytest.raises(ValidationError):
            StatusResponse()


class TestErrorResponse:
    """Test ErrorResponse model."""

    def test_valid_error_response(self):
        """Test valid error response creation."""
        response = ErrorResponse(
            error="Something went wrong",
            detail="Additional error details",
            error_type="ValidationError",
        )

        assert response.error == "Something went wrong"
        assert response.detail == "Additional error details"
        assert response.error_type == "ValidationError"

    def test_error_response_minimal(self):
        """Test error response with only required fields."""
        response = ErrorResponse(error="Error occurred")

        assert response.error == "Error occurred"
        assert response.detail is None
        assert response.error_type is None

    def test_error_response_validation(self):
        """Test error response validation."""
        # Missing required field
        with pytest.raises(ValidationError):
            ErrorResponse()


class TestModelExamples:
    """Test that all models have proper examples configured."""

    def test_all_models_have_examples(self):
        """Test that all models have examples in their configuration."""
        models = [
            QueryRequest,
            SearchRequest,
            SyncRequest,
            QueryResponse,
            SearchResponse,
            SyncResponse,
            StatusResponse,
            ErrorResponse,
        ]

        for model_class in models:
            assert hasattr(
                model_class, "model_config"
            ), f"{model_class.__name__} missing model_config"
            config = model_class.model_config

            assert (
                "json_schema_extra" in config
            ), f"{model_class.__name__} missing json_schema_extra"
            schema_extra = config["json_schema_extra"]

            # Should have either 'example' or 'examples'
            has_examples = "example" in schema_extra or "examples" in schema_extra
            assert has_examples, f"{model_class.__name__} missing examples"

    def test_examples_are_valid(self):
        """Test that all examples can create valid model instances."""
        models_with_examples = [
            (QueryRequest, "examples"),
            (SearchRequest, "examples"),
            (SyncRequest, "examples"),
            (QueryResponse, "example"),
            (SearchResponse, "example"),
            (SyncResponse, "example"),
            (StatusResponse, "example"),
            (ErrorResponse, "example"),
        ]

        for model_class, example_key in models_with_examples:
            config = model_class.model_config
            schema_extra = config["json_schema_extra"]

            if example_key == "examples":
                examples = schema_extra["examples"]
                for example in examples:
                    # Should not raise validation error
                    instance = model_class(**example)
                    assert instance is not None
            else:
                example = schema_extra["example"]
                # Should not raise validation error
                instance = model_class(**example)
                assert instance is not None


class TestFieldValidation:
    """Test specific field validation rules."""

    def test_string_length_validation(self):
        """Test string length validation across models."""
        # QueryRequest query field
        with pytest.raises(ValidationError):
            QueryRequest(query="ab")  # Too short

        with pytest.raises(ValidationError):
            QueryRequest(query="x" * 501)  # Too long

        # SearchRequest query field
        with pytest.raises(ValidationError):
            SearchRequest(query="a")  # Too short

        with pytest.raises(ValidationError):
            SearchRequest(query="x" * 201)  # Too long

    def test_integer_range_validation(self):
        """Test integer range validation."""
        # QueryRequest n_results field
        with pytest.raises(ValidationError):
            QueryRequest(query="test", n_results=0)  # Below minimum

        with pytest.raises(ValidationError):
            QueryRequest(query="test", n_results=51)  # Above maximum

        # SearchRequest limit field
        with pytest.raises(ValidationError):
            SearchRequest(query="test", limit=0)  # Below minimum

        with pytest.raises(ValidationError):
            SearchRequest(query="test", limit=101)  # Above maximum

    def test_optional_fields(self):
        """Test optional field handling."""
        # All optional fields should accept None
        request = QueryRequest(
            query="test",
            provider=None,
            model=None,
        )
        assert request.provider is None
        assert request.model is None

    def test_list_fields(self):
        """Test list field validation."""
        # Empty lists should be valid
        request = SearchRequest(query="test", entity_types=[])
        assert request.entity_types == []

        # Lists with valid values
        request = SearchRequest(query="test", entity_types=["test_item", "log"])
        assert request.entity_types == ["test_item", "log"]
