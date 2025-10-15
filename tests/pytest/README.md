# ARK Pytest Test Suite

This directory contains comprehensive pytest tests for the ARK (Agentic Runtime for Kubernetes) platform.

## Overview

The test suite performs a complete ARK workflow:
1. **Virtual Environment Setup** - Creates isolated Python environment
2. **OpenJDK Setup** - Checks and configures OpenJDK if needed
3. **ARK Installation** - Installs ARK platform and CLI
4. **Model Creation** - Skips model creation (interactive command requires user input)
5. **Pods Verification** - Verifies three required ARK pods are running (ark-api, ark-dashboard, ark-mcp)
6. **Dashboard Verification** - Starts ARK dashboard and tests HTTP accessibility on common ports
7. **Pytest Execution** - Tests Kubernetes client functionality
8. **Cleanup** - Removes all resources and virtual environment

## Files

- `test_complete_ark_workflow.py` - Main test file with complete workflow
- `pytest.ini` - Pytest configuration
- `requirements.txt` - Python dependencies
- `conftest.py` - Pytest fixtures
- `README.md` - This file

## Quick Start

### Option 1: Using pytest directly (Recommended)
```bash
# Run all tests with verbose output

python3 -m pytest test_complete_ark_workflow.py -sv
```


## Test Structure

The tests are organized as individual test functions:

- `test_ark_venv_setup()` - Virtual environment setup
- `test_ark_openjdk_setup()` - OpenJDK availability and PATH configuration
- `test_ark_installation()` - ßARK installation
- `test_ark_model_creation()` - Default model creation (skipped due to interactive prompts)
- `test_ark_pods_verification()` - Verifies three required ARK pods (ark-api, ark-dashboard, ark-mcp)
- `test_ark_dashboard_verification()` - Starts dashboard and tests HTTP accessibility on common ports
- `test_ark_pytest_execution()` - Kubernetes client test
- `test_ark_cleanup()` - Resource cleanup
- `test_complete_ark_workflow()` - Integration summary

## Prerequisites

- Python 3.7+
- Kubernetes cluster (minikube, kind, etc.)
- kubectl configured
- Node.js and npm (for ARK CLI)
- OpenJDK 11+ (system-level installation, not Python package)

## Environment Variables

- `ARK_NAMESPACE` - ARK namespace (default: "default")
- `ARK_CONTROLLER_NAMESPACE` - Controller namespace (default: "ark-system")

## Troubleshooting


### Clean Start

Clean up everything and start fresh:
```bash
# Clean up test artifacts
rm -rf .pytest_cache __pycache__ venv

# Run tests
python3 -m pytest test_complete_ark_workflow.py -v
```
