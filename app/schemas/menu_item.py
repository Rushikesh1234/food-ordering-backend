from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, Annotated
from decimal import Decimal
from app.schemas.global_contraints import PriceDecimal

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

class MenuItemResponse(BaseModel):
    id: int
    restaurant_id: int
    name: str
    description: Optional[str] = None
    price: PriceDecimal

    model_config = ConfigDict(from_attributes=True)