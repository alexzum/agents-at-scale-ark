#!/usr/bin/env python3
"""
Authentication inspector for ark-api.
This script helps you inspect which routes have authentication and manage them.
"""

import sys
import os
from pathlib import Path

# Add the ark-api source to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

def inspect_auth_status():
    """Inspect the current authentication status of all routes."""
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
        
        from ark_api.auth.middleware import get_router_auth_status, list_authenticated_routes, list_unauthenticated_routes
        from ark_api.auth.config import AUTHENTICATED_ROUTES, PUBLIC_ROUTES, is_route_authenticated
        
        print("🔍 ARK API Authentication Inspector")
        print("=" * 50)
        
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
        
        total_routes = 0
        authenticated_routes = 0
        unauthenticated_routes = 0
        
        for router_name, router in routers:
            print(f"\n📋 {router_name} Router:")
            print("-" * 30)
            
            auth_routes = list_authenticated_routes(router)
            unauth_routes = list_unauthenticated_routes(router)
            
            if auth_routes:
                print(f"  ✅ Authenticated routes ({len(auth_routes)}):")
                for route in sorted(auth_routes):
                    print(f"    - {route}")
                authenticated_routes += len(auth_routes)
            
            if unauth_routes:
                print(f"  ❌ Unauthenticated routes ({len(unauth_routes)}):")
                for route in sorted(unauth_routes):
                    print(f"    - {route}")
                unauthenticated_routes += len(unauth_routes)
            
            total_routes += len(auth_routes) + len(unauth_routes)
        
        print(f"\n📊 Summary:")
        print(f"  Total routes: {total_routes}")
        print(f"  Authenticated: {authenticated_routes}")
        print(f"  Unauthenticated: {unauthenticated_routes}")
        print(f"  Authentication coverage: {(authenticated_routes/total_routes*100):.1f}%")
        
        # Show configuration
        print(f"\n⚙️  Configuration:")
        print(f"  Configured authenticated routes: {len(AUTHENTICATED_ROUTES)}")
        print(f"  Configured public routes: {len(PUBLIC_ROUTES)}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_route_auth_check():
    """Test the route authentication checking logic."""
    try:
        from ark_api.auth.config import is_route_authenticated
        
        print("\n🧪 Testing Route Authentication Logic:")
        print("-" * 40)
        
        test_routes = [
            "/api/v1/namespaces",
            "/v1/namespaces/default/agents",
            "/v1/namespaces/default/agents/my-agent",
            "/v1/namespaces/default/queries",
            "/v1/namespaces/default/queries/my-query",
            "/health",
            "/docs",
            "/openapi.json",
            "/v1/system-info",
            "/some/unknown/route",
        ]
        
        for route in test_routes:
            is_auth = is_route_authenticated(route)
            status = "🔒 AUTH" if is_auth else "🔓 PUBLIC"
            print(f"  {status} {route}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing route auth: {e}")
        return False

def show_auth_commands():
    """Show useful commands for managing authentication."""
    print("\n🛠️  Useful Commands:")
    print("-" * 20)
    print("1. Add authentication to a new route:")
    print("   from ark_api.auth.config import add_authenticated_route")
    print("   add_authenticated_route('/new/route/path')")
    print()
    print("2. Remove authentication from a route:")
    print("   from ark_api.auth.config import remove_authenticated_route")
    print("   remove_authenticated_route('/route/to/remove')")
    print()
    print("3. Add a public route:")
    print("   from ark_api.auth.config import add_public_route")
    print("   add_public_route('/public/endpoint')")
    print()
    print("4. Check if a route needs auth:")
    print("   from ark_api.auth.config import is_route_authenticated")
    print("   is_route_authenticated('/some/route')")
    print()
    print("5. Get all authenticated routes:")
    print("   from ark_api.auth.config import get_authenticated_routes")
    print("   routes = get_authenticated_routes()")

if __name__ == "__main__":
    print("Starting ARK API Authentication Inspector...")
    
    success1 = inspect_auth_status()
    success2 = test_route_auth_check()
    show_auth_commands()
    
    if success1 and success2:
        print("\n✅ Inspection completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Some inspections failed.")
        sys.exit(1)
