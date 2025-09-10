# Authentication Module Tests

This directory contains comprehensive tests for the `ark-sdk` authentication module.

## Test Structure

### Unit Tests
- **`test_config.py`** - Tests for `AuthConfig` class and environment variable loading
- **`test_exceptions.py`** - Tests for custom exception classes
- **`test_dependencies.py`** - Tests for FastAPI dependency injection
- **`test_validator.py`** - Tests for `TokenValidator` class and JWT validation logic

### Integration Tests
- **`test_integration.py`** - End-to-end tests for complete authentication flows

### Test Utilities
- **`conftest.py`** - Pytest configuration and shared fixtures
- **`run_tests.py`** - Standalone test runner script
- **`README.md`** - This documentation file

## Running Tests

### Using unittest (Python standard library)
```bash
# Run all tests
python -m unittest discover -s . -p 'test_*.py' -v

# Run specific test file
python test_config.py

# Run with coverage
python -m coverage run -m unittest discover -s . -p 'test_*.py'
python -m coverage report
python -m coverage html
```

### Using pytest
```bash
# Run all tests
pytest

# Run specific test file
pytest test_config.py

# Run with coverage
pytest --cov=ark_sdk.auth --cov-report=html

# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Run only fast tests (skip slow ones)
pytest -m "not slow"
```

### Using the test runner script
```bash
# Make the script executable
chmod +x run_tests.py

# Run all tests
./run_tests.py
```

## Test Coverage

The test suite covers:

### Configuration (`test_config.py`)
- ✅ Default configuration values
- ✅ Environment variable loading
- ✅ Case-insensitive environment variables
- ✅ OKTA priority over JWT configuration
- ✅ Invalid numeric value handling
- ✅ Empty string value handling

### Exceptions (`test_exceptions.py`)
- ✅ All custom exception classes
- ✅ Exception inheritance hierarchy
- ✅ Exception chaining
- ✅ Edge cases (None, empty messages)

### Dependencies (`test_dependencies.py`)
- ✅ Successful token validation
- ✅ Missing Authorization header
- ✅ Invalid header format
- ✅ Expired token handling
- ✅ Invalid token handling
- ✅ General validation errors
- ✅ Bearer prefix handling
- ✅ Case-insensitive Bearer prefix
- ✅ Whitespace handling
- ✅ Empty token handling

### Validator (`test_validator.py`)
- ✅ JWKS client creation and caching
- ✅ Successful token validation
- ✅ OKTA priority over JWT configuration
- ✅ Fallback to JWT configuration
- ✅ No audience/issuer configuration
- ✅ Missing JWKS URL
- ✅ Expired signature handling
- ✅ Invalid token handling
- ✅ Decode error handling
- ✅ General exception handling
- ✅ JWKS client exceptions
- ✅ Signing key exceptions

### Integration (`test_integration.py`)
- ✅ Complete authentication flow
- ✅ Configuration priority testing
- ✅ Fallback behavior testing
- ✅ Error handling in complete flow
- ✅ Different JWT algorithms
- ✅ Retry mechanism configuration

## Test Data and Mocking

### Mock Data
- **JWT Payloads**: Standard and OKTA-specific token payloads
- **Configuration**: Various AuthConfig scenarios
- **JWKS Client**: Mocked PyJWKClient with signing keys
- **PyJWT**: Mocked JWT decode operations

### Environment Variables
Tests use isolated environment variables to avoid conflicts:
- `ARK_JWT_ALGORITHM`
- `ARK_JWT_AUDIENCE`
- `ARK_JWT_ISSUER`
- `ARK_OKTA_AUDIENCE`
- `ARK_OKTA_ISSUER`
- `ARK_JWKS_URL`
- `ARK_JWKS_CACHE_TTL`
- `ARK_TOKEN_VALIDATION_RETRIES`

## Fixtures (pytest)

### Configuration Fixtures
- `auth_config` - Default configuration with OKTA values
- `auth_config_no_okta` - Configuration without OKTA values
- `auth_config_minimal` - Minimal configuration for edge cases

### Mock Fixtures
- `mock_jwks_client` - Mocked JWKS client
- `mock_token_payload` - Standard JWT payload
- `mock_okta_token_payload` - OKTA-specific JWT payload
- `mock_pyjwt` - Mocked PyJWT library
- `mock_fastapi_dependency` - Mocked FastAPI dependency

### Utility Fixtures
- `clean_env` - Clean environment for isolated testing

## Test Markers

- `@pytest.mark.unit` - Unit tests
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.slow` - Slow-running tests

## Dependencies

The tests require:
- `unittest` (Python standard library)
- `pytest` (optional, for advanced features)
- `coverage` (optional, for coverage reporting)
- `fastapi` (for dependency testing)
- `jwt` (for JWT validation testing)
- `pyjwt-key-fetcher` (for JWKS testing)

## Best Practices

1. **Isolation**: Each test is isolated and doesn't depend on others
2. **Mocking**: External dependencies are properly mocked
3. **Coverage**: All code paths are tested
4. **Edge Cases**: Boundary conditions and error cases are covered
5. **Documentation**: Tests are well-documented and self-explanatory
6. **Performance**: Tests run quickly and efficiently

## Contributing

When adding new tests:
1. Follow the existing naming conventions
2. Add appropriate docstrings
3. Include both positive and negative test cases
4. Use descriptive test names
5. Add fixtures for reusable test data
6. Update this README if adding new test categories
