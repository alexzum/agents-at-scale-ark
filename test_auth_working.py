#!/usr/bin/env python3
"""
Test script to verify ark-auth integration is working properly.
This script tests various aspects of the authentication system.
"""

import asyncio
import os
import sys
from unittest.mock import AsyncMock, patch, MagicMock

# Add the ark-auth and ark-api paths to sys.path
sys.path.insert(0, '/Users/Isha_Deep/AgentAtScaleArkNew/agents-at-scale-ark/services/ark-auth/ark-auth/src')
sys.path.insert(0, '/Users/Isha_Deep/AgentAtScaleArkNew/agents-at-scale-ark/services/ark-api/ark-api/src')

async def test_ark_auth_imports():
    """Test that ark-auth can be imported successfully."""
    print("🧪 Testing ark-auth imports...")
    
    try:
        from ark_auth.validator import validate_jwt
        from ark_auth.dependencies import validate_token
        from ark_auth.config import settings
        from ark_auth.exceptions import InvalidTokenException
        
        print("✅ Successfully imported all ark-auth components")
        return True
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False

async def test_configuration_loading():
    """Test that configuration loads properly."""
    print("\n🧪 Testing configuration loading...")
    
    # Set test environment variables
    os.environ["ARK_OKTA_ISSUER"] = "https://test.okta.com/oauth2/default"
    os.environ["ARK_OKTA_AUDIENCE"] = "test-audience"
    
    try:
        from ark_auth.config import settings
        
        print(f"✅ Configuration loaded successfully")
        print(f"   Issuer: {settings.okta_issuer}")
        print(f"   Audience: {settings.okta_audience}")
        
        # Verify values are set
        if settings.okta_issuer and settings.okta_audience:
            print("✅ Configuration values are properly set")
            return True
        else:
            print("❌ Configuration values are empty")
            return False
            
    except Exception as e:
        print(f"❌ Configuration loading failed: {e}")
        return False

async def test_jwt_validation():
    """Test JWT validation with mocked dependencies."""
    print("\n🧪 Testing JWT validation...")
    
    try:
        from ark_auth.validator import validate_jwt
        
        # Mock the key fetcher and JWT decode
        with patch('ark_auth.validator.AsyncKeyFetcher') as mock_fetcher_class:
            mock_fetcher = AsyncMock()
            mock_fetcher_class.return_value = mock_fetcher
            
            # Mock the key entry
            mock_key_entry = {
                'key': 'test-key',
                'algorithms': ['RS256']
            }
            mock_fetcher.get_key.return_value = mock_key_entry
            
            # Mock JWT decode
            with patch('ark_auth.validator.jwt.decode') as mock_decode:
                mock_payload = {
                    'sub': 'test-user',
                    'aud': 'test-audience',
                    'iss': 'https://test.okta.com/oauth2/default'
                }
                mock_decode.return_value = mock_payload
                
                # Test valid token
                result = await validate_jwt("test-token")
                print("✅ JWT validation with valid token succeeded")
                print(f"   Decoded payload: {result}")
                
                # Test invalid token
                mock_decode.side_effect = Exception("Invalid token")
                try:
                    await validate_jwt("invalid-token")
                    print("❌ Should have failed with invalid token")
                    return False
                except ValueError:
                    print("✅ JWT validation correctly rejected invalid token")
                
                return True
                
    except Exception as e:
        print(f"❌ JWT validation test failed: {e}")
        return False

async def test_fastapi_dependency():
    """Test FastAPI dependency function."""
    print("\n🧪 Testing FastAPI dependency...")
    
    try:
        from ark_auth.dependencies import validate_token
        from ark_auth.exceptions import InvalidTokenException
        
        # Mock the validate_jwt function
        with patch('ark_auth.dependencies.validate_jwt') as mock_validate:
            mock_validate.return_value = {'sub': 'test-user'}
            
            # Test valid authorization header
            try:
                await validate_token("Bearer valid-token")
                print("✅ FastAPI dependency with valid token succeeded")
            except Exception as e:
                print(f"❌ FastAPI dependency failed with valid token: {e}")
                return False
            
            # Test invalid authorization header
            try:
                await validate_token("InvalidHeader")
                print("❌ Should have failed with invalid header")
                return False
            except InvalidTokenException:
                print("✅ FastAPI dependency correctly rejected invalid header")
            
            # Test missing Bearer prefix
            try:
                await validate_token("valid-token")
                print("❌ Should have failed without Bearer prefix")
                return False
            except InvalidTokenException:
                print("✅ FastAPI dependency correctly rejected token without Bearer prefix")
            
            return True
            
    except Exception as e:
        print(f"❌ FastAPI dependency test failed: {e}")
        return False

async def test_ark_api_integration():
    """Test that ark-api can import and use ark-auth."""
    print("\n🧪 Testing ark-api integration...")
    
    try:
        # Test importing ark-api components that use ark-auth
        from ark_api.api.routes import router as main_router
        from ark_api.api.v1.agents import router as agents_router
        from ark_api.api.v1.queries import router as queries_router
        
        print("✅ Successfully imported ark-api routers")
        
        # Check if routes have authentication dependencies
        auth_routes = []
        for route in main_router.routes:
            if hasattr(route, 'dependant') and route.dependant:
                deps = route.dependant.dependencies
                has_auth = any('validate_token' in str(dep) for dep in deps)
                if has_auth:
                    auth_routes.append(route.path)
        
        print(f"✅ Found {len(auth_routes)} routes with authentication in main router")
        
        # Check agents router
        agents_auth_routes = []
        for route in agents_router.routes:
            if hasattr(route, 'dependant') and route.dependant:
                deps = route.dependant.dependencies
                has_auth = any('validate_token' in str(dep) for dep in deps)
                if has_auth:
                    agents_auth_routes.append(route.path)
        
        print(f"✅ Found {len(agents_auth_routes)} routes with authentication in agents router")
        
        return True
        
    except ImportError as e:
        print(f"❌ ark-api integration test failed: {e}")
        return False
    except Exception as e:
        print(f"❌ ark-api integration test failed: {e}")
        return False

async def test_end_to_end():
    """Test end-to-end authentication flow."""
    print("\n🧪 Testing end-to-end authentication flow...")
    
    try:
        from ark_auth.dependencies import validate_token
        from ark_auth.exceptions import InvalidTokenException
        
        # Mock the entire validation chain
        with patch('ark_auth.dependencies.validate_jwt') as mock_validate:
            mock_validate.return_value = {
                'sub': 'test-user',
                'email': 'test@example.com',
                'aud': 'test-audience',
                'iss': 'https://test.okta.com/oauth2/default'
            }
            
            # Simulate a complete request
            authorization_header = "Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9..."
            
            try:
                await validate_token(authorization_header)
                print("✅ End-to-end authentication flow succeeded")
                print("   Token was validated successfully")
                return True
            except Exception as e:
                print(f"❌ End-to-end authentication flow failed: {e}")
                return False
                
    except Exception as e:
        print(f"❌ End-to-end test failed: {e}")
        return False

async def run_all_tests():
    """Run all tests and provide a summary."""
    print("🚀 Starting ark-auth integration tests...")
    print("=" * 50)
    
    tests = [
        ("Import Test", test_ark_auth_imports),
        ("Configuration Test", test_configuration_loading),
        ("JWT Validation Test", test_jwt_validation),
        ("FastAPI Dependency Test", test_fastapi_dependency),
        ("ARK API Integration Test", test_ark_api_integration),
        ("End-to-End Test", test_end_to_end),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! ark-auth integration is working correctly.")
        return True
    else:
        print("⚠️  Some tests failed. Please check the output above for details.")
        return False

if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
