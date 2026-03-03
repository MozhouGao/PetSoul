"""
Authentication — Auth0 JWT verification

Validates JWT tokens issued by Auth0. The frontend handles the Auth0 login
flow (Universal Login or SDK); the backend only verifies incoming tokens.
"""

import logging
from typing import Optional
from functools import lru_cache

import jwt
from jwt import PyJWKClient
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from pet_soul.config import CONFIG

logger = logging.getLogger(__name__)

bearer_scheme = HTTPBearer()

# Cache the JWKS client so we don't re-fetch keys on every request
_jwks_client: Optional[PyJWKClient] = None


def _get_jwks_client() -> PyJWKClient:
    global _jwks_client
    if _jwks_client is None:
        jwks_url = f"https://{CONFIG.auth0_domain}/.well-known/jwks.json"
        _jwks_client = PyJWKClient(jwks_url)
    return _jwks_client


def verify_token(token: str) -> dict:
    """Verify an Auth0 JWT and return the decoded payload.

    Returns:
        Decoded JWT payload containing 'sub', 'email', etc.

    Raises:
        HTTPException 401 on any verification failure.
    """
    try:
        client = _get_jwks_client()
        signing_key = client.get_signing_key_from_jwt(token)

        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            audience=CONFIG.auth0_audience,
            issuer=f"https://{CONFIG.auth0_domain}/",
        )
        return payload

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
        )
    except jwt.InvalidTokenError as e:
        logger.warning("Auth0 token verification failed: %s", e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )
    except Exception as e:
        logger.error("Unexpected auth error: %s", e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
        )


def get_current_user(
    creds: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> dict:
    """FastAPI dependency — returns the authenticated user's Auth0 payload.

    The payload typically contains:
        - sub: Auth0 user ID (e.g. "auth0|abc123")
        - email: user email (if requested in scopes)
        - name: display name
    """
    payload = verify_token(creds.credentials)
    return payload


def get_user_id(
    creds: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> str:
    """FastAPI dependency — returns just the Auth0 user ID (sub claim)."""
    payload = verify_token(creds.credentials)
    return payload["sub"]
