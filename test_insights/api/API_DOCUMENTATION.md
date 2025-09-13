# TestInsight API Documentation

TestInsight provides a FastAPI-based web API that allows Slack bots and other applications to query ReportPortal test data using natural language processing and AI.

## Quick Start

### 1. Install Dependencies

```bash
# Install FastAPI dependencies (if not already installed)
poetry install
```

### 2. Configure Environment

Create a `.env` file or use the configuration wizard:

```bash
test_insights config init
```

### 3. Start the API Server

Using the CLI command:

```bash
test_insights api start
```

Or using the standalone script:

```bash
python run_api.py
```

Or with custom options:

```bash
test_insights api start --host 0.0.0.0 --port 8080 --reload
```

### 4. Access API Documentation

Once the server is running, visit:

- Interactive API docs: http://localhost:8000/docs
- Alternative docs: http://localhost:8000/redoc

## API Endpoints

### Core Endpoints

#### `POST /query`

Process natural language queries about test data using AI.

**Request Body:**

```json
{
  "query": "Show me failed tests from the last 7 days",
  "provider": "openai", // optional: openai, anthropic, ollama
  "model": "gpt-4-turbo-preview", // optional
  "stream": false, // optional: enable streaming
  "show_sources": true, // optional: include source documents
  "n_results": 20 // optional: number of documents to retrieve
}
```

**Response:**

```json
{
  "response": "Based on the test data, here are the failed tests...",
  "analysis": {
    "intent": "search",
    "entity_types": ["test_item"],
    "time_filter": {...}
  },
  "metrics": {
    "failure_rate": 15.2,
    "total_items": 150
  },
  "search_results": [...],  // if show_sources=true
  "model": "gpt-4-turbo-preview",
  "usage": {
    "total_tokens": 1250,
    "prompt_tokens": 800,
    "completion_tokens": 450
  }
}
```

#### `POST /search`

Search vector storage for specific content.

**Request Body:**

```json
{
  "query": "timeout error",
  "entity_types": ["test_item", "log"], // optional filter
  "limit": 10
}
```

#### `POST /sync`

Trigger data synchronization with ReportPortal.

**Request Body:**

```json
{
  "projects": ["web-app", "api-service"], // optional: specific projects
  "entity_types": ["launch", "test_item"], // optional: specific entities
  "full": false // optional: full vs incremental sync
}
```

#### `GET /status`

Get system status and storage statistics.

#### `GET /health`

Health check endpoint.

#### `GET /config`

Get current configuration (sensitive values masked).

#### `DELETE /storage`

Clear all stored data (use with caution).

## Slack Bot Integration

The API is designed to work seamlessly with Slack bots. Here's how queries from Slack are typically processed:

### Example Slack Bot Query Flow

1. **User types in Slack:** `/test-insights "What tests failed yesterday?"`

2. **Slack bot calls API:**

   ```python
   import httpx

   async def handle_slack_command(query_text):
       async with httpx.AsyncClient() as client:
           response = await client.post(
               "http://your-api-server:8000/query",
               json={
                   "query": query_text,
                   "show_sources": False,  # Don't clutter Slack with sources
                   "n_results": 15
               }
           )
           return response.json()
   ```

3. **API processes and returns:** AI-generated response based on ReportPortal data

4. **Bot posts to Slack:** Formatted response with test insights

### Common Slack Query Patterns

The API handles various query types that are common in Slack:

- **Status queries:** "What's the test status for today?"
- **Failure analysis:** "Why did the login tests fail?"
- **Trend analysis:** "How are our test results trending?"
- **Specific searches:** "Find tests with timeout errors"
- **Comparisons:** "Compare this week vs last week"
- **Metrics:** "What's our success rate this month?"

## Query Parameters from CLI Interface

The API accepts the same parameters as the CLI interface:

### Query Command Parameters

- `query`: Natural language question
- `provider`: LLM provider (openai, anthropic, ollama)
- `model`: Specific model to use
- `stream`: Enable response streaming
- `show_sources`: Include source documents
- `n_results`: Number of documents to retrieve

### Search Command Parameters

- `query`: Search text
- `entity_types`: Filter by entity types
- `limit`: Number of results

### Sync Command Parameters

- `projects`: Specific projects to sync
- `entity_types`: Specific entity types to sync
- `full`: Full vs incremental sync

## Configuration

The API uses the same configuration as the CLI tool. Key settings:

```env
# ReportPortal
REPORTPORTAL_URL=https://your-reportportal.com
REPORTPORTAL_API_TOKEN=your-token
REPORTPORTAL_PROJECT=your-project

# LLM Provider
LLM_PROVIDER=openai
OPENAI_API_KEY=your-key

# Or use Anthropic
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=your-key

# Or use Ollama (local)
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama2

# Storage
CHROMA_PERSIST_DIRECTORY=./chroma_db
```

## Error Handling

The API provides consistent error responses:

```json
{
  "error": "Description of what went wrong",
  "error_type": "LLMProviderError",
  "detail": "Additional technical details"
}
```

Error types:

- `LLMProviderError`: Issues with AI providers
- `StorageError`: Vector database issues
- `SyncError`: ReportPortal synchronization issues
- `ConfigurationError`: Configuration problems
- `HTTPError`: Standard HTTP errors
- `InternalError`: Unexpected server errors

## Development

### Running in Development Mode

```bash
test_insights api start --reload --log-level debug
```

### Testing the API

Use the provided examples:

```bash
python test_insights/examples/api_usage_examples.py
```

Or test individual endpoints:

```bash
curl -X POST "http://localhost:8000/query" \
     -H "Content-Type: application/json" \
     -d '{"query": "Show me test failures", "show_sources": false}'
```

### Adding Custom Endpoints

To add new endpoints, modify `test_insights/api/app.py`:

1. Add request/response models to `test_insights/api/models.py`
2. Implement the endpoint function
3. Add appropriate error handling
4. Update this documentation

## Production Deployment

### Using Docker

```bash
# Build image
docker build -t testinsight-api .

# Run container
docker run -p 8000:8000 --env-file .env testinsight-api
```

### Using Docker Compose

The project includes a `docker-compose.yaml` that can be extended:

```yaml
services:
  api:
    build: .
    ports:
      - "8000:8000"
    env_file:
      - .env
    command: python -m test_insights.api.app
```

### Security Considerations

For production deployment:

1. **Configure CORS properly** - Update `allow_origins` in the FastAPI app
2. **Use HTTPS** - Deploy behind a reverse proxy with SSL
3. **API Authentication** - Add authentication middleware if needed
4. **Rate limiting** - Implement rate limiting for API endpoints
5. **Environment variables** - Never commit API keys to version control

## Monitoring

The API provides several monitoring endpoints:

- `/health` - Basic health check
- `/status` - Detailed system status
- Structured logging with correlation IDs
- Error tracking and metrics

For production monitoring, consider integrating with:

- Prometheus/Grafana for metrics
- ELK stack for log aggregation
- APM tools like New Relic or Datadog

## Support

For issues and questions:

1. Check the API documentation at `/docs`
2. Review the examples in `test_insights/examples/`
3. Check logs for detailed error information
4. Ensure ReportPortal connectivity and credentials are correct
