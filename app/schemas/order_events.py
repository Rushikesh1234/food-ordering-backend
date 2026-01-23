from typing import List
from decimal import Decimal
from app.events.base import BaseEvent
from pydantic import BaseModel

class OrderItemPayload(BaseModel):
    item_id: int
    quantity: int
    price_per_unit: float

class OrderCreatedEvent(BaseEvent):
    event_type: str = "OrderCreated"
    order_id: int
    user_id: int
    restaurant_id: int
    items: List[OrderItemPayload]
    total_amount: float

class OrderStateUpdatedEvent(BaseEvent):
    event_type: str = "OrderStatusUpdated"
    order_id: int
    old_status: str
    new_status: str
    user_id: int
    actor_role: str
    restaurant_id: int