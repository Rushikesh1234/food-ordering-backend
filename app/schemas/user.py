from pydantic import BaseModel, StringConstraints, ConfigDict, Field
from typing import Optional, Annotated
from datetime import datetime
from app.schemas.global_contraints import EmailStr, PasswordStr
from enum import Enum

class UserRole(str, Enum):
    ADMIN = 'admin'
    CUSTOMER = 'customer'
    RESTAURANT_OWNER = 'restaurant_owner'

class UserLogin(BaseModel):
    email: EmailStr = Field(
        examples=["The email address of the user."],
        description="The email address of the user."
    )
    password: PasswordStr = Field(
        examples=["The password for the user account."],
        description="The password for the user account."
    )

class UserCreate(BaseModel):
    email: EmailStr = Field(
        examples=["user@example.com"],
        description="The email address of the user."
    )
    password: PasswordStr = Field(
        examples=["StrongP@ssw0rd"],
        description="The password for the user account."
    )
    role: Annotated[Optional[UserRole], StringConstraints(max_length=50)] = UserRole.CUSTOMER

class UserResponse(BaseModel):
    id: int
    email: EmailStr
    role: UserRole
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    user_id: Optional[int] = None
    role: Optional[UserRole] = None