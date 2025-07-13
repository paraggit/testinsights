

## Project Structure

test_insights-assistant/
├── pyproject.toml
├── README.md
├── .env.example
├── .gitignore
├── src/
│   └── test_insights/
│       ├── __init__.py
│       ├── config/
│       │   ├── __init__.py
│       │   └── settings.py
│       ├── core/
│       │   ├── __init__.py
│       │   ├── exceptions.py
│       │   └── logging.py
│       ├── data_sync/
│       │   ├── __init__.py
│       │   ├── api/
│       │   │   ├── __init__.py
│       │   │   ├── client.py
│       │   │   └── models.py
│       │   ├── storage/
│       │   │   ├── __init__.py
│       │   │   ├── chromadb_client.py
│       │   │   └── embeddings.py
│       │   ├── sync/
│       │   │   ├── __init__.py
│       │   │   ├── orchestrator.py
│       │   │   ├── strategies.py
│       │   │   └── transformers.py
│       │   └── utils/
│       │       ├── __init__.py
│       │       └── helpers.py
│       ├── llm/  # Future feature
│       │   └── __init__.py
│       └── rag/  # Future feature
│           └── __init__.py
└── tests/
    ├── __init__.py
    ├── conftest.py
    └── data_sync/
        ├── __init__.py
        └── test_sync.py


# ReportPortal AI Assistant

An AI-powered assistant for ReportPortal that syncs data to a vector database (ChromaDB) for intelligent search and analysis. This project is designed as a modular component of a larger AI system that will include LLM interfaces, RAG models, and other AI-driven features.

## Features

- **Full Data Synchronization**: Complete sync of all ReportPortal data
- **Incremental Updates**: Efficient sync of only changed data
- **Vector Storage**: Store data in ChromaDB with embeddings for semantic search
- **Modular Architecture**: Designed to integrate with future AI components
- **CLI Interface**: Easy-to-use command-line interface
- **Configurable**: Flexible configuration via environment variables
- **Rate Limiting**: Respect API rate limits with built-in throttling
- **Error Handling**: Robust error handling with retries

## Installation

### Prerequisites

- Python 3.9 or higher
- Poetry for dependency management
- Access to a ReportPortal instance
- API token for ReportPortal

### Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/test_insights-assistant.git
cd test_insights-assistant
```

2. Install dependencies using Poetry:
```bash
poetry install
```

3. Copy the example environment file and configure:
```bash
cp .env.example .env
# Edit .env with your ReportPortal credentials
```

4. Initialize configuration (optional):
```bash
poetry run test_insights config init
```

## Configuration

Configure the application using environment variables in the `.env` file:

- `REPORTPORTAL_URL`: Your ReportPortal instance URL
- `REPORTPORTAL_API_TOKEN`: API authentication token
- `REPORTPORTAL_PROJECT`: Default project name (optional)
- `CHROMA_PERSIST_DIRECTORY`: Directory for ChromaDB storage
- `SYNC_BATCH_SIZE`: Number of items to sync per batch
- `SYNC_RATE_LIMIT`: API requests per second limit

## Usage

### Command Line Interface

The application provides a CLI with several commands:

#### Sync Commands

**Full Sync** - Replace all data:
```bash
poetry run test_insights sync run --full --project OCS   
```

**Incremental Sync** - Update only changed data (default):
```bash
poetry run test_insights sync run --project OCS   
```

**Sync Specific Projects**:
```bash
poetry run test_insights sync run -p project1 -p project2
```

**Sync Specific Entity Types**:
```bash
poetry run test_insights sync run -e launch -e test_item
```

**Check Sync Status**:
```bash
poetry run test_insights sync status
```

#### Storage Commands

**Search Vector Database**:
```bash
poetry run test_insights storage search "failed test with timeout error"
```

**Search with Filters**:
```bash
poetry run test_insights storage search "error" -e log -e test_item -n 20
```

**Clear All Data**:
```bash
poetry run test_insights storage clear
```

#### Configuration Commands

**Show Current Configuration**:
```bash
poetry run test_insights config show
```

### Python API

You can also use the synchronization features programmatically:

```python
import asyncio
from test_insights.data_sync.sync.orchestrator import SyncOrchestrator

async def main():
    orchestrator = SyncOrchestrator()
    
    # Run full sync
    stats = await orchestrator.sync(
        sync_type="full",
        project_names=["my-project"],
        entity_types=["launch", "test_item", "log"]
    )
    
    print(f"Synced {stats['entity_stats']} entities")

asyncio.run(main())
```

## Architecture

The project follows a modular architecture designed for extensibility:

```
src/test_insights/
├── config/          # Configuration management
├── core/            # Core utilities and exceptions
├── data_sync/       # Data synchronization module
│   ├── api/         # ReportPortal API client
│   ├── storage/     # ChromaDB storage layer
│   └── sync/        # Synchronization strategies
├── llm/             # Future: LLM integration
└── rag/             # Future: RAG implementation
```

### Key Components

1. **API Client**: Async HTTP client for ReportPortal API with rate limiting and retries
2. **Storage Client**: ChromaDB interface for vector storage and retrieval
3. **Sync Orchestrator**: Coordinates synchronization between API and storage
4. **Sync Strategies**: Full and incremental sync implementations

## Data Model

The system stores the following entity types:

- **Projects**: ReportPortal projects
- **Users**: User accounts and roles
- **Launches**: Test execution launches
- **Test Items**: Individual test cases and suites
- **Logs**: Error and warning logs from failed tests
- **Filters**: Saved search filters
- **Dashboards**: Dashboard configurations and widgets

Each entity is converted to embeddings using sentence transformers for semantic search capabilities.

## Development

### Running Tests

```bash
poetry run pytest
```

### Code Quality

```bash
# Format code
poetry run black src tests

# Sort imports
poetry run isort src tests

# Type checking
poetry run mypy src

# Linting
poetry run flake8 src tests
```

### Adding New Features

1. Create feature modules under appropriate directories
2. Implement sync strategies for new data types
3. Add CLI commands in `cli.py`
4. Update tests and documentation

## Future Enhancements

This module is designed as part of a larger AI assistant system. Future additions will include:

- **LLM Integration**: Natural language interface for querying ReportPortal data
- **RAG System**: Retrieval-augmented generation for intelligent responses
- **Anomaly Detection**: AI-driven test failure pattern recognition
- **Predictive Analytics**: Forecast test stability and failure trends
- **Automated Reporting**: Generate intelligent test reports and summaries

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and questions:
- Create an issue in the GitHub repository
- Check existing issues for solutions
- Refer to ReportPortal documentation for API details


# LLM Integration for ReportPortal AI Assistant

The LLM integration enables natural language querying of your ReportPortal test data using advanced language models. It combines vector search with AI-powered analysis to provide insights about test failures, trends, and patterns.

## Features

- **Natural Language Queries**: Ask questions in plain English about your test data
- **Multiple LLM Providers**: Support for OpenAI, Anthropic Claude, and local models via Ollama
- **Smart Query Understanding**: Automatically detects intent, time ranges, and entity types
- **Metrics Calculation**: Automatically calculates success rates, failure rates, and other metrics
- **Source Attribution**: See which test data was used to generate responses
- **Streaming Responses**: Real-time response streaming for better user experience

## Quick Start

### 1. Configure LLM Provider

Choose and configure one of the supported providers:

#### OpenAI (GPT-4)
```bash
# Add to .env file
OPENAI_API_KEY=your-api-key-here
LLM_PROVIDER=openai

# Or use CLI
poetry run test_insights query configure --openai-key YOUR_KEY
```

#### Anthropic (Claude)
```bash
# Add to .env file
ANTHROPIC_API_KEY=your-api-key-here
LLM_PROVIDER=anthropic

# Or use CLI
poetry run test_insights query configure --anthropic-key YOUR_KEY
```

#### Ollama (Local LLMs)
```bash
# Install and start Ollama
brew install ollama  # macOS
ollama serve

# Pull a model
ollama pull llama2

# Configure in .env
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama2
```

### 2. Sync Your Data

Before querying, make sure your ReportPortal data is synced:

```bash
poetry run test_insights sync run --project YOUR_PROJECT_NAME
```

### 3. Start Asking Questions

```bash
# Basic query
poetry run test_insights query ask "What tests failed today?"

# With sources
poetry run test_insights query ask "Find timeout errors in API tests" --show-sources

# Streaming response
poetry run test_insights query ask "Analyze test failure trends this week" --stream

# Use specific provider
poetry run test_insights query ask "Why are login tests failing?" --provider anthropic
```

## Example Queries

View example queries:
```bash
poetry run test_insights query examples
```

Common query patterns:

### Finding Failures
- "Show me all failed tests from the last 24 hours"
- "What tests failed with timeout errors?"
- "Find broken tests in the checkout module"

### Root Cause Analysis
- "Why did the login tests fail yesterday?"
- "What's causing the API test failures?"
- "Analyze the error patterns in failed tests"

### Trends and Metrics
- "What's the test failure trend over the last week?"
- "Calculate the success rate for API tests"
- "How many tests passed vs failed today?"

### Comparisons
- "Compare test results between this week and last week"
- "What's the difference in failure rates between environments?"

## Advanced Usage

### Python API

```python
import asyncio
from test_insights.llm.providers.openai_provider import OpenAIProvider
from test_insights.llm.rag_pipeline import RAGPipeline

async def query_tests():
    # Initialize provider
    llm = OpenAIProvider(model="gpt-4-turbo-preview")
    
    # Create RAG pipeline
    rag = RAGPipeline(llm)
    
    # Query with options
    result = await rag.query(
        "What are the most common test failures?",
        n_results=30,  # Retrieve more documents
        include_raw_results=True  # Include source documents
    )
    
    print(result['response'])
    print(f"Based on {len(result['search_results'])} documents")

asyncio.run(query_tests())
```

### Streaming Responses

```python
async def stream_response():
    llm = OpenAIProvider()
    rag = RAGPipeline(llm)
    
    result = await rag.query(
        "Provide a detailed analysis of test failures",
        stream=True
    )
    
    async for chunk in result['response']:
        print(chunk, end='', flush=True)
```

### Query with Feedback

```python
async def refine_query():
    llm = OpenAIProvider()
    rag = RAGPipeline(llm)
    
    # Initial query
    result = await rag.query("What tests are failing?")
    
    # Refine with feedback
    refined = await rag.query_with_feedback(
        query="What tests are failing?",
        previous_response=result['response'],
        feedback="I need more details about the error messages"
    )
    
    print(refined['response'])
```

## Configuration Options

### Environment Variables

```bash
# LLM Provider Selection
LLM_PROVIDER=openai  # openai, anthropic, or ollama

# Model Configuration
LLM_TEMPERATURE=0.7  # 0.0-1.0, higher = more creative
LLM_MAX_TOKENS=2000  # Maximum response length

# RAG Configuration
RAG_N_RESULTS=20  # Number of documents to retrieve
RAG_INCLUDE_RAW_RESULTS=false  # Include source docs in response

# Provider-Specific Settings
OPENAI_MODEL=gpt-4-turbo-preview
ANTHROPIC_MODEL=claude-3-opus-20240229
OLLAMA_MODEL=llama2
```

### Query Analysis

The system automatically analyzes queries to understand:

- **Intent**: count, analysis, trend, comparison, or search
- **Time Range**: "last 7 days", "yesterday", "this week"
- **Status Filter**: failed, passed, broken, skipped
- **Entity Types**: launches, tests, logs
- **Keywords**: Important terms for search

## Best Practices

1. **Be Specific**: Include test names, error messages, or time ranges
2. **Use Natural Language**: Ask questions as you would to a colleague
3. **Iterate**: Use feedback to refine responses
4. **Check Sources**: Use `--show-sources` to verify information
5. **Sync Regularly**: Keep data up-to-date with incremental syncs

## Troubleshooting

### No Results Found
- Ensure data is synced: `poetry run test_insights sync status`
- Check if the time range in your query matches available data
- Try broader search terms

### API Key Issues
- Verify API keys are set correctly in `.env`
- Check key permissions and quotas
- For OpenAI: Ensure GPT-4 access is enabled

### Ollama Connection Failed
- Check Ollama is running: `ollama serve`
- Verify the URL matches your setup
- Ensure the model is downloaded: `ollama pull llama2`

### Slow Responses
- Reduce `RAG_N_RESULTS` for faster retrieval
- Use a faster model (e.g., gpt-3.5-turbo)
- Enable streaming for perceived performance

## Security Considerations

- API keys are stored locally in `.env` file
- No data is sent to LLM providers except the query and retrieved context
- Use Ollama for completely local processing
- Sensitive test data remains in your local vector database