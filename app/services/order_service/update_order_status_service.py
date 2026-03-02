from fastapi import HTTPException
from sqlalchemy.orm import Session
from typing import cast
import uuid

from app.models.order import Order
from app.models.user import User
from app.models.outbox import Outbox

from app.services.order_service.order_state_machine import validate_transitions

# We are not going to publish the event directly from the service, 
# instead we will create an entry in the outbox table and 
# a separate process will read from the outbox table and 
# publish the event to Kafka. This is to ensure that if Kafka is down, 
# we don't lose any events and we can retry publishing the events later.

# from app.events.kafka_publisher import KafkaEventPublisher
# event_publisher = KafkaEventPublisher()

from app.schemas.order_events import OrderStateUpdatedEvent
from app.schemas.user import UserRole

def update_order(
        db: Session, 
        current_user: User, 
        order_id: int, 
        new_status: str, 
        driver_id: int | None = None,
        commit: bool = True
    ):
    try:
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
            if cast(str, current_user.role) not in [UserRole.ADMIN, UserRole.SYSTEM]:
                raise HTTPException(status_code=403, detail="System-only action or Admin access required")
            is_driver = db.query(User).filter(User.id == driver_id, User.role == UserRole.DRIVER).first()
            if not is_driver:
                raise HTTPException(status_code=400, detail="Invalid driver ID")
            if is_driver:
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

        '''
        # This approach of generating or updating a payload and committing it to 
        # the database before creating a Kafka event is generic and easy to implement. 
        # However, there is a major catch and a significant vulnerability: 
        # if the database update succeeds but Kafka is down, 
        # the database will show the order as updated, 
        # but Kafka will never record the event. 
        # Consequently, dependent consumers will never process those orders.
        # 
        # To resolve this, I use the Outbox Pattern, 
        # which helps achieve a Change Data Capture (CDC) methodology. 
        # I create an 'outbox' table in the database to store the Kafka event objects. 
        # By committing the business logic and the outbox entry within 
        # a single database transaction, we ensure that both the state change 
        # and the event are persisted successfully. 
        # This eliminates the risk of 'missing' Kafka jobs or 
        # inconsistent entries between the database and the message broker.

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
        '''

        event_data = OrderStateUpdatedEvent(
            order_id=cast(int, order.id),
            old_status=old_status,
            new_status=new_status,
            user_id=cast(int, order.user_id),
            actor_role=cast(str, current_user.role),
            restaurant_id=cast(int, order.restaurant_id)
        )

        event_entry = Outbox(
            id = uuid.uuid4(),
            aggregatetype = "Order",
            aggregateid = str(order.id),
            type = event_data.event_type,
            payload = event_data.model_dump(mode='json')
        )
        db.add(event_entry)

        if commit:
            db.commit()
            db.refresh(order)
        else:
            db.flush()
        
        return order
    except Exception as e:
        db.rollback()
        if isinstance(e, Exception):
            raise e
        print(f"CRITICAL SYSTEM ERROR: {e}")
        raise HTTPException(status_code=500, detail="Order update and event persistence failed") from e