from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException, Depends
import uuid
from typing import cast, final

from order_service.config.redis_config import redis_client, IDEMPOTENCY_TTL

from order_service.models.order import Order, OrderStatus
from order_service.models.order_item import OrderItem
from order_service.models.outbox import Outbox

from order_service.schemas.user import UserAuthSchema
from order_service.schemas.order import OrderCreate, OrderResponse
from order_service.schemas.order_events import OrderCreatedEvent, OrderItemPayload

from order_service.logic.validate_service import validate_restaurant, validate_menu_items

# We are not going to publish the event directly from the service, 
# instead we will create an entry in the outbox table and 
# a separate process will read from the outbox table and 
# publish the event to Kafka. This is to ensure that if Kafka is down, 
# we don't lose any events and we can retry publishing the events later.

# from app.events.in_memory_publisher import InMemoryPublisher
# from app.events.kafka_publisher import KafkaEventPublisher

# event_publisher = InMemoryPublisher()
# event_publisher = KafkaEventPublisher()

def create_order(
        order_data: OrderCreate,
        db: Session, 
        user: UserAuthSchema
    ) -> OrderResponse:

    redis_idempotency_key = f"idemp:user_{user.id}:{order_data.idempotency_key}"
    db_idempotency_key = str(order_data.idempotency_key)

    is_new = redis_client.set(redis_idempotency_key, "Processing", nx=True, ex=IDEMPOTENCY_TTL)
    if not is_new:
        status = redis_client.get(redis_idempotency_key)
        if status and status == b"Completed":
            existing_order = db.query(Order).filter(Order.idempotency_key == db_idempotency_key).first()
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
            status=OrderStatus.CREATED,
            idempotency_key=db_idempotency_key
        )

        db.add(new_order)
        db.flush()

        event_items_payload = []
        for item in validated_items:
            unit_price_cents = item["price"]

            db_order_item = OrderItem(
                order_id=new_order.id,
                menu_item_id=item["menu_item"].id,
                quantity=item["quantity"],
                price=unit_price_cents
            )
            db.add(db_order_item)

            event_items_payload.append(
                OrderItemPayload(
                    item_id=cast(int, db_order_item.menu_item_id),
                    quantity=cast(int, db_order_item.quantity),
                    price_per_unit=float(unit_price_cents) / 100.0
                )
            )
        
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
            items = event_items_payload,
            total_amount = cast(int, new_order.total_amount)
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

        redis_client.set(redis_idempotency_key, "Completed", ex=IDEMPOTENCY_TTL)
        
        final_order = db.query(Order).options(
            joinedload(Order.order_items).joinedload(OrderItem.menu_item)
        ).filter(Order.id == new_order.id).first()

        return OrderResponse.model_validate(final_order)
    
    except Exception as e:
        db.rollback()
        redis_client.delete(redis_idempotency_key)

        if "unique constraint" in str(e).lower() and "idempotency_key" in str(e).lower():
            retry_order = db.query(Order).filter(
                Order.idempotency_key == db_idempotency_key
            ).first()
            if retry_order: return OrderResponse.model_validate(retry_order)
        if isinstance(e, Exception):
            raise e
        
        print(f"CRITICAL ORDER FAILURE: {str(e)}")
        raise HTTPException(status_code=500, detail="Could not create order and event.") from e