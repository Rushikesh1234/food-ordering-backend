from app.events.base import BaseEvent

class RestaurantCreatedEvent(BaseEvent):
    event_type: str = "RestaurantCreated"
    restaurant_id: int
    restaurant_name: str
    restaurant_address: str
    restaurant_phone_number: str
    owner_id: int
