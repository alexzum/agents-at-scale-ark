"""
Test cases for ARK_SKIP_AUTH environment variable functionality.
"""

import os
import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient

from src.ark_api.main import app


class TestSkipAuth(unittest.TestCase):
    """Test ARK_SKIP_AUTH environment variable functionality."""

    def setUp(self):
        """Set up test client."""
        self.client = TestClient(app)

    def test_auth_enabled_by_default(self):
        """Test that authentication is enabled by default."""
        # Ensure ARK_SKIP_AUTH is not set
        with patch.dict(os.environ, {}, clear=True):
            # Try to access a protected endpoint without auth
            response = self.client.get("/v1/namespaces")
            # Should get 401 Unauthorized
            self.assertEqual(response.status_code, 401)

    def test_auth_disabled_with_skip_auth_true(self):
        """Test that authentication is disabled when ARK_SKIP_AUTH=true."""
        with patch.dict(os.environ, {"ARK_SKIP_AUTH": "true"}):
            # Try to access a protected endpoint without auth
            response = self.client.get("/v1/namespaces")
            # Should get 200 OK (auth is skipped) or 500 (K8s not available in test)
            self.assertIn(response.status_code, [200, 500])

    def test_auth_disabled_with_skip_auth_uppercase(self):
        """Test that authentication is disabled when ARK_SKIP_AUTH=TRUE."""
        with patch.dict(os.environ, {"ARK_SKIP_AUTH": "TRUE"}):
            # Try to access a protected endpoint without auth
            response = self.client.get("/v1/namespaces")
            # Should get 200 OK (auth is skipped) or 500 (K8s not available in test)
            self.assertIn(response.status_code, [200, 500])

    def test_auth_enabled_with_skip_auth_false(self):
        """Test that authentication is enabled when ARK_SKIP_AUTH=false."""
        with patch.dict(os.environ, {"ARK_SKIP_AUTH": "false"}):
            # Try to access a protected endpoint without auth
            response = self.client.get("/v1/namespaces")
            # Should get 401 Unauthorized
            self.assertEqual(response.status_code, 401)

    def test_public_routes_always_accessible(self):
        """Test that public routes are always accessible regardless of ARK_SKIP_AUTH."""
        # Test with auth enabled
        with patch.dict(os.environ, {"ARK_SKIP_AUTH": "false"}):
            response = self.client.get("/health")
            self.assertEqual(response.status_code, 200)

        # Test with auth disabled
        with patch.dict(os.environ, {"ARK_SKIP_AUTH": "true"}):
            response = self.client.get("/health")
            self.assertEqual(response.status_code, 200)


if __name__ == "__main__":
    unittest.main()
