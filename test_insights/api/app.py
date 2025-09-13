"""FastAPI application for TestInsight."""

import time
from contextlib import asynccontextmanager
from typing import Any, Dict, Optional

import structlog
from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from test_insights.api.exceptions import (
    LLMProviderException,
    StorageException,
    TestInsightException,
    general_exception_handler,
    http_exception_handler,
    test_insight_exception_handler,
)
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
from test_insights.api.swagger_config import (
    customize_openapi_schema,
    get_redoc_html,
    get_swagger_ui_html,
)
from test_insights.config.settings import settings
from test_insights.core.logging import setup_logging
from test_insights.data_sync.storage.chromadb_client import ChromaDBClient
from test_insights.data_sync.sync.orchestrator import SyncOrchestrator
from test_insights.rag.rag_pipeline import RAGPipeline

# Setup logging
setup_logging(settings.log_level, settings.log_format)
logger = structlog.get_logger(__name__)

# Global instances
storage_client: Optional[ChromaDBClient] = None
sync_orchestrator: Optional[SyncOrchestrator] = None


@asynccontextmanager
async def lifespan(app: FastAPI):  # type: ignore
    """Manage application lifecycle."""
    global storage_client, sync_orchestrator

    logger.info("Starting TestInsight API...")

    # Initialize storage client
    storage_client = ChromaDBClient()
    sync_orchestrator = SyncOrchestrator()

    logger.info("TestInsight API started successfully")

    yield

    logger.info("Shutting down TestInsight API...")


app = FastAPI(
    title=settings.custom_api_title,
    description=f"""
    ## {settings.custom_api_description}

    TestInsight provides intelligent analysis of your ReportPortal test execution data
    using advanced AI and natural language processing.

    ### Key Features

    * **Natural Language Queries**: Ask questions about your test data in plain English
    * **Multiple AI Providers**: Support for OpenAI, Anthropic, and local Ollama models
    * **Semantic Search**: Find relevant test data using vector similarity search
    * **Data Synchronization**: Keep your local data in sync with ReportPortal
    * **Real-time Insights**: Get immediate answers about test failures, trends, and patterns

    ### Getting Started

    1. **Configure your environment**: Set up ReportPortal credentials and AI provider keys
    2. **Sync your data**: Use the `/sync` endpoint to import test data
    3. **Start querying**: Ask questions using the `/query` endpoint

    ### Example Queries

    * "What tests failed yesterday?"
    * "Show me the success rate for API tests this week"
    * "Why did the login tests fail?"
    * "Find tests with timeout errors"
    * "Compare test results between this week and last week"

    ### Authentication

    This API currently doesn't require authentication, but you should secure it
    appropriately for production use.

    ### Rate Limits

    Rate limiting depends on your AI provider's limits. Consider implementing your own
    rate limiting for production deployments.
    """,
    version=settings.custom_api_version,
    lifespan=lifespan,
    contact={
        "name": settings.contact_name,
        "email": settings.contact_email,
        "url": settings.contact_url,
    },
    license_info={
        "name": settings.license_name,
        "url": settings.license_url,
    },
    servers=[
        {
            "url": f"http://{settings.api_host}:{settings.api_port}",
            "description": "Development server",
        },
        {
            "url": "https://api.testinsight.example.com",
            "description": "Production server",
        },
    ],
    tags_metadata=[
        {
            "name": "queries",
            "description": "Natural language query processing using AI",
        },
        {
            "name": "search",
            "description": "Direct vector database search operations",
        },
        {
            "name": "sync",
            "description": "Data synchronization with ReportPortal",
        },
        {
            "name": "system",
            "description": "System status and configuration endpoints",
        },
    ],
    docs_url="/docs" if settings.enable_docs else None,
    redoc_url="/redoc" if settings.enable_redoc else None,
    openapi_url="/openapi.json" if settings.enable_openapi_json else None,
)

# Add exception handlers
app.add_exception_handler(TestInsightException, test_insight_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom OpenAPI schema
app.openapi = lambda: customize_openapi_schema(app)


# Custom documentation endpoints
@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    """Custom Swagger UI with enhanced styling."""
    from fastapi.responses import HTMLResponse

    return HTMLResponse(get_swagger_ui_html(openapi_url=app.openapi_url))


@app.get("/redoc", include_in_schema=False)
async def custom_redoc_html():
    """Custom ReDoc with enhanced styling."""
    from fastapi.responses import HTMLResponse

    return HTMLResponse(get_redoc_html(openapi_url=app.openapi_url))


def get_llm_provider(provider_name: Optional[str] = None, model: Optional[str] = None):
    """Get LLM provider instance."""
    provider_name = provider_name or settings.llm_provider

    try:
        if provider_name == "openai":
            from test_insights.llm.providers.openai_provider import OpenAIProvider

            return OpenAIProvider(
                model=model or settings.openai_model,
                temperature=settings.llm_temperature,
                max_tokens=settings.llm_max_tokens,
            )
        elif provider_name == "anthropic":
            from test_insights.llm.providers.anthropic_provider import AnthropicProvider

            return AnthropicProvider(
                model=model or settings.anthropic_model,
                temperature=settings.llm_temperature,
                max_tokens=settings.llm_max_tokens,
            )
        elif provider_name == "ollama":
            from test_insights.llm.providers.ollama_provider import OllamaProvider

            return OllamaProvider(
                base_url=settings.ollama_base_url,
                model=model or settings.ollama_model,
                temperature=settings.llm_temperature,
                max_tokens=settings.llm_max_tokens,
            )
        else:
            raise ValueError(f"Unknown provider: {provider_name}")

    except Exception as e:
        logger.error(f"Failed to initialize LLM provider: {e}")
        raise LLMProviderException(f"Failed to initialize LLM provider: {str(e)}")


@app.get(
    "/",
    response_model=Dict[str, str],
    tags=["system"],
    summary="API Root",
    description="Get basic information about the TestInsight API",
)
async def root():
    """
    Welcome endpoint for the TestInsight API.

    Returns basic information about the API including version and documentation links.
    """
    return {"message": "TestInsight API", "version": "0.1.0", "docs": "/docs"}


@app.get(
    "/health",
    response_model=Dict[str, str],
    tags=["system"],
    summary="Health Check",
    description="Check if the API and its dependencies are operational",
    responses={
        200: {
            "description": "Service is healthy",
            "content": {"application/json": {"example": {"status": "healthy"}}},
        },
        503: {"description": "Service is unhealthy", "model": ErrorResponse},
    },
)
async def health_check():
    """
    Health check endpoint for monitoring and load balancers.

    Verifies that the API is running and can connect to its dependencies
    (vector database, etc.). Returns HTTP 200 if healthy, 503 if not.
    """
    try:
        # Basic health check - verify storage is accessible
        await storage_client.get_collection_info()
        return {"status": "healthy"}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise StorageException("Service unavailable - storage check failed")


@app.post(
    "/query",
    response_model=QueryResponse,
    tags=["queries"],
    summary="Natural Language Query",
    description="Process natural language queries about your test data using AI",
    responses={
        200: {"description": "Query processed successfully", "model": QueryResponse},
        500: {"description": "Query processing failed", "model": ErrorResponse},
    },
)
async def query_endpoint(request: QueryRequest):
    """
    Process natural language queries about test data using AI.

    This is the main endpoint for asking questions about your ReportPortal test data.
    The AI will analyze your query, retrieve relevant data, and provide insights.

    **How it works:**
    1. Your query is analyzed to understand intent and extract parameters
    2. Relevant documents are retrieved from the vector database
    3. The AI generates a response based on the retrieved data
    4. Additional metrics and analysis are included when relevant

    **Supported query types:**
    - **Status queries**: "What tests failed yesterday?"
    - **Trend analysis**: "How are our test results trending?"
    - **Root cause analysis**: "Why did the login tests fail?"
    - **Metrics**: "What's our success rate this month?"
    - **Comparisons**: "Compare this week vs last week"

    **Tips for better results:**
    - Be specific about time periods ("last 7 days", "yesterday")
    - Mention specific test names or error types when relevant
    - Ask for metrics or statistics when you need numbers
    - Use `show_sources=true` to see which data was used
    """
    logger.info("Processing query", query=request.query)

    try:
        # Get LLM provider
        llm = get_llm_provider(request.provider, request.model)

        # Handle Ollama provider differently due to async context manager
        if request.provider == "ollama" or (
            not request.provider and settings.llm_provider == "ollama"
        ):
            async with llm:
                rag = RAGPipeline(llm)
                result = await rag.query(
                    request.query,
                    n_results=request.n_results,
                    include_raw_results=request.show_sources,
                    stream=request.stream,
                )
        else:
            rag = RAGPipeline(llm)
            result = await rag.query(
                request.query,
                n_results=request.n_results,
                include_raw_results=request.show_sources,
                stream=request.stream,
            )

        if request.stream:
            # For streaming responses, we need to handle it differently
            # This is a simplified version - you might want to implement Server-Sent Events
            response_chunks = []
            async for chunk in result["response"]:
                response_chunks.append(chunk)

            result["response"] = "".join(response_chunks)

        return QueryResponse(
            response=result["response"],
            analysis=result.get("analysis"),
            metrics=result.get("metrics"),
            search_results=result.get("search_results"),
            model=result.get("model"),
            usage=result.get("usage"),
        )

    except Exception as e:
        logger.error(f"Query processing failed: {e}")
        raise LLMProviderException(f"Query processing failed: {str(e)}")


@app.post(
    "/search",
    response_model=SearchResponse,
    tags=["search"],
    summary="Vector Search",
    description="Search for documents in the vector database using semantic similarity",
    responses={
        200: {"description": "Search completed successfully", "model": SearchResponse},
        500: {"description": "Search failed", "model": ErrorResponse},
    },
)
async def search_endpoint(request: SearchRequest):
    """
    Search for documents in vector storage using semantic similarity.

    This endpoint performs direct semantic search across your stored ReportPortal data
    without AI processing. It's useful for finding specific documents or exploring
    what data is available.

    **Use cases:**
    - Find specific error messages or test names
    - Explore available data before asking AI questions
    - Locate documents containing specific keywords
    - Debug what data is stored in the system

    **How it works:**
    1. Your search query is converted to a vector representation
    2. The system finds documents with similar vector representations
    3. Results are ranked by similarity score (lower distance = more similar)

    **Entity types you can filter by:**
    - `test_item`: Individual test cases
    - `launch`: Test execution runs
    - `log`: Test execution logs
    - `project`: Project information
    - `user`: User information
    - `filter`: Saved filters
    - `dashboard`: Dashboard configurations
    """
    logger.info("Processing search", query=request.query)

    try:
        results = await storage_client.query(
            query_text=request.query,
            entity_types=request.entity_types,
            n_results=request.limit,
        )

        return SearchResponse(results=results, total_found=len(results))

    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise StorageException(f"Search failed: {str(e)}")


@app.post(
    "/sync",
    response_model=SyncResponse,
    tags=["sync"],
    summary="Synchronize Data",
    description="Trigger synchronization of data from ReportPortal to the local vector database",
    responses={
        200: {"description": "Sync completed (may have succeeded or failed)", "model": SyncResponse}
    },
)
async def sync_endpoint(request: SyncRequest, background_tasks: BackgroundTasks):
    """
    Trigger data synchronization with ReportPortal.

    This endpoint synchronizes data from your ReportPortal instance to the local
    vector database. You need to sync data before you can query it with AI.

    **Sync Types:**
    - **Incremental** (default): Only sync new/changed data since last sync
    - **Full**: Re-sync all data (takes longer but ensures completeness)

    **Parameters:**
    - **projects**: Limit sync to specific projects (if not specified, syncs all)
    - **entity_types**: Limit sync to specific data types (if not specified, syncs all)

    **When to sync:**
    - After new test runs complete in ReportPortal
    - When setting up the system for the first time (use `full: true`)
    - When you suspect data is missing or outdated

    **Performance notes:**
    - Incremental syncs are much faster than full syncs
    - Large datasets may take several minutes to sync
    - The operation continues even if the API request times out

    **Entity types available:**
    - `project`: Project configurations
    - `user`: User information
    - `launch`: Test execution runs
    - `test_item`: Individual test cases and results
    - `log`: Test execution logs and error details
    - `filter`: Saved search filters
    - `dashboard`: Dashboard configurations
    """
    logger.info("Starting sync", request=request.dict())

    sync_type = "full" if request.full else "incremental"

    try:
        start_time = time.time()

        stats = await sync_orchestrator.sync(
            sync_type=sync_type,
            project_names=request.projects,
            entity_types=request.entity_types,
        )

        duration = time.time() - start_time

        return SyncResponse(
            success=True,
            message=f"Sync completed successfully ({sync_type})",
            stats=stats,
            duration_seconds=duration,
        )

    except Exception as e:
        logger.error(f"Sync failed: {e}")
        return SyncResponse(
            success=False, message=f"Sync failed: {str(e)}", stats=None, duration_seconds=None
        )


@app.get(
    "/status",
    response_model=StatusResponse,
    tags=["system"],
    summary="System Status",
    description="Get detailed system status and data statistics",
    responses={
        200: {"description": "Status retrieved successfully", "model": StatusResponse},
        500: {"description": "Status check failed", "model": ErrorResponse},
    },
)
async def status_endpoint():
    """
    Get comprehensive system status and statistics.

    This endpoint provides detailed information about the current state of the system,
    including data storage statistics and synchronization history.

    **Information provided:**
    - Overall system operational status
    - Total number of documents stored
    - Breakdown of documents by entity type
    - Last synchronization timestamp and type
    - Storage health and capacity information

    **Use cases:**
    - Monitor system health
    - Check if data sync is needed
    - Verify data availability before querying
    - Troubleshoot system issues
    - Monitor data growth over time
    """
    try:
        status_info = await sync_orchestrator.get_sync_status()

        return StatusResponse(
            status="operational",
            storage_stats=status_info.get("storage_stats"),
            last_sync=status_info.get("last_sync"),
            sync_type=status_info.get("sync_type"),
        )

    except Exception as e:
        logger.error(f"Status check failed: {e}")
        raise StorageException(f"Status check failed: {str(e)}")


@app.delete(
    "/storage",
    response_model=Dict[str, str],
    tags=["system"],
    summary="Clear Storage",
    description="Delete all stored data from the vector database",
    responses={
        200: {
            "description": "Storage cleared successfully",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Successfully deleted 1250 documents",
                        "status": "completed",
                    }
                }
            },
        },
        500: {"description": "Storage clear failed", "model": ErrorResponse},
    },
)
async def clear_storage_endpoint():
    """
    Clear all data from vector storage.

    **⚠️ WARNING: This operation is irreversible!**

    This endpoint permanently deletes all stored test data from the vector database.
    After clearing storage, you'll need to run a full sync to restore data.

    **When to use:**
    - Resetting the system during development/testing
    - Clearing corrupted or outdated data
    - Starting fresh with new ReportPortal data
    - Freeing up storage space

    **What gets deleted:**
    - All test execution data
    - All project and user information
    - All logs and error details
    - All cached embeddings and vectors

    **After clearing storage:**
    1. Run a full sync: `POST /sync` with `{"full": true}`
    2. Wait for sync to complete
    3. Verify data with `GET /status`
    4. Resume normal querying operations
    """
    logger.warning("Clearing all storage data")

    try:
        entity_types = ["project", "user", "launch", "test_item", "log", "filter", "dashboard"]

        total_deleted = 0
        for entity_type in entity_types:
            deleted = await storage_client.delete_by_entity_type(entity_type)
            total_deleted += deleted

        return {"message": f"Successfully deleted {total_deleted} documents", "status": "completed"}

    except Exception as e:
        logger.error(f"Storage clear failed: {e}")
        raise StorageException(f"Storage clear failed: {str(e)}")


@app.get(
    "/config",
    response_model=Dict[str, Any],
    tags=["system"],
    summary="System Configuration",
    description="Get current system configuration with sensitive values masked",
    responses={
        200: {
            "description": "Configuration retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "reportportal_url": "https://reportportal.example.com",
                        "reportportal_project": "web-app",
                        "api_token": "***abc123",
                        "llm_provider": "openai",
                        "embedding_model": "all-MiniLM-L6-v2",
                        "chroma_collection_name": "reportportal_data",
                        "sync_batch_size": 100,
                        "sync_rate_limit": 10,
                    }
                }
            },
        }
    },
)
async def get_config():
    """
    Get current system configuration with sensitive values masked.

    This endpoint returns the current configuration settings for the TestInsight system.
    Sensitive values like API keys and tokens are masked for security.

    **Configuration categories:**
    - **ReportPortal**: Connection settings and project configuration
    - **AI/LLM**: Provider settings and model configurations
    - **Storage**: Vector database and embedding settings
    - **Sync**: Data synchronization parameters and limits

    **Use cases:**
    - Verify system configuration
    - Troubleshoot connection issues
    - Check which AI provider is configured
    - Validate sync settings
    - Debug configuration problems

    **Security note:**
    API keys and sensitive tokens are masked (e.g., "***abc123") to prevent
    accidental exposure in logs or screenshots.
    """
    config = {
        "reportportal_url": settings.reportportal_url,
        "reportportal_project": settings.reportportal_project or "Not specified",
        "api_token": (
            f"***{settings.reportportal_api_token[-4:]}"
            if settings.reportportal_api_token
            else "Not set"
        ),
        "llm_provider": settings.llm_provider,
        "embedding_model": settings.embedding_model,
        "chroma_collection_name": settings.chroma_collection_name,
        "sync_batch_size": settings.sync_batch_size,
        "sync_rate_limit": settings.sync_rate_limit,
    }

    return config


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
