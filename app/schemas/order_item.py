from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from app.schemas.global_contraints import PriceDecimal, QuantityInt
from app.schemas.menu_item import MenuItemResponse

class OrderItemCreate(BaseModel):
    menu_item_id: int = Field(
        examples=[100, 200, 300],
        description="The ID of the menu item being ordered."
    )
    quantity: QuantityInt = Field(
        examples=[1, 2, 3],
        description="The quantity of the menu item being ordered."
    )

class OrderItemResponse(BaseModel):
    id: int
    order_id: int
    menu_item: MenuItemResponse
    quantity: QuantityInt
    price: PriceDecimal

    model_config = ConfigDict(from_attributes=True)
