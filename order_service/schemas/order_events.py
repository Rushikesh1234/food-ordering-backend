from typing import List
from decimal import Decimal
from pydantic import BaseModel

from order_service.schemas.event_base import BaseEvent

class OrderItemPayload(BaseModel):
    item_id: int
    quantity: int
    price_per_unit: int

class OrderCreatedEvent(BaseEvent):
    event_type: str = "OrderCreated"
    order_id: int
    user_id: int
    restaurant_id: int
    items: List[OrderItemPayload]
    total_amount: int

class OrderStateUpdatedEvent(BaseEvent):
    event_type: str = "OrderStatusUpdated"
    order_id: int
    old_status: str
    new_status: str
    user_id: int
    actor_role: str
    restaurant_id: int

class OrderPaidEvent(BaseEvent):
    event_type: str = "OrderPaid"
    order_id: int
    user_id: int
    restaurant_id: int
    items: List[OrderItemPayload]
    total_amount: int