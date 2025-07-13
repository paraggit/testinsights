# ReportPortal AI Assistant

An intelligent assistant for ReportPortal that syncs test data to a vector database and enables natural language querying using Large Language Models (LLMs). This tool helps you analyze test failures, identify patterns, and get insights from your ReportPortal data using simple English questions.

## Features

- **Data Synchronization**: Sync ReportPortal data to ChromaDB vector database
- **Natural Language Queries**: Ask questions in plain English about your test data
- **Multiple LLM Support**: OpenAI GPT-4, Anthropic Claude, and local Ollama models
- **Full & Incremental Sync**: Efficient data synchronization strategies
- **Smart Search**: Vector-based semantic search for relevant test data
- **CLI Interface**: Easy-to-use command-line interface
- **Docker Support**: Containerized deployment options

## Installation & Setup

### Prerequisites

- Python 3.9 or higher
- Poetry for dependency management
- Access to a ReportPortal instance
- API token for ReportPortal
- LLM API key (OpenAI, Anthropic) or local Ollama setup

### 1. Clone and Install Dependencies

```bash
git clone <repository-url>
cd test_insights-assistant
poetry install
```

### 2. Environment Configuration

Copy the example environment file and configure your settings:

```bash
cp .env.example .env
```

Edit `.env` file with your configuration:

```bash
# ReportPortal Configuration
REPORTPORTAL_URL=https://your-reportportal-instance.com
REPORTPORTAL_API_TOKEN=your_api_token_here
REPORTPORTAL_PROJECT=your_default_project_name

# ChromaDB Configuration
CHROMA_PERSIST_DIRECTORY=./chroma_db
CHROMA_COLLECTION_NAME=reportportal_data

# LLM Provider (choose one)
LLM_PROVIDER=openai  # or anthropic, ollama

# OpenAI Configuration (if using OpenAI)
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4-turbo-preview

# Anthropic Configuration (if using Claude)
ANTHROPIC_API_KEY=your_anthropic_api_key
ANTHROPIC_MODEL=claude-3-opus-20240229

# Ollama Configuration (if using local LLM)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama2

# Sync Configuration
SYNC_BATCH_SIZE=100
SYNC_RATE_LIMIT=10
```

### 3. Initialize Configuration (Optional)

Run the configuration wizard:

```bash
poetry run test_insights config init
```

### 4. Verify Setup

Check your configuration:

```bash
poetry run test_insights config show
```

## Data Synchronization

### Full Synchronization

Sync all data from ReportPortal (replaces existing data):

```bash
# Sync all projects and entity types
poetry run test_insights sync run --full

# Sync specific project
poetry run test_insights sync run --full --project YOUR_PROJECT_NAME

# Sync specific entity types
poetry run test_insights sync run --full --project YOUR_PROJECT -e launch -e test_item -e log

# Sync multiple projects
poetry run test_insights sync run --full -p project1 -p project2
```

### Incremental Synchronization

Sync only recent changes (default behavior):

```bash
# Incremental sync (last 7 days by default)
poetry run test_insights sync run

# Incremental sync for specific project
poetry run test_insights sync run --project YOUR_PROJECT_NAME

# Multiple projects incremental sync
poetry run test_insights sync run -p project1 -p project2
```

### Sync Status and Monitoring

```bash
# Check sync status
poetry run test_insights sync status

# View storage statistics
poetry run test_insights storage search "test" --json-output
```

## Natural Language Querying

### Setup LLM Provider

Configure your preferred LLM provider:

```bash
# OpenAI setup
poetry run test_insights query configure --openai-key YOUR_KEY

# Anthropic setup
poetry run test_insights query configure --anthropic-key YOUR_KEY

# Ollama setup (requires Ollama running locally)
poetry run test_insights query configure --ollama-url http://localhost:11434
```

### Basic Queries

```bash
# Simple question
poetry run test_insights query ask "What tests failed today?"

# With source documents shown
poetry run test_insights query ask "Find timeout errors in API tests" --show-sources

# Streaming response
poetry run test_insights query ask "Analyze test failure trends this week" --stream

# Use specific provider
poetry run test_insights query ask "Why are login tests failing?" --provider anthropic
```

## Example Prompts and Use Cases

### 1. Test Failure Analysis

```bash
# Find recent failures
poetry run test_insights query ask "Show me all failed tests from the last 24 hours"

# Specific error types
poetry run test_insights query ask "Find tests that failed with timeout errors"

# Component-specific failures
poetry run test_insights query ask "What tests failed in the authentication module?"

# Pattern analysis
poetry run test_insights query ask "What are the most common error messages in failed tests?"
```

### 2. Root Cause Investigation

```bash
# Why questions
poetry run test_insights query ask "Why did the login tests fail yesterday?"

# Deep analysis
poetry run test_insights query ask "What's causing the API test failures? Analyze the error patterns"

# Infrastructure issues
poetry run test_insights query ask "Are there any database connection errors in the failed tests?"

# Environment-specific issues
poetry run test_insights query ask "Compare failures between staging and production environments"
```

### 3. Metrics and Statistics

```bash
# Success rates
poetry run test_insights query ask "What's the success rate for API tests this month?"

# Failure trends
poetry run test_insights query ask "What's the test failure trend over the last week?"

# Counts and totals
poetry run test_insights query ask "How many tests passed vs failed today?"

# Performance metrics
poetry run test_insights query ask "Which tests are taking the longest to run?"
```

### 4. Comparative Analysis

```bash
# Time-based comparisons
poetry run test_insights query ask "Compare test results between this week and last week"

# Component comparisons
poetry run test_insights query ask "Compare the failure rates between UI and API tests"

# Release comparisons
poetry run test_insights query ask "How do test results compare between version 1.2 and 1.3?"

# Environment comparisons
poetry run test_insights query ask "What's the difference in failure rates between dev and prod?"
```

### 5. Test History and Trends

```bash
# Historical analysis
poetry run test_insights query ask "Show me the history of the checkout flow tests"

# Stability analysis
poetry run test_insights query ask "Identify tests that pass and fail intermittently"

# Regression detection
poetry run test_insights query ask "Which tests started failing after the latest deployment?"

# Long-term trends
poetry run test_insights query ask "How has our overall test stability changed over the last month?"
```

### 6. Specific Test Investigation

```bash
# Individual test analysis
poetry run test_insights query ask "Tell me about the 'user_login_test' - when did it last pass?"

# Test suite analysis
poetry run test_insights query ask "Analyze all tests in the payment processing suite"

# Error log analysis
poetry run test_insights query ask "Show me the error logs for failed integration tests"

# Stack trace analysis
poetry run test_insights query ask "Find all tests with NullPointerException errors"
```

## Advanced Usage

### Storage Management

```bash
# Search vector database directly
poetry run test_insights storage search "failed test timeout" --limit 10

# Search with entity type filters
poetry run test_insights storage search "error" -e log -e test_item

# Clear all data
poetry run test_insights storage clear
```

### Python API Usage

```python
import asyncio
from test_insights import SyncOrchestrator, RAGPipeline
from test_insights.llm.providers.openai_provider import OpenAIProvider

async def main():
    # Sync data
    orchestrator = SyncOrchestrator()
    stats = await orchestrator.sync(
        sync_type="incremental",
        project_names=["my-project"]
    )

    # Query with LLM
    llm = OpenAIProvider()
    rag = RAGPipeline(llm)

    result = await rag.query("What tests failed today?")
    print(result['response'])

asyncio.run(main())
```

### Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up -d

# Run sync in container
docker-compose exec test_insights poetry run test_insights sync run

# Run queries in container
docker-compose exec test_insights poetry run test_insights query ask "What tests failed?"
```

## Tips for Effective Queries

1. **Be Specific**: Include test names, error types, or time ranges

   - ✅ "Find timeout errors in payment API tests from last 3 days"
   - ❌ "Show errors"

2. **Use Natural Language**: Ask as you would ask a colleague

   - ✅ "Why are the login tests failing after the latest deployment?"
   - ✅ "What's the pattern in database connection failures?"

3. **Include Context**: Mention specific modules, environments, or time periods

   - ✅ "Compare UI test stability between staging and production this week"
   - ✅ "Analyze error patterns in the checkout flow since Monday"

4. **Request Metrics**: Ask for specific measurements
   - ✅ "What's the failure rate for integration tests this month?"
   - ✅ "How many tests passed vs failed in the last build?"

## Troubleshooting

### Common Issues

**No data found:**

```bash
# Check if data is synced
poetry run test_insights sync status

# Try broader search terms
poetry run test_insights query ask "Show me any test results from today"
```

**LLM API errors:**

```bash
# Verify API keys
poetry run test_insights config show

# Test with different provider
poetry run test_insights query ask "test query" --provider ollama
```

**Sync issues:**

```bash
# Check ReportPortal connection
curl -H "Authorization: Bearer YOUR_TOKEN" "YOUR_REPORTPORTAL_URL/api/v1/project/list"

# Try smaller batch size
export SYNC_BATCH_SIZE=10
poetry run test_insights sync run
```

## Development

### Running Tests

```bash
poetry run pytest
```

### Code Quality

```bash
# Format code
poetry run black src tests

# Type checking
poetry run mypy src

# Linting
poetry run flake8 src tests
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

- Create an issue for bugs or feature requests
- Check existing issues for solutions
- Refer to ReportPortal documentation for API details
