from restaurant_service.schemas.event_base import BaseEvent

class OrderAcceptedByRestaurant(BaseEvent):
    event_type: str = "OrderAcceptedByRestaurant"
    order_id: int
    restaurant_id: int
    estimated_prep_time: int

class OrderCancelledByRestaurant(BaseEvent):
    event_type: str = "OrderCancelledByRestaurant"
    order_id: int
    restaurant_id: int

class OrderReadyByRestaurant(BaseEvent):
    event_type: str = "OrderReadyByRestaurant"
    order_id: int
    restaurant_id: int