#!/usr/bin/env python3
"""
Test runner script for TestInsight API tests.

This script provides an easy way to run different types of tests with proper configuration.
"""

import argparse
import subprocess
import sys
from pathlib import Path


def run_command(cmd: list[str], description: str) -> int:
    """Run a command and return the exit code."""
    print(f"\n{'=' * 60}")
    print(f"🧪 {description}")
    print(f"{'=' * 60}")
    print(f"Running: {' '.join(cmd)}")
    print()

    try:
        # Run from project root (parent of scripts directory)
        project_root = Path(__file__).parent.parent
        result = subprocess.run(cmd, cwd=project_root)
        return result.returncode
    except KeyboardInterrupt:
        print("\n❌ Tests interrupted by user")
        return 1
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return 1


def main():
    """Main test runner function."""
    parser = argparse.ArgumentParser(description="TestInsight API Test Runner")

    parser.add_argument(
        "--type",
        choices=["all", "unit", "integration", "api", "config"],
        default="all",
        help="Type of tests to run (default: all)",
    )

    parser.add_argument("--coverage", action="store_true", help="Run tests with coverage reporting")

    parser.add_argument("--verbose", "-v", action="store_true", help="Run tests in verbose mode")

    parser.add_argument("--fast", action="store_true", help="Skip slow tests")

    parser.add_argument("--file", help="Run tests from specific file")

    parser.add_argument("--pattern", "-k", help="Run tests matching pattern")

    args = parser.parse_args()

    # Build pytest command
    cmd = ["poetry", "run", "pytest"]

    # Add verbosity
    if args.verbose:
        cmd.append("-v")
    else:
        cmd.append("-q")

    # Add coverage
    if args.coverage:
        cmd.extend(
            [
                "--cov=test_insights",
                "--cov-report=html",
                "--cov-report=term-missing",
                "--cov-branch",
            ]
        )

    # Add test type filtering
    if args.type == "unit":
        cmd.extend(["-m", "unit"])
    elif args.type == "integration":
        cmd.extend(["-m", "integration"])
    elif args.type == "api":
        cmd.extend(["-m", "api"])
    elif args.type == "config":
        cmd.extend(["-m", "config"])

    # Skip slow tests if requested
    if args.fast:
        cmd.extend(["-m", "not slow"])

    # Add pattern matching
    if args.pattern:
        cmd.extend(["-k", args.pattern])

    # Add specific file
    if args.file:
        cmd.append(args.file)
    else:
        # Default to test directory
        cmd.append("test_insights/tests/")

    # Add additional pytest options
    cmd.extend(
        [
            "--tb=short",  # Shorter traceback format
            "--strict-markers",  # Strict marker checking
            "--disable-warnings",  # Reduce noise
        ]
    )

    print("🚀 TestInsight API Test Runner")
    print(f"📋 Test type: {args.type}")
    print(f"📊 Coverage: {'enabled' if args.coverage else 'disabled'}")
    print(f"🔍 Verbose: {'enabled' if args.verbose else 'disabled'}")

    # Run the tests
    exit_code = run_command(cmd, f"Running {args.type} tests")

    if exit_code == 0:
        print("\n✅ All tests passed!")

        if args.coverage:
            print("📊 Coverage report generated in htmlcov/")
            print("   Open htmlcov/index.html to view detailed coverage")
    else:
        print(f"\n❌ Tests failed with exit code {exit_code}")

    return exit_code


def run_specific_test_suites():
    """Run specific test suites with predefined configurations."""
    test_suites = {
        "quick": {
            "description": "Quick smoke tests",
            "cmd": [
                "poetry",
                "run",
                "pytest",
                "-x",
                "-q",
                "--tb=line",
                "test_insights/tests/api/test_endpoints.py::TestRootEndpoint",
                "test_insights/tests/config/test_settings.py::TestSettings::test_default_settings",
            ],
        },
        "api": {
            "description": "All API endpoint tests",
            "cmd": ["poetry", "run", "pytest", "-v", "test_insights/tests/api/"],
        },
        "config": {
            "description": "Configuration and settings tests",
            "cmd": ["poetry", "run", "pytest", "-v", "test_insights/tests/config/"],
        },
        "models": {
            "description": "Model validation tests",
            "cmd": ["poetry", "run", "pytest", "-v", "test_insights/tests/api/test_models.py"],
        },
        "integration": {
            "description": "Integration workflow tests",
            "cmd": ["poetry", "run", "pytest", "-v", "test_insights/tests/api/test_integration.py"],
        },
    }

    if len(sys.argv) > 1 and sys.argv[1] in test_suites:
        suite_name = sys.argv[1]
        suite = test_suites[suite_name]

        exit_code = run_command(suite["cmd"], suite["description"])
        return exit_code

    return None


if __name__ == "__main__":
    # Check for specific test suite commands
    suite_result = run_specific_test_suites()
    if suite_result is not None:
        sys.exit(suite_result)

    # Run main test runner
    sys.exit(main())
