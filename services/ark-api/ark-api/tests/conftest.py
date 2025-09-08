"""Test configuration and fixtures."""

import os
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

# Set environment variable to skip authentication during tests
os.environ["ARK_SKIP_AUTH"] = "true"

@pytest.fixture(scope="session")
def test_client():
    """Create a test client with authentication disabled."""
    # Ensure ARK_SKIP_AUTH is set
    os.environ["ARK_SKIP_AUTH"] = "true"
    
    from ark_api.main import app
    return TestClient(app)

@pytest.fixture(autouse=True)
def skip_auth():
    """Automatically skip authentication for all tests."""
    with patch.dict(os.environ, {"ARK_SKIP_AUTH": "true"}):
        yield
