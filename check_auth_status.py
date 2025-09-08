#!/usr/bin/env python3
"""
Simple script to check the current authentication status without requiring dependencies.
This script examines the code to see if authentication is properly integrated.
"""

import os
import re
from pathlib import Path

def check_auth_imports():
    """Check if ark-auth is properly imported in ark-api."""
    print("🔍 Checking ark-auth imports in ark-api...")
    
    # Check main routes file
    routes_file = Path("services/ark-api/ark-api/src/ark_api/api/routes.py")
    if routes_file.exists():
        content = routes_file.read_text()
        if "from ark_auth.dependencies import validate_token" in content:
            print("✅ ark-auth imported in main routes")
        else:
            print("❌ ark-auth not imported in main routes")
            return False
    else:
        print("❌ Main routes file not found")
        return False
    
    # Check agents file
    agents_file = Path("services/ark-api/ark-api/src/ark_api/api/v1/agents.py")
    if agents_file.exists():
        content = agents_file.read_text()
        if "from ark_auth.dependencies import validate_token" in content:
            print("✅ ark-auth imported in agents routes")
        else:
            print("❌ ark-auth not imported in agents routes")
            return False
    else:
        print("❌ Agents file not found")
        return False
    
    # Check queries file
    queries_file = Path("services/ark-api/ark-api/src/ark_api/api/v1/queries.py")
    if queries_file.exists():
        content = queries_file.read_text()
        if "from ark_auth.dependencies import validate_token" in content:
            print("✅ ark-auth imported in queries routes")
        else:
            print("❌ ark-auth not imported in queries routes")
            return False
    else:
        print("❌ Queries file not found")
        return False
    
    return True

def check_auth_usage():
    """Check if validate_token is being used in route functions."""
    print("\n🔍 Checking validate_token usage in routes...")
    
    files_to_check = [
        "services/ark-api/ark-api/src/ark_api/api/routes.py",
        "services/ark-api/ark-api/src/ark_api/api/v1/agents.py",
        "services/ark-api/ark-api/src/ark_api/api/v1/queries.py",
    ]
    
    total_usage = 0
    
    for file_path in files_to_check:
        file = Path(file_path)
        if file.exists():
            content = file.read_text()
            # Count occurrences of Depends(validate_token)
            usage_count = content.count("Depends(validate_token)")
            if usage_count > 0:
                print(f"✅ {file_path}: {usage_count} usages of validate_token")
                total_usage += usage_count
            else:
                print(f"❌ {file_path}: No usage of validate_token")
        else:
            print(f"❌ {file_path}: File not found")
    
    if total_usage > 0:
        print(f"✅ Total validate_token usages found: {total_usage}")
        return True
    else:
        print("❌ No validate_token usages found")
        return False

def check_auth_files():
    """Check if ark-auth files exist and are properly structured."""
    print("\n🔍 Checking ark-auth file structure...")
    
    auth_files = [
        "services/ark-auth/ark-auth/src/ark_auth/__init__.py",
        "services/ark-auth/ark-auth/src/ark_auth/validator.py",
        "services/ark-auth/ark-auth/src/ark_auth/dependencies.py",
        "services/ark-auth/ark-auth/src/ark_auth/config.py",
        "services/ark-auth/ark-auth/src/ark_auth/exceptions.py",
        "services/ark-auth/ark-auth/pyproject.toml",
    ]
    
    all_exist = True
    
    for file_path in auth_files:
        file = Path(file_path)
        if file.exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} - Missing")
            all_exist = False
    
    return all_exist

def check_dependency_config():
    """Check if ark-auth is properly configured as a dependency."""
    print("\n🔍 Checking dependency configuration...")
    
    pyproject_file = Path("services/ark-api/ark-api/pyproject.toml")
    if pyproject_file.exists():
        content = pyproject_file.read_text()
        
        if "ark-auth" in content:
            print("✅ ark-auth listed in ark-api dependencies")
            
            # Check if it's configured as a local dependency
            if "path" in content and "ark-auth" in content:
                print("✅ ark-auth configured as local dependency")
                return True
            else:
                print("⚠️  ark-auth dependency configuration unclear")
                return False
        else:
            print("❌ ark-auth not found in ark-api dependencies")
            return False
    else:
        print("❌ ark-api pyproject.toml not found")
        return False

def check_route_patterns():
    """Check if routes follow the expected authentication pattern."""
    print("\n🔍 Checking route authentication patterns...")
    
    # Check for the pattern: _: None = Depends(validate_token)
    pattern = r"_\s*:\s*None\s*=\s*Depends\(validate_token\)"
    
    files_to_check = [
        "services/ark-api/ark-api/src/ark_api/api/routes.py",
        "services/ark-api/ark-api/src/ark_api/api/v1/agents.py",
        "services/ark-api/ark-api/src/ark_api/api/v1/queries.py",
    ]
    
    total_matches = 0
    
    for file_path in files_to_check:
        file = Path(file_path)
        if file.exists():
            content = file.read_text()
            matches = re.findall(pattern, content)
            if matches:
                print(f"✅ {file_path}: {len(matches)} proper auth patterns found")
                total_matches += len(matches)
            else:
                print(f"⚠️  {file_path}: No proper auth patterns found")
    
    if total_matches > 0:
        print(f"✅ Total proper auth patterns: {total_matches}")
        return True
    else:
        print("❌ No proper authentication patterns found")
        return False

def show_manual_verification_steps():
    """Show steps for manual verification."""
    print("\n🛠️  Manual Verification Steps:")
    print("=" * 40)
    print("1. Install dependencies:")
    print("   cd services/ark-api/ark-api")
    print("   pip install -e .")
    print()
    print("2. Set environment variables:")
    print("   export ARK_OKTA_ISSUER='https://your-okta-domain.okta.com/oauth2/default'")
    print("   export ARK_OKTA_AUDIENCE='your-audience'")
    print()
    print("3. Test imports:")
    print("   python3 -c \"from ark_auth.dependencies import validate_token; print('Import successful')\"")
    print()
    print("4. Test configuration:")
    print("   python3 -c \"from ark_auth.config import settings; print(f'Issuer: {settings.okta_issuer}')\"")
    print()
    print("5. Start the API server:")
    print("   cd services/ark-api/ark-api")
    print("   python3 -m uvicorn src.ark_api.main:app --reload")
    print()
    print("6. Test protected endpoints:")
    print("   curl -H 'Authorization: Bearer your-jwt-token' http://localhost:8000/api/v1/namespaces")
    print("   curl http://localhost:8000/health  # Should work without auth")

def main():
    """Run all checks."""
    print("🔍 ARK Auth Status Checker")
    print("=" * 30)
    
    checks = [
        ("File Structure", check_auth_files),
        ("Dependency Config", check_dependency_config),
        ("Auth Imports", check_auth_imports),
        ("Auth Usage", check_auth_usage),
        ("Route Patterns", check_route_patterns),
    ]
    
    passed = 0
    total = len(checks)
    
    for check_name, check_func in checks:
        try:
            result = check_func()
            if result:
                passed += 1
        except Exception as e:
            print(f"❌ {check_name} failed: {e}")
    
    print(f"\n📊 Results: {passed}/{total} checks passed")
    
    if passed == total:
        print("🎉 All checks passed! Authentication is properly integrated.")
        print("   You can now test with the manual verification steps below.")
    else:
        print("⚠️  Some checks failed. Please review the output above.")
    
    show_manual_verification_steps()

if __name__ == "__main__":
    main()
