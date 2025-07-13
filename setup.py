"""Setup script for reportportal-ai-assistant."""

from setuptools import setup, find_packages

setup(
    name="reportportal-ai-assistant",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    entry_points={
        "console_scripts": [
            "reportportal-ai=test_insights.cli:cli",
        ],
    },
)