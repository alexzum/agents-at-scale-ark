#!/usr/bin/env python3
"""
Simple script to list all routes that need authentication in ark-api.
"""

import sys
import os
from pathlib import Path

# Add the ark-api source to the path
sys.path.insert(0, str(Path(__file__).parent / "services" / "ark-api" / "ark-api" / "src"))

def list_authenticated_routes():
    """List all routes that currently have authentication."""
    try:
        from ark_api.api import router as main_router
        from ark_api.api.v1 import router as v1_router
        from ark_api.api.v1.agents import router as agents_router
        from ark_api.api.v1.queries import router as queries_router
        from ark_api.api.v1.teams import router as teams_router
        from ark_api.api.v1.tools import router as tools_router
        from ark_api.api.v1.models import router as models_router
        from ark_api.api.v1.mcp_servers import router as mcp_router
        from ark_api.api.v1.memories import router as memories_router
        from ark_api.api.v1.a2a_servers import router as a2a_router
        from ark_api.api.v1.events import router as events_router
        from ark_api.api.v1.secrets import router as secrets_router
        from ark_api.api.v1.system_info import router as system_info_router
        from ark_api.api.v1.ark_services import router as ark_services_router
        from ark_api.api.health import router as health_router
        
        print("🔒 Routes with Authentication:")
        print("=" * 40)
        
        # Check each router
        routers = [
            ("Main API", main_router),
            ("V1 API", v1_router),
            ("Agents", agents_router),
            ("Queries", queries_router),
            ("Teams", teams_router),
            ("Tools", tools_router),
            ("Models", models_router),
            ("MCP Servers", mcp_router),
            ("Memories", memories_router),
            ("A2A Servers", a2a_router),
            ("Events", events_router),
            ("Secrets", secrets_router),
            ("System Info", system_info_router),
            ("ARK Services", ark_services_router),
            ("Health", health_router),
        ]
        
        all_auth_routes = []
        
        for router_name, router in routers:
            auth_routes = []
            for route in router.routes:
                if hasattr(route, 'path') and hasattr(route, 'dependant'):
                    has_auth = False
                    if route.dependant and route.dependant.dependencies:
                        has_auth = any('validate_token' in str(dep) for dep in route.dependant.dependencies)
                    if has_auth:
                        auth_routes.append(route.path)
                        all_auth_routes.append(f"{router_name}: {route.path}")
            
            if auth_routes:
                print(f"\n{router_name}:")
                for route in sorted(auth_routes):
                    print(f"  - {route}")
        
        print(f"\n📊 Total authenticated routes: {len(all_auth_routes)}")
        
        # Show all routes in a single list
        print(f"\n📋 All Authenticated Routes:")
        print("-" * 30)
        for route in sorted(all_auth_routes):
            print(f"  {route}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure you're running this from the project root directory.")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def list_unauthenticated_routes():
    """List all routes that don't have authentication."""
    try:
        from ark_api.api import router as main_router
        from ark_api.api.v1 import router as v1_router
        from ark_api.api.v1.agents import router as agents_router
        from ark_api.api.v1.queries import router as queries_router
        from ark_api.api.v1.teams import router as teams_router
        from ark_api.api.v1.tools import router as tools_router
        from ark_api.api.v1.models import router as models_router
        from ark_api.api.v1.mcp_servers import router as mcp_router
        from ark_api.api.v1.memories import router as memories_router
        from ark_api.api.v1.a2a_servers import router as a2a_router
        from ark_api.api.v1.events import router as events_router
        from ark_api.api.v1.secrets import router as secrets_router
        from ark_api.api.v1.system_info import router as system_info_router
        from ark_api.api.v1.ark_services import router as ark_services_router
        from ark_api.api.health import router as health_router
        
        print("\n🔓 Routes without Authentication:")
        print("=" * 40)
        
        # Check each router
        routers = [
            ("Main API", main_router),
            ("V1 API", v1_router),
            ("Agents", agents_router),
            ("Queries", queries_router),
            ("Teams", teams_router),
            ("Tools", tools_router),
            ("Models", models_router),
            ("MCP Servers", mcp_router),
            ("Memories", memories_router),
            ("A2A Servers", a2a_router),
            ("Events", events_router),
            ("Secrets", secrets_router),
            ("System Info", system_info_router),
            ("ARK Services", ark_services_router),
            ("Health", health_router),
        ]
        
        all_unauth_routes = []
        
        for router_name, router in routers:
            unauth_routes = []
            for route in router.routes:
                if hasattr(route, 'path') and hasattr(route, 'dependant'):
                    has_auth = False
                    if route.dependant and route.dependant.dependencies:
                        has_auth = any('validate_token' in str(dep) for dep in route.dependant.dependencies)
                    if not has_auth:
                        unauth_routes.append(route.path)
                        all_unauth_routes.append(f"{router_name}: {route.path}")
            
            if unauth_routes:
                print(f"\n{router_name}:")
                for route in sorted(unauth_routes):
                    print(f"  - {route}")
        
        print(f"\n📊 Total unauthenticated routes: {len(all_unauth_routes)}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="List ark-api routes with/without authentication")
    parser.add_argument("--type", choices=["auth", "unauth", "all"], default="all", 
                       help="Type of routes to list (default: all)")
    
    args = parser.parse_args()
    
    if args.type in ["auth", "all"]:
        list_authenticated_routes()
    
    if args.type in ["unauth", "all"]:
        list_unauthenticated_routes()
