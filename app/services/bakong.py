"""Async Bakong API client: auth + balance summary."""

import logging
from typing import Any

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

TOKEN_KEYS = ("id_token", "token", "access_token", "accessToken", "jwt")


async def get_auth_token() -> str:
    """Authenticate and return Bearer token."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.post(
            f"{settings.bakong_base_url.rstrip('/')}/api/v2/authenticate",
            json={
                "username": settings.bakong_username,
                "password": settings.bakong_password,
                "rememberMe": True,
            },
        )
        r.raise_for_status()
        data = r.json()
        token = None
        for key in TOKEN_KEYS:
            token = data.get(key)
            if token:
                break
        if not token and "data" in data:
            inner = data["data"]
            if isinstance(inner, str):
                token = inner
            elif isinstance(inner, dict):
                for key in TOKEN_KEYS:
                    token = inner.get(key)
                    if token:
                        break
        if not token:
            logger.warning(
                "No token in auth response; response keys: %s",
                list(data.keys()),
            )
            raise ValueError("No token in auth response")
        return token


async def get_balance_summary(token: str) -> dict[str, Any]:
    """Fetch iroha account summary (balance) using Bearer token."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.get(
            f"{settings.bakong_base_url.rstrip('/')}/tps/api/iroha-account-summary",
            params={"branch": "ALL", "type": "ALL"},
            headers={"Authorization": f"Bearer {token}"},
        )
        r.raise_for_status()
        return r.json()
