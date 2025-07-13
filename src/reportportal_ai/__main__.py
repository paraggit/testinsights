"""Main entry point for the reportportal_ai package."""

import sys
from src.reportportal_ai.cli import cli

if __name__ == "__main__":
    sys.exit(cli())