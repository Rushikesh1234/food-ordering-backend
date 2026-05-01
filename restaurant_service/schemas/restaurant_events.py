from restaurant_service.schemas.event_base import BaseEvent

from restaurant_service.schemas.restaurant import ContactSchema, AddressSchema

class RestaurantCreatedEvent(BaseEvent):
    event_type: str = "RestaurantCreated"
    restaurant_id: int
    restaurant_name: str
    restaurant_slug:str
    contact: ContactSchema
    address: AddressSchema
    owner_id: int
    is_active: bool
