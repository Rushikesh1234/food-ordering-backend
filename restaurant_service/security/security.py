import jwt
from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends, HTTPException
from typing import cast

from restaurant_service.config.auth_config import SECRET_KEY, JWT_ALGORITHM
from restaurant_service.config.redis_config import redis_client

from restaurant_service.schemas.user import UserRole, UserAuthSchema

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
async def get_current_user(
        token: str = Depends(oauth2_scheme)
    ) -> UserAuthSchema:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[JWT_ALGORITHM])

        jti = payload.get("jti")
        if await redis_client.exists(f"token_bl:{jti}"):
            raise HTTPException(status_code=401, detail="Token revoked (logged out)")

        user_id = payload.get("sub")
        role = payload.get("role")
        email = payload.get("email")
        restaurant_id = payload.get("restaurant_id")

        if user_id is None or role is None:
            raise HTTPException(status_code=401, detail="Invalid token claims")
        
        return UserAuthSchema(
            id = int(user_id),
            email = email or "",
            role = UserRole(role),
            restaurant_id = restaurant_id
        )
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Could not validate token")


# role-based dependency functions
def require_admin(current_user: UserAuthSchema = Depends(get_current_user)):
    if cast(str, current_user.role) != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin privileges required")
    return current_user

def require_restaurant_owner_or_admin(current_user: UserAuthSchema = Depends(get_current_user)):
    if current_user.role not in [UserRole.RESTAURANT_OWNER, UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Restaurant Owner or Admin privileges required")
    return current_user

def require_customer_or_admin(current_user: UserAuthSchema = Depends(get_current_user)):
    if current_user.role not in [UserRole.CUSTOMER, UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Customer or Admin privileges required")
    return current_user

def require_driver_or_admin(current_user: UserAuthSchema = Depends(get_current_user)):
    if current_user.role not in [UserRole.DRIVER, UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Driver or Admin privileges required")
    return current_user

def require_order_updater(current_user: UserAuthSchema = Depends(get_current_user)):
    if current_user.role not in [UserRole.ADMIN, UserRole.RESTAURANT_OWNER, UserRole.DRIVER, UserRole.SYSTEM]:
        raise HTTPException(status_code=403, detail="Restaurant Owner, Driver or Admin privileges required")
    return current_user