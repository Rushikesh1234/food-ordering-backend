import jwt
from fastapi import HTTPException

from auth_service.schemas.user import TokenResponse

from auth_service.logic.create_access_tokens import create_tokens

from auth_service.config.auth_config import SECRET_KEY, JWT_ALGORITHM

async def refresh_tokens(refresh_token: str) -> TokenResponse:
    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=JWT_ALGORITHM)
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")
        
        user_id = payload.get("sub")
        role = payload.get("role")

        new_access_token, new_refresh_token = create_tokens(user_id, role)

        return TokenResponse.model_validate({
            "access_token": new_access_token, 
            "refresh_token": new_refresh_token, 
            "token_type": "bearer"
        })
    
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Session expired, please login again")