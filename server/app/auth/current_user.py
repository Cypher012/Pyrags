from typing import Annotated

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import ValidationError

from app.auth.jwt import get_signing_key
from app.auth.schemas import TokenUser
from app.core.config import config

bearer = HTTPBearer()


async def get_current_user(
    creds: Annotated[HTTPAuthorizationCredentials, Depends(bearer)],
) -> TokenUser:
    token = creds.credentials

    try:
        kid = jwt.get_unverified_header(token).get("kid")
        if not isinstance(kid, str) or not kid:
            raise jwt.InvalidTokenError("Missing signing key ID")
        key = await get_signing_key(kid)
        payload = jwt.decode(
            token,
            key.key,
            algorithms=["EdDSA"],
            issuer=config.FRONTEND_URL,
            audience=config.FRONTEND_URL,
        )

        return TokenUser.model_validate(payload)
    except (jwt.PyJWTError, ValidationError) as exc:
        raise HTTPException(status_code=401, detail="invalid or expired token") from exc
