#!/usr/bin/env python3
"""
Quick test to verify ark-auth is working.
Run this to do a basic check of the authentication system.
"""

import os
import sys

def test_imports():
    """Test basic imports."""
    print("🔍 Testing imports...")
    
    try:
        # Add paths
        sys.path.insert(0, '/Users/Isha_Deep/AgentAtScaleArkNew/agents-at-scale-ark/services/ark-auth/ark-auth/src')
        sys.path.insert(0, '/Users/Isha_Deep/AgentAtScaleArkNew/agents-at-scale-ark/services/ark-api/ark-api/src')
        
        from ark_auth.validator import validate_jwt
        from ark_auth.dependencies import validate_token
        from ark_auth.config import settings
        from ark_auth.exceptions import InvalidTokenException
        
        print("✅ All imports successful")
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def test_configuration():
    """Test configuration loading."""
    print("\n🔍 Testing configuration...")
    
    # Set test environment variables
    os.environ["ARK_OKTA_ISSUER"] = "https://test.okta.com/oauth2/default"
    os.environ["ARK_OKTA_AUDIENCE"] = "test-audience"
    
    try:
        from ark_auth.config import settings
        
        if settings.okta_issuer and settings.okta_audience:
            print(f"✅ Configuration loaded: {settings.okta_issuer}")
            return True
        else:
            print("❌ Configuration values are empty")
            return False
    except Exception as e:
        print(f"❌ Configuration failed: {e}")
        return False

def test_ark_api_routes():
    """Test that ark-api routes have authentication."""
    print("\n🔍 Testing ark-api route authentication...")
    
    try:
        from ark_api.api.routes import router as main_router
        from ark_api.api.v1.agents import router as agents_router
        
        # Check main router
        main_auth_count = 0
        for route in main_router.routes:
            if hasattr(route, 'dependant') and route.dependant:
                deps = route.dependant.dependencies
                has_auth = any('validate_token' in str(dep) for dep in deps)
                if has_auth:
                    main_auth_count += 1
        
        # Check agents router
        agents_auth_count = 0
        for route in agents_router.routes:
            if hasattr(route, 'dependant') and route.dependant:
                deps = route.dependant.dependencies
                has_auth = any('validate_token' in str(dep) for dep in deps)
                if has_auth:
                    agents_auth_count += 1
        
        print(f"✅ Main router: {main_auth_count} routes with auth")
        print(f"✅ Agents router: {agents_auth_count} routes with auth")
        
        if main_auth_count > 0 and agents_auth_count > 0:
            return True
        else:
            print("❌ No routes found with authentication")
            return False
            
    except Exception as e:
        print(f"❌ Route test failed: {e}")
        return False

def main():
    """Run quick tests."""
    print("🚀 Quick ark-auth Test")
    print("=" * 30)
    
    tests = [
        test_imports,
        test_configuration,
        test_ark_api_routes,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print(f"\n📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ark-auth is working correctly!")
        return True
    else:
        print("⚠️  Some issues found. Check the output above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
