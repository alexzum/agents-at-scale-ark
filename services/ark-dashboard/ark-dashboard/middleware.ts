import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export function middleware(request: NextRequest) {
  // Get the base path from environment (no default)
  const basePath = process.env.ARK_DASHBOARD_BASE_PATH || '';
  
  // Proxy anything starting with /api/ to the backend, stripping the /api prefix
  // This includes: /api/v1/*, /api/docs, /api/openapi.json
  const apiPath = `${basePath}/api/`;
  
  if (request.nextUrl.pathname.startsWith(apiPath)) {
    // Read environment variables at runtime
    const host = process.env.ARK_API_SERVICE_HOST || '0.0.0.0';
    const port = process.env.ARK_API_SERVICE_PORT || '8000';
    const protocol = process.env.ARK_API_SERVICE_PROTOCOL || 'http';
    
    // Remove the base path and /api prefix to get the backend path
    let backendPath = request.nextUrl.pathname.replace(basePath, '');
    backendPath = backendPath.replace('/api', '');
    
    // Construct the target URL
    const targetUrl = `${protocol}://${host}:${port}${backendPath}${request.nextUrl.search}`;
    
    // Rewrite the request to the backend with standard HTTP forwarding headers
    // These X-Forwarded-* headers help the backend understand the external request context:
    // - X-Forwarded-Prefix: tells backend it's being served from /api path externally
    // - X-Forwarded-Host: original host header from the client request  
    // - X-Forwarded-Proto: original protocol (http/https) from the client request
    // The backend uses these to generate correct URLs for OpenAPI specs and CORS handling
    const response = NextResponse.rewrite(targetUrl);
    response.headers.set('X-Forwarded-Prefix', '/api');
    response.headers.set('X-Forwarded-Host', request.headers.get('host') || '');
    response.headers.set('X-Forwarded-Proto', request.nextUrl.protocol.slice(0, -1)); // Remove trailing ':'
    return response;
  }
  
  // For all other requests, continue normally
  return NextResponse.next();
}

export const config = {
  matcher: '/((?!_next/static|_next/image|favicon.ico).*)',
};
