from auth_service.schemas.event_base import BaseEvent

from auth_service.schemas.global_contraints import EmailStr

class UserCreatedEvent(BaseEvent):
    event_type: str = "UserCreated"
    user_id: int
    role: str
    is_active: bool
    name: EmailStr