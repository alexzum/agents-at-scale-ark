"""Integration tests for authentication functionality."""

import unittest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, Mock

class TestAuthenticationIntegration(unittest.TestCase):
    """Test authentication integration with the real app."""
    
    def setUp(self):
        """Set up test client with real app (with authentication)."""
        from ark_api.main import app
        self.client = TestClient(app)
    
    def test_protected_endpoint_without_auth_returns_401(self):
        """Test that protected endpoints return 401 without authentication."""
        response = self.client.get("/api/v1/namespaces")
        self.assertEqual(response.status_code, 401)
        self.assertIn("Missing or invalid authorization header", response.json()["detail"])
    
    def test_protected_endpoint_with_invalid_auth_returns_401(self):
        """Test that protected endpoints return 401 with invalid auth."""
        response = self.client.get(
            "/api/v1/namespaces",
            headers={"Authorization": "InvalidToken"}
        )
        self.assertEqual(response.status_code, 401)
    
    def test_protected_endpoint_with_bearer_but_no_token_returns_401(self):
        """Test that protected endpoints return 401 with Bearer but no token."""
        response = self.client.get(
            "/api/v1/namespaces",
            headers={"Authorization": "Bearer"}
        )
        self.assertEqual(response.status_code, 401)
    
    @patch('ark_api.auth.middleware.validate_token', new_callable=AsyncMock)
    @patch('ark_api.api.v1.namespaces.client.CoreV1Api')
    def test_protected_endpoint_with_valid_token_succeeds(self, mock_v1_api, mock_validate_token):
        """Test that protected endpoints work with valid token."""
        # Mock the token validation to succeed (no exception)
        mock_validate_token.return_value = None
        
        # Mock the Kubernetes API response
        mock_api_instance = mock_v1_api.return_value
        mock_response = Mock()
        mock_response.items = []
        mock_api_instance.list_namespace = Mock(return_value=mock_response)
        
        response = self.client.get(
            "/api/v1/namespaces",
            headers={"Authorization": "Bearer valid-token"}
        )
        # Authentication should pass, but we'll get a 200 or other non-401 status
        self.assertNotEqual(response.status_code, 401)
    
    def test_public_endpoints_work_without_auth(self):
        """Test that public endpoints work without authentication."""
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        
        response = self.client.get("/ready")
        self.assertEqual(response.status_code, 200)
        
        response = self.client.get("/docs")
        self.assertEqual(response.status_code, 200)
