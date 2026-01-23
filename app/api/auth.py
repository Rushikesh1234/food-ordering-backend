from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import cast

from app.schemas.user import UserResponse, UserCreate, UserLogin, TokenResponse, TokenData

from app.models.user import User

from app.db.session import get_db

from app.core.security import hash_password, verify_password, create_access_token

router = APIRouter()

@router.post("/login", response_model=TokenResponse)
def login(
    user: UserLogin, 
    db: Session = Depends(get_db)
    ):

    db_user = db.query(User).filter(User.email == user.email).first()

    if not db_user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if not verify_password(user.password, cast(str, db_user.hashed_password)):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token(user_id = cast(int, db_user.id), role = cast(str, db_user.role))

    return {"access_token": token, "token_type": "bearer"}

@router.post("/register", response_model=UserResponse)
def register(
    user: UserCreate, 
    db: Session = Depends(get_db)
    ):
    
    existing_user = db.query(User).filter(User.email == user.email).first()
    
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    new_user = User(
        email=user.email,
        hashed_password=hash_password(user.password),
        role=user.role
    )

    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to register user") from e
    
    return new_user
