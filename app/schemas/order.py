from pydantic import BaseModel, ConfigDict, Field, UUID4
from typing import Optional
from datetime import datetime
from app.schemas.order_item import OrderItemCreate, OrderItemResponse
from app.schemas.global_contraints import PriceDecimal

class OrderCreate(BaseModel):
    restaurant_id: int = Field(
        examples=[10, 20, 30],
        description="The ID of the restaurant from which the order is placed."
    )
    order_items: list[OrderItemCreate] = Field(
        description="A list of items included in the order."
    )
    idempotency_key: UUID4 = Field(
        description="A unique key to ensure idempotency of order creation requests."
    )

class OrderResponse(BaseModel):
    id: int
    user_id: int
    restaurant_id: int
    driver_id: Optional[int] = None
    total_amount: PriceDecimal
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    order_items: list[OrderItemResponse] = []

    model_config = ConfigDict(from_attributes=True)

class OrderListResponse(BaseModel):
    total_counts: int
    last_id: int
    size: int
    orders: list[OrderResponse]