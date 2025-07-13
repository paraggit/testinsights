"""Command-line interface for ReportPortal AI Assistant."""

import asyncio
import json
from pathlib import Path

import click
import structlog
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from test_insights.config.settings import settings
from test_insights.core.logging import setup_logging
from test_insights.data_sync.storage.chromadb_client import ChromaDBClient
from test_insights.data_sync.sync.orchestrator import SyncOrchestrator

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
    type=click.Choice(["project", "user", "launch", "test_item", "log", "filter", "dashboard"]),
    help="Entity types to sync (can be specified multiple times)",
)
@click.option(
    "--full",
    is_flag=True,
    help="Perform full sync (default is incremental)",
)
def run(project, entity_type, full):
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

                console.print("\n[bold green]Sync completed successfully![/bold green]")

                if stats.get("entity_stats"):
                    table = Table(title="Sync Statistics")
                    table.add_column("Entity Type", style="cyan")
                    table.add_column("Count", style="green")

                    for entity, count in stats["entity_stats"].items():
                        table.add_row(entity, str(count))

                    console.print(table)

                if stats.get("errors"):
                    console.print("\n[bold red]Errors encountered:[/bold red]")
                    for error in stats["errors"]:
                        console.print(f"  - {error}")

                console.print(f"\nDuration: {stats.get('duration_seconds', 0):.2f} seconds")

            except Exception as e:
                progress.update(task, completed=True)
                console.print(f"[bold red]Sync failed: {e}[/bold red]")
                logger.exception("Sync failed")
                raise click.ClickException(str(e))

    asyncio.run(run_sync())


@sync.command()
def status():
    """Show synchronization status."""

    async def get_status():
        orchestrator = SyncOrchestrator()
        status_info = await orchestrator.get_sync_status()

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

        if status_info.get("last_sync"):
            console.print(f"\nLast sync: {status_info['last_sync']}")
            console.print(f"Sync type: {status_info.get('sync_type', 'N/A')}")

    asyncio.run(get_status())


@cli.group()
def storage():
    """Storage management commands."""
    pass


@storage.command()
@click.confirmation_option(prompt="Are you sure you want to clear all stored data?")
def clear():
    """Clear all data from vector storage."""

    async def clear_storage():
        client = ChromaDBClient()

        with console.status("Clearing storage..."):
            entity_types = ["project", "user", "launch", "test_item", "log", "filter", "dashboard"]

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
    type=click.Choice(["project", "user", "launch", "test_item", "log", "filter", "dashboard"]),
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
def search(query, entity_type, limit, json_output):
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

    api_settings = {
        "ReportPortal URL": settings.reportportal_url,
        "ReportPortal Project": settings.reportportal_project or "Not specified",
        "API Token": (
            f"***{settings.reportportal_api_token[-4:]}"
            if settings.reportportal_api_token
            else "Not set"
        ),
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

    env_content = []

    console.print("[cyan]ReportPortal API Settings[/cyan]")
    url = click.prompt("ReportPortal URL", default="https://reportportal.example.com")
    token = click.prompt("API Token", hide_input=True)
    project = click.prompt("Default Project (optional)", default="")

    env_content.extend(
        [
            f"REPORTPORTAL_URL={url}",
            f"REPORTPORTAL_API_TOKEN={token}",
        ]
    )
    if project:
        env_content.append(f"REPORTPORTAL_PROJECT={project}")

    console.print("\n[cyan]Storage Settings[/cyan]")
    chroma_dir = click.prompt(
        "ChromaDB Directory",
        default="./chroma_db",
    )
    env_content.append(f"CHROMA_PERSIST_DIRECTORY={chroma_dir}")

    console.print("\n[cyan]Sync Settings[/cyan]")
    batch_size = click.prompt("Sync Batch Size", default=100, type=int)
    rate_limit = click.prompt("Rate Limit (req/s)", default=10, type=int)

    env_content.extend(
        [
            f"SYNC_BATCH_SIZE={batch_size}",
            f"SYNC_RATE_LIMIT={rate_limit}",
        ]
    )

    with open(".env", "w") as f:
        f.write("\n".join(env_content))
        f.write("\n")

    console.print("\n[bold green]Configuration saved to .env file![/bold green]")
    console.print("You can now run 'test_insights sync run' to start synchronization.")


@cli.group()
def query():
    """Natural language query commands."""
    pass


@query.command()
@click.argument("question")
@click.option(
    "--provider",
    type=click.Choice(["openai", "anthropic", "ollama"]),
    default=None,
    help="LLM provider to use (defaults to config)",
)
@click.option(
    "--model",
    help="Model to use (defaults to provider's default)",
)
@click.option(
    "--stream",
    is_flag=True,
    help="Stream the response",
)
@click.option(
    "--show-sources",
    is_flag=True,
    help="Show source documents used for the answer",
)
@click.option(
    "--n-results",
    default=20,
    help="Number of documents to retrieve",
)
def ask(question, provider, model, stream, show_sources, n_results):
    """Ask a natural language question about your test data."""

    async def run_query():
        provider_name = provider or settings.llm_provider

        try:
            if provider_name == "openai":
                from test_insights.llm.providers.openai_provider import OpenAIProvider

                llm = OpenAIProvider(
                    model=model or settings.openai_model,
                    temperature=settings.llm_temperature,
                    max_tokens=settings.llm_max_tokens,
                )
            elif provider_name == "anthropic":
                from test_insights.llm.providers.anthropic_provider import AnthropicProvider

                llm = AnthropicProvider(
                    model=model or settings.anthropic_model,
                    temperature=settings.llm_temperature,
                    max_tokens=settings.llm_max_tokens,
                )
            elif provider_name == "ollama":
                from test_insights.llm.providers.ollama_provider import OllamaProvider

                llm = OllamaProvider(
                    base_url=settings.ollama_base_url,
                    model=model or settings.ollama_model,
                    temperature=settings.llm_temperature,
                    max_tokens=settings.llm_max_tokens,
                )
            else:
                raise click.ClickException(f"Unknown provider: {provider_name}")

        except Exception as e:
            console.print(f"[bold red]Failed to initialize LLM provider: {e}[/bold red]")
            raise click.ClickException(str(e))

        from test_insights.rag.rag_pipeline import RAGPipeline

        rag = RAGPipeline(llm)

        console.print(f"[bold blue]Processing query:[/bold blue] {question}\n")

        with console.status("Searching and analyzing..."):
            try:
                result = await rag.query(
                    question,
                    n_results=n_results,
                    include_raw_results=show_sources,
                    stream=stream,
                )
            except Exception as e:
                console.print(f"[bold red]Query failed: {e}[/bold red]")
                raise click.ClickException(str(e))

        if stream:
            console.print("[bold green]Response:[/bold green]\n")
            async for chunk in result["response"]:
                console.print(chunk, end="")
            console.print("\n")
        else:
            console.print("[bold green]Response:[/bold green]")
            console.print(result["response"])

        if result.get("analysis"):
            console.print(f"\n[dim]Intent: {result['analysis']['intent']}[/dim]")
            console.print(
                f"[dim]Entity types: {', '.join(result['analysis']['entity_types'])}[/dim]"
            )

        if result.get("metrics"):
            console.print("\n[bold]Metrics:[/bold]")
            table = Table()
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="green")

            metrics = result["metrics"]
            if "failure_rate" in metrics:
                table.add_row("Failure Rate", f"{metrics['failure_rate']:.1f}%")
            if "success_rate" in metrics:
                table.add_row("Success Rate", f"{metrics['success_rate']:.1f}%")

            console.print(table)

        if show_sources and result.get("search_results"):
            console.print(f"\n[bold]Sources ({len(result['search_results'])} documents):[/bold]")
            for i, doc in enumerate(result["search_results"][:5], 1):
                metadata = doc["metadata"]
                console.print(f"\n[cyan]{i}. {metadata.get('entity_type', 'Unknown')}[/cyan]")
                console.print(f"   Distance: {doc['distance']:.4f}")
                console.print(f"   Preview: {doc['document'][:150]}...")

        if result.get("usage"):
            usage = result["usage"]
            console.print(
                f"\n[dim]Tokens used: {usage.get('total_tokens', 'N/A')} "
                f"(prompt: {usage.get('prompt_tokens', 'N/A')}, "
                f"completion: {usage.get('completion_tokens', 'N/A')})[/dim]"
            )

    if provider == "ollama":

        async def run_with_ollama():
            from test_insights.llm.providers.ollama_provider import OllamaProvider

            llm = OllamaProvider(
                base_url=settings.ollama_base_url,
                model=model or settings.ollama_model,
                temperature=settings.llm_temperature,
                max_tokens=settings.llm_max_tokens,
            )
            async with llm:
                from test_insights.rag.rag_pipeline import RAGPipeline

                rag = RAGPipeline(llm)

                console.print(f"[bold blue]Processing query:[/bold blue] {question}\n")

                with console.status("Searching and analyzing..."):
                    try:
                        result = await rag.query(
                            question,
                            n_results=n_results,
                            include_raw_results=show_sources,
                            stream=stream,
                        )
                    except Exception as e:
                        console.print(f"[bold red]Query failed: {e}[/bold red]")
                        raise click.ClickException(str(e))

                if stream:
                    console.print("[bold green]Response:[/bold green]\n")
                    async for chunk in result["response"]:
                        console.print(chunk, end="")
                    console.print("\n")
                else:
                    console.print("[bold green]Response:[/bold green]")
                    console.print(result["response"])

                if result.get("analysis"):
                    console.print(f"\n[dim]Intent: {result['analysis']['intent']}[/dim]")
                    console.print(
                        f"[dim]Entity types: {', '.join(result['analysis']['entity_types'])}[/dim]"
                    )

        asyncio.run(run_with_ollama())
    else:
        asyncio.run(run_query())


@query.command()
def examples():
    """Show example queries you can ask."""
    examples = [
        ("Find failed tests", "Show me all failed tests from the last 24 hours"),
        ("Root cause analysis", "Why did the login tests fail yesterday?"),
        ("Trends", "What's the test failure trend over the last week?"),
        ("Specific errors", "Find tests that failed with timeout errors"),
        ("Metrics", "What's the success rate for API tests this month?"),
        ("Comparisons", "Compare test results between this week and last week"),
        ("Test history", "Show me the history of the checkout flow tests"),
        ("Error patterns", "What are the most common error messages in failed tests?"),
        ("Performance", "Which tests are taking the longest to run?"),
        ("Flaky tests", "Identify tests that pass and fail intermittently"),
    ]

    console.print("[bold]Example Queries:[/bold]\n")

    table = Table()
    table.add_column("Category", style="cyan")
    table.add_column("Example Query", style="green")

    for category, example in examples:
        table.add_row(category, example)

    console.print(table)

    console.print("\n[dim]Tips:[/dim]")
    console.print("• Be specific about time periods (e.g., 'last 7 days', 'yesterday')")
    console.print("• Mention test names or error messages for targeted results")
    console.print("• Ask for metrics like success rate, failure rate, or counts")
    console.print("• Use --show-sources to see which documents were used")


@query.command()
@click.option(
    "--openai-key",
    help="OpenAI API key",
)
@click.option(
    "--anthropic-key",
    help="Anthropic API key",
)
@click.option(
    "--ollama-url",
    help="Ollama server URL",
)
def configure(openai_key, anthropic_key, ollama_url):
    """Configure LLM providers."""
    console.print("[bold]LLM Configuration[/bold]\n")

    updates = []

    if openai_key:
        updates.append(f"OPENAI_API_KEY={openai_key}")
        console.print("✓ OpenAI API key set")

    if anthropic_key:
        updates.append(f"ANTHROPIC_API_KEY={anthropic_key}")
        console.print("✓ Anthropic API key set")

    if ollama_url:
        updates.append(f"OLLAMA_BASE_URL={ollama_url}")
        console.print(f"✓ Ollama URL set to {ollama_url}")

    if updates:
        env_path = Path(".env")

        if env_path.exists():
            with open(env_path, "a") as f:
                f.write("\n# LLM Configuration\n")
                for update in updates:
                    f.write(f"{update}\n")
        else:
            with open(env_path, "w") as f:
                f.write("# LLM Configuration\n")
                for update in updates:
                    f.write(f"{update}\n")

        console.print("\n[bold green]Configuration saved to .env file[/bold green]")
    else:
        console.print("Choose your LLM provider:\n")
        console.print("1. OpenAI (GPT-4)")
        console.print("2. Anthropic (Claude)")
        console.print("3. Ollama (Local LLMs)")

        choice = click.prompt("Enter choice (1-3)", type=int)

        if choice == 1:
            key = click.prompt("Enter OpenAI API key", hide_input=True)
            with open(".env", "a") as f:
                f.write(f"\nOPENAI_API_KEY={key}\n")
                f.write("LLM_PROVIDER=openai\n")
            console.print("[bold green]OpenAI configured![/bold green]")

        elif choice == 2:
            key = click.prompt("Enter Anthropic API key", hide_input=True)
            with open(".env", "a") as f:
                f.write(f"\nANTHROPIC_API_KEY={key}\n")
                f.write("LLM_PROVIDER=anthropic\n")
            console.print("[bold green]Anthropic configured![/bold green]")

        elif choice == 3:
            url = click.prompt("Enter Ollama URL", default="http://localhost:11434")
            model = click.prompt("Enter model name", default="llama2")
            with open(".env", "a") as f:
                f.write(f"\nOLLAMA_BASE_URL={url}\n")
                f.write(f"OLLAMA_MODEL={model}\n")
                f.write("LLM_PROVIDER=ollama\n")
            console.print("[bold green]Ollama configured![/bold green]")
            console.print("\nMake sure Ollama is running: ollama serve")


if __name__ == "__main__":
    cli()
