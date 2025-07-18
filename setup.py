"""Setup script for reportportal-ai-assistant."""

from setuptools import find_packages, setup

setup(
    name="reportportal-ai-assistant",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    entry_points={
        "console_scripts": [
            "tests_insights=test_insights.cli:cli",
        ],
    },
)
