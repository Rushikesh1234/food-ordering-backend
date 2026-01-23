from fastapi import HTTPException
from sqlalchemy.orm import Session
from typing import cast

from app.models.order import Order
from app.models.user import User

from app.services.order_validation.order_state_machine import validate_transitions

from app.events.kafka_publisher import KafkaEventPublisher

from app.schemas.order_events import OrderStateUpdatedEvent
from app.schemas.user import UserRole

event_publisher = KafkaEventPublisher()

def update_order_status(db: Session, current_user: User, order_id: int, new_status: str, driver_id: int | None = None):
    order = db.query(Order).filter(Order.id == order_id).first()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    old_status = str(order.status)

    validate_transitions(old_status, new_status)

    if new_status in ["ACCEPTED", "PREPARING", "READY"]:
        if cast(str, current_user.role) == UserRole.RESTAURANT_OWNER:
            if order.restaurant.owner_id != current_user.id:
                raise HTTPException(
                    status_code=403, 
                    detail="You can only update orders for your own restaurant."
                )
        elif cast(str, current_user.role) != UserRole.ADMIN: 
            raise HTTPException(status_code=403, detail="Restaurant or Admin access required")

    if new_status == "ASSIGNED":
        if cast(str, current_user.role) not in [UserRole.ADMIN, UserRole.SYSYEM]:
            raise HTTPException(status_code=403, detail="System-only action or Admin access required")
        if driver_id:
            order.driver_id = driver_id # type: ignore
    
    if new_status in ["PICKED_UP", "DELIVERED"]:
        if cast(str, current_user.role) == UserRole.DRIVER:
            if cast(int, order.driver_id) != current_user.id:
                raise HTTPException(
                    status_code=403, 
                    detail="You cannot update an order that is not assigned to you."
                )
        elif cast(str, current_user.role) != UserRole.ADMIN:
            raise HTTPException(status_code=403, detail="Driver or Admin access required")
        
    order.status = new_status # type: ignore

    db.commit()
    db.refresh(order)

    try:
        event = OrderStateUpdatedEvent(
            order_id=cast(int, order.id),
            old_status=old_status,
            new_status=new_status,
            user_id=cast(int, order.user_id),
            actor_role=cast(str, current_user.role),
            restaurant_id=cast(int, order.restaurant_id)
        )
        event_publisher.publish(event)

    except Exception as e:
        print(f"KAFKA PUBLISH ERROR: {e}")

    return order