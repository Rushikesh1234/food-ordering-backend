from sqlalchemy.orm import Session
from fastapi import HTTPException
from decimal import Decimal
import uuid
from typing import cast

from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.order import Outbox
from app.models.user import User

from app.schemas.order import OrderCreate, OrderResponse
from app.schemas.order_events import OrderCreatedEvent, OrderItemPayload

from app.services.order_validation_service.validate_service import validate_restaurant, validate_menu_items

# from app.events.in_memory_publisher import InMemoryPublisher
from app.events.kafka_publisher import KafkaEventPublisher

# event_publisher = InMemoryPublisher()
event_publisher = KafkaEventPublisher()

from app.core.redis_config import redis_client, IDEMPOTENCY_TTL

def create_order(db: Session, user: User, order_data: OrderCreate) -> OrderResponse:

    redis_idempotency_key = f"idemp:user_{user.id}:{order_data.idempotency_key}"

    db_idempotency_key = str(order_data.idempotency_key)

    is_new = redis_client.set(redis_idempotency_key, "Processing", nx=True, ex=IDEMPOTENCY_TTL)

    if not is_new:
        existing_order = db.query(Order).filter(
            Order.idempotency_key == db_idempotency_key
        ).first()

        if existing_order:
            return OrderResponse.model_validate(existing_order)
    
        raise HTTPException(status_code=409, detail="Order is already being processed.")

    try:        
        validate_restaurant(db, order_data.restaurant_id)
        total_amount, validated_items = validate_menu_items(
            db, order_data.restaurant_id, order_data.order_items
        )

        new_order = Order(
            user_id=user.id,
            restaurant_id=order_data.restaurant_id,
            total_amount=total_amount,
            status='CREATED',
            idempotency_key=db_idempotency_key
        )

        db.add(new_order)
        db.flush()

        for item in validated_items:
            order_item = OrderItem(
                order_id=new_order.id,
                menu_item_id=item["menu_item"].id,
                quantity=item["quantity"],
                price=item["price"]
            )
            db.add(order_item)
        
        # need to refresh db, to pull recently created order_item for kafka loop for event creation
        # db.refresh(new_order, attribute_names=['order_items'])
        # I avoid db.refresh(new_order) here for two critical reasons:
        # It prevents an unnecessary SELECT round-trip to the DB since, I already have 'validated_items' in memory.
        # And, second reason, Inside a transaction, I want to minimize the time the database connection is held open, especially for high-scale systems.

        '''
        # For Kafka
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
        try:
            event = OrderCreatedEvent(
                order_id = cast(int, new_order.id),
                user_id = cast(int, user.id),
                restaurant_id = cast(int, new_order.restaurant_id),
                items = [
                    OrderItemPayload(
                        item_id=cast(int, item.menu_item_id),
                        quantity=item.quantity,
                        price_per_unit=float(cast(Decimal, item.price))
                    )
                    for item in new_order.order_items
                ],
                total_amount = float(cast(Decimal,new_order.total_amount))
            )
            event_publisher.publish(event)
        except Exception as e:
            print(f"KAFKA PUBLISH ERROR: {e}")
        '''

        event_data = OrderCreatedEvent(
            order_id = cast(int, new_order.id),
            user_id = cast(int, user.id),
            restaurant_id = cast(int, new_order.restaurant_id),
            items = [
                OrderItemPayload(
                    item_id=cast(int, item.menu_item_id),
                    quantity=item.quantity,
                    price_per_unit=float(cast(Decimal, item.price))
                )
                for item in new_order.order_items
            ],
            total_amount = float(cast(Decimal,new_order.total_amount))
        )
        
        event_entry = Outbox(
            id = uuid.uuid4(),
            aggregatetype = "Order",
            aggregateid = str(new_order.id),
            type = event_data.event_type,
            payload = event_data.model_dump(mode='json')
        )
        db.add(event_entry)

        db.commit()
        db.refresh(new_order)

        redis_client.set(redis_idempotency_key, "Completed", ex=IDEMPOTENCY_TTL)

        return OrderResponse.model_validate(new_order)
    
    except HTTPException as e:
        db.rollback()
        redis_client.delete(redis_idempotency_key)
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail="Order creation failed") from e
    except Exception as e:
        db.rollback()
        redis_client.delete(redis_idempotency_key)
        if "unique constraint" in str(e).lower() and "idempotency_key" in str(e).lower():
            retry_order = db.query(Order).filter(
                Order.idempotency_key == db_idempotency_key
            ).first()
            return OrderResponse.model_validate(retry_order)
        if isinstance(e, Exception):
            raise e
        raise HTTPException(status_code=500, detail="Could not create order and event.") from e