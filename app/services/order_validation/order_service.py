from sqlalchemy.orm import Session
from fastapi import HTTPException
from decimal import Decimal

from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.user import User

from app.schemas.order import OrderCreate, OrderResponse
from app.schemas.order_events import OrderCreatedEvent, OrderItemPayload

from app.services.order_validation.validate_service import validate_restaurant, validate_menu_items

# from app.events.in_memory_publisher import InMemoryPublisher
from app.events.kafka_publisher import KafkaEventPublisher

from typing import cast

# event_publisher = InMemoryPublisher()
event_publisher = KafkaEventPublisher()

def create_order(db: Session, user: User, order_data: OrderCreate) -> OrderResponse:

    try:
        validate_restaurant(db, order_data.restaurant_id)
        total_amount, validated_items = validate_menu_items(
            db, order_data.restaurant_id, order_data.order_items
        )

        new_order = Order(
            user_id=user.id,
            restaurant_id=order_data.restaurant_id,
            total_amount=total_amount,
            status='CREATED'
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
        
        db.commit()
        # need to refresh db, to pull recently created order_item for kafka loop for event creation
        db.refresh(new_order, attribute_names=['order_items'])

        # For Kafka
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

        return OrderResponse.model_validate(new_order)
    
    except HTTPException as e:
        db.rollback()
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail="Order creation failed") from e
    except Exception as e:
        db.rollback()
        if isinstance(e, Exception):
            raise e
        raise HTTPException(status_code=500, detail="Order creation failed") from e