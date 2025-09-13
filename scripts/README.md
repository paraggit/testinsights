# TestInsight Utility Scripts

This directory contains utility scripts for development and testing of the TestInsight API.

## 📁 Scripts Overview

### 🧪 `run_tests.py` - Test Runner Script

Comprehensive test runner for the TestInsight API test suite.

#### Usage

```bash
# From project root
python scripts/run_tests.py [options]

# Or make it executable and run directly
chmod +x scripts/run_tests.py
./scripts/run_tests.py [options]
```

#### Quick Commands

```bash
# Quick smoke tests
python scripts/run_tests.py quick

# All tests
python scripts/run_tests.py --type all

# Specific test types
python scripts/run_tests.py --type api
python scripts/run_tests.py --type config
python scripts/run_tests.py --type integration

# With coverage report
python scripts/run_tests.py --coverage

# Verbose output
python scripts/run_tests.py --verbose

# Fast tests (skip slow ones)
python scripts/run_tests.py --fast

# Specific test file
python scripts/run_tests.py --file test_insights/tests/api/test_endpoints.py

# Pattern matching
python scripts/run_tests.py --pattern "test_query"
```

#### Predefined Test Suites

```bash
# Quick smoke tests
python scripts/run_tests.py quick

# All API endpoint tests
python scripts/run_tests.py api

# Configuration tests
python scripts/run_tests.py config

# Model validation tests
python scripts/run_tests.py models

# Integration workflow tests
python scripts/run_tests.py integration
```

#### Features

- ✅ **Multiple test types** - Unit, integration, API, config
- ✅ **Coverage reporting** - HTML and terminal reports
- ✅ **Pattern matching** - Run specific tests by name
- ✅ **Performance options** - Fast mode, parallel execution
- ✅ **Detailed output** - Verbose and quiet modes
- ✅ **CI/CD ready** - Designed for automated testing

### 🚀 `run_api.py` - API Server Launcher

Standalone script to launch the FastAPI development server.

#### Usage

```bash
# From project root
python scripts/run_api.py [options]

# Or make it executable and run directly
chmod +x scripts/run_api.py
./scripts/run_api.py [options]
```

#### Options

```bash
# Basic usage (uses settings from .env or defaults)
python scripts/run_api.py

# Custom host and port
python scripts/run_api.py --host 127.0.0.1 --port 9000

# Enable auto-reload for development
python scripts/run_api.py --reload

# Custom log level
python scripts/run_api.py --log-level debug

# Multiple workers (production)
python scripts/run_api.py --workers 4

# Combination
python scripts/run_api.py --host 0.0.0.0 --port 8080 --reload --log-level info
```

#### Features

- ✅ **Environment integration** - Uses `.env` file and settings
- ✅ **CLI overrides** - Command-line arguments override config
- ✅ **Development mode** - Auto-reload and debug options
- ✅ **Production ready** - Multi-worker support
- ✅ **Flexible configuration** - Host, port, logging customization

## 🔧 Setup Instructions

### Prerequisites

Make sure you have the project dependencies installed:

```bash
# Install project dependencies
poetry install

# Or if using pip
pip install -r requirements.txt
```

### Environment Configuration

Create a `.env` file in the project root (use `.env.example` as template):

```bash
# Copy example environment file
cp .env.example .env

# Edit with your settings
nano .env
```

### Make Scripts Executable (Optional)

```bash
# Make scripts executable
chmod +x scripts/run_tests.py
chmod +x scripts/run_api.py

# Now you can run them directly
./scripts/run_tests.py quick
./scripts/run_api.py --reload
```

## 📋 Common Workflows

### Development Workflow

```bash
# 1. Start API server in development mode
python scripts/run_api.py --reload --log-level debug

# 2. In another terminal, run tests
python scripts/run_tests.py quick

# 3. Run specific tests while developing
python scripts/run_tests.py --pattern "test_query" --verbose

# 4. Generate coverage report
python scripts/run_tests.py --coverage
```

### Testing Workflow

```bash
# Quick validation
python scripts/run_tests.py quick

# Full test suite
python scripts/run_tests.py --type all --verbose

# API-specific tests
python scripts/run_tests.py api

# Integration tests
python scripts/run_tests.py integration

# Generate coverage report
python scripts/run_tests.py --coverage
open htmlcov/index.html
```

### Production Deployment

```bash
# Test everything before deployment
python scripts/run_tests.py --type all

# Start production server
python scripts/run_api.py --host 0.0.0.0 --port 8000 --workers 4 --log-level info
```

## 🎯 Integration with Project

### CLI Integration

The main CLI also provides API commands:

```bash
# Using the main CLI
poetry run test_insights api start --host 127.0.0.1 --port 8000 --reload

# Using the standalone script
python scripts/run_api.py --host 127.0.0.1 --port 8000 --reload
```

### IDE Integration

You can configure your IDE to use these scripts:

#### VS Code Tasks (`.vscode/tasks.json`)

```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Run API Server",
      "type": "shell",
      "command": "python",
      "args": ["scripts/run_api.py", "--reload"],
      "group": "build",
      "presentation": {
        "echo": true,
        "reveal": "always",
        "focus": false,
        "panel": "new"
      }
    },
    {
      "label": "Run Tests",
      "type": "shell",
      "command": "python",
      "args": ["scripts/run_tests.py", "--verbose"],
      "group": "test",
      "presentation": {
        "echo": true,
        "reveal": "always",
        "focus": false,
        "panel": "new"
      }
    }
  ]
}
```

### Docker Integration

```dockerfile
# Copy scripts
COPY scripts/ /app/scripts/

# Make executable
RUN chmod +x /app/scripts/*.py

# Use in container
CMD ["python", "scripts/run_api.py", "--host", "0.0.0.0", "--port", "8000"]
```

## 🔍 Troubleshooting

### Common Issues

1. **Import Errors**

   ```bash
   # Make sure you're in the project root
   cd /path/to/TestInsight
   python scripts/run_tests.py
   ```

2. **Permission Denied**

   ```bash
   # Make scripts executable
   chmod +x scripts/*.py
   ```

3. **Environment Issues**

   ```bash
   # Check if .env file exists
   ls -la .env

   # Create from example if missing
   cp .env.example .env
   ```

4. **Dependencies Missing**
   ```bash
   # Install dependencies
   poetry install
   # or
   pip install -r requirements.txt
   ```

### Debug Mode

Both scripts support verbose output for debugging:

```bash
# Test runner debug
python scripts/run_tests.py --verbose --pattern "specific_test"

# API server debug
python scripts/run_api.py --log-level debug --reload
```

## 🎉 Benefits

Moving these scripts to the `scripts/` directory provides:

- ✅ **Cleaner project root** - Less clutter in main directory
- ✅ **Better organization** - Utility scripts grouped together
- ✅ **Clear purpose** - Obvious development/testing tools
- ✅ **Easy discovery** - Developers know where to find utilities
- ✅ **Maintainability** - Centralized script management
- ✅ **Documentation** - Clear usage instructions in one place

These scripts make development and testing of the TestInsight API much more convenient and efficient! 🚀
