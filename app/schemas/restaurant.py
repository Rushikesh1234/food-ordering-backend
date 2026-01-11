from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from app.schemas.global_contraints import MobileNumberStr

class RestaurantCreate(BaseModel):
    name: str = Field(
        examples=["Pizza Palace", "Sushi World"],
        description="The name of the restaurant."
    )
    address: str = Field(
        examples=["123 Main Street", "456 Oak Avenue"],
        description="The address of the restaurant."
    )
    phone_number: Optional[MobileNumberStr] = Field(
        examples=["+1234567890", "+1987654321"],
        description="The contact phone number of the restaurant."
    )

class RestaurantResponse(BaseModel):
    id: int
    name: str
    address: str
    phone_number: Optional[MobileNumberStr] = None

    model_config = ConfigDict(from_attributes=True)

class RestaurantListResponse(BaseModel):
    total_counts: int
    last_id: int
    size: int
    restaurants: list[RestaurantResponse]
