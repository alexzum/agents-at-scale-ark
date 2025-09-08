"""Base test class with authentication disabled."""

import os
import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient

# Set environment variable to skip authentication during tests
os.environ["ARK_SKIP_AUTH"] = "true"

class BaseTestCase(unittest.TestCase):
    """Base test case with authentication disabled."""
    
    def setUp(self):
        """Set up test client with authentication disabled."""
        # Ensure ARK_SKIP_AUTH is set for all tests
        os.environ["ARK_SKIP_AUTH"] = "true"
        from ark_api.main import app
        self.client = TestClient(app)
