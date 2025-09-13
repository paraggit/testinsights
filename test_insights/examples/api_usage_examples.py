"""
Examples of how to use the TestInsight API.

This file demonstrates various ways to interact with the TestInsight FastAPI endpoints.
"""

import asyncio

import httpx


class TestInsightAPIClient:
    """Simple client for TestInsight API."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

    async def health_check(self):
        """Check API health."""
        response = await self.client.get(f"{self.base_url}/health")
        return response.json()

    async def query(
        self,
        query: str,
        provider: str = None,
        model: str = None,
        show_sources: bool = False,
        n_results: int = 20,
    ):
        """Send a natural language query."""
        payload = {"query": query, "show_sources": show_sources, "n_results": n_results}

        if provider:
            payload["provider"] = provider
        if model:
            payload["model"] = model

        response = await self.client.post(f"{self.base_url}/query", json=payload)
        return response.json()

    async def search(self, query: str, entity_types: list = None, limit: int = 10):
        """Search vector storage."""
        payload = {"query": query, "limit": limit}

        if entity_types:
            payload["entity_types"] = entity_types

        response = await self.client.post(f"{self.base_url}/search", json=payload)
        return response.json()

    async def sync_data(self, projects: list = None, entity_types: list = None, full: bool = False):
        """Trigger data synchronization."""
        payload = {"full": full}

        if projects:
            payload["projects"] = projects
        if entity_types:
            payload["entity_types"] = entity_types

        response = await self.client.post(f"{self.base_url}/sync", json=payload)
        return response.json()

    async def get_status(self):
        """Get system status."""
        response = await self.client.get(f"{self.base_url}/status")
        return response.json()

    async def get_config(self):
        """Get system configuration."""
        response = await self.client.get(f"{self.base_url}/config")
        return response.json()

    async def clear_storage(self):
        """Clear all storage data."""
        response = await self.client.delete(f"{self.base_url}/storage")
        return response.json()


async def example_basic_usage():
    """Basic usage examples."""
    print("=== Basic API Usage Examples ===\n")

    async with TestInsightAPIClient() as client:
        # Health check
        print("1. Health Check:")
        try:
            health = await client.health_check()
            print(f"   Status: {health.get('status', 'unknown')}")
        except Exception as e:
            print(f"   Error: {e}")

        print()

        # Get system status
        print("2. System Status:")
        try:
            status = await client.get_status()
            print(f"   Status: {status.get('status', 'unknown')}")
            if status.get("storage_stats"):
                stats = status["storage_stats"]
                print(f"   Total documents: {stats.get('total_documents', 0)}")
        except Exception as e:
            print(f"   Error: {e}")

        print()

        # Example query
        print("3. Natural Language Query:")
        try:
            result = await client.query(
                "Show me failed tests from the last 7 days", show_sources=True, n_results=10
            )
            print(f"   Response: {result.get('response', 'No response')[:200]}...")
            if result.get("metrics"):
                print(f"   Metrics: {result['metrics']}")
        except Exception as e:
            print(f"   Error: {e}")

        print()

        # Vector search
        print("4. Vector Search:")
        try:
            search_results = await client.search(
                "timeout error", entity_types=["test_item"], limit=5
            )
            print(f"   Found {search_results.get('total_found', 0)} results")
        except Exception as e:
            print(f"   Error: {e}")


async def example_slack_bot_queries():
    """Example queries that might come from a Slack bot."""
    print("=== Slack Bot Query Examples ===\n")

    # Simulate queries that would come from Slack
    slack_queries = [
        {
            "user": "developer1",
            "query": "What tests failed in the login module yesterday?",
            "context": "user asking about specific failures",
        },
        {
            "user": "qa_lead",
            "query": "Show me the test success rate for this week",
            "context": "weekly status check",
        },
        {
            "user": "devops",
            "query": "Are there any performance test failures in the API suite?",
            "context": "performance monitoring",
        },
        {
            "user": "manager",
            "query": "Compare test results between this week and last week",
            "context": "trend analysis request",
        },
    ]

    async with TestInsightAPIClient() as client:
        for i, slack_query in enumerate(slack_queries, 1):
            print(f"{i}. Query from {slack_query['user']}:")
            print(f"   Question: \"{slack_query['query']}\"")
            print(f"   Context: {slack_query['context']}")

            try:
                result = await client.query(
                    slack_query["query"],
                    show_sources=False,  # Don't show sources in Slack responses
                    n_results=15,
                )

                response = result.get("response", "No response available")
                print(f"   Response: {response[:300]}...")

                if result.get("analysis"):
                    analysis = result["analysis"]
                    print(f"   Intent: {analysis.get('intent', 'unknown')}")
                    print(f"   Entity types: {analysis.get('entity_types', [])}")

            except Exception as e:
                print(f"   Error: {e}")

            print()


async def example_sync_operations():
    """Example synchronization operations."""
    print("=== Data Synchronization Examples ===\n")

    async with TestInsightAPIClient() as client:
        # Incremental sync for specific projects
        print("1. Incremental Sync for Specific Projects:")
        try:
            result = await client.sync_data(
                projects=["web-app", "api-service"],
                entity_types=["launch", "test_item"],
                full=False,
            )
            print(f"   Success: {result.get('success', False)}")
            print(f"   Message: {result.get('message', 'No message')}")
            if result.get("stats"):
                print(f"   Stats: {result['stats']}")
        except Exception as e:
            print(f"   Error: {e}")

        print()

        # Full sync
        print("2. Full Sync (All Projects):")
        try:
            result = await client.sync_data(full=True)
            print(f"   Success: {result.get('success', False)}")
            print(f"   Message: {result.get('message', 'No message')}")
            if result.get("duration_seconds"):
                print(f"   Duration: {result['duration_seconds']:.2f} seconds")
        except Exception as e:
            print(f"   Error: {e}")


async def example_advanced_queries():
    """Advanced query examples with different providers."""
    print("=== Advanced Query Examples ===\n")

    advanced_queries = [
        {
            "query": "Analyze the root cause of API timeout failures in the last 24 hours",
            "provider": "anthropic",  # Use Claude for detailed analysis
            "description": "Root cause analysis with Claude",
        },
        {
            "query": "What's the trend of test failures over the past month?",
            "provider": "openai",
            "model": "gpt-4-turbo-preview",
            "description": "Trend analysis with GPT-4",
        },
        {
            "query": "Find all tests that are flaky (inconsistent pass/fail)",
            "provider": "ollama",
            "model": "llama2",
            "description": "Pattern detection with local LLM",
        },
    ]

    async with TestInsightAPIClient() as client:
        for i, query_config in enumerate(advanced_queries, 1):
            print(f"{i}. {query_config['description']}:")
            print(f"   Query: \"{query_config['query']}\"")
            print(f"   Provider: {query_config['provider']}")

            try:
                result = await client.query(
                    query_config["query"],
                    provider=query_config["provider"],
                    model=query_config.get("model"),
                    show_sources=True,
                    n_results=25,
                )

                print(f"   Model used: {result.get('model', 'unknown')}")
                print(f"   Response: {result.get('response', 'No response')[:200]}...")

                if result.get("usage"):
                    usage = result["usage"]
                    print(f"   Token usage: {usage.get('total_tokens', 'N/A')}")

            except Exception as e:
                print(f"   Error: {e}")

            print()


async def main():
    """Run all examples."""
    print("TestInsight API Usage Examples")
    print("=" * 50)
    print()

    await example_basic_usage()
    print()

    await example_slack_bot_queries()
    print()

    await example_sync_operations()
    print()

    await example_advanced_queries()
    print()

    print("Examples completed!")


if __name__ == "__main__":
    asyncio.run(main())
