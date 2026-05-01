from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
import jwt
from fastapi import Depends
from datetime import datetime

from auth_service.config.auth_config import SECRET_KEY, JWT_ALGORITHM
from auth_service.config.redis_config import redis_client

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
async def logout(
    token: str = Depends(oauth2_scheme)
):
    payload = jwt.decode(token, SECRET_KEY, algorithms=[JWT_ALGORITHM])
    jti = payload.get("jti")
    exp = payload.get("exp")

    now = datetime.utcnow().timestamp()
    ttl = int(exp-now)

    if ttl > 0:
        await redis_client.setex(f"token_bl:{jti}", ttl, "blacklisted")
    
    return {"detail": "Successfully logged out"}