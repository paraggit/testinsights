"""Command-line interface for ReportPortal AI Assistant."""

import asyncio
import json
from typing import List, Optional

import click
import structlog
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

from .config.settings import settings
from .data_sync.sync.orchestrator import SyncOrchestrator
from .data_sync.storage.chromadb_client import ChromaDBClient
from .core.logging import setup_logging

# Setup console for rich output
console = Console()

# Setup logging
setup_logging(settings.log_level, settings.log_format)
logger = structlog.get_logger(__name__)


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """ReportPortal AI Assistant CLI."""
    pass


@cli.group()
def sync():
    """Data synchronization commands."""
    pass


@sync.command()
@click.option(
    "--project",
    "-p",
    multiple=True,
    help="Project names to sync (can be specified multiple times)",
)
@click.option(
    "--entity-type",
    "-e",
    multiple=True,
    type=click.Choice(
        ["project", "user", "launch", "test_item", "log", "filter", "dashboard"]
    ),
    help="Entity types to sync (can be specified multiple times)",
)
@click.option(
    "--full",
    is_flag=True,
    help="Perform full sync (default is incremental)",
)
def run(project: List[str], entity_type: List[str], full: bool):
    """Run data synchronization."""
    sync_type = "full" if full else "incremental"
    projects = list(project) if project else None
    entity_types = list(entity_type) if entity_type else None
    
    console.print(f"[bold blue]Starting {sync_type} sync...[/bold blue]")
    
    if projects:
        console.print(f"Projects: {', '.join(projects)}")
    else:
        console.print("Projects: All")
    
    if entity_types:
        console.print(f"Entity types: {', '.join(entity_types)}")
    else:
        console.print("Entity types: All")
    
    async def run_sync():
        orchestrator = SyncOrchestrator()
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Syncing data...", total=None)
            
            try:
                stats = await orchestrator.sync(
                    sync_type=sync_type,
                    project_names=projects,
                    entity_types=entity_types,
                )
                
                progress.update(task, completed=True)
                
                # Display results
                console.print("\n[bold green]Sync completed successfully![/bold green]")
                
                # Show statistics table
                if stats.get("entity_stats"):
                    table = Table(title="Sync Statistics")
                    table.add_column("Entity Type", style="cyan")
                    table.add_column("Count", style="green")
                    
                    for entity, count in stats["entity_stats"].items():
                        table.add_row(entity, str(count))
                    
                    console.print(table)
                
                # Show errors if any
                if stats.get("errors"):
                    console.print("\n[bold red]Errors encountered:[/bold red]")
                    for error in stats["errors"]:
                        console.print(f"  - {error}")
                
                # Show timing
                console.print(
                    f"\nDuration: {stats.get('duration_seconds', 0):.2f} seconds"
                )
                
            except Exception as e:
                progress.update(task, completed=True)
                console.print(f"[bold red]Sync failed: {e}[/bold red]")
                logger.exception("Sync failed")
                raise click.ClickException(str(e))
    
    # Run async function
    asyncio.run(run_sync())


@sync.command()
def status():
    """Show synchronization status."""
    async def get_status():
        orchestrator = SyncOrchestrator()
        status_info = await orchestrator.get_sync_status()
        
        # Display storage statistics
        if status_info.get("storage_stats"):
            stats = status_info["storage_stats"]
            
            console.print("[bold]Storage Statistics[/bold]")
            console.print(f"Total documents: {stats.get('total_documents', 0)}")
            
            if stats.get("by_entity_type"):
                table = Table(title="Documents by Entity Type")
                table.add_column("Entity Type", style="cyan")
                table.add_column("Count", style="green")
                
                for entity_type, count in stats["by_entity_type"].items():
                    table.add_row(entity_type, str(count))
                
                console.print(table)
        
        # Display last sync info
        if status_info.get("last_sync"):
            console.print(f"\nLast sync: {status_info['last_sync']}")
            console.print(f"Sync type: {status_info.get('sync_type', 'N/A')}")
    
    asyncio.run(get_status())


@cli.group()
def storage():
    """Storage management commands."""
    pass


@storage.command()
@click.confirmation_option(
    prompt="Are you sure you want to clear all stored data?"
)
def clear():
    """Clear all data from vector storage."""
    async def clear_storage():
        client = ChromaDBClient()
        
        with console.status("Clearing storage..."):
            entity_types = [
                "project", "user", "launch", "test_item",
                "log", "filter", "dashboard"
            ]
            
            total_deleted = 0
            for entity_type in entity_types:
                deleted = await client.delete_by_entity_type(entity_type)
                total_deleted += deleted
                if deleted > 0:
                    console.print(f"Deleted {deleted} {entity_type} documents")
            
            console.print(
                f"\n[bold green]Successfully deleted {total_deleted} documents[/bold green]"
            )
    
    asyncio.run(clear_storage())


@storage.command()
@click.argument("query")
@click.option(
    "--entity-type",
    "-e",
    multiple=True,
    type=click.Choice(
        ["project", "user", "launch", "test_item", "log", "filter", "dashboard"]
    ),
    help="Filter by entity types",
)
@click.option(
    "--limit",
    "-n",
    default=10,
    help="Number of results to return",
)
@click.option(
    "--json-output",
    is_flag=True,
    help="Output results as JSON",
)
def search(query: str, entity_type: List[str], limit: int, json_output: bool):
    """Search for documents in vector storage."""
    async def search_storage():
        client = ChromaDBClient()
        
        entity_types = list(entity_type) if entity_type else None
        
        with console.status("Searching..."):
            results = await client.query(
                query_text=query,
                entity_types=entity_types,
                n_results=limit,
            )
        
        if json_output:
            console.print(json.dumps(results, indent=2))
        else:
            if not results:
                console.print("No results found")
                return
            
            console.print(f"\n[bold]Found {len(results)} results:[/bold]\n")
            
            for i, result in enumerate(results, 1):
                console.print(f"[bold cyan]Result {i}:[/bold cyan]")
                console.print(f"Type: {result['metadata'].get('entity_type')}")
                console.print(f"Distance: {result['distance']:.4f}")
                console.print(f"Document: {result['document'][:200]}...")
                
                # Show key metadata
                metadata = result["metadata"]
                if metadata.get("entity_type") == "launch":
                    console.print(f"Launch: {metadata.get('launch_name')}")
                    console.print(f"Status: {metadata.get('status')}")
                elif metadata.get("entity_type") == "test_item":
                    console.print(f"Item: {metadata.get('item_name')}")
                    console.print(f"Status: {metadata.get('status')}")
                
                console.print("-" * 80)
    
    asyncio.run(search_storage())


@cli.group()
def config():
    """Configuration management commands."""
    pass


@config.command()
def show():
    """Show current configuration."""
    console.print("[bold]Current Configuration:[/bold]\n")
    
    # Group settings by category
    api_settings = {
        "ReportPortal URL": settings.reportportal_url,
        "ReportPortal Project": settings.reportportal_project or "Not specified",
        "API Token": f"***{settings.reportportal_api_token[-4:]}" 
                     if settings.reportportal_api_token else "Not set",
    }
    
    sync_settings = {
        "Batch Size": settings.sync_batch_size,
        "Rate Limit": f"{settings.sync_rate_limit} req/s",
        "Timeout": f"{settings.sync_timeout}s",
        "Max Retries": settings.sync_max_retries,
        "Incremental Sync": "Enabled" if settings.enable_incremental_sync else "Disabled",
        "Full Sync": "Enabled" if settings.enable_full_sync else "Disabled",
    }
    
    storage_settings = {
        "ChromaDB Directory": str(settings.chroma_persist_directory),
        "Collection Name": settings.chroma_collection_name,
        "Embedding Model": settings.embedding_model,
        "Embedding Batch Size": settings.embedding_batch_size,
    }
    
    # Display settings
    for title, settings_dict in [
        ("API Settings", api_settings),
        ("Sync Settings", sync_settings),
        ("Storage Settings", storage_settings),
    ]:
        table = Table(title=title, show_header=False)
        table.add_column("Setting", style="cyan")
        table.add_column("Value", style="green")
        
        for key, value in settings_dict.items():
            table.add_row(key, str(value))
        
        console.print(table)
        console.print()


@config.command()
def init():
    """Initialize configuration with a wizard."""
    console.print("[bold]ReportPortal AI Assistant Configuration Wizard[/bold]\n")
    
    # Create .env file content
    env_content = []
    
    # API settings
    console.print("[cyan]ReportPortal API Settings[/cyan]")
    url = click.prompt("ReportPortal URL", default="https://reportportal.example.com")
    token = click.prompt("API Token", hide_input=True)
    project = click.prompt("Default Project (optional)", default="")
    
    env_content.extend([
        f"REPORTPORTAL_URL={url}",
        f"REPORTPORTAL_API_TOKEN={token}",
    ])
    if project:
        env_content.append(f"REPORTPORTAL_PROJECT={project}")
    
    # Storage settings
    console.print("\n[cyan]Storage Settings[/cyan]")
    chroma_dir = click.prompt(
        "ChromaDB Directory",
        default="./chroma_db",
    )
    env_content.append(f"CHROMA_PERSIST_DIRECTORY={chroma_dir}")
    
    # Sync settings
    console.print("\n[cyan]Sync Settings[/cyan]")
    batch_size = click.prompt("Sync Batch Size", default=100, type=int)
    rate_limit = click.prompt("Rate Limit (req/s)", default=10, type=int)
    
    env_content.extend([
        f"SYNC_BATCH_SIZE={batch_size}",
        f"SYNC_RATE_LIMIT={rate_limit}",
    ])
    
    # Write .env file
    with open(".env", "w") as f:
        f.write("\n".join(env_content))
        f.write("\n")
    
    console.print("\n[bold green]Configuration saved to .env file![/bold green]")
    console.print("You can now run 'reportportal_ai sync run' to start synchronization.")


if __name__ == "__main__":
    cli()