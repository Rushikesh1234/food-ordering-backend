
import jwt, json
from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from typing import cast

from auth_service.config.auth_config import SECRET_KEY, JWT_ALGORITHM
from auth_service.config.redis_config import redis_client

from auth_service.db.session import get_db

from auth_service.models.user import User

from auth_service.schemas.user import UserRole, UserResponse

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
async def get_current_user(
        token: str = Depends(oauth2_scheme), 
        db: Session = Depends(get_db)
    ):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[JWT_ALGORITHM])

        jti = payload.get("jti")
        if await redis_client.exists(f"token_bl:{jti}"):
            raise HTTPException(status_code=401, detail="Token revoked (logged out)")

        user_id = payload.get("sub")
        role = payload.get("role")
        if user_id is None or role is None:
            raise HTTPException(status_code=401, detail="Invalid token")

        user_cache_key = f"user_cache:{user_id}"
        cached_user = await redis_client.get(user_cache_key)

        if cached_user:
            return UserResponse(**json.loads(cached_user))
        
        user = db.query(User).filter(User.id == int(user_id)).first()
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
        
        user_data = UserResponse.model_validate(user)
        await redis_client.setex(user_cache_key, 3600, user_data.model_dump_json())
        
        return user_data
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Could not validate token")


# role-based dependency functions
def require_admin(current_user: UserResponse = Depends(get_current_user)):
    if cast(str, current_user.role) != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin privileges required")
    return current_user

def require_restaurant_owner_or_admin(current_user: UserResponse = Depends(get_current_user)):
    if current_user.role not in [UserRole.RESTAURANT_OWNER, UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Restaurant Owner or Admin privileges required")
    return current_user

def require_customer_or_admin(current_user: UserResponse = Depends(get_current_user)):
    if current_user.role not in [UserRole.CUSTOMER, UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Customer or Admin privileges required")
    return current_user

def require_driver_or_admin(current_user: UserResponse = Depends(get_current_user)):
    if current_user.role not in [UserRole.DRIVER, UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Driver or Admin privileges required")
    return current_user

def require_order_updater(current_user: UserResponse = Depends(get_current_user)):
    if current_user.role not in [UserRole.ADMIN, UserRole.RESTAURANT_OWNER, UserRole.DRIVER, UserRole.SYSTEM]:
        raise HTTPException(status_code=403, detail="Restaurant Owner, Driver or Admin privileges required")
    return current_user