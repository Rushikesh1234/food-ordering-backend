from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from typing import cast

from auth_service.db.session import get_db

from auth_service.schemas.user import UserLogin, TokenResponse

from auth_service.models.user import User

from auth_service.logic.password_handler import verify_password
from auth_service.logic.create_access_tokens import create_tokens

def login(
        user: UserLogin, 
        db: Session = Depends(get_db)
    ) -> TokenResponse:

    db_user = db.query(User).filter(User.email == user.email).first()

    if not db_user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if not verify_password(user.password, cast(str, db_user.hashed_password)):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token, refresh_token = create_tokens(user_id = cast(int, db_user.id), role = cast(str, db_user.role))

    return TokenResponse.model_validate({
        "access_token": access_token, 
        "refresh_token": refresh_token, 
        "token_type": "bearer"
    })