from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import Optional, Annotated
from decimal import Decimal

from restaurant_service.schemas.global_contraints import PriceDecimal

class MenuItemCreate(BaseModel):
    restaurant_id: int = Field(
        examples=[10, 20, 30],
        description="The ID of the restaurant to which the menu item belongs."
    )
    name: str = Field(
        examples=["Margherita Pizza", "California Roll"],
        description="The name of the menu item."
    )
    description: Optional[str] = Field(
        examples=["Classic pizza with tomatoes and mozzarella", "Roll with crab and avocado"],
        description="A brief description of the menu item."
    )
    price: PriceDecimal = Field(
        examples=[Decimal("9.99"), Decimal("12.50")],
        description="The price of the menu item."
    )
    is_available: bool = True

    @field_validator("price", mode="after")
    @classmethod
    def convert_price_to_cents(cls, v: Decimal) -> int:
        return int(v.quantize(Decimal("1.00")) * 100)
    
class MenuItemResponse(BaseModel):
    id: int
    restaurant_id: int
    name: str
    description: Optional[str] = None
    price: PriceDecimal
    is_available: bool

    model_config = ConfigDict(from_attributes=True)

    @field_validator("price", mode="before")
    @classmethod
    def convert_cents_to_decimal(cls, v:int) -> PriceDecimal:
        return Decimal(v) / Decimal(100)
