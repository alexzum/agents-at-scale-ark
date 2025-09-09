"""Example of better test authentication using mocks."""

import unittest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient

class TestWithMockedAuth(unittest.TestCase):
    """Test class that mocks authentication instead of skipping it."""
    
    def setUp(self):
        """Set up test client with mocked authentication."""
        # Mock the authentication middleware to always allow requests
        with patch('ark_api.auth.middleware.AuthMiddleware.dispatch') as mock_dispatch:
            # Make the middleware just pass through without authentication
            async def mock_middleware_dispatch(self, request, call_next):
                return await call_next(request)
            
            mock_dispatch.side_effect = mock_middleware_dispatch
            
            from ark_api.main import app
            self.client = TestClient(app)
    
    def test_protected_endpoint_with_mock(self):
        """Test that protected endpoints work with mocked auth."""
        response = self.client.get("/api/v1/namespaces")
        self.assertEqual(response.status_code, 200)
