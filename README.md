

## Project Structure

reportportal_ai-assistant/
├── pyproject.toml
├── README.md
├── .env.example
├── .gitignore
├── src/
│   └── reportportal_ai/
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
git clone https://github.com/yourusername/reportportal_ai-assistant.git
cd reportportal_ai-assistant
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
poetry run reportportal_ai config init
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
poetry run reportportal_ai sync run --full
```

**Incremental Sync** - Update only changed data (default):
```bash
poetry run reportportal_ai sync run
```

**Sync Specific Projects**:
```bash
poetry run reportportal_ai sync run -p project1 -p project2
```

**Sync Specific Entity Types**:
```bash
poetry run reportportal_ai sync run -e launch -e test_item
```

**Check Sync Status**:
```bash
poetry run reportportal_ai sync status
```

#### Storage Commands

**Search Vector Database**:
```bash
poetry run reportportal_ai storage search "failed test with timeout error"
```

**Search with Filters**:
```bash
poetry run reportportal_ai storage search "error" -e log -e test_item -n 20
```

**Clear All Data**:
```bash
poetry run reportportal_ai storage clear
```

#### Configuration Commands

**Show Current Configuration**:
```bash
poetry run reportportal_ai config show
```

### Python API

You can also use the synchronization features programmatically:

```python
import asyncio
from reportportal_ai.data_sync.sync.orchestrator import SyncOrchestrator

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
src/reportportal_ai/
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