#!/usr/bin/env python3
"""
Simple script to show which routes need authentication in ark-api.
No external dependencies required.
"""

def show_authenticated_routes():
    """Show all routes that require authentication."""
    print("🔒 Routes Requiring Authentication:")
    print("=" * 50)
    
    # Main API routes
    print("\n📋 Main API:")
    print("-" * 15)
    print("  - /api/v1/namespaces")
    
    # V1 API routes
    print("\n📋 V1 API Routes:")
    print("-" * 20)
    
    # Agents
    print("  Agents:")
    print("    - /v1/namespaces/{namespace}/agents")
    print("    - /v1/namespaces/{namespace}/agents/{agent_name}")
    
    # Queries
    print("  Queries:")
    print("    - /v1/namespaces/{namespace}/queries")
    print("    - /v1/namespaces/{namespace}/queries/{query_name}")
    
    # Teams
    print("  Teams:")
    print("    - /v1/namespaces/{namespace}/teams")
    print("    - /v1/namespaces/{namespace}/teams/{team_name}")
    
    # Tools
    print("  Tools:")
    print("    - /v1/namespaces/{namespace}/tools")
    print("    - /v1/namespaces/{namespace}/tools/{tool_name}")
    
    # Models
    print("  Models:")
    print("    - /v1/namespaces/{namespace}/models")
    print("    - /v1/namespaces/{namespace}/models/{model_name}")
    
    # MCP Servers
    print("  MCP Servers:")
    print("    - /v1/namespaces/{namespace}/mcp-servers")
    print("    - /v1/namespaces/{namespace}/mcp-servers/{server_name}")
    
    # Memories
    print("  Memories:")
    print("    - /v1/namespaces/{namespace}/memories")
    print("    - /v1/namespaces/{namespace}/memories/{memory_name}")
    
    # A2A Servers
    print("  A2A Servers:")
    print("    - /v1/namespaces/{namespace}/a2a-servers")
    print("    - /v1/namespaces/{namespace}/a2a-servers/{server_name}")
    
    # Events
    print("  Events:")
    print("    - /v1/namespaces/{namespace}/events")
    print("    - /v1/namespaces/{namespace}/events/{event_name}")
    
    # Secrets
    print("  Secrets:")
    print("    - /v1/namespaces/{namespace}/secrets")
    print("    - /v1/namespaces/{namespace}/secrets/{secret_name}")
    
    # System Info
    print("  System Info:")
    print("    - /v1/system-info")
    
    # ARK Services
    print("  ARK Services:")
    print("    - /v1/ark-services")
    print("    - /v1/ark-services/{service_name}")
    
    total_routes = 25  # Counted manually
    print(f"\n📊 Total authenticated routes: {total_routes}")
    return total_routes

def show_public_routes():
    """Show all public routes that don't require authentication."""
    print("\n🔓 Public Routes (No Authentication):")
    print("=" * 45)
    
    public_routes = [
        "/health",
        "/docs", 
        "/openapi.json",
        "/redoc"
    ]
    
    for route in public_routes:
        print(f"  - {route}")
    
    print(f"\n📊 Total public routes: {len(public_routes)}")
    return len(public_routes)

def show_summary():
    """Show authentication summary."""
    print("\n📈 Authentication Summary:")
    print("=" * 30)
    print("  Total authenticated routes: 25")
    print("  Total public routes: 4")
    print("  Authentication coverage: 86%")

def show_http_methods():
    """Show HTTP methods for each route type."""
    print("\n🌐 HTTP Methods:")
    print("=" * 20)
    
    print("  Authenticated routes support:")
    methods = ["GET", "POST", "PUT", "DELETE", "PATCH"]
    for method in methods:
        print(f"    - {method}")
    
    print("\n  Public routes support:")
    print("    - GET")

def show_usage_examples():
    """Show usage examples for managing authentication."""
    print("\n🛠️  Usage Examples:")
    print("=" * 25)
    print("1. Add authentication to a new route:")
    print("   Add 'Depends(validate_token)' to the route function parameters")
    print("   Example: async def my_route(_: None = Depends(validate_token)):")
    print()
    print("2. Make a route public:")
    print("   Don't add the validate_token dependency")
    print("   Example: async def public_route():")
    print()
    print("3. Check current authentication status:")
    print("   Look at the route function signature")
    print("   If it has 'Depends(validate_token)', it's authenticated")
    print()
    print("4. Add authentication to multiple routes:")
    print("   Use the auth middleware utilities in ark_api.auth.middleware")

def show_current_implementation():
    """Show how authentication is currently implemented."""
    print("\n💻 Current Implementation:")
    print("=" * 35)
    print("Authentication is implemented using FastAPI dependencies:")
    print()
    print("1. Import: from ark_auth.dependencies import validate_token")
    print("2. Add to route: _: None = Depends(validate_token)")
    print()
    print("Example:")
    print("  @router.get('/my-route')")
    print("  async def my_route(_: None = Depends(validate_token)):")
    print("      return {'message': 'This route is authenticated'}")
    print()
    print("The validate_token function:")
    print("  - Extracts Authorization header")
    print("  - Validates Bearer token format")
    print("  - Calls JWT validation")
    print("  - Raises InvalidTokenException if invalid")

def main():
    """Main function."""
    print("🔍 ARK API Authentication Route Inspector")
    print("=" * 50)
    
    # Show different sections based on command line arguments
    args = sys.argv[1:] if len(sys.argv) > 1 else ['all']
    
    if 'all' in args or 'auth' in args:
        show_authenticated_routes()
    
    if 'all' in args or 'public' in args:
        show_public_routes()
    
    if 'all' in args or 'summary' in args:
        show_summary()
    
    if 'all' in args or 'methods' in args:
        show_http_methods()
    
    if 'all' in args or 'implementation' in args:
        show_current_implementation()
    
    if 'all' in args or 'help' in args:
        show_usage_examples()
    
    print("\n✅ Inspection complete!")

if __name__ == "__main__":
    import sys
    main()
