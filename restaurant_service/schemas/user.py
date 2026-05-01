from pydantic import BaseModel
from typing import Optional
from enum import Enum

class UserRole(str, Enum):
    ADMIN = 'admin'
    CUSTOMER = 'customer'
    RESTAURANT_OWNER = 'restaurant_owner'
    DRIVER = "driver"
    SYSTEM = "system"

class UserAuthSchema(BaseModel):
    id: int
    email:str
    role: UserRole
    restaurant_id: Optional[int] = None