
import jwt
from datetime import datetime, timedelta
import uuid

from auth_service.config.auth_config import SECRET_KEY, JWT_ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES

def create_tokens(user_id: int, role: str):

    access_jti = str(uuid.uuid4())
    access_payload = {
        "sub": str(user_id),
        "role": role,
        "jti": access_jti,
        "exp": datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
        "iat": datetime.utcnow(),
        "type": "access"
    }
    access_token = jwt.encode(access_payload, SECRET_KEY, algorithm=JWT_ALGORITHM)

    refresh_jti = str(uuid.uuid4())
    refresh_payload = {
        "sub": str(user_id),
        "role": role,
        "jti": str(refresh_jti),
        "exp": datetime.utcnow() + timedelta(days=7),
        "iat": datetime.utcnow(),
        "type": "refresh"
    }
    refresh_token = jwt.encode(refresh_payload, SECRET_KEY, algorithm=JWT_ALGORITHM)

    return access_token, refresh_token