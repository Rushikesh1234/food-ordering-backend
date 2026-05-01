from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import Optional
from decimal import Decimal

from order_service.schemas.global_contraints import PriceDecimal, QuantityInt

class OrderItemCreate(BaseModel):
    menu_item_id: int = Field(
        examples=[100, 200, 300],
        description="The ID of the menu item being ordered."
    )
    quantity: QuantityInt = Field(
        examples=[1, 2, 3],
        description="The quantity of the menu item being ordered."
    )

class OrderMenuItemInfo(BaseModel):
    id: int
    name: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

class OrderItemResponse(BaseModel):
    id: int
    order_id: int
    menu_item_id: int
    quantity: QuantityInt
    price: PriceDecimal

    model_config = ConfigDict(from_attributes=True)

    @field_validator("price", mode="before")
    @classmethod
    def convert_cents_to_decimal(cls, v:int) -> PriceDecimal:
        return Decimal(v) / Decimal(100)
