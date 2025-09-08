# How to Test ARK Auth Integration

This guide shows you how to verify that ark-auth is working properly with ark-api.

## ✅ Current Status

Based on the code analysis, authentication is properly integrated:
- **11 routes** have authentication enabled
- **ark-auth** is properly imported in all route files
- **Dependencies** are correctly configured
- **File structure** is complete

## 🧪 Testing Methods

### 1. Quick Code Check (No Dependencies Required)

```bash
# Run the status checker
python3 check_auth_status.py
```

This will verify:
- ✅ File structure is correct
- ✅ Dependencies are configured
- ✅ Imports are in place
- ✅ Authentication patterns are used

### 2. Install Dependencies and Test

```bash
# Install ark-api with dependencies
cd services/ark-api/ark-api
pip install -e .

# Test basic import
python3 -c "from ark_auth.dependencies import validate_token; print('✅ Import successful')"
```

### 3. Test Configuration

```bash
# Set environment variables
export ARK_OKTA_ISSUER="https://test.okta.com/oauth2/default"
export ARK_OKTA_AUDIENCE="test-audience"

# Test configuration loading
python3 -c "from ark_auth.config import settings; print(f'Issuer: {settings.okta_issuer}')"
```

### 4. Test API Server

```bash
# Start the API server
cd services/ark-api/ark-api
python3 -m uvicorn src.ark_api.main:app --reload --port 8000
```

### 5. Test Endpoints

#### Test Public Endpoints (Should Work Without Auth)
```bash
# Health check - should work
curl http://localhost:8000/health

# API docs - should work
curl http://localhost:8000/docs
```

#### Test Protected Endpoints (Should Require Auth)
```bash
# Without auth - should fail with 401
curl http://localhost:8000/api/v1/namespaces

# With invalid auth - should fail with 401
curl -H "Authorization: Bearer invalid-token" http://localhost:8000/api/v1/namespaces

# With valid auth - should work (if you have a real JWT token)
curl -H "Authorization: Bearer your-real-jwt-token" http://localhost:8000/api/v1/namespaces
```

## 🔍 What to Look For

### ✅ Success Indicators

1. **Import Test**: No import errors
2. **Configuration Test**: Environment variables loaded correctly
3. **API Server**: Starts without errors
4. **Public Endpoints**: Return 200 OK
5. **Protected Endpoints**: Return 401 Unauthorized without auth

### ❌ Failure Indicators

1. **Import Errors**: Missing dependencies or modules
2. **Configuration Errors**: Environment variables not loaded
3. **Server Errors**: API server fails to start
4. **Auth Bypass**: Protected endpoints work without authentication

## 🛠️ Troubleshooting

### Common Issues

1. **ModuleNotFoundError: No module named 'ark_auth'**
   ```bash
   # Solution: Install dependencies
   cd services/ark-api/ark-api
   pip install -e .
   ```

2. **Configuration not loading**
   ```bash
   # Solution: Set environment variables
   export ARK_OKTA_ISSUER="https://your-domain.okta.com/oauth2/default"
   export ARK_OKTA_AUDIENCE="your-audience"
   ```

3. **JWT validation fails**
   - Check that your JWT token is valid
   - Verify the issuer and audience match your configuration
   - Ensure the token is not expired

### Debug Mode

Enable debug logging to see what's happening:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📊 Current Authentication Status

Based on the code analysis:

- **Main API Routes**: 1 route with auth
- **Agents Routes**: 5 routes with auth (list, create, get, update, delete)
- **Queries Routes**: 5 routes with auth (list, create, get, update, delete)
- **Total**: 11 routes protected

### Routes with Authentication

```
/api/v1/namespaces
/v1/namespaces/{namespace}/agents
/v1/namespaces/{namespace}/agents/{agent_name}
/v1/namespaces/{namespace}/queries
/v1/namespaces/{namespace}/queries/{query_name}
```

### Routes without Authentication

```
/health
/docs
/openapi.json
/redoc
```

## 🚀 Next Steps

1. **Install Dependencies**: Run `pip install -e .` in the ark-api directory
2. **Set Configuration**: Configure your Okta issuer and audience
3. **Test Endpoints**: Use the curl commands above to test
4. **Monitor Logs**: Check server logs for any authentication errors
5. **Add More Routes**: Use the same pattern to add auth to other routes

## 📝 Adding Authentication to New Routes

To add authentication to a new route:

```python
from fastapi import Depends
from ark_auth.dependencies import validate_token

@router.get("/my-new-route")
async def my_new_route(_: None = Depends(validate_token)):
    return {"message": "This route is protected"}
```

The authentication is now properly integrated and ready for testing! 🎉
