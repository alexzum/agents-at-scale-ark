#!/usr/bin/env python3
"""
Simple script to show which routes need authentication in ark-api.
Reads from the auth_routes.yaml configuration file.
"""

import yaml
import sys
from pathlib import Path

def load_auth_config():
    """Load the authentication configuration from YAML file."""
    config_path = Path(__file__).parent / "services" / "ark-api" / "ark-api" / "auth_routes.yaml"
    
    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        print(f"❌ Configuration file not found: {config_path}")
        return None
    except yaml.YAMLError as e:
        print(f"❌ Error parsing YAML: {e}")
        return None

def show_authenticated_routes(config):
    """Show all routes that require authentication."""
    print("🔒 Routes Requiring Authentication:")
    print("=" * 50)
    
    total_routes = 0
    
    for category, routes in config.items():
        if category in ['public_routes', 'methods', 'summary']:
            continue
            
        print(f"\n📋 {category.replace('_', ' ').title()}:")
        print("-" * 30)
        
        for route in routes:
            print(f"  - {route}")
            total_routes += 1
    
    print(f"\n📊 Total authenticated routes: {total_routes}")
    return total_routes

def show_public_routes(config):
    """Show all public routes that don't require authentication."""
    print("\n🔓 Public Routes (No Authentication):")
    print("=" * 45)
    
    public_routes = config.get('public_routes', [])
    for route in public_routes:
        print(f"  - {route}")
    
    print(f"\n📊 Total public routes: {len(public_routes)}")
    return len(public_routes)

def show_summary(config):
    """Show authentication summary."""
    print("\n📈 Authentication Summary:")
    print("=" * 30)
    
    summary = config.get('summary', {})
    print(f"  Total authenticated routes: {summary.get('total_authenticated_routes', 'N/A')}")
    print(f"  Total public routes: {summary.get('total_public_routes', 'N/A')}")
    print(f"  Authentication coverage: {summary.get('authentication_coverage', 'N/A')}")

def show_http_methods(config):
    """Show HTTP methods for each route type."""
    print("\n🌐 HTTP Methods:")
    print("=" * 20)
    
    methods = config.get('methods', {})
    
    print("  Authenticated routes support:")
    for method in methods.get('authenticated', []):
        print(f"    - {method}")
    
    print("\n  Public routes support:")
    for method in methods.get('public', []):
        print(f"    - {method}")

def show_usage_examples():
    """Show usage examples for managing authentication."""
    print("\n🛠️  Usage Examples:")
    print("=" * 25)
    print("1. Add authentication to a new route:")
    print("   Add the route to auth_routes.yaml under the appropriate category")
    print()
    print("2. Make a route public:")
    print("   Add the route to the 'public_routes' section in auth_routes.yaml")
    print()
    print("3. Check if a route needs auth:")
    print("   Look up the route in this configuration file")
    print()
    print("4. Update authentication in code:")
    print("   Add 'Depends(validate_token)' to the route function parameters")

def main():
    """Main function."""
    print("🔍 ARK API Authentication Route Inspector")
    print("=" * 50)
    
    config = load_auth_config()
    if not config:
        sys.exit(1)
    
    # Show different sections based on command line arguments
    args = sys.argv[1:] if len(sys.argv) > 1 else ['all']
    
    if 'all' in args or 'auth' in args:
        show_authenticated_routes(config)
    
    if 'all' in args or 'public' in args:
        show_public_routes(config)
    
    if 'all' in args or 'summary' in args:
        show_summary(config)
    
    if 'all' in args or 'methods' in args:
        show_http_methods(config)
    
    if 'all' in args or 'help' in args:
        show_usage_examples()
    
    print("\n✅ Inspection complete!")

if __name__ == "__main__":
    main()
