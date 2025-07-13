"""Basic usage example for ReportPortal AI Assistant."""

import asyncio
import os
from dotenv import load_dotenv

from test_insights.data_sync.sync.orchestrator import SyncOrchestrator
from test_insights.data_sync.storage.chromadb_client import ChromaDBClient
from test_insights.core.logging import setup_logging

# Load environment variables
load_dotenv()

# Setup logging
setup_logging("INFO", "console")


async def example_full_sync():
    """Example: Perform a full sync of all data."""
    print("=== Full Sync Example ===\n")
    
    orchestrator = SyncOrchestrator()
    
    # Perform full sync for specific projects
    stats = await orchestrator.sync(
        sync_type="full",
        project_names=["demo-project"],  # Replace with your project names
        entity_types=["project", "launch", "test_item", "log"]
    )
    
    print(f"Sync completed in {stats['duration_seconds']:.2f} seconds")
    print(f"Entity statistics: {stats['entity_stats']}")
    
    if stats.get('errors'):
        print(f"Errors encountered: {len(stats['errors'])}")


async def example_incremental_sync():
    """Example: Perform an incremental sync of recent changes."""
    print("\n=== Incremental Sync Example ===\n")
    
    orchestrator = SyncOrchestrator()
    
    # Sync only recent changes (last 24 hours by default)
    stats = await orchestrator.sync(
        sync_type="incremental",
        project_names=["demo-project"]
    )
    
    print(f"Incremental sync completed")
    print(f"Updated entities: {stats['entity_stats']}")


async def example_search():
    """Example: Search for test failures in vector database."""
    print("\n=== Search Example ===\n")
    
    client = ChromaDBClient()
    
    # Search for test failures related to timeouts
    results = await client.query(
        query_text="test failed timeout connection error",
        entity_types=["test_item", "log"],
        n_results=5
    )
    
    print(f"Found {len(results)} relevant results:\n")
    
    for i, result in enumerate(results, 1):
        print(f"Result {i}:")
        print(f"  Type: {result['metadata']['entity_type']}")
        print(f"  Distance: {result['distance']:.4f}")
        print(f"  Content: {result['document'][:150]}...")
        
        # Show specific metadata based on entity type
        if result['metadata']['entity_type'] == 'test_item':
            print(f"  Test: {result['metadata'].get('item_name', 'N/A')}")
            print(f"  Status: {result['metadata'].get('status', 'N/A')}")
        elif result['metadata']['entity_type'] == 'log':
            print(f"  Level: {result['metadata'].get('level', 'N/A')}")
        
        print()


async def example_statistics():
    """Example: Get storage statistics."""
    print("\n=== Storage Statistics Example ===\n")
    
    client = ChromaDBClient()
    
    stats = await client.get_statistics()
    
    print(f"Total documents: {stats['total_documents']}")
    print("\nDocuments by type:")
    
    for entity_type, count in stats['by_entity_type'].items():
        print(f"  {entity_type}: {count}")


async def example_custom_sync():
    """Example: Custom sync with specific entity types."""
    print("\n=== Custom Sync Example ===\n")
    
    orchestrator = SyncOrchestrator()
    
    # Sync only launches and their test items (skip logs)
    stats = await orchestrator.sync(
        sync_type="full",
        project_names=["demo-project"],
        entity_types=["launch", "test_item"]
    )
    
    print("Custom sync completed")
    print(f"Synced: {stats['entity_stats']}")


async def example_advanced_search():
    """Example: Advanced search with filters."""
    print("\n=== Advanced Search Example ===\n")
    
    client = ChromaDBClient()
    
    # Search for failed launches in a specific project
    results = await client.query(
        query_text="build failed integration tests",
        n_results=10,
        where={
            "entity_type": "launch",
            "status": "FAILED",
            "project_name": "demo-project"
        }
    )
    
    print(f"Found {len(results)} failed launches")
    
    for result in results[:3]:  # Show first 3
        entity_data = result['entity_data']
        print(f"\nLaunch: {entity_data.get('name', 'N/A')}")
        print(f"Number: #{entity_data.get('number', 'N/A')}")
        print(f"Status: {entity_data.get('status', 'N/A')}")
        print(f"Start Time: {entity_data.get('startTime', 'N/A')}")


async def main():
    """Run all examples."""
    try:
        # Check if required environment variables are set
        if not os.getenv("REPORTPORTAL_URL") or not os.getenv("REPORTPORTAL_API_TOKEN"):
            print("Error: Please set REPORTPORTAL_URL and REPORTPORTAL_API_TOKEN in .env file")
            return
        
        # Run examples
        await example_full_sync()
        await example_incremental_sync()
        await example_search()
        await example_statistics()
        await example_custom_sync()
        await example_advanced_search()
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())