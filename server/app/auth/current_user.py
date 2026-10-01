from typing import Annotated

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.auth.jwt import get_signing_key
from app.auth.model import TokenUser
from config import config

bearer = HTTPBearer()


async def get_user_current(
    creds: Annotated[HTTPAuthorizationCredentials, Depends(bearer)],
) -> TokenUser:
    token = creds.credentials

    try:
        kid = jwt.get_unverified_header(token)["kid"]
        key = await get_signing_key(kid)
        payload = jwt.decode(
            token,
            key.key,
            algorithms=["EdDSA"],
            issuer=config.FRONTEND_URL,
            audience=config.FRONTEND_URL,
        )
    
        return TokenUser.model_validate(payload)
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="invalid or expired token")
