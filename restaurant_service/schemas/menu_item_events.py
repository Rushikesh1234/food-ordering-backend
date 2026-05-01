from restaurant_service.schemas.event_base import BaseEvent

class MenuItemCreatedEvent(BaseEvent):
    event_type: str = "MenuItemCreated"
    menuitem_id: int
    restaurant_id:int
    restaurant_name:str
    menuitem_name: str
    menuitem_description: str
    menuitem_price: int
    menuitem_available: bool