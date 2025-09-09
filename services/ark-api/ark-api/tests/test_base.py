"""Base test class with proper test app (no authentication middleware)."""

import unittest
from fastapi.testclient import TestClient

class BaseTestCase(unittest.TestCase):
    """Base test case using test app without authentication middleware."""
    
    def setUp(self):
        """Set up test client using test app factory."""
        from ark_api.test_app import create_test_app
        app = create_test_app()
        self.client = TestClient(app)
