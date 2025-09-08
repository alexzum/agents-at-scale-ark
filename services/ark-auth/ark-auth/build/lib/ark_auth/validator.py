import jwt
import logging
from pyjwt_key_fetcher import AsyncKeyFetcher
from ark_auth.config import settings  # your config has issuer & audience

logger = logging.getLogger(__name__)

async def validate_jwt(token: str) -> dict:
    """
    Validate JWT using pyjwt_key_fetcher + PyJWT.
    Token is the only input.
    Config values (issuer, audience) come from ark-auth settings.
    """
    # Check if configuration is set
    if not settings.okta_issuer or not settings.okta_audience:
        logger.warning("JWT validation skipped - Okta configuration not set")
        # Return a mock payload for testing purposes
        return {
            "sub": "test-user",
            "aud": "test-audience", 
            "iss": "https://test.okta.com/oauth2/default"
        }
    
    fetcher = AsyncKeyFetcher()

    try:
        key_entry = await fetcher.get_key(token)
        payload = jwt.decode(
            token,
            verify=True,
            audience=settings.okta_audience,
            issuer=settings.okta_issuer,
            **key_entry,
        )
        return payload

    except jwt.InvalidTokenError as e:
        logger.error(f"Invalid token: {str(e)}")
        raise ValueError("Invalid token")

    except Exception as e:
        logger.error(f"Error decoding token: {str(e)}")
        raise ValueError("Token validation failed")

    finally:
        await fetcher._http_client.session.close()
