from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
import jwt

class AuthenticationMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, secret_key: str, unprotected_routes: list):
        super().__init__(app)
        self.secret_key = secret_key
        self.unprotected_routes = unprotected_routes

    async def dispatch(self, request: Request, call_next):
        # Skip authentication for unprotected routes
        if any(request.url.path.startswith(route) for route in self.unprotected_routes):
            return await call_next(request)

        # Check for Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")

        token = auth_header.split(" ")[1]

        try:
            # Validate the token
            jwt.decode(token, self.secret_key, algorithms=["HS256"])
        except jwt.PyJWTError:
            raise HTTPException(status_code=401, detail="Invalid token")

        return await call_next(request)