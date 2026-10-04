import logging

import httpx
from fastapi import HTTPException
from jwt import PyJWK

from app.core.config import config

logger = logging.getLogger(__name__)

_jwks_cache: dict[str, PyJWK] = {}


async def get_jwks():
    logger.info("Fetching JWKS")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(config.JWKS_URL)
            response.raise_for_status()
            return response.json()
    except (httpx.HTTPError, ValueError) as exc:
        logger.exception("Could not fetch JWKS")
        raise HTTPException(
            status_code=503, detail="Token verification is temporarily unavailable"
        ) from exc


async def get_signing_key(kid: str) -> PyJWK:
    if kid not in _jwks_cache:
        jwks = await get_jwks()
        _jwks_cache.clear()
        for k in jwks["keys"]:
            _jwks_cache[k["kid"]] = PyJWK(k)
    key = _jwks_cache.get(kid)
    if key is None:
        raise HTTPException(status_code=401, detail="Unknown signing key")
    return key
