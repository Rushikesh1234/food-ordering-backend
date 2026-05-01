from datetime import datetime
from pydantic import Field

from driver_service.schemas.event_base import BaseEvent

class DriverAssignedEvent(BaseEvent):
    event_type: str = "DriverAssigned"
    order_id: int
    driver_id: int
    timestamp: datetime = Field(default_factory=datetime.now)