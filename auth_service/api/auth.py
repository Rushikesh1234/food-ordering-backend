from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from auth_service.schemas.user import UserResponse, UserCreate, UserLogin, TokenResponse

from auth_service.db.session import get_db

from auth_service.logic.login_service import login
from auth_service.logic.register_user_service import register
from auth_service.logic.refresh_token_service import refresh_tokens
from auth_service.logic.logout_service import logout

router = APIRouter()

@router.post("/login", response_model=TokenResponse)
def login_service(
        user: UserLogin, 
        db: Session = Depends(get_db)
    ) -> TokenResponse:
    return login(user, db)

@router.post("/register", response_model=UserResponse)
def register_service(
        user: UserCreate, 
        db: Session = Depends(get_db)
    ) -> UserResponse:
    return register(user, db)

@router.get("/refresh", response_model=TokenResponse)
async def refresh_token_service(
        refresh_token: str
    ) -> TokenResponse:
    return await refresh_tokens(refresh_token)

@router.post("/logout")
async def logout_servie(
        result = Depends(logout)
    ):
    return result