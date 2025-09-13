#!/usr/bin/env python3
"""
Startup script for TestInsight FastAPI server.

This script starts the FastAPI server with appropriate configuration.
"""

import argparse
import sys
from pathlib import Path

import uvicorn


def main():
    """Main entry point for the API server."""
    # Import settings after adding project root to path
    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root))
    from test_insights.config.settings import settings

    parser = argparse.ArgumentParser(description="TestInsight API Server")
    parser.add_argument("--host", help="Host to bind to (overrides config)")
    parser.add_argument("--port", type=int, help="Port to bind to (overrides config)")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload for development")
    parser.add_argument(
        "--log-level",
        choices=["debug", "info", "warning", "error"],
        help="Log level (overrides config)",
    )
    parser.add_argument("--workers", type=int, help="Number of worker processes")

    args = parser.parse_args()

    # Check if .env file exists
    env_file = Path(".env")
    if not env_file.exists():
        print("Warning: .env file not found. Make sure to configure your environment variables.")
        print("Run 'test_insights config init' to create a configuration file.")

    # Use CLI args or fall back to settings
    effective_host = args.host or settings.api_host
    effective_port = args.port or settings.api_port
    effective_log_level = args.log_level or settings.effective_log_level.lower()
    effective_workers = args.workers or settings.workers

    print(f"Starting TestInsight API server on {effective_host}:{effective_port}")

    if settings.enable_docs:
        print(f"API documentation: http://localhost:{effective_port}/docs")
    if settings.enable_redoc:
        print(f"Alternative docs: http://localhost:{effective_port}/redoc")

    try:
        uvicorn.run(
            "test_insights.api.app:app",
            host=effective_host,
            port=effective_port,
            reload=args.reload or settings.is_development(),
            log_level=effective_log_level,
            workers=effective_workers if not args.reload else 1,
        )
    except KeyboardInterrupt:
        print("\nShutting down server...")
        sys.exit(0)
    except Exception as e:
        print(f"Failed to start server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
