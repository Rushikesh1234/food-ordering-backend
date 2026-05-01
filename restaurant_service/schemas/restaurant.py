from pydantic import BaseModel, ConfigDict, Field, HttpUrl
from typing import Optional, List
from datetime import datetime

from restaurant_service.schemas.global_contraints import MobileNumberStr, EmailStr

class ContactSchema(BaseModel):
    phone: Optional[MobileNumberStr] = Field(
        examples=["+1234567890", "+1987654321"],
        description="The contact phone number of the restaurant."
    )
    email: EmailStr = Field(
        examples=["restaurant@example.com"],
        description="The email address of the restaurant."
    )
    website: Optional[HttpUrl] = None

class GeoSchema(BaseModel):
    lat: float = Field(
        examples=[37.256],
    )
    lon: float = Field(
        examples=[-122.123],
    )
class AddressSchema(BaseModel):
    street: str
    unit: Optional[str] = None
    city: str
    state_code: str
    zip_code: str
    geo: GeoSchema

class SettingsSchema(BaseModel):
    is_accepting_orders: bool = True
    average_prep_time_minutes: int = 15

class RestaurantCreate(BaseModel):
    name: str = Field(
        examples=["Pizza Palace", "Sushi World"],
        description="The name of the restaurant."
    )
    slug: str = Field(
        examples=["starbucks-seattle-100"]
    )
    cuisine_type : List[str] = ["Cafe"]
    address: AddressSchema
    contact: ContactSchema
    settings: SettingsSchema = SettingsSchema()

class RestaurantResponse(RestaurantCreate):
    id: int
    owner_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class RestaurantListResponse(BaseModel):
    total_counts: int
    last_id: int
    size: int
    restaurants: list[RestaurantResponse]
