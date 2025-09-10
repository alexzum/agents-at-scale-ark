"""Tests for authentication configuration."""
import os
import unittest
from unittest.mock import patch
from ark_sdk.auth.config import AuthConfig


class TestAuthConfig(unittest.TestCase):
    """Test cases for AuthConfig class."""

    def setUp(self):
        """Set up test environment."""
        # Clear any existing environment variables
        for key in list(os.environ.keys()):
            if key.startswith('ARK_'):
                del os.environ[key]

    def test_default_config(self):
        """Test default configuration values."""
        config = AuthConfig()
        
        self.assertEqual(config.jwt_algorithm, "RS256")
        self.assertIsNone(config.jwt_audience)
        self.assertIsNone(config.jwt_issuer)
        self.assertIsNone(config.okta_issuer)
        self.assertIsNone(config.okta_audience)
        self.assertIsNone(config.jwks_url)
        self.assertEqual(config.jwks_cache_ttl, 3600)
        self.assertEqual(config.token_validation_retries, 3)

    def test_environment_variable_loading(self):
        """Test loading configuration from environment variables."""
        test_env = {
            'ARK_JWT_ALGORITHM': 'HS256',
            'ARK_JWT_AUDIENCE': 'test-audience',
            'ARK_JWT_ISSUER': 'test-issuer',
            'ARK_OKTA_ISSUER': 'https://test.okta.com/oauth2/default',
            'ARK_OKTA_AUDIENCE': 'okta-audience',
            'ARK_JWKS_URL': 'https://test.okta.com/.well-known/jwks.json',
            'ARK_JWKS_CACHE_TTL': '7200',
            'ARK_TOKEN_VALIDATION_RETRIES': '5'
        }
        
        with patch.dict(os.environ, test_env):
            config = AuthConfig()
            
            self.assertEqual(config.jwt_algorithm, 'HS256')
            self.assertEqual(config.jwt_audience, 'test-audience')
            self.assertEqual(config.jwt_issuer, 'test-issuer')
            self.assertEqual(config.okta_issuer, 'https://test.okta.com/oauth2/default')
            self.assertEqual(config.okta_audience, 'okta-audience')
            self.assertEqual(config.jwks_url, 'https://test.okta.com/.well-known/jwks.json')
            self.assertEqual(config.jwks_cache_ttl, 7200)
            self.assertEqual(config.token_validation_retries, 5)

    def test_case_insensitive_environment_variables(self):
        """Test that environment variables are case insensitive."""
        test_env = {
            'ark_jwt_algorithm': 'ES256',
            'ark_okta_issuer': 'https://test.okta.com/oauth2/default',
            'ark_okta_audience': 'okta-audience'
        }
        
        with patch.dict(os.environ, test_env):
            config = AuthConfig()
            
            self.assertEqual(config.jwt_algorithm, 'ES256')
            self.assertEqual(config.okta_issuer, 'https://test.okta.com/oauth2/default')
            self.assertEqual(config.okta_audience, 'okta-audience')

    def test_okta_priority_over_jwt(self):
        """Test that OKTA values take priority over JWT values when both are set."""
        test_env = {
            'ARK_JWT_AUDIENCE': 'jwt-audience',
            'ARK_JWT_ISSUER': 'jwt-issuer',
            'ARK_OKTA_AUDIENCE': 'okta-audience',
            'ARK_OKTA_ISSUER': 'https://test.okta.com/oauth2/default'
        }
        
        with patch.dict(os.environ, test_env):
            config = AuthConfig()
            
            # OKTA values should be present
            self.assertEqual(config.okta_audience, 'okta-audience')
            self.assertEqual(config.okta_issuer, 'https://test.okta.com/oauth2/default')
            
            # JWT values should also be present (for backward compatibility)
            self.assertEqual(config.jwt_audience, 'jwt-audience')
            self.assertEqual(config.jwt_issuer, 'jwt-issuer')

    def test_invalid_numeric_values(self):
        """Test handling of invalid numeric environment variables."""
        test_env = {
            'ARK_JWKS_CACHE_TTL': 'invalid-number',
            'ARK_TOKEN_VALIDATION_RETRIES': 'not-a-number'
        }
        
        with patch.dict(os.environ, test_env):
            # Should use default values when invalid numbers are provided
            config = AuthConfig()
            self.assertEqual(config.jwks_cache_ttl, 3600)  # Default value
            self.assertEqual(config.token_validation_retries, 3)  # Default value

    def test_empty_string_values(self):
        """Test handling of empty string environment variables."""
        test_env = {
            'ARK_JWT_AUDIENCE': '',
            'ARK_OKTA_ISSUER': '',
            'ARK_JWKS_URL': ''
        }
        
        with patch.dict(os.environ, test_env):
            config = AuthConfig()
            
            # Empty strings should be treated as None
            self.assertIsNone(config.jwt_audience)
            self.assertIsNone(config.okta_issuer)
            self.assertIsNone(config.jwks_url)


if __name__ == '__main__':
    unittest.main()
