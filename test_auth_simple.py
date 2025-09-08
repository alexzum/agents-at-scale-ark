#!/usr/bin/env python3
"""
Simple test script to verify authentication is working.
"""

import requests
import os

# Set the base URL for the API
BASE_URL = "http://localhost:8000"

def test_public_endpoints():
    """Test that public endpoints work without authentication."""
    print("Testing public endpoints...")
    
    # Test health endpoint
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"Health endpoint: {response.status_code}")
        if response.status_code == 200:
            print("✓ Health endpoint accessible")
        else:
            print(f"✗ Health endpoint failed: {response.text}")
    except Exception as e:
        print(f"✗ Health endpoint error: {e}")
    
    # Test docs endpoint
    try:
        response = requests.get(f"{BASE_URL}/docs")
        print(f"Docs endpoint: {response.status_code}")
        if response.status_code == 200:
            print("✓ Docs endpoint accessible")
        else:
            print(f"✗ Docs endpoint failed: {response.text}")
    except Exception as e:
        print(f"✗ Docs endpoint error: {e}")

def test_protected_endpoints():
    """Test that protected endpoints require authentication."""
    print("\nTesting protected endpoints...")
    
    # Test namespaces endpoint without auth
    try:
        response = requests.get(f"{BASE_URL}/api/v1/namespaces")
        print(f"Namespaces endpoint (no auth): {response.status_code}")
        if response.status_code == 401:
            print("✓ Namespaces endpoint properly protected")
        else:
            print(f"✗ Namespaces endpoint should be protected: {response.text}")
    except Exception as e:
        print(f"✗ Namespaces endpoint error: {e}")

def test_with_skip_auth():
    """Test with ARK_SKIP_AUTH=true to bypass authentication."""
    print("\nTesting with ARK_SKIP_AUTH=true...")
    
    # Set environment variable
    os.environ["ARK_SKIP_AUTH"] = "true"
    
    try:
        response = requests.get(f"{BASE_URL}/api/v1/namespaces")
        print(f"Namespaces endpoint (skip auth): {response.status_code}")
        if response.status_code == 200:
            print("✓ Namespaces endpoint accessible with skip auth")
        else:
            print(f"✗ Namespaces endpoint failed even with skip auth: {response.text}")
    except Exception as e:
        print(f"✗ Namespaces endpoint error: {e}")
    finally:
        # Clean up environment variable
        if "ARK_SKIP_AUTH" in os.environ:
            del os.environ["ARK_SKIP_AUTH"]

if __name__ == "__main__":
    print("ARK API Authentication Test")
    print("=" * 40)
    
    test_public_endpoints()
    test_protected_endpoints()
    test_with_skip_auth()
    
    print("\nTest completed!")
