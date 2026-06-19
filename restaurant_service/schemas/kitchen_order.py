from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import datetime

class KitchenItem(BaseModel):
    item_id: int
    quantity: int
    price_per_unit: Optional[int] = None

class KitchenOrderResponse(BaseModel):
    id: int
    order_id: int
    restaurant_id: int
    items: List[KitchenItem]
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class KitchenOrdersResponse(BaseModel):
    orders: list[KitchenOrderResponse]