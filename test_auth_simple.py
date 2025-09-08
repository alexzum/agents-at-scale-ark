#!/usr/bin/env python3
"""
Simple test to verify authentication is working without Kubernetes dependency.
"""
import asyncio
from fastapi import FastAPI, Depends
from ark_auth.dependencies import validate_token

app = FastAPI()

@app.get("/test-auth")
async def test_auth(_: None = Depends(validate_token)):
    return {"message": "Authentication successful!"}

@app.get("/test-public")
async def test_public():
    return {"message": "Public endpoint"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
