from pydantic import BaseModel, Field
from datetime import datetime, timezone
from uuid import uuid4

class BaseEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid4()))
    event_type: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))