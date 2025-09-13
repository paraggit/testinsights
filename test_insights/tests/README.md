# TestInsight API Tests

Comprehensive test suite for the TestInsight API, covering all endpoints, models, configurations, and integration workflows.

## 🧪 Test Structure

```
test_insights/tests/
├── api/                    # API endpoint tests
│   ├── test_endpoints.py   # Individual endpoint tests
│   ├── test_integration.py # Integration workflow tests
│   └── test_models.py      # Pydantic model validation tests
├── config/                 # Configuration tests
│   └── test_settings.py    # Settings and environment variable tests
├── fixtures/               # Test fixtures and mock data
│   ├── mock_data.py        # Sample data for testing
│   └── test_client.py      # Test client and fixtures
└── conftest.py             # Pytest configuration and shared fixtures
```

## 🚀 Running Tests

### Quick Test Commands

```bash
# Quick smoke tests
poetry run python run_tests.py quick

# All tests
poetry run python run_tests.py --type all

# Specific test types
poetry run python run_tests.py --type api
poetry run python run_tests.py --type config
poetry run python run_tests.py --type integration

# With coverage
poetry run python run_tests.py --coverage

# Specific test file
poetry run python run_tests.py --file test_insights/tests/api/test_endpoints.py

# Pattern matching
poetry run python run_tests.py --pattern "test_query"
```

### Direct Pytest Commands

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=test_insights --cov-report=html

# Run specific test file
poetry run pytest test_insights/tests/api/test_endpoints.py

# Run tests by marker
poetry run pytest -m api
poetry run pytest -m unit
poetry run pytest -m integration

# Verbose output
poetry run pytest -v

# Stop on first failure
poetry run pytest -x
```

## 📋 Test Categories

### 🔗 API Endpoint Tests (`test_endpoints.py`)

Tests for all FastAPI endpoints:

- **Root Endpoint** (`/`) - Basic API information
- **Health Check** (`/health`) - Service health monitoring
- **Query Endpoint** (`/query`) - Natural language query processing
- **Search Endpoint** (`/search`) - Vector database search
- **Sync Endpoint** (`/sync`) - Data synchronization
- **Status Endpoint** (`/status`) - System status
- **Storage Endpoint** (`/storage`) - Storage management
- **Config Endpoint** (`/config`) - Configuration retrieval
- **Documentation Endpoints** - Swagger/ReDoc/OpenAPI

**Test Coverage:**

- ✅ Successful responses
- ✅ Error handling
- ✅ Input validation
- ✅ Different LLM providers
- ✅ Authentication scenarios
- ✅ Edge cases

### 🔄 Integration Tests (`test_integration.py`)

End-to-end workflow tests:

- **Slack Bot Workflows** - Complete chat bot interactions
- **Data Sync Workflows** - Initial setup, incremental sync, project-specific sync
- **Query Analysis Workflows** - Different query intents and provider switching
- **Search and Query Workflows** - Combined exploration and querying
- **Error Recovery Workflows** - Failure scenarios and recovery

### 📝 Model Tests (`test_models.py`)

Pydantic model validation:

- **Request Models** - `QueryRequest`, `SearchRequest`, `SyncRequest`
- **Response Models** - `QueryResponse`, `SearchResponse`, `SyncResponse`, etc.
- **Field Validation** - String lengths, integer ranges, optional fields
- **Example Validation** - All model examples are valid
- **Error Scenarios** - Validation error handling

### ⚙️ Configuration Tests (`test_settings.py`)

Settings and environment configuration:

- **Default Values** - Proper default settings
- **Environment Overrides** - Environment variable precedence
- **Type Validation** - Boolean, integer, float parsing
- **Helper Methods** - Configuration utility methods
- **Path Handling** - File path settings
- **Provider Configurations** - LLM and service configurations

## 🎯 Test Fixtures

### Mock Data (`fixtures/mock_data.py`)

Realistic test data:

- Mock search results
- RAG pipeline responses
- Sync statistics
- Storage status
- Error scenarios
- Slack bot queries

### Test Client (`fixtures/test_client.py`)

Pre-configured test clients:

- `client_with_mocks` - Fully mocked dependencies
- `mock_storage_client` - ChromaDB mock
- `mock_sync_orchestrator` - Sync service mock
- `mock_llm_provider` - LLM provider mocks
- `mock_rag_pipeline` - RAG pipeline mock

## 🏷️ Test Markers

Use pytest markers to run specific test categories:

```bash
# Unit tests only
poetry run pytest -m unit

# Integration tests only
poetry run pytest -m integration

# API endpoint tests
poetry run pytest -m api

# Configuration tests
poetry run pytest -m config

# Skip slow tests
poetry run pytest -m "not slow"

# Tests requiring LLM
poetry run pytest -m requires_llm

# Tests requiring storage
poetry run pytest -m requires_storage
```

## 📊 Coverage Reports

Generate detailed coverage reports:

```bash
# HTML coverage report
poetry run python run_tests.py --coverage

# View coverage report
open htmlcov/index.html

# Terminal coverage report
poetry run pytest --cov=test_insights --cov-report=term-missing
```

**Coverage Goals:**

- Overall: > 90%
- API endpoints: > 95%
- Models: > 98%
- Configuration: > 85%

## 🔧 Test Configuration

### Pytest Configuration (`pyproject.toml`)

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["test_insights/tests"]
addopts = ["--strict-markers", "--disable-warnings"]
markers = [
    "unit: Unit tests",
    "integration: Integration tests",
    "api: API endpoint tests",
    "config: Configuration tests",
    "slow: Slow-running tests",
]
```

### Environment Variables

Test-specific environment variables are set in `conftest.py`:

```python
test_env = {
    "REPORTPORTAL_URL": "https://test.reportportal.com",
    "REPORTPORTAL_API_TOKEN": "test_token_12345",
    "LLM_PROVIDER": "openai",
    "DEV_MODE": "true",
}
```

## 🎭 Mocking Strategy

### API Dependencies

All external dependencies are mocked:

- **ChromaDB Client** - Vector database operations
- **Sync Orchestrator** - ReportPortal synchronization
- **LLM Providers** - OpenAI, Anthropic, Ollama
- **RAG Pipeline** - Query processing

### Mock Consistency

Mocks return realistic data:

- Proper response formats
- Realistic timing
- Error scenarios
- Edge cases

## 🚨 Error Testing

Comprehensive error scenario coverage:

### Validation Errors

- Missing required fields
- Invalid field values
- Type mismatches
- Range violations

### Service Errors

- LLM provider failures
- Storage connectivity issues
- Sync failures
- Timeout scenarios

### Integration Errors

- Workflow interruptions
- Recovery scenarios
- Fallback mechanisms

## 🎯 Best Practices

### Test Organization

- **Descriptive test names** - Clear intent and expected outcome
- **Logical grouping** - Related tests in same class
- **Proper fixtures** - Reusable test setup
- **Clean assertions** - Single concept per assertion

### Mock Usage

- **Realistic responses** - Mock data matches real API responses
- **Consistent behavior** - Mocks behave predictably
- **Error scenarios** - Test failure paths
- **Isolation** - Tests don't affect each other

### Performance

- **Fast execution** - Most tests run in milliseconds
- **Parallel execution** - Use `pytest-xdist` for speed
- **Selective running** - Use markers for targeted testing

## 🔍 Debugging Tests

### Verbose Output

```bash
# Detailed test output
poetry run pytest -v -s

# Show all output
poetry run pytest -v -s --capture=no

# Debug specific test
poetry run pytest -v -s test_insights/tests/api/test_endpoints.py::TestQueryEndpoint::test_query_basic
```

### Test Debugging

```bash
# Stop on first failure
poetry run pytest -x

# Drop into debugger on failure
poetry run pytest --pdb

# Show local variables in traceback
poetry run pytest --tb=long
```

## 📈 Continuous Integration

Tests are designed for CI/CD environments:

- **Fast execution** - Complete suite runs in < 30 seconds
- **Reliable mocking** - No external dependencies
- **Clear reporting** - Detailed failure information
- **Coverage tracking** - Automated coverage reports

### GitHub Actions Example

```yaml
- name: Run Tests
  run: |
    poetry install
    poetry run python run_tests.py --coverage

- name: Upload Coverage
  uses: codecov/codecov-action@v3
  with:
    file: ./coverage.xml
```

## 🎉 Test Results

Current test metrics:

- **✅ 100+ test cases** covering all functionality
- **🎯 >95% code coverage** for API endpoints
- **⚡ <30 second** full test suite execution
- **🔄 100% async** test compatibility
- **🎭 Comprehensive mocking** of all external dependencies

The test suite ensures that your TestInsight API is robust, reliable, and ready for production deployment!
